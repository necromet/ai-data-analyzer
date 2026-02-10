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

def planner_agent_system_prompt(user_input: str, chat_history: list = None):
    # Load all schema documentation
    schema_docs = load_schema_docs()
    
    # Combine all schema docs into one reference section
    schema_reference = "\n\n".join(schema_docs.values())
    example = example_output()
    
    # Format chat history for context
    chat_history_text = ""
    if chat_history:
        chat_history_text = "\n<chat_history>\n"
        for entry in chat_history:
            user_msg = entry.get("user_input", "")
            assistant_msg = entry.get("final_response", "")
            timestamp = entry.get("timestamp", "")
            chat_history_text += f"[{timestamp}]\nUser: {user_msg}\nAssistant: {assistant_msg}\n\n"
        chat_history_text += "</chat_history>\n\n"

    system_prompt = f"""
Input: {user_input}
{chat_history_text}
System Prompt:
Your task is to create 1 simple task(s) relevant on the user's input; either to generate SQL Queries or Visualization. Each task should be clear and concise. Prioritize tasks that involve data exploration, SQL query generation, and visualization creation.

If chat history is provided, use it to:
- Understand context from previous queries and responses
- Avoid redundant tasks that were already completed
- Build on previous analyses when appropriate
- Maintain continuity in the conversation

<rules>
- Do not write any SQL queries directly.
- Do not include any other explanations outside of the to do list.
- Each to do item should focus on a single task.
- Only 1 SQL Query or 1 Visualization per to do item.
- Flag each item whether it requires SQL generation and visualization creation. Follow example output for flagging format. If visualization is true, SQL must also be true.
- Numbering format
- Simple and focused 
- No assumption
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
- Ensure every query provides a summary (e.g., total sales, average rating, count of customers) rather than a list of individual records.
- Use customer_unique_id (customers table) to track and aggregate metrics for unique customers.
- Categories: Product categories are in Portuguese - join with product_category_name_translation when the user asks for English category names.
- Never do "SELECT *" queries.
</important_notes>
"""
    return system_prompt
