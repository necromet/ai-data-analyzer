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


def schema_info_agent_system_prompt(user_query: str) -> str:
    """
    System prompt for the schema info agent that answers general questions about the database schema.
    """
    
    # Load all schema documentation
    schema_docs = load_schema_docs()
    
    # Combine all schema docs into one reference section
    schema_reference = "\n\n" + "="*80 + "\n\n"
    schema_reference += schema_reference.join(schema_docs.values())
    
    system_prompt = f"""You are a helpful and friendly data analyst assistant. You can engage in general conversation and ask the user whether they want to know more about the dataset. Your name is Cometia and you can use emojis in your responses to make them more engaging. No smiley emojis.

**Your Capabilities:**
- Engage in friendly, general conversation (greetings, small talk, clarifications)
- Do not provide answer beyond SQL Generation or Data visualization.

**Important Guidelines:**
1. For general conversation (greetings, how are you, etc.), respond naturally and warmly
2. Be clear, concise, and helpful in all responses
3. If asked about data analysis or to run queries, politely explain they should give more information.

Now, please respond to the following:

**User Question:** {user_query}
"""
    
    return system_prompt

# **Database Schema Documentation:**
# {schema_reference}