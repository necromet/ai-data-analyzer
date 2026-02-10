from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from agent.planner_agent_system_prompt import planner_agent_system_prompt
from agent.sql_agent_system_prompt import generate_sql_system_prompt
from agent.data_viz_system_prompt import data_vis_system_prompt
from agent.response_synthesizer_system_prompt import response_synthesizer_system_prompt
from agent.database_tools import get_db_connection
from agent.artifacts.bar_chart import (
    echarts_bar, 
    echarts_bar_horizontal, 
    echarts_bar_stacked, 
    echarts_bar_grouped
)
from agent.artifacts.line_chart import (
    echarts_line,
    echarts_line_smooth,
    echarts_line_stacked,
    echarts_area,
    echarts_area_stacked
)
from agent.artifacts.pie_chart import echarts_pie
from agent.artifacts.scatter_chart import echarts_scatter
from agent.artifacts.box_plot import (
    echarts_boxplot,
    echarts_boxplot_horizontal
)
from agent.artifacts.heatmap_chart import (
    echarts_heatmap,
    echarts_heatmap_time_series,
    echarts_heatmap_correlation,
    echarts_heatmap_calendar
)
from typing import TypedDict, List, Annotated
from typing_extensions import NotRequired
import operator
import sqlparse
import pandas as pd
from datetime import datetime
import json
import os
import re

# Module-level cache to store query results
query_results_cache = {}

def parse_sql_query(sql_text: str) -> str:
    """
    Parse and clean SQL query by removing markdown code block markers.
    Removes ```sql and ``` from the input string.
    
    Args:
        sql_text: Raw SQL text that may contain markdown formatting
        
    Returns:
        Cleaned SQL query string
    """
    if not sql_text:
        return sql_text
    
    # Remove markdown code blocks in one pass
    cleaned = re.sub(r'^\s*```(?:sql)?\s*\n?|\n?\s*```\s*$', '', sql_text.strip(), flags=re.IGNORECASE)
    return cleaned.strip()

general_agent_model_name = "gpt-5-mini-2025-08-07"
# general_agent_model_name = "gpt-4o-mini-2024-07-18"
general_agent_model = ChatOpenAI(
    model = general_agent_model_name,
    temperature = 0.2,
    max_tokens = 3000
)

class AgentState(TypedDict):
    # 1. Inputs & Strategy
    user_query: str  # Required: must be provided when invoking the graph
    plan_steps: NotRequired[List[dict]]  # List of dicts with item_no, visualization, sql_required, task
    current_step_index: NotRequired[int]  # Global index for overall plan progress

    # 2. The SQL Workspace
    generated_sql: NotRequired[str]
    analysis_history: NotRequired[Annotated[List[dict], operator.add]]

    # 3. Flags and Troubleshooting
    error_log: NotRequired[str]

    # 4. Final Outputs
    final_response: NotRequired[str]
    chat_history: NotRequired[Annotated[List[dict], operator.add]]  # Conversation history with user input and final responses


def initialize_db(state: AgentState):
    """Initialize database connection before processing any requests."""
    try:
        conn = get_db_connection()
        print(" ! Database initialization node completed successfully")
    except Exception as e:
        print(f" ! Database initialization failed: {e}")
        raise
    return state

def extract_agent_response_content(result) -> str:
    """Extract text content from various agent result formats."""
    content = ""
    
    if "messages" in result:
        messages = result["messages"]
        # Get the last AI message
        for msg in reversed(messages):
            if hasattr(msg, 'content'):
                content = msg.content
                break
    elif hasattr(result, 'content'):
        content = result.content
    else:
        content = str(result)
    
    return content

