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

def example_output():
    """Example output for planner agent system prompt."""
    example_output = """{
    "to_do_list": [
        {
            "item_no": 0,
            "visualization": true,
            "sql_required": true, 
            "task": "Identify ..."
        },
        {
            "item_no": 1,
            "visualization": false,
            "sql_required": true, 
            "task": "For the ..."
        },
        ...
    ]
}
"""
    return example_output

def planner_agent_system_prompt(user_input: str):
    # Load all schema documentation
    schema_docs = load_schema_docs()
    
    # Combine all schema docs into one reference section
    schema_reference = "\n\n".join(schema_docs.values())
    example = example_output()

    system_prompt = f"""
Input: {user_input}

System Prompt:
Your task is to create 1 to 3 to do list relevant on the user's input to generate insights or analysis based on data and visualization. Each to do item should be a clear and concise action that contributes to achieving the overall analysis goal. Prioritize tasks that involve data exploration, SQL query generation, and visualization creation.

<rules>
- Do not write any SQL queries directly.
- Do not include any other explanations outside of the to do list.
- Each to do item should be actionable and specific.
- Each to do item should focus on a single task.
- Flag each item whether it requires SQL generation and visualization creation. Follow example output for flagging format. If visualization is true, SQL must also be true.
- Only create to do list items in numbering format.
- Do not overcomplicate the to do list; keep it simple and focused. Do not assume any information beyond the user input.
</rules>

<example_output>
{example}
</example_output>

<db_schema_information>
{schema_reference}
</db_schema_information>

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
- Aggregation Focus: Ensure every query provides a summary (e.g., total sales, average rating, count of customers) rather than a list of individual records.
- Repeat Customers: Use customer_unique_id to track and aggregate metrics for unique customers.
- Time Analysis: Dates are stored as timestamps - use appropriate date functions for time-based aggregations (e.g., monthly totals, daily averages).
- Categories: Product categories are in Portuguese - join with product_category_name_translation when the user asks for English category names.
- Always return the column names in English as they appear in the schema information.
- Never do "SELECT *" queries.
</important_notes>
"""
    return system_prompt
