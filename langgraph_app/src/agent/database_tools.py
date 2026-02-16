import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import threading
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PostgreSQL connection parameters
# You can customize these or use environment variables
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "edward_local"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "schema": os.getenv("POSTGRES_SCHEMA", "olist_db")  # Default to 'public' schema
}

# Thread-local storage for database connections
thread_local = threading.local()

def get_db_connection():
    """Get a thread-safe PostgreSQL database connection for LangGraph.
    
    This function uses thread-local storage to ensure each thread
    has its own database connection, which is essential for LangGraph's
    concurrent execution model.
    
    Returns:
        psycopg2 connection object
    """
    if not hasattr(thread_local, "conn") or thread_local.conn is None or thread_local.conn.closed:
        print(f" ! Attempting to connect to PostgreSQL database...")
        try:
            conn = psycopg2.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                database=DB_CONFIG["database"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"]
            )
            # Set autocommit mode for read-only SELECT queries
            conn.autocommit = True
            
            # Set search_path to the specified schema
            if DB_CONFIG["schema"] and DB_CONFIG["schema"] != "public":
                cursor = conn.cursor()
                cursor.execute(f"SET search_path TO {DB_CONFIG['schema']}, public;")
                cursor.close()
                print(f" ! Schema set to: {DB_CONFIG['schema']}")
            
            thread_local.conn = conn
            print(f" ! PostgreSQL connected successfully: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
        except Exception as e:
            raise Exception(f"Failed to connect to PostgreSQL database: {e}")
    
    return thread_local.conn

def connect_db(host: str = None, port: int = None, database: str = None, user: str = None, password: str = None, schema: str = None):
    """Connect to PostgreSQL database with custom parameters.
    
    Args:
        host: PostgreSQL host (default: from DB_CONFIG)
        port: PostgreSQL port (default: from DB_CONFIG)
        database: Database name (default: from DB_CONFIG)
        user: Username (default: from DB_CONFIG)
        password: Password (default: from DB_CONFIG)
        schema: Schema name (default: from DB_CONFIG)
    
    Returns:
        psycopg2 connection object
    """
    conn = psycopg2.connect(
        host=host or DB_CONFIG["host"],
        port=port or DB_CONFIG["port"],
        database=database or DB_CONFIG["database"],
        user=user or DB_CONFIG["user"],
        password=password or DB_CONFIG["password"]
    )
    
    # Set search_path if schema is specified
    schema_to_use = schema or DB_CONFIG["schema"]
    if schema_to_use and schema_to_use != "public":
        cursor = conn.cursor()
        cursor.execute(f"SET search_path TO {schema_to_use}, public;")
        cursor.close()
    
    print(f" ! PostgreSQL database connected: {database or DB_CONFIG['database']}")
    return conn
