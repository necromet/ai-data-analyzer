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


def generate_sql_system_prompt(user_input: str) -> str:
    # Load all schema documentation
    schema_docs = load_schema_docs()
    
    # Combine all schema docs into one reference section
    schema_reference = "\n\n".join(schema_docs.values())
    dialect = "DuckDB SQL"

    system_prompt = f"""
Input: {user_input}

System Prompt:
You are a text-to-SQL expert for an e-commerce database specializing in data summarization. 
SQL Language: {dialect}.

Given:
- Input

Your role:
<role>
- Transform input to a SQL query for aggregation and data summarization only.
- Output: SQL Query
- Never GROUP BY with identifier (customer_id, seller_id, etc). 
- Never create raw row-level data.
- Never do "SELECT *" queries.
- Forbidden Statements: 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE', 'MERGE', 'COMMIT'
- No explanations, pleasantries, or additional text.
- Do not make up any table or column names.
</role>

<database_schema_info>
{schema_reference}
</database_schema_info>

<database_schema_relationships>
- orders.customer_id = customers.customer_id
- orders.order_id = order_items.order_id
- orders.order_id = order_reviews.order_id
- orders.order_id = order_payments.order_id
- order_items.product_id = products.product_id
- order_items.seller_id = sellers.seller_id
- customers.customer_zip_code_prefix = geolocation.zip_code_prefix
- sellers.seller_zip_code_prefix = geolocation.zip_code_prefix
</database_schema_relationships>

<important_notes>
- Repeat Customers: Use customer_unique_id.
- Time Analysis: Use appropriate date functions for time-based aggregations (e.g., monthly totals, daily averages).
- Categories: Product categories are in Portuguese - join with product_category_name_translation.
</important_notes>
"""
    return system_prompt