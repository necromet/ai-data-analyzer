def fix_sql_error_prompt(sql_query: str, error_message: str) -> str:
    """Generate prompt for SQL error fixing tool."""
    prompt = f"""
    The following SQL query resulted in an error when executed:

    SQL Query:
    {sql_query}

    Error Message:
    {error_message}

    Please analyze the error and provide a corrected SQL query. Ensure the new query adheres to the following rules:
    - Fix the issues that caused the error.
    - Avoid any DML operations.
    - Ensure all table and column names are valid as per the database schema.
    - Limit results to 100 rows.
    - Return only the corrected SQL query without any additional text.
    - To generate distance calculations between two geographic points, haversine formula is needed. However, modify the query to clamp the ACOS argument to [-1, 1] using DuckDB's GREATEST and LEAST functions (or similar clamping logic).
    """
    return prompt