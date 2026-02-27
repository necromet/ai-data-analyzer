from pathlib import Path

def load_schema_docs():
    """Load all database schema documentation from db_doc folder."""
    # Get the path to db_doc folder (located under src alongside agent)
    current_file = Path(__file__)
    # agent/ -> src/ -> db_doc
    db_doc_path = current_file.parent.parent / "db_doc"
    
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


def schema_info_agent_system_prompt():
    """
    System prompt for the schema info agent that answers general questions about the database schema.
    """
    # Load all schema documentation
    db_schema_name = "Olist E-Commerce Database"
    schema_docs = load_schema_docs()
    
    # Combine all schema docs into one reference section
    schema_reference = "\n\n" + "="*80 + "\n\n"
    schema_reference += schema_reference.join(schema_docs.values())
    
    system_prompt = f"""Your main goal is to help and engage conversation with user. Do not answer a question if you do not have enough information. Admit it if you don't know. Never answer a question that is not related to the {db_schema_name} schema except for engaging conversation. Always refer to the documentation when answering questions about the schema.

Schema Information on {db_schema_name}:
<schema_reference>
{schema_reference}
</schema_reference>
"""
    
    return system_prompt