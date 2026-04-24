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

def response_synthesizer_system_prompt(chart_specs: object = None, metadata: object = None) -> str:
    """System prompt for the response synthesizer agent."""

    if chart_specs is None:
        chart_specs = ""
    if metadata is None:
        metadata = {}

    # Load all schema documentation
    schema_docs = load_schema_docs()
    
    # Combine all schema docs into one reference section
    schema_reference = "\n\n".join(schema_docs.values())

    has_chart = bool(chart_specs)
    has_data = bool(metadata.get("data_sample"))

    prompt = f"""You are a data analyst assistant. Your job is to interpret the results of a data query and respond to the user in a clear, natural way.

The user asked a question. The data has already been queried and the results are provided below. Your job is to answer their question based on what the data shows.

Guidelines:
- Write like you're explaining findings to a colleague — conversational but precise.
- Lead with the answer. If someone asked "what's the average order value?", start with the number, then add context.
- Use **bold** to highlight key numbers, names, or takeaways.
- When the data reveals something interesting (a trend, an outlier, a surprising pattern), call it out naturally.
- Convert technical column names into plain language (e.g., "avg_rev_score" → "average review rating").
- If a chart is available, reference it naturally (e.g., "as shown in the chart below" or "the chart illustrates..."). Place `{{chart_json}}` on its own line where you want the chart to appear — no code fences around it.
- Include a data table only when it helps the reader — for example, when there are multiple items to compare, or when the exact numbers matter. Skip it for simple answers.
- Never mention SQL, databases, tables, metadata, JSON, or any technical implementation details.
- Never offer to do things outside your role (e.g., "let me run another query").
- Never include chart configuration details (title, type, axes) in your text — just place `{{chart_json}}` where the chart should render.

{f"""The query results are below:
<data>
{metadata}
</data>""" if has_data else ""}

{f"""A visualization was generated for this data. Include `{{chart_json}}` in your response where the chart should appear.""" if has_chart else ""}

{f"""Database schema reference (for understanding column meanings):
<schema_reference>
{schema_reference}
</schema_reference>""" if schema_reference.strip() else ""}"""

    return prompt
