from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from agent.context_resolver_agent_system_prompt import context_resolver_agent_system_prompt
from agent.intention_agent_system_prompt import intention_agent_system_prompt
from agent.planner_agent_system_prompt import planner_agent_system_prompt
from agent.schema_info_agent_system_prompt import schema_info_agent_system_prompt
from agent.sql_agent_system_prompt import generate_sql_system_prompt
from agent.data_viz_system_prompt import data_vis_system_prompt
from agent.response_synthesizer_system_prompt import response_synthesizer_system_prompt
from agent.database_tools import get_db_connection
from agent.artifacts.bar_chart import (
    echarts_bar, 
    echarts_bar_horizontal, 
    echarts_bar_stacked, 
    echarts_bar_grouped,
    # echarts_bar_stacked_dual_axis,
    # echarts_bar_grouped_dual_axis
)
from agent.artifacts.line_chart import (
    echarts_line,
    # echarts_line_smooth,
    # echarts_line_stacked,
    echarts_area,
    echarts_area_stacked
)
from agent.artifacts.bar_line_chart import (
    echarts_bar_line,
    # echarts_bar_line_single_axis
)
from agent.artifacts.pie_chart import echarts_pie
from agent.artifacts.scatter_chart import echarts_scatter
from agent.artifacts.box_plot import (
    echarts_boxplot,
    # echarts_boxplot_horizontal,
    # echarts_boxplot_multi_column,
    # echarts_boxplot_dual_axis
)
from agent.artifacts.heatmap_chart import (
    echarts_heatmap,
    # echarts_heatmap_time_series,
    echarts_heatmap_correlation,
    # echarts_heatmap_calendar
)
from typing import TypedDict, List, Annotated, Any
from typing_extensions import NotRequired
import operator
import sqlparse
import pandas as pd
from datetime import datetime, date, time
from decimal import Decimal
import json
import os
import re

# Module-level cache to store query results
query_results_cache = {}

def convert_decimals_to_float(obj):
    """Recursively convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimals_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_float(item) for item in obj]
    return obj

def convert_dates_to_strings(obj):
    """Recursively convert date/datetime/time objects to ISO format strings for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, time):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_dates_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates_to_strings(item) for item in obj]
    return obj

def extract_token_usage(result, agent_name: str = "unknown", turn_number: int = 1) -> dict:
    """Extract token usage from agent result.
    
    Args:
        result: Agent invocation result containing usage metadata
        agent_name: Name of the agent for identification
        turn_number: The turn/run number in the current session
        
    Returns:
        Dictionary with token usage data or None if not found
    """
    try:
        # Extract usage metadata from result
        usage_data = None
        model_name = "unknown"
        
        if "messages" in result:
            messages = result["messages"]
            # Get the last AI message
            for msg in reversed(messages):
                if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                    usage_data = msg.usage_metadata
                    if hasattr(msg, 'response_metadata'):
                        model_name = msg.response_metadata.get('model_name', 'unknown')
                    break
        elif hasattr(result, 'usage_metadata') and result.usage_metadata:
            usage_data = result.usage_metadata
            if hasattr(result, 'response_metadata'):
                model_name = result.response_metadata.get('model_name', 'unknown')
        
        if not usage_data:
            return None
        
        # Extract token counts
        input_tokens = usage_data.get('input_tokens', 0)
        output_tokens = usage_data.get('output_tokens', 0)
        total_tokens = usage_data.get('total_tokens', 0)
        
        # Extract reasoning tokens from output_token_details
        reasoning_tokens = 0
        if 'output_token_details' in usage_data:
            reasoning_tokens = usage_data['output_token_details'].get('reasoning', 0)
        
        # Create token usage record
        token_record = {
            "turn_number": turn_number,
            "agent_name": agent_name,
            "model_name": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "total_tokens": total_tokens,
            "timestamp": datetime.now().isoformat()
        }
        
        return token_record
        
    except Exception as e:
        print(f"Error extracting token usage: {e}")
        return None

