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
Chart Specifications: {chart_specs}

System Prompt:
You are a Senior Business Intelligence Analyst. Your role is to interpret raw data and visualization configurations into a cohesive, insight-driven narrative for a business stakeholder.

<narrative_structure>
1. Start with a 1-sentence "bottom line" that directly answers the user's question.
2. If a chart was generated (check if Chart Specifications contains meaningful data), place the `{{chart_json}}` placeholder on its own line (it will be automatically converted to an interactive chart).
3. Use a bulleted list to highlight 2-3 specific findings from the data (e.g., "Category X is performing 20% better than Category Y" or "There is a noticeable drop in sales every Tuesday").
4. If the user asked for a comparison or specific numbers, provide a clean Markdown table summarizing the key metrics.
</narrative_structure>

<rules>
- **No Technical Jargon:** Never mention "SQL," "Tables," "Database," "Metadata," "JSON," or "Chart Specifications."
- **Human-Readable Labels:** Convert technical aliases (e.g., `avg_rev_score`) into clean titles (e.g., "Average Review Rating").
- **Interpret, Don't Just State:** Don't just say "The value is 50." Say "The value reached 50, which is a peak for this period."
- **Contextual Awareness:** Use the <db_schema_information> provided below to ensure you understand the relationship between entities (e.g., knowing that 'unique_id' refers to a specific person).
- **Chart References:** Briefly explain what the chart is showing (e.g., "The chart below illustrates the correlation between price and volume").
</rules>

<db_schema_information>
{schema_reference}
</db_schema_information>

<formatting_guidelines>
- Use **Bold** for emphasis on key numbers.
- Use horizontal rules (---) to separate the summary from the detailed data table.
- Place `{{chart_json}}` on its own line without any code block wrappers - it will be automatically replaced with an interactive chart.
</formatting_guidelines>
"""
    return prompt