def parse_plan_steps(text: str) -> List[dict]:
    """Parse plan steps from JSON formatted text."""
    
    try:
        # Try to parse as JSON
        parsed = json.loads(text)
        
        # Handle if the response is already structured with to_do_list
        if isinstance(parsed, dict) and "to_do_list" in parsed:
            return parsed["to_do_list"]
        
        # Handle if the response is directly a list
        if isinstance(parsed, list):
            return parsed
        
        # If neither, wrap it as a single task
        return [{
            "item_no": 0,
            "visualization": False,
            "sql_required": True,
            "task": str(parsed)
        }]
    
    except json.JSONDecodeError:
        # Fallback: If JSON parsing fails, treat as a single unstructured task
        return [{
            "item_no": 0,
            "visualization": False,
            "sql_required": True,
            "task": text.strip()
        }]

def planner_agent(state: AgentState):
    """Custom node that extracts user query from state for the planner."""
    # Get user query directly from AgentState
    user_query = state.get("user_query", "")
    chat_history = state.get("chat_history", [])
    
    # Create agent with dynamic system prompt
    agent = create_agent(
        general_agent_model,
        system_prompt=planner_agent_system_prompt(user_input=user_query, chat_history=chat_history)
    )
    
    result = agent.invoke({"messages": [{"role": "user", "content": user_query}]})
    
    # Extract and parse plan steps
    plan_content = extract_agent_response_content(result)
    plan_steps = parse_plan_steps(plan_content)
    
    return {
        "plan_steps": plan_steps,
        "current_step_index": 0
    }

