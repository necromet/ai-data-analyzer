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


def generate_sql_system_prompt():
    # Load all schema documentation
    schema_docs = load_schema_docs()
    
    # Combine all schema docs into one reference section
    schema_reference = "\n\n".join(schema_docs.values())
    dialect = "PostgreSQL"

    system_prompt = f"""Your goal is to transform the input into a SINGLE, focused SQL query that answers one specific business question. The output must be "Tidy Data" ready for visualization tools.
SQL Language: {dialect}

Your constraints:
<role_constraints>
1.  Queries must return aggregated metrics (SUM, AVG, COUNT) grouped by relevant dimensions (Time, Category, Location).
2.  **Tidy Data Rule:** Return a single tabular dataset where each row is an observation and each column is a variable. 
    -   NEVER use `UNION ALL` to stack different data grains (e.g., do not combine "Overall Sales" and "Sales by Category" in one result).
    -   NEVER generate "Kitchen Sink" queries with multiple unrelated CTEs.
3.  Do not perform complex statistical modeling (Regression, Correlation Matrices, R-squared) inside SQL. Fetch the raw aggregated data; the visualization layer will handle the math.
4.  Limit all IDs (`customer_id`, `order_id`, etc.) to the first 10 characters (e.g., `LEFT(id, 10)`).
5.  **Safety:**
    -   Forbidden: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT, EXECUTE.
    -   Never use `SELECT *`.
    -   Never return raw, un-aggregated row-level data (e.g., a list of specific orders).
    -  Always use ABSOLUTE values for financial metrics and difference (e.g., `ABS(SUM(payment_value))`, `ABS(DATE_DIFF('day', CAST(o.order_estimated_delivery_date AS DATE), CAST(o.order_delivered_customer_date AS DATE)))`).
6.  Output ONLY the SQL query. No markdown, no explanations, no comments.
7.  Never use CURRENT_DATE since the dataset is static. Use dates from the data to match the user's implied time frame (e.g., `WHERE order_purchase_timestamp >= '2023-01-01'`).
</role_constraints>

Database Schema Reference for SQL Generation:
<database_schema_info>
{schema_reference}
</database_schema_info>

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

SQL Generation Error Prevention:
<error_prevention>
- Ensure compatibility with {dialect}. Use explicit casting if using string literals in date functions (e.g., `CAST('2023-01-01' AS DATE)`).
- Qualify all column names with table aliases (e.g., `p.product_id` instead of `product_id`).
- Use `COALESCE` for columns that might be null but are critical for grouping (e.g., category names).
</error_prevention>
"""
    return system_prompt

# SQL Generation Rules:
# <sql_rules>
# - Always use `COUNT(DISTINCT customer_unique_id)` from the `customers` table, not `customer_id`.
# - Product categories are in Portuguese. You MUST join `products` with `product_category_name_translation` and use `product_category_name_english` for display.
# - Use standard date truncation for time-series (e.g., Monthly Sales). Filter invalid dates where necessary.
# - **Review Scores:** Average them (`AVG(review_score)`). Do not return individual review text.
# </sql_rules>