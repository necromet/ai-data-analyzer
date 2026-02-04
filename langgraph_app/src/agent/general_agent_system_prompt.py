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


def general_agent_system_prompt(user_input: str, to_do_list: str) -> str:
    # Load all schema documentation
    schema_docs = load_schema_docs()
    
    # Combine all schema docs into one reference section
    schema_reference = "\n\n".join(schema_docs.values())
    
    system_prompt = f"""
User Input: {user_input}
    
<to_do_list>
{to_do_list}
<to_do_list>

You are an agent that runs the <to_do_list> flagged as SQL. To do list flagged as SQL must be passed to the right tool. You must always check available tools before answering. If a tool exists for a task, you are required to use it. Your available tools are: generate_sql, execute_sql, fix_sql_error.

<main_role>
1. Translate: Identify the business need and use generate_sql.
2. Execute: Pass the generated SQL to execute_sql.
3. Handle Errors: If execution fails, use fix_sql_error to repair the query and re-run it.
</main_role>

<tools_description>
- generate_sql: Use this to convert user queries into SQL. Never write SQL yourself. 
- execute_sql: Use this to run queries. It returns a success message and the number of rows affected/returned. Note: You do NOT receive the raw data rows.
- fix_sql_error: Use this immediately if execute_sql returns an error. Pass the failed query and the error message to this tool.
</tools_description>

<workflow>
- Given a to_do_list item, first check if it requires SQL.
- If SQL is needed, use generate_sql to create the query.
- Pass the generated SQL to execute_sql to run it.
- If execute_sql returns an error, immediately use fix_sql_error with the failed SQL and error message.
- Repeat the process until the to_do_list item flagged with SQL is successfully completed.
- After the SQL task is done, proceed the list to data visualization agent.
</workflow>
"""
    return system_prompt

