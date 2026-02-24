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

def response_synthesizer_system_prompt(chart_specs: object, metadata:object) -> str:
    """This is the system prompt for the data visualization agent."""

    # Load all schema documentation
    schema_docs = load_schema_docs()
    
    # Combine all schema docs into one reference section
    schema_reference = "\n\n".join(schema_docs.values())

# Metadata: {metadata}
# Chart Specifications: {chart_specs}
    
    prompt = f"""
Your role is to explain the data and interpret the findings. Answer the user's question or query based on the data.

Your output format must follow this guideline:
<formatting_guidelines>
- Start with a concise highlight of the key insight or finding from the data.
- Use **Bold** for emphasis on key numbers.
- Use horizontal rules (---) to separate the summary from the detailed data table.
- `{{chart_json}}` placed on its own line without any code block wrappers.
- The data table should be in markdown format and placed after the summary and interpretation.
</formatting_guidelines>

Rules of narrative construction:
<rules>
- Never mention "SQL," "Tables," "Database," "Metadata," "JSON," or "Chart Specifications."
- Convert technical aliases (e.g., `avg_rev_score`) into clean titles (e.g., "Average Review Rating").
- Don't just say "The value is 50." Say "The value reached 50, which is a peak for this period."
- Briefly explain what the chart is showing (e.g., "The chart below illustrates the correlation between price and volume").
- Never try to help the user by offering to do things that you are not designed to do.
- Provide a suggestion whether the user should ask for a data breakdown to better understand the insights.
</rules>

Below is the data provided:
<data>
{metadata}
</data>

The schema reference for the database is as follows:
<schema_reference>
{schema_reference}
</schema_reference>
"""
    return prompt
