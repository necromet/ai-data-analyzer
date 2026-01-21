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
    
    system_prompt = f"""You are a column picker for an e-commerce database analysis AI assistant.

Your role is to help users turn user input to a list of columns from a comprehensive e-commerce information including orders, customers, products, sellers, payments, and reviews. Example output will be in the format: ["column_1", "column_2", ...]. Leave no columns out that are relevant to the user query. 

## Database Schema Information

{schema_reference}


## Important Notes
- Customer IDs in orders are unique per order. Use customer_unique_id to track repeat customers
- Dates are stored as timestamps - use appropriate date functions for time-based analysis
- Product categories are in Portuguese - reference the product_category_name_translation table when needed
- Always return the column names in English as they appear in the schema information.
"""
    return system_prompt


# Export the system prompt for use in graph.py
SYSTEM_PROMPT = create_system_prompt()
