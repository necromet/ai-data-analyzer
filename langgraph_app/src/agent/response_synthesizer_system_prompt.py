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

def response_synthesizer_system_prompt(user_input: str, chart_specs: object, metadata:object) -> str:
    """This is the system prompt for the data visualization agent."""

    # Load all schema documentation
    schema_docs = load_schema_docs()
    
    # Combine all schema docs into one reference section
    schema_reference = "\n\n".join(schema_docs.values())
    
    prompt = f"""
User Input: {user_input}
Metadata: {metadata}

Chart Specifications:
{chart_specs}

System Prompt:
You are a response synthesizer agent; given user input. chart specifications, and metadata. Your task is to synthesize a concise and clear response to the user input based on the data provided. Use {{chart_json_(index)}} as a placeholder for the chart JSON object; No literal echarts option object. Replace index with the index number of chart specifications. Instead of column names like cust_uid, use descriptive terms like 'Customer ID' in your response. 

<db_schema_information>
{schema_reference}
</db_schema_information>

Suggestion for synthesis:
- Visualization can be in the top or in-line with text. Integrate it with the rest of the paragraph.
- Reference database schema information to better understand the data context.
- Create table for metadata so that the user can easily read it.
- Reference chart specifications when describing the chart.
- Ensure the response is relevant to the user input.
- Explain key insights from metadata.
- Do not create assumptions beyond the provided data.
- The response should be in a paragraph format. Use less bullet points. You can use bullet points sparingly for clarity.
"""
    return prompt
