from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.messages import SystemMessage
from agent.planner_agent_system_prompt import planner_agent_system_prompt
from agent.sql_agent_system_prompt import generate_sql_system_prompt
from agent.general_agent_system_prompt import general_agent_system_prompt
from agent.fix_sql_error_system_prompt import fix_sql_error_prompt
from agent.data_viz_system_prompt import data_vis_system_prompt
from agent.response_synthesizer_system_prompt import response_synthesizer_system_prompt
from agent.database_tools import get_db_connection
from typing import TypedDict, List, Annotated, Union
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
    
    # Remove ```sql at the beginning (case-insensitive)
    cleaned = re.sub(r'^\s*```sql\s*\n?', '', sql_text, flags=re.IGNORECASE)
    
    # Remove ``` at the end
    cleaned = re.sub(r'\n?\s*```\s*$', '', cleaned)
    
    # Also remove standalone ``` markers that might appear
    cleaned = re.sub(r'^\s*```\s*\n?', '', cleaned)
    
    return cleaned.strip()

general_agent_model_name = "gpt-5-mini-2025-08-07"
# general_agent_model_name = "gpt-4o-mini-2024-07-18"
general_agent_model = ChatOpenAI(
    model = general_agent_model_name,
    temperature = 0.2,
    max_tokens = 10000
)

class AgentState(TypedDict):
    # 1. Inputs & Strategy
    user_query: str  # Required: must be provided when invoking the graph
    plan_steps: NotRequired[List[dict]]  # List of dicts with item_no, visualization, sql_required, task
    current_step_index: NotRequired[int]  # Global index for overall plan progress
    visualization_step_index: NotRequired[int]  # Local index for tracking visualization progress

    # 2. The SQL Workspace
    generated_sql: NotRequired[str]
    analysis_history: NotRequired[Annotated[List[dict], operator.add]]

    # 3. Flags and Troubleshooting
    error_log: NotRequired[str]
    needs_visual: NotRequired[bool]

    # 4. Final Outputs
    final_response: NotRequired[str]


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

def analysis_router(state: AgentState):
    # The Synthesizer or a specialized Evaluator decides if we are done
    if state.get("current_step_index", 0) >= len(state.get("plan_steps", [])):
        return "Data_Visual_Agent"
    return "Text_to_SQL_Agent"

def planner_agent(state: AgentState):
    """Custom node that extracts user query from state for the planner."""
    # Get user query directly from AgentState
    user_query = state.get("user_query", "")
    
    # Create agent with dynamic system prompt
    agent = create_agent(
        general_agent_model,
        system_prompt=planner_agent_system_prompt(user_input=user_query)
    )
    
    result = agent.invoke({"messages": [{"role": "user", "content": user_query}]})
    
    # Extract and parse plan steps
    plan_content = extract_agent_response_content(result)
    plan_steps = parse_plan_steps(plan_content)
    
    return {
        "plan_steps": plan_steps,
        "current_step_index": 0,
        "visualization_step_index": 0
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
        return {
            "error_log": "No SQL query generated to execute.",
            "needs_visual": False
        }
    
    # Parse and clean the SQL query to remove markdown code block markers
    sql_query = parse_sql_query(sql_query)
    
    try:
        # Validate first
        forbidden = detect_dml_statements(sql_query)
        if forbidden:
            error_msg = f"""ERROR: Cannot execute SQL. Forbidden statements detected: {', '.join([s['statement'] for s in forbidden])}
            
            Please regenerate the SQL query without these forbidden operations."""
            return {
                "error_log": error_msg,
                "needs_visual": False
            }
        
        # Get thread-safe connection
        conn = get_db_connection()
        
        # Execute and immediately materialize to DataFrame
        result = conn.execute(sql_query).fetchdf()
        
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
            "needs_visual": True,  # Assume we want visualization by default
            "analysis_history": [analysis_entry],
            "current_step_index": next_index
        }
    
    except Exception as e:
        error_msg = f"""ERROR: Failed to execute SQL query.

        Error Details: {str(e)}

        Please analyze the error and regenerate a corrected SQL query. 
        """
        return {
            "error_log": error_msg,
            "needs_visual": False
        }


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

def echarts_line(x_column: str, y_column: str) -> dict:
    """Generate line charts for echarts.js using the latest query result data."""
    query_result = get_latest_query_result()
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    x_data = [row.get(x_column) for row in data]
    y_data = [row.get(y_column) for row in data]
    
    return {
      "xAxis": {
        "type": "category",
        "data": x_data
      },
      "yAxis": {
        "type": "value"
      },
      "series": [
        {
          "data": y_data,
          "type": "line"
        }
      ]
    }

def echarts_bar(x_column: str, y_column: str) -> dict:
    """Generate bar charts for echarts.js using the latest query result data."""
    query_result = get_latest_query_result()
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    x_data = [row.get(x_column) for row in data]
    y_data = [row.get(y_column) for row in data]
    
    return {
      "xAxis": {
        "type": "category",
        "data": x_data
      },
      "yAxis": {
        "type": "value"
      },
      "series": [
        {
          "data": y_data,
          "type": "bar"
        }
      ]
    }

