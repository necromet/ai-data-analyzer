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

def output_format():
    """Example output for planner agent system prompt."""
    output_format = """{
    "plan": [
        {
            "visualization": true,
            "sql_required": true, 
            "task": "Clear, concise description of what needs to be done",
            "chart_type": "bar_grouped"
        }
    ]
}

CRITICAL JSON FORMATTING RULES:
- ALL string values MUST be enclosed in double quotes (e.g., "bar_grouped", not bar_grouped)
- Boolean values (true/false) must be lowercase without quotes
- chart_type must ALWAYS be a quoted string (e.g., "bar_grouped", "line", "none")
- This must be valid JSON that can be parsed by json.loads()
- Example: "chart_type": "bar_grouped" ✓   "chart_type": bar_grouped ✗
"""
    return output_format

def planner_agent_system_prompt(user_input: str, chat_history: list = None):
    # Load all schema documentation
    schema_docs = load_schema_docs()
    
    # Combine all schema docs into one reference section
    schema_reference = "\n\n".join(schema_docs.values())
    output_format_str = output_format()
    
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

    system_prompt = f"""Role: You are a Technical Planner for data visualization. Your specific goal is to translate a user request into a SINGLE, ATOMIC data retrieval task that feeds exactly one chart.

Input: {user_input}
Chat History:
{chat_history_text}

Task Selection Logic:
1.  **Analyze Context:** Check chat history to avoid redundancy.
2.  **Select Chart Type:** Choose the single best chart from the list below. If no visualization is needed, select "none".
    <chart_list>
    line, line_smooth, line_stacked, area, area_stacked, bar, bar_horizontal, bar_stacked, bar_grouped, bar_stacked_dual_axis, bar_grouped_dual_axis, bar_line, bar_line_single_axis, pie, scatter, boxplot, boxplot_horizontal, boxplot_dual_axis, heatmap, heatmap_time_series, heatmap_correlation, heatmap_calendar
    </chart_list>
3.  **Define the Data Task:** Write a task description that asks ONLY for the columns needed to render that specific chart.

<CRITICAL_RULES>
-   **One Chart = One Dataset:** Do not ask for multiple levels of aggregation (e.g., do NOT ask for "Overall totals AND monthly breakdown AND category summary" in one task). Pick the most important one.
-   **No Statistical Instructions:** Do not ask the SQL agent to calculate "regression coefficients," "R-squared," "correlations," or "bins/quartiles."
    -   *Incorrect:* "Calculate linear regression of price vs. rating."
    -   *Correct:* "Retrieve average price and average rating per product for a scatter plot."
-   **Tidy Data Only:** The task must describe a flat dataset (columns and rows), not a complex report structure.
-   **No "Analysis" Steps:** Do not describe post-processing steps like "controlling for X" or "within-category analysis." Just ask for the raw aggregated data (e.g., "Group by Category").
-   **Portuguese Translation:** Explicitly mention "Use English category names" in the task if the user implies it.
</CRITICAL_RULES>

<output_format>
{output_format_str}
</output_format>

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

<examples>

Example 1 (Simple Trend):
Input: "How has our revenue grown over the last year?"
Task: Calculate total revenue grouped by month for the last 12 months.
SQL: true
Visualization: true
Chart Type: line_smooth

Example 2 (Complex Analysis Simplification):
Input: "Analyze the impact of description length on review scores using regression."
**BAD Task:** Calculate linear regression coefficients and R-squared for description length vs review scores.
**GOOD Task:** Retrieve product description length and average review score for every product.
SQL: true
Visualization: true
Chart Type: scatter

Example 3 (Comparison):
Input: "Compare sales between different seller states."
Task: Calculate total sales volume for each seller state.
SQL: true
Visualization: true
Chart Type: bar_horizontal

</examples>
"""
    return system_prompt

# <db_schema_information>
# {schema_reference}
# </db_schema_information>