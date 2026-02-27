#!/usr/bin/env python3
"""
Import CSV data from olist_data directory to PostgreSQL database.

Usage:
    python import_csv_to_postgresql.py

Requirements:
    - PostgreSQL database named 'edward_local' must exist
    - pip install pandas psycopg2-binary
"""

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from pathlib import Path
from typing import Dict, Optional
import argparse
import getpass
import sys


def import_csv_to_postgresql(
    db_name: str = "edward_local",
    host: str = "localhost",
    port: int = 5432,
    user: str = "postgres",
    password: str = "",
    data_dir: Optional[str] = None,
    schema: str = "public"
):
    """
    Import CSV data from olist_data directory to PostgreSQL database.
    
    Args:
        db_name: Name of the PostgreSQL database (default: edward_local)
        host: PostgreSQL server host (default: localhost)
        port: PostgreSQL server port (default: 5432)
        user: PostgreSQL username (default: postgres)
        password: PostgreSQL password
        data_dir: Path to CSV data directory (default: ./olist_data)
    
    Returns:
        bool: True if import successful, False otherwise
    """
    
    # allow overriding parameters via environment variables (used by the
    # docker helper container).  the CLI flags still take precedence.
    db_name = os.getenv("POSTGRES_DB", db_name)
    host = os.getenv("POSTGRES_HOST", host)
    port = int(os.getenv("POSTGRES_PORT", port))
    user = os.getenv("POSTGRES_USER", user)
    password = os.getenv("POSTGRES_PASSWORD", password)
    schema = os.getenv("POSTGRES_SCHEMA", schema)

    # Set data directory
    if data_dir is None:
        data_dir = Path(__file__).parent / "olist_data"
    else:
        data_dir = Path(data_dir)
    
    # Mapping of table names to CSV files
    datasets = {
        'customers': 'olist_customers_dataset.csv',
        'geolocation': 'olist_geolocation_dataset.csv',
        'order_items': 'olist_order_items_dataset.csv',
        'order_payments': 'olist_order_payments_dataset.csv',
        'order_reviews': 'olist_order_reviews_dataset.csv',
        'orders': 'olist_orders_dataset.csv',
        'products': 'olist_products_dataset.csv',
        'sellers': 'olist_sellers_dataset.csv',
        'product_category_translation': 'product_category_name_translation.csv'
    }
    
    # Define table schemas with proper PostgreSQL data types
    table_schemas = {
        'customers': """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id VARCHAR(50) PRIMARY KEY,
                customer_unique_id VARCHAR(50),
                customer_zip_code_prefix VARCHAR(10),
                customer_city VARCHAR(100),
                customer_state VARCHAR(2)
            )
        """,
        'geolocation': """
            CREATE TABLE IF NOT EXISTS geolocation (
                id SERIAL PRIMARY KEY,
                geolocation_zip_code_prefix VARCHAR(10),
                geolocation_lat NUMERIC(10, 7),
                geolocation_lng NUMERIC(10, 7),
                geolocation_city VARCHAR(100),
                geolocation_state VARCHAR(2)
            )
        """,
        'orders': """
            CREATE TABLE IF NOT EXISTS orders (
                order_id VARCHAR(50) PRIMARY KEY,
                customer_id VARCHAR(50),
                order_status VARCHAR(20),
                order_purchase_timestamp TIMESTAMP,
                order_approved_at TIMESTAMP,
                order_delivered_carrier_date TIMESTAMP,
                order_delivered_customer_date TIMESTAMP,
                order_estimated_delivery_date TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """,
        'products': """
            CREATE TABLE IF NOT EXISTS products (
                product_id VARCHAR(50) PRIMARY KEY,
                product_category_name VARCHAR(100),
                product_name_lenght INTEGER,
                product_description_lenght INTEGER,
                product_photos_qty INTEGER,
                product_weight_g INTEGER,
                product_length_cm INTEGER,
                product_height_cm INTEGER,
                product_width_cm INTEGER
            )
        """,
        'sellers': """
            CREATE TABLE IF NOT EXISTS sellers (
                seller_id VARCHAR(50) PRIMARY KEY,
                seller_zip_code_prefix VARCHAR(10),
                seller_city VARCHAR(100),
                seller_state VARCHAR(2)
            )
        """,
        'order_items': """
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id VARCHAR(50),
                order_item_id INTEGER,
                product_id VARCHAR(50),
                seller_id VARCHAR(50),
                shipping_limit_date TIMESTAMP,
                price NUMERIC(10, 2),
                freight_value NUMERIC(10, 2),
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                FOREIGN KEY (seller_id) REFERENCES sellers(seller_id),
                UNIQUE (order_id, order_item_id)
            )
        """,
        'order_payments': """
            CREATE TABLE IF NOT EXISTS order_payments (
                id SERIAL PRIMARY KEY,
                order_id VARCHAR(50),
                payment_sequential INTEGER,
                payment_type VARCHAR(20),
                payment_installments INTEGER,
                payment_value NUMERIC(10, 2),
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                UNIQUE (order_id, payment_sequential)
            )
        """,
        'order_reviews': """
            CREATE TABLE IF NOT EXISTS order_reviews (
                review_id VARCHAR(50) PRIMARY KEY,
                order_id VARCHAR(50),
                review_score INTEGER,
                review_comment_title TEXT,
                review_comment_message TEXT,
                review_creation_date TIMESTAMP,
                review_answer_timestamp TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        """,
        'product_category_translation': """
            CREATE TABLE IF NOT EXISTS product_category_translation (
                product_category_name VARCHAR(100) PRIMARY KEY,
                product_category_name_english VARCHAR(100)
            )
        """
    }
    
    # Order of table creation (respecting foreign key dependencies)
    table_order = [
        'customers',
        'orders',
        'products',
        'sellers',
        'geolocation',
        'product_category_translation',
        'order_items',
        'order_payments',
        'order_reviews'
    ]
    
    conn = None
    cursor = None
    
    try:
        # Connect to PostgreSQL
        print(f"Connecting to PostgreSQL database '{db_name}' at {host}:{port}...")
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cursor = conn.cursor()
        print("✓ Connected successfully!\n")

        # ensure the target schema exists and configure search_path
        if schema and schema != "public":
            cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {};").format(sql.Identifier(schema)))
            cursor.execute(sql.SQL("SET search_path TO {}, public;").format(sql.Identifier(schema)))

        # if the customers table already has rows in this schema, skip work
        cursor.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema=%s AND table_name='customers';",
            (schema,)
        )
        if cursor.fetchone()[0] > 0:
            cursor.execute(sql.SQL("SELECT count(*) FROM {}.customers").format(sql.Identifier(schema)))
            if cursor.fetchone()[0] > 0:
                print("database appears to be populated, skipping import.")
                return True

        # Create tables in order (they'll be created in the active schema due
        # to search_path settings above).
        print("Creating tables...")
        for table_name in table_order:
            if table_name in table_schemas:
                cursor.execute(table_schemas[table_name])
                print(f"  ✓ Created/verified table '{table_name}'")
        conn.commit()
        print()
        
        # Import data from CSVs
        print("Importing data from CSV files...")
        print("=" * 60)
        
        # primary key columns used for deduplication/conflict handling
        primary_keys: Dict[str, Optional[list]] = {
            'customers': ['customer_id'],
            'orders': ['order_id'],
            'products': ['product_id'],
            'sellers': ['seller_id'],
            'geolocation': None,
            'product_category_translation': ['product_category_name'],
            'order_items': ['order_id', 'order_item_id'],
            'order_payments': ['order_id', 'payment_sequential'],
            'order_reviews': ['review_id'],
        }

        for table_name in table_order:
            if table_name not in datasets:
                continue

            csv_file = datasets[table_name]
            csv_path = data_dir / csv_file

            if not csv_path.exists():
                print(f"⚠ Warning: {csv_file} not found, skipping...")
                continue

            print(f"\nProcessing {csv_file}...")

            # Read CSV file
            # parse dates and sanitize NaN/blank strings before further processing
            df = pd.read_csv(csv_path)

            # Replace any literal 'NaN' or empty-string values with None so that
            # psycopg2 will send NULL instead of trying to coerce some
            # non-numeric representation.  Blank strings often appear in the raw
            # datasets for missing timestamps/fields.
            df = df.replace({
                r'^\s*NaN\s*$': None,
                r'^\s*$': None,
            }, regex=True)

            # Convert date/time columns for this table to proper datetime dtype.
            # NaT results from coercion of bad/missing dates; we'll fix those
            # explicitly afterwards so they aren't passed to the database.
            datetime_cols = {
                'orders': [
                    'order_purchase_timestamp',
                    'order_approved_at',
                    'order_delivered_carrier_date',
                    'order_delivered_customer_date',
                    'order_estimated_delivery_date',
                ],
                'order_items': ['shipping_limit_date'],
                'order_reviews': ['review_creation_date', 'review_answer_timestamp'],
            }
            for col in datetime_cols.get(table_name, []):
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            # Replace any literal 'NaT' strings with None as well.
            df = df.replace({r'^NaT$': None}, regex=True)

            # drop duplicates based on the primary key(s) so we never try to insert
            # the same logical record twice; the SQL conflict clause below also
            # guards against it, but it's convenient to know when the CSV itself
            # contains duplicates.
            pk = primary_keys.get(table_name)
            if pk:
                before = len(df)
                df = df.drop_duplicates(subset=pk)
                removed = before - len(df)
                if removed:
                    print(f"  ⚠ Dropped {removed} duplicate rows based on PK {pk}")

            print(f"  - Rows: {len(df):,}")
            print(f"  - Columns: {list(df.columns)}")
            
            # Clear existing data
            cursor.execute(f"DELETE FROM {table_name}")
            
            # Prepare column names
            columns = list(df.columns)
            
            # For tables with SERIAL primary key, exclude it from insert
            if table_name in ['geolocation', 'order_items', 'order_payments']:
                insert_columns = columns
            else:
                insert_columns = columns
            
            # Prepare insert query; include ON CONFLICT DO NOTHING if we know the
            # primary key columns for this table.
            pk = primary_keys.get(table_name)
            if pk:
                insert_query = sql.SQL(
                    "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO NOTHING"
                ).format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(map(sql.Identifier, insert_columns)),
                    sql.SQL(', ').join(sql.Placeholder() * len(insert_columns)),
                    sql.SQL(', ').join(map(sql.Identifier, pk)),
                )
            else:
                insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(map(sql.Identifier, insert_columns)),
                    sql.SQL(', ').join(sql.Placeholder() * len(insert_columns))
                )
            
            # Convert DataFrame to object dtype and replace any remaining
            # pandas NaT/NaN values with None.  Using astype(object) forces the
            # conversion so datetime NaT values don't get preserved as a special
            # type that psycopg2 would stringify as 'NaT'.
            df = df.astype(object).where(pd.notnull(df), None)
            records = []
            # build records manually to ensure all NaT-like objects are cleaned
            for row in df.itertuples(index=False, name=None):
                cleaned = tuple(None if pd.isna(v) else v for v in row)
                records.append(cleaned)
            
            # Batch insert
            batch_size = 1000
            total_inserted = 0
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                cursor.executemany(insert_query, batch)
                total_inserted += len(batch)
                if i % 10000 == 0 and i > 0:
                    print(f"  - Inserted {total_inserted:,} rows so far...")
            
            conn.commit()
            print(f"  ✓ Imported {total_inserted:,} rows to '{table_name}'")
        
        # Create indexes for better query performance
        print("\n" + "=" * 60)
        print("Creating indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_customers_unique_id ON customers(customer_unique_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status)",
            "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)",
            "CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_order_items_seller_id ON order_items(seller_id)",
            "CREATE INDEX IF NOT EXISTS idx_order_payments_order_id ON order_payments(order_id)",
            "CREATE INDEX IF NOT EXISTS idx_order_reviews_order_id ON order_reviews(order_id)",
            "CREATE INDEX IF NOT EXISTS idx_geolocation_zip ON geolocation(geolocation_zip_code_prefix)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
            index_name = index_sql.split('idx_')[1].split(' ON')[0]
            print(f"  ✓ {index_name}")
        
        conn.commit()
        
        # Show summary
        print("\n" + "=" * 60)
        print("DATABASE IMPORT SUMMARY")
        print("=" * 60)
        
        for table_name in table_order:
            qualified = f"{schema}.{table_name}" if schema and schema != "public" else table_name
            cursor.execute(f"SELECT COUNT(*) FROM {qualified}")
            count = cursor.fetchone()[0]
            print(f"  {qualified:30s}: {count:,} rows")
        
        print("\n✓ Data import completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("\n✓ Database connection closed.")


def main():
    """Main function to parse arguments and run the import."""
    parser = argparse.ArgumentParser(
        description='Import Olist CSV data to PostgreSQL database'
    )
    parser.add_argument(
        '--db-name',
        default='edward_local',
        help='PostgreSQL database name (default: edward_local)'
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='PostgreSQL host (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5432,
        help='PostgreSQL port (default: 5432)'
    )
    parser.add_argument(
        '--user',
        default='postgres',
        help='PostgreSQL username (default: postgres)'
    )
    parser.add_argument(
        '--password',
        help='PostgreSQL password (will prompt if not provided)'
    )
    parser.add_argument(
        '--data-dir',
        default='olist_data',
        help='Path to CSV data directory (default: olist_data)'
    )
    parser.add_argument(
        '--schema',
        default='public',
        help='Target PostgreSQL schema (default: public)'
    )
    
    args = parser.parse_args()
    
    # Determine password: CLI argument > environment (PGPASSWORD or POSTGRES_PASSWORD) > prompt
    password = (
        args.password
        or os.environ.get("PGPASSWORD")
        or os.environ.get("POSTGRES_PASSWORD")
    )
    if not password:
        # only prompt if running in a TTY; otherwise abort
        if sys.stdin.isatty():
            password = getpass.getpass(f"PostgreSQL password for user '{args.user}': ")
        else:
            sys.stderr.write(
                "Error: no password supplied (use --password or set PGPASSWORD/POSTGRES_PASSWORD) and cannot prompt in non-interactive mode.\n"
            )
            return 1
    
    # Run import
    success = import_csv_to_postgresql(
        db_name=args.db_name,
        host=args.host,
        port=args.port,
        user=args.user,
        password=password,
        data_dir=args.data_dir,
        schema=args.schema
    )
    
    if success:
        print("\n🎉 All data has been successfully imported to the database!")
        return 0
    else:
        print("\n❌ Import failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    exit(main())