def data_visual_agent_node(state: AgentState):
    """Custom node that creates visualizations based on query results."""
    # Get user query and plan from state
    user_input = state.get("user_query", "")
    plan_steps = state.get("plan_steps", [])
    
    # Get local visualization index (tracks which visualization step to process)
    viz_step_index = state.get("visualization_step_index", 0)
    
    # Get steps that need visualization
    viz_steps = [s for s in plan_steps if s.get("visualization", False)]
    
    # Get the analysis history to find SQL executions
    analysis_history = state.get("analysis_history", [])
    sql_executions = [entry for entry in analysis_history if entry.get("type") == "sql_execution"]
    
    # Match the current visualization step with the corresponding SQL execution
    # Assume visualization steps correspond to SQL executions in order
    if viz_step_index < len(sql_executions) and viz_step_index < len(viz_steps):
        query_key = sql_executions[viz_step_index]["query_key"]
        query_result = query_results_cache.get(query_key)
        current_task = viz_steps[viz_step_index].get("task", user_input)
    else:
        query_result = get_latest_query_result()
        current_task = user_input

    # Get actual query results from cache
    if query_result and query_result.get("data"):
        column_names = query_result["metadata"]["columns"]
        row_example = query_result["data"][0] if query_result["data"] else {}
    else:
        # Fallback to placeholder if no query results available
        column_names = ["example_column_1", "example_column_2", "example_column_3"]
        row_example = {
            "example_column_1": "value1",
            "example_column_2": 123,
            "example_column_3": 45.67
        }
    
    # Create agent with dynamic system prompt
    agent = create_agent(
        general_agent_model,
        system_prompt=data_vis_system_prompt(
            user_input=user_input, 
            query_result=query_result, 
            column_names=column_names, 
            row_example=row_example
        )
    )
    
    # Invoke agent with a simple message state for tool calling
    result = agent.invoke({"messages": [{"role": "user", "content": f"Create visualization for: {user_input}"}]})
    
    # Extract visualization output and store in state
    viz_content = extract_agent_response_content(result)
    
    # Add visualization to analysis history
    viz_step_index = state.get("visualization_step_index", 0)
    analysis_history = state.get("analysis_history", [])
    sql_executions = [entry for entry in analysis_history if entry.get("type") == "sql_execution"]
    
    viz_entry = {
        "type": "visualization",
        "query_key": sql_executions[viz_step_index]["query_key"] if viz_step_index < len(sql_executions) else None,
        "visualization_content": viz_content[:200] + "..." if len(viz_content) > 200 else viz_content,
        "timestamp": datetime.now().isoformat()
    }
    
    # Increment local visualization index
    next_viz_index = viz_step_index + 1
    
    return {
        "final_response": viz_content,
        "analysis_history": [viz_entry],
        "visualization_step_index": next_viz_index
    }


def response_synthesizer_agent_node(state: AgentState):
    """Custom node that synthesizes response with actual query results."""
    # Get user query from state
    user_input = state.get("user_query", "")
    
    # Get data visualizer output from state if available
    data_visualizer = state.get("final_response", "")
    
    # Get actual query results from cache
    query_result = get_latest_query_result()
    metadata = {}
    if query_result:
        metadata = query_result.get("metadata", {})
        # Also include a sample of the data for context
        if query_result.get("data"):
            metadata["data_sample"] = query_result["data"][:5]  # First 5 rows
    
    # Create agent with dynamic system prompt including actual metadata
    agent = create_agent(
        general_agent_model,
        system_prompt=response_synthesizer_system_prompt(
            user_input=user_input, 
            data_visualizer=data_visualizer, 
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
    
    return {"final_response": final_content}

def route_after_exec(state: AgentState):
    """Route after SQL execution based on error status, plan completion, and visualization needs."""
    # Check if there was an error - if so, loop back to fix the SQL
    if state.get("error_log", ""):
        return "Text_to_SQL_Agent"  # Loop back for self-correction
    
    # Check if all data analysis steps are completed (excluding visualization steps)
    current_step = state.get("current_step_index", 0)
    plan_steps = state.get("plan_steps", [])
    
    # Count only data retrieval steps that require SQL
    data_steps = [s for s in plan_steps if s.get("sql_required", True)]
    total_data_steps = len(data_steps)
    
    if current_step < total_data_steps:
        # More data steps to process - continue with next SQL generation
        return "Text_to_SQL_Agent"
    
    # All SQL steps completed - check if any step requires visualization
    has_visualization_step = any(s.get("visualization", False) for s in plan_steps)
    if has_visualization_step:
        return "Data_Visual_Agent"
    
    # No visualization needed - go directly to response synthesizer
    return "Response_Synthesizer"

def route_after_visualization(state: AgentState):
    """Route after visualization to check if more visualizations are needed."""
    viz_step_index = state.get("visualization_step_index", 0)
    plan_steps = state.get("plan_steps", [])
    
    # Count total steps that need visualization
    viz_steps = [s for s in plan_steps if s.get("visualization", False)]
    total_viz_steps = len(viz_steps)
    
    # Check if we need to visualize more results
    if viz_step_index < total_viz_steps:
        return "Data_Visual_Agent"  # Loop back for next visualization
    
    # All visualizations complete - synthesize final response
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
        "Data_Visual_Agent": "Data_Visual_Agent"
    }
)

graph.add_conditional_edges(
    "Data_Visual_Agent",
    route_after_visualization,
    {
        "Data_Visual_Agent": "Data_Visual_Agent",
        "Response_Synthesizer": "Response_Synthesizer"
    }
)

graph.add_edge("Response_Synthesizer", END)

# Compile the graph for LangGraph Studio
# Note: LangGraph API provides built-in persistence, no custom checkpointer needed
app = graph.compile(
    interrupt_before=["Human_Review"]  # Graph stops RIGHT before entering this node
)