def save_query_results(query_key: str = None, save_all: bool = False) -> dict:
    """Save query results from cache to the query_results folder as JSON files."""
    # Get the directory where this file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    query_results_dir = os.path.join(current_dir, "query_results")
    
    # Create directory if it doesn't exist
    os.makedirs(query_results_dir, exist_ok=True)
    
    results = {
        "success": True,
        "saved_count": 0,
        "failed_count": 0,
        "errors": []
    }
    
    # Determine which keys to save
    keys_to_save = []
    if save_all:
        keys_to_save = list(query_results_cache.keys())
    elif query_key:
        if query_key in query_results_cache:
            keys_to_save = [query_key]
        else:
            results["success"] = False
            results["errors"].append(f"Query key '{query_key}' not found in cache")
            return results
    else:
        results["errors"].append("No query_key provided and save_all is False")
        return results
    
    # Save each query result
    for key in keys_to_save:
        try:
            file_path = os.path.join(query_results_dir, f"{key}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(query_results_cache[key], f, indent=2, ensure_ascii=False)
            results["saved_count"] += 1
        except Exception as e:
            results["failed_count"] += 1
            results["errors"].append(f"Failed to save {key}: {str(e)}")
            results["success"] = False
    
    return results

def text_to_sql_agent(state: AgentState):
    """Generate or fix SQL query based on user request and any previous errors."""
    user_query = state.get("user_query", "")
    error_log = state.get("error_log", "")
    last_sql = state.get("generated_sql", "")
    
    # Get current plan step context
    current_step_index = state.get("current_step_index", 0)
    plan_steps = state.get("plan_steps", [])
    
    # Filter out steps that don't require SQL or are visualization-only
    data_steps = [s for s in plan_steps if s.get("sql_required", True)]
    current_step_dict = data_steps[current_step_index] if current_step_index < len(data_steps) else None
    current_step = current_step_dict.get("task", user_query) if current_step_dict else user_query

    if error_log:
        # CONTEXT: The agent is now in "Fix Mode"
        prompt = f"""
        The user asked: {user_query}
        Your previous SQL: {last_sql}
        It failed with this error: {error_log}
        Please provide a corrected DuckDB SQL query. Do not include any explanations or additional text, just SQL.

        System Prompt:
        {generate_sql_system_prompt(user_input="")}
        """
    else:
        # CONTEXT: The agent is in "Initial Generation Mode"
        # Include the current step being processed
        prompt = f"""
        {generate_sql_system_prompt(user_input=current_step)}
        """

    response = general_agent_model.invoke(prompt)
    return {"generated_sql": response.content, "error_log": ""}  # Clear the error once we retry

def sql_executor(state: AgentState) -> AgentState:
    """Execute a SELECT query and return results with updated state."""
    sql_query = state.get("generated_sql", "")
    
    if not sql_query:
        return {"error_log": "No SQL query generated to execute."}
    
    # Parse and clean the SQL query to remove markdown code block markers
    sql_query = parse_sql_query(sql_query)
    
    try:
        # Validate first
        forbidden = detect_dml_statements(sql_query)
        if forbidden:
            error_msg = f"""ERROR: Cannot execute SQL. Forbidden statements detected: {', '.join([s['statement'] for s in forbidden])}
            
            Please regenerate the SQL query without these forbidden operations."""
            return {"error_log": error_msg}
        
        # Get thread-safe connection
        conn = get_db_connection()
        
        # Execute and immediately materialize to DataFrame
        result = conn.execute(sql_query).fetchdf()
        
        # Convert datetime/timestamp columns to ISO format strings for JSON serialization
        for col in result.columns:
            if pd.api.types.is_datetime64_any_dtype(result[col]):
                result[col] = result[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Store metadata in JSON format
        metadata = {
            "columns": result.columns.to_list(),
            "num_columns": len(result.columns),
            "num_rows": len(result),
            "describe": result.describe().to_dict(orient='split')
        }
        records_json = result.to_dict(orient='records')
        result_json = {
            "sql_query": sql_query,
            "metadata": metadata,
            "data": records_json
        }

        # Generate a unique key for this query result
        query_key = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Store result_json in module-level cache (will be saved at session end)
        query_results_cache[query_key] = result_json
        
        success_message = f"The SQL Query {sql_query} executed successfully. Rows returned: {len(result)}. Columns: {', '.join(result.columns)}. Result stored with key: {query_key}"
        
        # Add to analysis history
        analysis_entry = {
            "type": "sql_execution",
            "query_key": query_key,
            "sql": sql_query,
            "rows": len(result),
            "columns": result.columns.to_list(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Increment the step index to track progress
        current_index = state.get("current_step_index", 0)
        next_index = current_index + 1
        
        # Return updated state
        return {
            "error_log": "",  # Clear any previous errors
            "analysis_history": [analysis_entry],
            "current_step_index": next_index
        }
    
    except Exception as e:
        error_msg = f"""ERROR: Failed to execute SQL query.

        Error Details: {str(e)}

        Please analyze the error and regenerate a corrected SQL query. 
        """
        return {"error_log": error_msg}


def detect_dml_statements(content: str) -> list[dict[str, str]]:
    """Detect forbidden SQL statements (DML, DDL, DCL, TCL)."""
    # This list covers DDL, DML, DCL, and TCL
    forbidden_types = {
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 
        'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE', 'MERGE', 
        'COMMIT'
    }
    
    found_statements = []
    
    parsed = sqlparse.parse(content)
    
    for statement in parsed:
        root_keyword = statement.get_type()
        
        if root_keyword in forbidden_types:
            found_statements.append({
                "statement": root_keyword,
                "full_query": str(statement).strip()
            })
        else:
            for token in statement.flatten():
                if token.is_keyword and token.value.upper() in forbidden_types:
                    found_statements.append({
                        "statement": token.value.upper(),
                        "full_query": "Detected inside sub-query or block"
                    })
                    break # Avoid duplicate entries for the same query

    return found_statements


def human_review_node(state: AgentState):
    # This is the "Breakpoint" - the graph pauses here.
    pass

def get_latest_query_result():
    """Retrieve the most recent query result from cache."""
    if not query_results_cache:
        return None
    # Get the most recent query key (they're timestamped)
    latest_key = max(query_results_cache.keys())
    return query_results_cache[latest_key]

def map_visualization_spec_to_chart(viz_spec: dict, query_result: dict = None) -> dict:
    """Map visualization specification to the appropriate chart function.
    
    Args:
        viz_spec: Dictionary with keys:
            - chart_type: Chart type (e.g., "bar", "line", "pie", "scatter", etc.)
            - title: Chart title (optional)
            - x_columns: Column name for x-axis
            - y_columns: Column name for y-axis
            - value_columns: List of column names (for stacked/grouped charts)
        query_result: Query result dict with metadata and data
    
    Returns:
        ECharts configuration dictionary
    """
    chart_type = viz_spec.get("chart_type", "").lower()
    title = viz_spec.get("title", "")
    x_col = viz_spec.get("x_columns", "")
    y_col = viz_spec.get("y_columns", "")
    value_columns = viz_spec.get("value_columns", [])  # For stacked/grouped charts
    
    # Helper function to ensure value_columns is a list
    def ensure_value_columns_list(value_cols, y_column, x_column):
        """Convert value_columns to list if needed, with fallback to y_col or x_col."""
        if value_cols:
            return value_cols
        if y_column:
            return [y_column] if isinstance(y_column, str) else y_column
        if x_column:
            return [x_column] if isinstance(x_column, str) else x_column
        return []
    
    if chart_type == "bar":
        return echarts_bar(x_col, y_col, query_result=query_result)
    elif chart_type == "bar_horizontal":
        return echarts_bar_horizontal(y_col, x_col, query_result=query_result)
    elif chart_type == "bar_stacked":
        category_col = x_col or y_col
        value_columns = ensure_value_columns_list(value_columns, y_col, x_col)
        return echarts_bar_stacked(category_col, value_columns, query_result=query_result, title=title)
    elif chart_type == "bar_grouped":
        category_col = x_col or y_col
        value_columns = ensure_value_columns_list(value_columns, y_col, x_col)
        return echarts_bar_grouped(category_col, value_columns, query_result=query_result, title=title)
    elif chart_type == "line":
        return echarts_line(x_col, y_col, query_result=query_result)
    elif chart_type == "line_smooth":
        return echarts_line_smooth(x_col, y_col, query_result=query_result)
    elif chart_type == "line_stacked":
        category_col = x_col or y_col
        value_columns = ensure_value_columns_list(value_columns, y_col, x_col)
        return echarts_line_stacked(category_col, value_columns, query_result=query_result)
    elif chart_type == "area":
        return echarts_area(x_col, y_col, query_result=query_result)
    elif chart_type == "area_stacked":
        category_col = x_col or y_col
        value_columns = ensure_value_columns_list(value_columns, y_col, x_col)
        return echarts_area_stacked(category_col, value_columns, query_result=query_result)
    elif chart_type == "pie":
        # For pie charts, x_columns is name_column, y_columns is value_column
        return echarts_pie(x_col, y_col, title=title, query_result=query_result)
    elif chart_type == "scatter":
        return echarts_scatter(x_col, y_col, title=title, query_result=query_result)
    elif chart_type == "boxplot":
        return echarts_boxplot(x_col, y_col, query_result=query_result, title=title)
    elif chart_type == "boxplot_horizontal":
        return echarts_boxplot_horizontal(x_col, y_col, query_result=query_result, title=title)
    elif chart_type == "heatmap":
        # value_columns should be a single column name for basic heatmap
        value_col = value_columns[0] if isinstance(value_columns, list) and value_columns else value_columns
        if not value_col:
            value_col = "value"  # fallback
        return echarts_heatmap(x_col, y_col, value_col, title=title, query_result=query_result)
    elif chart_type == "heatmap_time_series":
        # x_columns = date/time category, y_columns = time category, value_columns = value column
        value_col = value_columns[0] if isinstance(value_columns, list) and value_columns else value_columns
        if not value_col:
            value_col = "value"  # fallback
        return echarts_heatmap_time_series(x_col, y_col, value_col, title=title, query_result=query_result)
    elif chart_type == "heatmap_correlation":
        # value_columns should be a list of column names to correlate
        columns = value_columns if isinstance(value_columns, list) else [value_columns]
        return echarts_heatmap_correlation(columns, title=title, query_result=query_result)
    elif chart_type == "heatmap_calendar":
        # x_columns = date column, value_columns = value column, year from viz_spec
        value_col = value_columns[0] if isinstance(value_columns, list) and value_columns else value_columns
        if not value_col:
            value_col = "value"  # fallback
        year = viz_spec.get("year", 2024)  # Default to 2024 if not specified
        return echarts_heatmap_calendar(x_col, value_col, year, title=title, query_result=query_result)
    
    else:
        return {"error": f"Unknown chart type: {chart_type}"}

def data_visual_agent_node(state: AgentState):
    """Custom node that creates visualizations based on query results."""
    # Get user query from state
    user_input = state.get("user_query", "")
    
    # Get the most recent query result (from the step we just executed)
    query_result = get_latest_query_result()
    
    # Get the task description for the current visualization
    current_step_index = state.get("current_step_index", 0)
    plan_steps = state.get("plan_steps", [])
    data_steps = [s for s in plan_steps if s.get("sql_required", True)]
    
    # Get the step we just completed (current_step_index was already incremented)
    last_step_index = current_step_index - 1
    current_task = user_input
    if 0 <= last_step_index < len(data_steps):
        current_task = data_steps[last_step_index].get("task", user_input)
    
    query_key = None
    # Get actual query results from cache
    if query_result and isinstance(query_result, dict) and query_result.get("data"):
        metadata = query_result["metadata"]
        column_names = metadata["columns"]
        row_example = query_result["data"][0] if query_result["data"] else {}
        query_metadata = {
            "columns": column_names,
            "num_rows": metadata.get("num_rows", len(query_result["data"])),
            "num_columns": metadata.get("num_columns", len(column_names)),
            "sample_rows": query_result["data"][:3]
        }
        # Extract query_key from the most recent analysis history entry
        analysis_history = state.get("analysis_history", [])
        sql_entries = [e for e in analysis_history if e.get("type") == "sql_execution"]
        if sql_entries:
            query_key = sql_entries[-1].get("query_key")
    else:
        # Default fallback values
        column_names = ["example_column_1", "example_column_2", "example_column_3"]
        row_example = {"example_column_1": "value1", "example_column_2": 123, "example_column_3": 45.67}
        query_metadata = {"columns": column_names, "sample_rows": [row_example]}
    
    agent = create_agent(
        general_agent_model,
        system_prompt=data_vis_system_prompt(
            user_input=current_task, 
            query_metadata=query_metadata,
            column_names=column_names, 
            row_example=row_example
        )
    )
    
    result = agent.invoke({"messages": [{"role": "user", "content": f"Create visualization for: {current_task}"}]})
    
    # Extract visualization output and store in state
    viz_content = extract_agent_response_content(result)
    try:
        viz_spec = json.loads(viz_content)
        chart_config = map_visualization_spec_to_chart(viz_spec, query_result=query_result)
        # Convert back to JSON string for storage
        viz_output = json.dumps({
            "specification": viz_spec,
            "chart_config": chart_config
        }, indent=2)
    except json.JSONDecodeError:
        # If parsing fails, keep original content
        viz_output = viz_content
    
    # Add visualization to analysis history
    viz_entry = {
        "type": "visualization",
        "query_key": query_key,
        "visualization_content": viz_output,
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "final_response": viz_output,
        "analysis_history": [viz_entry]
    }


def response_synthesizer_agent_node(state: AgentState):
    """Custom node that synthesizes response with actual query results."""
    # Get user query from state
    user_input = state.get("user_query", "")
    
    # Get data visualizer output from state if available
    chart_specs = state.get("final_response", "")
    
    # Get actual query results from cache
    query_result = get_latest_query_result()
    metadata = {}
    if query_result and isinstance(query_result, dict):
        metadata = query_result.get("metadata", {})
        # Also include a sample of the data for context
        if query_result.get("data"):
            metadata["data_sample"] = query_result["data"][:5]  # First 5 rows
    
    # Create agent with dynamic system prompt including actual metadata
    agent = create_agent(
        general_agent_model,
        system_prompt=response_synthesizer_system_prompt(
            user_input=user_input, 
            chart_specs=chart_specs, 
            metadata=metadata
        )
    )
    
    # Invoke agent with a simple message state
    result = agent.invoke({"messages": [{"role": "user", "content": f"Synthesize response for: {user_input}"}]})
    
    # Extract final response and store in state
    final_content = extract_agent_response_content(result)
    
    # Save all query results from this session to disk
    save_query_results(save_all=True)
    print(f" ! Saved {len(query_results_cache)} query results to disk")
    
    # Add to chat history
    chat_entry = {
        "user_input": user_input,
        "final_response": final_content,
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "final_response": final_content,
        "chat_history": [chat_entry]
    }

def route_after_exec(state: AgentState):
    """Route after SQL execution based on error status, plan completion, and visualization needs."""
    # Check if there was an error - if so, loop back to fix the SQL
    if state.get("error_log", ""):
        return "Text_to_SQL_Agent"  # Loop back for self-correction
    
    # Get current step and plan
    current_step = state.get("current_step_index", 0)
    plan_steps = state.get("plan_steps", [])
    
    # Filter data steps that require SQL
    data_steps = [s for s in plan_steps if s.get("sql_required", True)]
    total_data_steps = len(data_steps)
    
    # Check if the step we just completed needs visualization
    # current_step has been incremented, so the last executed step is at index (current_step - 1)
    last_executed_step_index = current_step - 1
    if last_executed_step_index >= 0 and last_executed_step_index < len(data_steps):
        last_executed_step = data_steps[last_executed_step_index]
        if last_executed_step.get("visualization", False):
            # This step needs visualization before continuing
            return "Data_Visual_Agent"
    
    # Check if there are more data steps to process
    if current_step < total_data_steps:
        # More data steps to process - continue with next SQL generation
        return "Text_to_SQL_Agent"
    
    # All steps completed, no visualization needed - go to response synthesizer
    return "Response_Synthesizer"

def route_after_visualization(state: AgentState):
    """Route after visualization to check if more SQL steps or visualizations are needed."""
    current_step = state.get("current_step_index", 0)
    plan_steps = state.get("plan_steps", [])
    
    # Count data steps that require SQL
    data_steps = [s for s in plan_steps if s.get("sql_required", True)]
    total_data_steps = len(data_steps)
    
    # Check if there are more SQL steps to process
    if current_step < total_data_steps:
        # Continue with next SQL generation
        return "Text_to_SQL_Agent"
    
    # All steps complete - synthesize final response
    return "Response_Synthesizer"


graph = StateGraph(AgentState)
graph.add_node("Initialize_DB", initialize_db)
graph.add_node("Planner_Agent", planner_agent)
graph.add_node("Text_to_SQL_Agent", text_to_sql_agent)
graph.add_node("Human_Review", human_review_node)
graph.add_node("SQL_Executor", sql_executor)
graph.add_node("Data_Visual_Agent", data_visual_agent_node)
graph.add_node("Response_Synthesizer", response_synthesizer_agent_node)

# 1. Setup and Planning
graph.add_edge(START, "Initialize_DB")
graph.add_edge("Initialize_DB", "Planner_Agent")

# 2. Planning -> Human (Optional: Clarification)
graph.add_edge("Planner_Agent", "Text_to_SQL_Agent")

# Pause Point: Let human see the SQL before execution
graph.add_edge("Text_to_SQL_Agent", "Human_Review")
graph.add_edge("Human_Review", "SQL_Executor")

graph.add_conditional_edges(
    "SQL_Executor",
    route_after_exec,
    {
        "Text_to_SQL_Agent": "Text_to_SQL_Agent",
        "Data_Visual_Agent": "Data_Visual_Agent",
        "Response_Synthesizer": "Response_Synthesizer"
    }
)

graph.add_conditional_edges(
    "Data_Visual_Agent",
    route_after_visualization,
    {
        "Text_to_SQL_Agent": "Text_to_SQL_Agent",
        "Response_Synthesizer": "Response_Synthesizer"
    }
)

graph.add_edge("Response_Synthesizer", END)

# Compile the graph for LangGraph Studio
# Note: LangGraph API provides built-in persistence, no custom checkpointer needed
app = graph.compile(
    interrupt_before=["Human_Review"]  # Graph stops RIGHT before entering this node
)