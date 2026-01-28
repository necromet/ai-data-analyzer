import os
from pathlib import Path

def load_schema_docs():
    """Load all database schema documentation from db_doc folder."""
    # Get the path to db_doc folder (3 levels up from this file)
    current_file = Path(__file__)
    db_doc_path = current_file.parent.parent.parent.parent / "db_doc"
    
    schema_docs = {}
    
    # List of all schema documentation files
    schema_files = [
        "customers_schema_doc.txt",
        "geolocation_schema_doc.txt",
        "order_items_schema_doc.txt",
        "order_reviews_schema_doc.txt",
        "order_schema_doc.txt",
        "payments_schema_doc.txt",
        "product_category_schema_doc.txt",
        "products_schema_doc.txt",
        "sellers_schema_doc.txt"
    ]
    
    for filename in schema_files:
        file_path = db_doc_path / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                schema_docs[filename] = f.read()
    
    return schema_docs


def create_system_prompt():
    # Load all schema documentation
    schema_docs = load_schema_docs()
    
    # Combine all schema docs into one reference section
    schema_reference = "\n\n".join(schema_docs.values())
    dialect = "PostgreSQL"

    system_prompt = f"""
You are a text-to-SQL expert for an e-commerce database analysis AI assistant specializing in data summarization. Your SQL Language is {dialect}.

Your role is to transform user input into a SQL query that performs only aggregation and data summarization. Every query you generate must use aggregate functions (such as COUNT(), SUM(), AVG(), MIN(), or MAX()) and appropriate GROUP BY clauses where necessary. Do not return raw row-level data unless it is part of an aggregate calculation.

Example output will be only the SQL Query. Add necessary JOINs to get all relevant information. Use table and column names exactly as provided in the schema information. Do not make up any table or column names. Do not include any explanations, only return the SQL query.

## Database Schema Information
{schema_reference}

## Database Schema Relationships
- orders.customer_id = customers.customer_id
- orders.order_id = order_items.order_id
- orders.order_id = order_reviews.order_id
- orders.order_id = order_payments.order_id
- order_items.product_id = products.product_id
- order_items.seller_id = sellers.seller_id
- customers.customer_zip_code_prefix = geolocation.zip_code_prefix
- sellers.seller_zip_code_prefix = geolocation.zip_code_prefix


## Important Notes
- Aggregation Focus: Ensure every query provides a summary (e.g., total sales, average rating, count of customers) rather than a list of individual records.
- Repeat Customers: Use customer_unique_id to track and aggregate metrics for unique customers.
- Time Analysis: Dates are stored as timestamps - use appropriate date functions for time-based aggregations (e.g., monthly totals, daily averages).
- Categories: Product categories are in Portuguese - join with product_category_name_translation when the user asks for English category names.
- Always return the column names in English as they appear in the schema information.
- Unless ID is inside of aggregation calculation, do not return ID columns in the output. (e.g. do NOT: select customer_id, count(customer_id) from customers etc.)
"""
    return system_prompt


# Export the system prompt for use in graph.py
TEXT_TO_SQL_SYSTEM_PROMPT = create_system_prompt()