def save_token_usage_to_file(token_usage_log: List[dict]) -> dict:
    """Save accumulated token usage from entire run to a single JSON file.
    
    Args:
        token_usage_log: List of token usage records from all agents
        
    Returns:
        Dictionary with save status and file path
    """
    if not token_usage_log:
        return {"success": False, "error": "No token usage data to save"}
    
    # Get the directory where this file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    token_usage_dir = os.path.join(current_dir, "token_usage")
    
    # Create directory if it doesn't exist
    os.makedirs(token_usage_dir, exist_ok=True)
    
    try:
        # Calculate overall totals
        total_input = sum(record.get('input_tokens', 0) for record in token_usage_log)
        total_output = sum(record.get('output_tokens', 0) for record in token_usage_log)
        total_reasoning = sum(record.get('reasoning_tokens', 0) for record in token_usage_log)
        total_all = sum(record.get('total_tokens', 0) for record in token_usage_log)
        
        # Calculate per-agent totals
        by_model = {}
        for record in token_usage_log:
            model_name = record.get('model_name', 'unknown')
            if model_name not in by_model:
                by_model[model_name] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_tokens": 0,
                    "total_tokens": 0,
                    "call_count": 0
                }
            by_model[model_name]["input_tokens"] += record.get('input_tokens', 0)
            by_model[model_name]["output_tokens"] += record.get('output_tokens', 0)
            by_model[model_name]["reasoning_tokens"] += record.get('reasoning_tokens', 0)
            by_model[model_name]["total_tokens"] += record.get('total_tokens', 0)
            by_model[model_name]["call_count"] += 1
        
        # Create complete usage record
        usage_record = {
            "run_timestamp": datetime.now().isoformat(),
            "agents": token_usage_log,
            "totals": {
                "by_model": by_model,
                "overall": {
                    "input_tokens": total_input,
                    "output_tokens": total_output,
                    "reasoning_tokens": total_reasoning,
                    "total_tokens": total_all
                }
            }
        }
        
        # Generate filename with timestamp
        filename = f"token_usage_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        file_path = os.path.join(token_usage_dir, filename)
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(usage_record, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "file_path": file_path,
            "totals": usage_record["totals"]["overall"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

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

intention_agent_model_name = "gpt-5-mini-2025-08-07"
intention_agent_model = ChatOpenAI(
    model=intention_agent_model_name,
    temperature=0,
    max_tokens=500,
    reasoning_effort="low"
)

schema_agent_model_name = "gpt-5-mini-2025-08-07"
schema_agent_model = ChatOpenAI(
    model = schema_agent_model_name,
    temperature=0.3,
    max_tokens=5000,
    reasoning_effort="low"
)

general_agent_model_name = "gpt-5-mini-2025-08-07"
general_agent_model = ChatOpenAI(
    model = general_agent_model_name,
    temperature = 0.2,
    max_tokens = 3000,
    reasoning_effort="low"
)

sql_agent_model_name = "gpt-5-mini-2025-08-07"
sql_agent_model = ChatOpenAI(
    model = sql_agent_model_name,
    temperature = 0,
    max_tokens = 10000,
    reasoning_effort="low"
)

data_visual_agent_model_name = "gpt-5-mini-2025-08-07"
data_visual_agent_model = ChatOpenAI(
    model = data_visual_agent_model_name,
    temperature = 0,
    max_tokens = 3000,
    reasoning_effort="low"
)

class AgentState(TypedDict):
    # 1. Inputs & Strategy
    messages: NotRequired[Annotated[List[Any], operator.add]]  # Compatible with LangGraph SDK frontend (messages array)
    user_query: NotRequired[str]  # User query string (extracted from messages or provided directly)
    intention: NotRequired[str]  # User intention: "SCHEMA_INFO" or "ANALYZE"
    plan_steps: NotRequired[List[dict]]  # List of dicts with visualization, sql_required, task, chart_type
    current_step_index: NotRequired[int]  # Global index for overall plan progress
    turn_number: NotRequired[int]  # Track which run/turn this is in the session (1 for first run, 2 for second, etc.)

    # 2. The SQL Workspace
    generated_sql: NotRequired[str]
    analysis_history: NotRequired[Annotated[List[dict], operator.add]]

    # 3. Flags and Troubleshooting
    error_log: NotRequired[str]

    # 4. Final Outputs
    final_response: NotRequired[str]
    raw_agent_response: NotRequired[str]  # Raw agent response before chart_json placeholder substitution
    chart_configs: NotRequired[Annotated[List[dict], operator.add]]  # Chart configurations for visualization
    chat_history: NotRequired[Annotated[List[dict], operator.add]]  # Conversation history with user input and final responses
    token_usage_log: NotRequired[Annotated[List[dict], operator.add]]  # Token usage for each agent call


def preprocess_input(state: AgentState):
    """Extract user_query from messages (always use the latest human message) or from direct input."""
    # First check if user_query is already provided directly in the state
    user_query = state.get("user_query", "")
    messages = state.get("messages", [])
    chat_history = state.get("chat_history", [])

    print(chat_history)
    
    if messages:
        # Get the last human message
        for msg in reversed(messages):
            # Handle both dict and object message formats
            msg_type = msg.get("type") if isinstance(msg, dict) else getattr(msg, "type", None)
            msg_content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
            
            if msg_type == "human" and msg_content:
                user_query = msg_content
                break
    
    # Initialize turn_number if not present
    turn_number = state.get("turn_number", 1)
    
    print(f" ! Preprocessing: Extracted user query: {user_query[:100] if user_query else 'None'}...")

    agent = create_agent(
        intention_agent_model,
        system_prompt=context_resolver_agent_system_prompt()
    )

    # Convert chat_history entries {user_input, final_response} to {role, content} format
    formatted_history = []
    for entry in chat_history:
        if "user_input" in entry and "final_response" in entry:
            formatted_history.append({"role": "user", "content": entry["user_input"]})
            formatted_history.append({"role": "assistant", "content": entry["final_response"]})
    formatted_history.append({"role": "user", "content": user_query})

    result = agent.invoke({"messages": formatted_history})
    
    # Extract token usage
    token_usage = extract_token_usage(result, agent_name="context_resolver_agent", turn_number=turn_number)

    processed_text = extract_agent_response_content(result).strip()
    print(processed_text)

    # Don't return messages to avoid duplication - the frontend already has them
    return_dict = {
        "user_query": processed_text,
        "turn_number": turn_number
    }

    if token_usage:
        return_dict["token_usage_log"] = [token_usage]

    return return_dict


def intention_agent(state: AgentState):
    """Classify user intention: GENERAL_SCHEMA or ANALYZE."""
    user_query = state.get("user_query", "")
    turn_number = state.get("turn_number", 1)
    
    agent = create_agent(
        intention_agent_model,
        system_prompt=intention_agent_system_prompt()
    )
    
    result = agent.invoke({"messages": [{"role": "user", "content": user_query}]})
    
    # Extract token usage
    token_usage = extract_token_usage(result, agent_name="intention_agent", turn_number=turn_number)
    
    # Extract intention (should be "SCHEMA_INFO" or "ANALYZE")
    intention_text = extract_agent_response_content(result).strip().upper()
    print(intention_text)
    # Validate intention
    if "GENERAL_SCHEMA" in intention_text:
        intention = "GENERAL_SCHEMA"
    elif "ANALYZE" in intention_text:
        intention = "ANALYZE"
    else:
        # Default to ANALYZE if unclear
        intention = "ANALYZE"

    print(f" ! Intention Agent classified query as: {intention}")
    
    return_dict = {
        "intention": intention,
        "turn_number": turn_number
    }
    
    if token_usage:
        return_dict["token_usage_log"] = [token_usage]
    
    return return_dict


def schema_info_agent(state: AgentState):
    """Answer general questions about database schema without executing queries."""
    user_query = state.get("user_query", "")
    turn_number = state.get("turn_number", 1)
    
    agent = create_agent(
        schema_agent_model,
        system_prompt=schema_info_agent_system_prompt()
    )

    # Convert chat_history entries {user_input, final_response} to {role, content} format
    formatted_history = []
    for entry in state.get("chat_history", []):
        if "user_input" in entry and "final_response" in entry:
            formatted_history.append({"role": "user", "content": entry["user_input"]})
            formatted_history.append({"role": "assistant", "content": entry["final_response"]})
    formatted_history.append({"role": "user", "content": user_query})

    result = agent.invoke({"messages": formatted_history})
    
    # Extract token usage
    token_usage = extract_token_usage(result, agent_name="schema_info_agent", turn_number=turn_number)
    
    # Extract response
    response = extract_agent_response_content(result)
    
    print(" ! Schema Info Agent completed response")
    
    # Create chat history entry
    chat_entry = {
        "user_input": user_query,
        "final_response": response,
        "timestamp": datetime.now().isoformat()
    }
    
    return_dict = {
        "final_response": response,
        "chat_history": [chat_entry],
        "turn_number": turn_number + 1,
        "messages": [{"type": "ai", "content": response}]
    }
    
    if token_usage:
        return_dict["token_usage_log"] = [token_usage]
    
    print(return_dict)
    return return_dict


def initialize_db(state: AgentState):
    """Initialize database connection before processing any requests."""
    try:
        conn = get_db_connection()
        print(" ! Database initialization node completed successfully")
    except Exception as e:
        print(f" ! Database initialization failed: {e}")
        raise
    return {}

def extract_agent_response_content(result) -> str:
    """Extract text content from various agent result formats.

    Supports:
    - dict results with a `messages` list of dicts or objects
    - dict results with a top-level `content` key
    - objects with a `content` attribute
    - fallback to str(result)
    """
    content = ""

    # messages may be either objects (with .content) or dicts (with ['content'])
    if isinstance(result, dict) and "messages" in result:
        messages = result["messages"]
        # Get the last AI message; support both dict and object message formats
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("content"):
                content = msg.get("content")
                break
            elif hasattr(msg, "content") and getattr(msg, "content"):
                content = msg.content
                break
    # If result itself is a dict with a content key
    elif isinstance(result, dict) and result.get("content"):
        content = result.get("content")
    # Or an object with a content attribute
    elif hasattr(result, "content"):
        content = result.content
    else:
        content = str(result)

    return content

def repair_json(text: str) -> str:
    """Attempt to repair common JSON formatting issues.
    
    Fixes:
    - Unquoted string values (e.g., chart_type: bar_grouped -> chart_type: "bar_grouped")
    - Common chart type names without quotes
    """
    # Fix unquoted chart_type values - match known chart types
    chart_types = [
        'line', 'line_smooth', 'line_stacked', 'area', 'area_stacked',
        'bar', 'bar_horizontal', 'bar_stacked', 'bar_grouped',
        'bar_stacked_dual_axis', 'bar_grouped_dual_axis',
        'bar_line', 'bar_line_single_axis',
        'pie', 'boxplot', 'boxplot_horizontal', 'boxplot_dual_axis',
        'heatmap', 'heatmap_time_series', 'heatmap_correlation', 'heatmap_calendar',
        'none'
    ]
    
    # Create a pattern that matches: "chart_type": unquoted_value
    for chart_type in chart_types:
        # Match: "chart_type": chart_type_name (without quotes)
        pattern = rf'("chart_type"\s*:\s*)({chart_type})([,\s\}}])'
        replacement = rf'\1"\2"\3'
        text = re.sub(pattern, replacement, text)
    
    return text

def parse_plan_steps(text: str) -> List[dict]:
    """Parse plan steps from JSON formatted text."""
    
    try:
        # Try to parse as JSON
        parsed = json.loads(text)
        
        # Handle if the response is already structured with plan
        if isinstance(parsed, dict) and "plan" in parsed:
            return parsed["plan"]
        
        # Handle if the response is directly a list
        if isinstance(parsed, list):
            return parsed
        
        # If neither, wrap it as a single task
        return [{
            # "item_no": 0,
            "visualization": False,
            "sql_required": True,
            "task": str(parsed)
        }]
    
    except json.JSONDecodeError as e:
        # Try to repair JSON and parse again
        try:
            repaired_text = repair_json(text)
            parsed = json.loads(repaired_text)
            
            print(f" ! JSON repair successful: Fixed invalid JSON")
            
            # Handle if the response is already structured with plan
            if isinstance(parsed, dict) and "plan" in parsed:
                return parsed["plan"]
            
            # Handle if the response is directly a list
            if isinstance(parsed, list):
                return parsed
            
            # If neither, wrap it as a single task
            return [{
                "visualization": False,
                "sql_required": True,
                "task": str(parsed)
            }]
            
        except json.JSONDecodeError:
            # Fallback: If JSON parsing still fails, treat as a single unstructured task
            print(f" ! JSON parsing failed even after repair: {e}")
            return [{
                # "item_no": 0,
                "visualization": False,
                "sql_required": True,
                "task": text.strip()
            }]

def planner_agent(state: AgentState):
    """Custom node that extracts user query from state for the planner."""
    # Get user query directly from AgentState
    user_query = state.get("user_query", "")
    
    # Initialize turn_number if not present (first run in session)
    turn_number = state.get("turn_number", 1)
    
    # Create agent with dynamic system prompt
    agent = create_agent(
        general_agent_model,
        system_prompt=planner_agent_system_prompt()
    )
    
    result = agent.invoke({"messages": [{"role": "user", "content": user_query}]})
    print(result)
    # Extract token usage
    token_usage = extract_token_usage(result, agent_name="planner_agent", turn_number=turn_number)
    
    # Extract and parse plan steps
    plan_content = extract_agent_response_content(result)
    plan_steps = parse_plan_steps(plan_content)
    
    print("Parsed plan steps:", plan_steps)

    return_dict = {
        "plan_steps": plan_steps,
        "current_step_index": 0,
        "turn_number": turn_number
    }
    
    if token_usage:
        return_dict["token_usage_log"] = [token_usage]
    
    return return_dict

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
        Please provide a corrected PostgreSQL SQL query. Do not include any explanations or additional text, just SQL.

        System Prompt:
        {generate_sql_system_prompt()}
        """
    else:
        # CONTEXT: The agent is in "Initial Generation Mode"
        # Include the current step being processed
        prompt = f"""
        {generate_sql_system_prompt()}
        """

    agent = create_agent(
        sql_agent_model,
        system_prompt=prompt
    )

    response = agent.invoke({"messages": [{"role": "user", "content": current_step}]})
    
    # Extract token usage with turn number
    turn_number = state.get("turn_number", 1)
    token_usage = extract_token_usage(response, agent_name="text_to_sql_agent", turn_number=turn_number)
    
    # Get text content from agent response (supports dict or object results)
    response_text = extract_agent_response_content(response)
    
    # Parse and clean the SQL query for display
    sql_query = parse_sql_query(response_text)
    
    # Create a formatted review message for the frontend (since interrupt_before stops before Human_Review node)
    review_message = f"""**SQL Query Ready for Review**

**Task:** {current_step}

**Generated SQL:**
```sql
{sql_query}
```

Please review the SQL query above. Click **Continue** to execute it, or provide feedback to regenerate it."""
    
    return_dict = {
        "generated_sql": response_text,
        "error_log": "",  # Clear the error once we retry
        "messages": [{"type": "ai", "content": review_message}],
    }
    
    if token_usage:
        return_dict["token_usage_log"] = [token_usage]
    print(f" ! SQL Generated for review:\n{sql_query}")
    return return_dict

def sql_executor(state: AgentState) -> AgentState:
    """Execute a SELECT query and return results with updated state."""
    sql_query = state.get("generated_sql", "")
    
    if not sql_query:
        error_msg = "No SQL query generated to execute."
        return {
            "error_log": error_msg,
            "messages": [{"type": "ai", "content": f"**SQL Execution Error**\n\n{error_msg}"}]
        }
    
    # Parse and clean the SQL query to remove markdown code block markers
    sql_query = parse_sql_query(sql_query)
    
    try:
        # Validate first
        forbidden = detect_dml_statements(sql_query)
        if forbidden:
            error_msg = f"Cannot execute SQL. Forbidden statements detected: {', '.join([s['statement'] for s in forbidden])}. Please regenerate the SQL query without these forbidden operations."
            return {
                "error_log": error_msg,
                "messages": [{"type": "ai", "content": f"**SQL Execution Error**\n\n{error_msg}"}]
            }
        
        # Get thread-safe PostgreSQL connection
        conn = get_db_connection()
        
        # Execute query and fetch results into DataFrame
        cursor = conn.cursor()
        try:
            cursor.execute(sql_query)
            
            # Fetch column names
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch all rows
            rows = cursor.fetchall()
            
            # Convert to pandas DataFrame
            result = pd.DataFrame(rows, columns=columns)
        except Exception as e:
            # If not in autocommit mode, rollback the transaction
            if not conn.autocommit:
                conn.rollback()
            raise e
        finally:
            cursor.close()
        
        # Convert datetime/timestamp columns to ISO format strings for JSON serialization
        for col in result.columns:
            if pd.api.types.is_datetime64_any_dtype(result[col]):
                result[col] = result[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert Decimal types to float for JSON serialization
        for col in result.columns:
            if result[col].dtype == 'object':
                # Check if column contains Decimal objects
                if len(result[col]) > 0 and isinstance(result[col].iloc[0], Decimal):
                    result[col] = result[col].astype(float)
        
        # Round numeric columns to 2 decimal places
        for col in result.columns:
            if pd.api.types.is_numeric_dtype(result[col]) and pd.api.types.is_float_dtype(result[col]):
                result[col] = result[col].round(2)
        
        # Store metadata in JSON format
        metadata = {
            "columns": result.columns.to_list(),
            "num_columns": len(result.columns),
            "num_rows": len(result),
            "describe": result.describe().to_dict(orient='split')
        }
        records_json = result.to_dict(orient='records')
        
        # Convert any Decimal objects to float for JSON serialization
        records_json = convert_decimals_to_float(records_json)
        metadata = convert_decimals_to_float(metadata)
        
        # Convert any date/datetime/time objects to ISO format strings
        records_json = convert_dates_to_strings(records_json)
        metadata = convert_dates_to_strings(metadata)
        
        result_json = {
            "sql_query": sql_query,
            "metadata": metadata,
            "data": records_json
        }

        # Generate a unique key for this query result
        query_key = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Store result_json in module-level cache (will be saved at session end)
        query_results_cache[query_key] = result_json
        
        success_message = f"The SQL Query executed successfully! Rows returned: {len(result)}. Columns: {', '.join(result.columns)}."
        
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
        
        # Return updated state with the SQL output message
        return {
            "error_log": "",  # Clear any previous errors
            "analysis_history": [analysis_entry],
            "current_step_index": next_index,
            "messages": [{"type": "ai", "content": success_message}]
        }
    
    except Exception as e:
        error_msg = f"Failed to execute SQL query. Error details: {str(e)}"
        user_facing_msg = f"""**SQL Execution Error**

{str(e)}

*Attempting to regenerate the query...*"""
        return {
            "error_log": error_msg,
            "messages": [{"type": "ai", "content": user_facing_msg}]
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
    """Human review checkpoint - this node executes after user approves.
    
    Note: The review message is sent by text_to_sql_agent before the interrupt.
    This node simply passes through after user clicks Continue.
    """
    sql_query = state.get("generated_sql", "")
    sql_query = parse_sql_query(sql_query)
    
    # Return empty dict - the review message was already sent by text_to_sql_agent
    return {}

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
    x_axis_name = viz_spec.get("x_axis_name")
    y_axis_name = viz_spec.get("y_axis_name")
    series_labels = viz_spec.get("series_labels")  # Dict mapping column names to display labels
    series_name = viz_spec.get("series_name")  # For pie chart series name
    
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
        return echarts_bar(x_col, y_col, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name)
    elif chart_type == "bar_horizontal":
        return echarts_bar_horizontal(x_column = x_col, y_column = y_col, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name)
    elif chart_type == "bar_stacked":
        category_col = x_col or y_col
        value_columns = ensure_value_columns_list(value_columns, y_col, x_col)
        return echarts_bar_stacked(category_col, value_columns, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name, series_labels=series_labels)
    elif chart_type == "bar_grouped":
        category_col = x_col or y_col
        value_columns = ensure_value_columns_list(value_columns, y_col, x_col)
        return echarts_bar_grouped(category_col, value_columns, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name, series_labels=series_labels)
    # elif chart_type == "bar_stacked_dual_axis":
    #     category_col = x_col or y_col
    #     primary_cols = viz_spec.get("primary_value_columns", [])
    #     secondary_cols = viz_spec.get("secondary_value_columns", [])
    #     primary_axis_name = viz_spec.get("primary_axis_name")
    #     secondary_axis_name = viz_spec.get("secondary_axis_name")
    #     return echarts_bar_stacked_dual_axis(
    #         category_col, primary_cols, secondary_cols, 
    #         query_result=query_result, title=title,
    #         primary_axis_name=primary_axis_name, 
    #         secondary_axis_name=secondary_axis_name,
    #         x_axis_name=x_axis_name,
    #         series_labels=series_labels
    #     )
    # elif chart_type == "bar_grouped_dual_axis":
    #     category_col = x_col or y_col
    #     primary_cols = viz_spec.get("primary_value_columns", [])
    #     secondary_cols = viz_spec.get("secondary_value_columns", [])
    #     primary_axis_name = viz_spec.get("primary_axis_name")
    #     secondary_axis_name = viz_spec.get("secondary_axis_name")
    #     return echarts_bar_grouped_dual_axis(
    #         category_col, primary_cols, secondary_cols, 
    #         query_result=query_result, title=title,
    #         primary_axis_name=primary_axis_name, 
    #         secondary_axis_name=secondary_axis_name,
    #         x_axis_name=x_axis_name,
    #         series_labels=series_labels
    #     )
    elif chart_type == "line":
        return echarts_line(x_col, y_col, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name)
    # elif chart_type == "line_smooth":
    #     return echarts_line_smooth(x_col, y_col, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name)
    # elif chart_type == "line_stacked":
    #     category_col = x_col or y_col
    #     value_columns = ensure_value_columns_list(value_columns, y_col, x_col)
    #     return echarts_line_stacked(category_col, value_columns, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name, series_labels=series_labels)
    elif chart_type == "area":
        return echarts_area(x_col, y_col, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name)
    elif chart_type == "area_stacked":
        category_col = x_col or y_col
        value_columns = ensure_value_columns_list(value_columns, y_col, x_col)
        return echarts_area_stacked(category_col, value_columns, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name, series_labels=series_labels)
    elif chart_type == "pie":
        # For pie charts, x_columns is name_column, y_columns is value_column
        return echarts_pie(x_col, y_col, title=title, query_result=query_result, series_name=series_name)
    elif chart_type == "scatter":
        # Extract optional scatter/bubble chart parameters
        subtitle = viz_spec.get("subtitle")
        size_column = viz_spec.get("size_column")
        label_column = viz_spec.get("label_column")
        x_axis_name = viz_spec.get("x_axis_name")
        y_axis_name = viz_spec.get("y_axis_name")
        
        return echarts_scatter(
            x_col, y_col, 
            title=title,
            subtitle=subtitle,
            size_column=size_column,
            label_column=label_column,
            x_axis_name=x_axis_name,
            y_axis_name=y_axis_name,
            query_result=query_result
        )
    elif chart_type == "boxplot":
        # Check if we have value_columns (multi-column comparison) or category-based
        # if value_columns and isinstance(value_columns, list) and len(value_columns) > 0:
        #     return echarts_boxplot_multi_column(value_columns, query_result=query_result, title=title, orientation="vertical")
        # else:
            # Precomputed boxplot: x_col is category, stats from min/q1/median/q3/max columns
            min_col = viz_spec.get("min_col", "min")
            q1_col = viz_spec.get("q1_col", "q1")
            median_col = viz_spec.get("median_col", "median")
            q3_col = viz_spec.get("q3_col", "q3")
            max_col = viz_spec.get("max_col", "max")
            return echarts_boxplot(x_col, query_result=query_result, title=title,
                                   min_col=min_col, q1_col=q1_col, median_col=median_col,
                                   q3_col=q3_col, max_col=max_col)
    # elif chart_type == "boxplot_horizontal":
    #     if value_columns and isinstance(value_columns, list) and len(value_columns) > 0:
    #         return echarts_boxplot_multi_column(value_columns, query_result=query_result, title=title, orientation="horizontal")
    #     else:
    #         min_col = viz_spec.get("min_col", "min")
    #         q1_col = viz_spec.get("q1_col", "q1")
    #         median_col = viz_spec.get("median_col", "median")
    #         q3_col = viz_spec.get("q3_col", "q3")
    #         max_col = viz_spec.get("max_col", "max")
    #         return echarts_boxplot_horizontal(x_col, query_result=query_result, title=title,
    #                                           min_col=min_col, q1_col=q1_col, median_col=median_col,
    #                                           q3_col=q3_col, max_col=max_col)
    # elif chart_type == "boxplot_dual_axis":
    #     primary_cats = viz_spec.get("primary_categories", [])
    #     secondary_cats = viz_spec.get("secondary_categories", [])
    #     primary_axis_name = viz_spec.get("primary_axis_name")
    #     secondary_axis_name = viz_spec.get("secondary_axis_name")
    #     min_col = viz_spec.get("min_col", "min")
    #     q1_col = viz_spec.get("q1_col", "q1")
    #     median_col = viz_spec.get("median_col", "median")
    #     q3_col = viz_spec.get("q3_col", "q3")
    #     max_col = viz_spec.get("max_col", "max")
    #     return echarts_boxplot_dual_axis(
    #         x_col, primary_cats, secondary_cats,
    #         query_result=query_result, title=title,
    #         min_col=min_col, q1_col=q1_col, median_col=median_col,
    #         q3_col=q3_col, max_col=max_col,
    #         primary_axis_name=primary_axis_name,
    #         secondary_axis_name=secondary_axis_name
    #     )
    elif chart_type == "heatmap":
        # value_columns should be a single column name for basic heatmap
        value_col = value_columns[0] if isinstance(value_columns, list) and value_columns else value_columns
        if not value_col:
            value_col = "value"  # fallback
        return echarts_heatmap(x_col, y_col, value_col, title=title, query_result=query_result, x_axis_name=x_axis_name, y_axis_name=y_axis_name)
    # elif chart_type == "heatmap_time_series":
    #     # x_columns = date/time category, y_columns = time category, value_columns = value column
    #     value_col = value_columns[0] if isinstance(value_columns, list) and value_columns else value_columns
    #     if not value_col:
    #         value_col = "value"  # fallback
    #     return echarts_heatmap_time_series(x_col, y_col, value_col, title=title, query_result=query_result, x_axis_name=x_axis_name, y_axis_name=y_axis_name)
    elif chart_type == "heatmap_correlation":
        # value_columns should be a list of column names to correlate
        columns = value_columns if isinstance(value_columns, list) else [value_columns]
        return echarts_heatmap_correlation(columns, title=title, query_result=query_result)
    # elif chart_type == "heatmap_calendar":
    #     # x_columns = date column, value_columns = value column, year from viz_spec
    #     value_col = value_columns[0] if isinstance(value_columns, list) and value_columns else value_columns
    #     if not value_col:
    #         value_col = "value"  # fallback
    #     year = viz_spec.get("year", 2024)  # Default to 2024 if not specified
    #     return echarts_heatmap_calendar(x_col, value_col, year, title=title, query_result=query_result)
    elif chart_type == "bar_line":
        bar_columns = viz_spec.get("bar_columns", [])
        line_columns = viz_spec.get("line_columns", [])
        primary_axis_name = viz_spec.get("primary_axis_name", "")
        secondary_axis_name = viz_spec.get("secondary_axis_name", "")
        return echarts_bar_line(
            x_column=x_col,
            bar_columns=bar_columns,
            line_columns=line_columns,
            primary_axis_name=primary_axis_name,
            secondary_axis_name=secondary_axis_name,
            query_result=query_result,
            title=title,
            x_axis_name=x_axis_name,
            series_labels=series_labels
        )
    # elif chart_type == "bar_line_single_axis":
    #     bar_columns = viz_spec.get("bar_columns", [])
    #     line_columns = viz_spec.get("line_columns", [])
    #     axis_name = viz_spec.get("axis_name", "")
    #     return echarts_bar_line_single_axis(
    #         x_column=x_col,
    #         bar_columns=bar_columns,
    #         line_columns=line_columns,
    #         axis_name=axis_name,
    #         query_result=query_result,
    #         title=title,
    #         x_axis_name=x_axis_name,
    #         series_labels=series_labels
    #     )
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
    chart_type = "none"  # Default if not specified
    if 0 <= last_step_index < len(data_steps):
        current_task = data_steps[last_step_index].get("task", user_input)
        chart_type = data_steps[last_step_index].get("chart_type", "none")
    
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
        data_visual_agent_model,
        system_prompt=data_vis_system_prompt(
            query_metadata=query_metadata
        )
    )
    
    result = agent.invoke({"messages": [{"role": "user", "content": current_task}]})
    
    # Extract token usage with turn number
    turn_number = state.get("turn_number", 1)
    token_usage = extract_token_usage(result, agent_name="data_visual_agent", turn_number=turn_number)
    
    # Extract visualization output and store in state
    viz_content = extract_agent_response_content(result)
    try:
        viz_spec = json.loads(viz_content)
        
        # Handle both single dict and list of dicts
        if isinstance(viz_spec, list):
            # If it's a list, take the first item (most common case for single chart per step)
            if viz_spec:
                viz_spec = viz_spec[0]
            else:
                raise ValueError("Empty visualization specification list")
        
        # Generate chart config and include it in the output for visibility
        chart_config = map_visualization_spec_to_chart(viz_spec, query_result=query_result)
        
        # Store both spec AND chart config in viz_output for node visibility
        # This makes the full chart config visible in the node output
        viz_output = json.dumps({
            "specification": viz_spec,
            "chart_config": chart_config
        }, indent=2)
    except json.JSONDecodeError:
        # If parsing fails, keep original content
        viz_output = viz_content
    except (ValueError, KeyError) as e:
        # If visualization spec is invalid, log error and keep original content
        print(f"Warning: Invalid visualization specification: {e}")
        viz_output = viz_content
    
    # Add visualization to analysis history
    viz_entry = {
        "type": "visualization",
        "query_key": query_key,
        "visualization_content": viz_output,
        "timestamp": datetime.now().isoformat()
    }
    
    return_dict = {
        "final_response": viz_output,
        "analysis_history": [viz_entry],
        "chart_configs": [chart_config]  # Save chart config for later use
    }
    
    if token_usage:
        return_dict["token_usage_log"] = [token_usage]
    
    return return_dict


def response_synthesizer_agent_node(state: AgentState):
    """Custom node that synthesizes response with chart specs and minimal data summary.
    
    Only passes:
    - chart_specs: Visualization specifications (spec only, no full chart config)
    - metadata: Minimal summary with key statistics only
    - data_sample: First 5-10 rows only for context
    """
    # Get user query from state
    user_query = state.get("user_query", "")
    
    # Get data visualizer output from state - extract only the spec, not the full chart config
    viz_output = state.get("final_response", "")
    chart_specs = ""
    if viz_output:
        try:
            viz_output_json = json.loads(viz_output)
            # Only pass the specification to the response synthesizer, not the full chart_config
            chart_specs = json.dumps({"specification": viz_output_json.get("specification", {})}, indent=2)
        except json.JSONDecodeError:
            chart_specs = viz_output
    
    # Get query results from cache - extract only minimal metadata and small sample
    query_result = get_latest_query_result()
    metadata = {}
    if query_result and isinstance(query_result, dict):
        original_metadata = query_result.get("metadata", {})
        
        # Create minimal metadata summary (avoid full describe array)
        metadata = {
            "columns": original_metadata.get("columns", []),
            "num_columns": original_metadata.get("num_columns", 0),
            "num_rows": original_metadata.get("num_rows", 0)
        }
        
        # Extract only key summary statistics from describe (not full array)
        describe_data = original_metadata.get("describe", {})
        if describe_data and "data" in describe_data and "index" in describe_data:
            # Convert describe array format to simple dict with key stats only
            stats_summary = {}
            index_labels = describe_data["index"]
            for col_idx, col_name in enumerate(describe_data.get("columns", [])):
                if col_idx < len(describe_data["data"][0]):
                    stats_summary[col_name] = {
                        label: describe_data["data"][idx][col_idx] 
                        for idx, label in enumerate(index_labels)
                        if label in ["count", "mean", "min", "max", "25%", "50%", "75%"]
                    }
            metadata["summary_statistics"] = stats_summary
        
        # Include only a very small sample of the data for context (5-10 rows)
        if query_result.get("data"):
            metadata["data_sample"] = query_result["data"][:10]  # First 10 rows only
    
    # Create agent with dynamic system prompt including actual metadata
    agent = create_agent(
        general_agent_model,
        system_prompt=response_synthesizer_system_prompt(
            chart_specs=chart_specs, 
            metadata=metadata
        )
    )
    
    # Invoke agent with a simple message state
    result = agent.invoke(  {"messages": [{"role": "user", "content": user_query}]} )
    
    # Extract token usage with turn number
    turn_number = state.get("turn_number", 1)
    token_usage = extract_token_usage(result, agent_name="response_synthesizer_agent", turn_number=turn_number)
    
    # Extract final response and store in state
    raw_content = extract_agent_response_content(result)
    final_content = extract_agent_response_content(result)

    # Strip any JSON code blocks the LLM may have generated from the chart_specs context
    # (the LLM sometimes reproduces the viz spec as a code block; we only want the real ECharts config)
    final_content = re.sub(r'```json\s*\n.*?\n```', '', final_content, flags=re.DOTALL).strip()

    # Replace {{chart_json}} placeholder with actual chart config wrapped in JSON code block
    chart_configs = state.get("chart_configs", [])
    if chart_configs and "{chart_json}" in final_content:
        # Get the most recent chart config (last one added)
        latest_chart_config = chart_configs[-1]
        # Convert chart config to formatted JSON string and wrap in code block for rendering
        chart_json_str = json.dumps(latest_chart_config, indent=2, ensure_ascii=False)
        chart_json_block = f"```json\n{chart_json_str}\n```"
        # Replace the placeholder with the JSON code block
        final_content = final_content.replace("{chart_json}", chart_json_block)
    
    # Save all query results from this session to disk
    save_query_results(save_all=True)
    print(f" ! Saved {len(query_results_cache)} query results to disk")
    
    # Save accumulated token usage to file - only for current turn to avoid duplication
    turn_number = state.get("turn_number", 1)
    token_usage_log = state.get("token_usage_log", [])
    # Combine existing log with current usage
    complete_log = token_usage_log + ([token_usage] if token_usage else [])
    # Filter to only include current turn's token usage
    current_turn_log = [entry for entry in complete_log if entry.get("turn_number") == turn_number]
    
    if current_turn_log:
        save_result = save_token_usage_to_file(current_turn_log)
        if save_result["success"]:
            print(f" ! Saved token usage to disk: {save_result['totals']['total_tokens']} total tokens")
        else:
            print(f" ! Failed to save token usage: {save_result.get('error', 'Unknown error')}")
    
    # Add to chat history
    chat_entry = {
        "user_input": user_query,
        "final_response": raw_content,
        "timestamp": datetime.now().isoformat()
    }
    
    return_dict = {
        "final_response": final_content,
        "chat_history": [chat_entry],
        "turn_number": turn_number + 1,  # Increment turn number for next run
        "raw_agent_response": raw_content,
        "messages": [{"type": "ai", "content": final_content}]
    }
    
    if token_usage:
        return_dict["token_usage_log"] = [token_usage]
    print(return_dict)
    return return_dict

def route_intention(state: AgentState):
    """Route based on user intention classification."""
    intention = state.get("intention", "ANALYZE")
    
    if intention == "GENERAL_SCHEMA":
        return "Schema_Info_Agent"
    else:
        return "Planner_Agent"


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
graph.add_node("Preprocess_Input", preprocess_input)
graph.add_node("Intention_Agent", intention_agent)
graph.add_node("Schema_Info_Agent", schema_info_agent)
graph.add_node("Planner_Agent", planner_agent)
graph.add_node("Text_to_SQL_Agent", text_to_sql_agent)
graph.add_node("Human_Review", human_review_node)
graph.add_node("SQL_Executor", sql_executor)
graph.add_node("Data_Visual_Agent", data_visual_agent_node)
graph.add_node("Response_Synthesizer", response_synthesizer_agent_node)

# 0. Start with input preprocessing to extract user_query from messages
graph.add_edge(START, "Preprocess_Input")

# 1. Continue with Intention Classification
graph.add_edge("Preprocess_Input", "Intention_Agent")

# 2. Route based on intention
graph.add_conditional_edges(
    "Intention_Agent",
    route_intention,
    {
        "Schema_Info_Agent": "Schema_Info_Agent",
        "Planner_Agent": "Planner_Agent"
    }
)

# 3. Schema Info path goes directly to END
graph.add_edge("Schema_Info_Agent", END)

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