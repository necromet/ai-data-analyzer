from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt
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
    echarts_bar_grouped
)
from agent.artifacts.line_chart import (
    echarts_line,
    echarts_line_smooth,
    echarts_line_stacked,
    echarts_area,
    echarts_area_stacked
)
from agent.artifacts.bar_line_chart import (
    echarts_bar_line
)
from agent.artifacts.pie_chart import echarts_pie
from agent.artifacts.scatter_chart import echarts_scatter
from agent.artifacts.box_plot import (
    echarts_boxplot
)
from agent.artifacts.heatmap_chart import (
    echarts_heatmap,
    echarts_heatmap_correlation
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

# ---------------------------------------------------------------------------
# Module-level cache for query results (populated by sql_executor)
# ---------------------------------------------------------------------------
query_results_cache = {}

# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------
model_configs = {
    "intention_agent": {
        "model_name": "gpt-5-mini-2025-08-07",
        "temperature": 0,
        "max_tokens": 500,
        "reasoning_effort": "low"
    },
    "planner_agent": {
        "model_name": "gpt-5-mini-2025-08-07",
        "temperature": 0.2,
        "max_tokens": 1500,
        "reasoning_effort": "low"
    },
    "schema_agent": {
        "model_name": "gpt-5-mini-2025-08-07",
        "temperature": 0.3,
        "max_tokens": 5000,
        "reasoning_effort": "low"
    },
    "sql_agent": {
        "model_name": "gpt-5-mini-2025-08-07",
        "temperature": 0,
        "max_tokens": 10000,
        "reasoning_effort": "low"
    },
    "data_visual_agent": {
        "model_name": "gpt-5-mini-2025-08-07",
        "temperature": 0,
        "max_tokens": 3000,
        "reasoning_effort": "low"
    },
    "general_agent": {
        "model_name": "gpt-5-mini-2025-08-07",
        "temperature": 0.2,
        "max_tokens": 10000,
        "reasoning_effort": "low"
    }
}

agents = {
    agent_name: ChatOpenAI(**config)
    for agent_name, config in model_configs.items()
}

intention_agent_model = agents["intention_agent"]
planner_agent_model = agents["planner_agent"]
schema_agent_model = agents["schema_agent"]
sql_agent_model = agents["sql_agent"]
data_visual_agent_model = agents["data_visual_agent"]
general_agent_model = agents["general_agent"]

# ---------------------------------------------------------------------------
# Shared state definition
# ---------------------------------------------------------------------------
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
    sql_retry_count: NotRequired[int]  # Track number of SQL generation retries to prevent infinite loops
    human_decision: NotRequired[str]  # User decision at human review: "approve" or "cancel"

    # 4. Final Outputs
    final_response: NotRequired[str]
    raw_agent_response: NotRequired[str]  # Raw agent response before chart_json placeholder substitution
    chart_configs: NotRequired[Annotated[List[dict], operator.add]]  # Chart configurations for visualization
    chat_history: NotRequired[Annotated[List[dict], operator.add]]  # Conversation history with user input and final responses
    token_usage_log: NotRequired[Annotated[List[dict], operator.add]]  # Token usage for each agent call


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

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


def convert_data_to_toon_format(query_result: dict, data_limit: int = 30) -> str:
    """Convert query result data to TOON (table) format with a data limit.
    
    Example output:
    query_result[30]{product_id, product_name, total_revenue, total_quantity_sold}:
    1, "bb50f2e236", "beleza_saude", "63885.00", 195
    2, "6cdd538434", "beleza_saude", "54730.20", 156
    3, "d6160fb787", "pcs", "48899.34", 35
    ...
    
    Args:
        query_result: Dictionary containing 'data' and 'metadata' keys
        data_limit: Maximum number of rows to include in the output
        
    Returns:
        String in TOON table format
    """
    if not query_result or not isinstance(query_result, dict):
        return ""
    
    data = query_result.get("data", [])
    if not data:
        return ""
    
    metadata = query_result.get("metadata", {})
    columns = metadata.get("columns", [])
    num_rows = metadata.get("num_rows", len(data))
    
    # If no columns from metadata, try to extract from first row
    if not columns and data:
        columns = list(data[0].keys())
    
    table_name = "query_result"
    column_str = ", ".join(columns)
    
    lines = []
    lines.append(f'{table_name}[{data_limit}]{{{column_str}}}:')
    
    for idx, row in enumerate(data[:data_limit], start=1):  # Limit rows to data_limit
        values = []
        for col in columns:
            value = row.get(col)
            if value is None:
                values.append("null")
            elif isinstance(value, str):
                # Escape double quotes in strings
                escaped = value.replace('"', '\\"')
                values.append(f'"{escaped}"')
            elif isinstance(value, (int, float)):
                values.append(str(value))
            else:
                values.append(f'"{str(value)}"')
        
        line = f"{idx}, {', '.join(values)}"
        lines.append(line)
    
    data_toon = "\n".join(lines)
    print(data_toon)
    return data_toon


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
        usage_data = None
        model_name = "unknown"

        if "messages" in result:
            messages = result["messages"]
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

        input_tokens = usage_data.get('input_tokens', 0)
        output_tokens = usage_data.get('output_tokens', 0)
        total_tokens = usage_data.get('total_tokens', 0)

        reasoning_tokens = 0
        if 'output_token_details' in usage_data:
            reasoning_tokens = usage_data['output_token_details'].get('reasoning', 0)

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

    current_dir = os.path.dirname(os.path.abspath(__file__))
    token_usage_dir = os.path.join(current_dir, "token_usage")
    os.makedirs(token_usage_dir, exist_ok=True)

    try:
        total_input = sum(record.get('input_tokens', 0) for record in token_usage_log)
        total_output = sum(record.get('output_tokens', 0) for record in token_usage_log)
        total_reasoning = sum(record.get('reasoning_tokens', 0) for record in token_usage_log)
        total_all = sum(record.get('total_tokens', 0) for record in token_usage_log)

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

        filename = f"token_usage_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        file_path = os.path.join(token_usage_dir, filename)

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
    """Parse and clean SQL query by removing markdown code block markers.

    Args:
        sql_text: Raw SQL text that may contain markdown formatting

    Returns:
        Cleaned SQL query string
    """
    if not sql_text:
        return sql_text

    cleaned = re.sub(r'^\s*```(?:sql)?\s*\n?|\n?\s*```\s*$', '', sql_text.strip(), flags=re.IGNORECASE)
    return cleaned.strip()


def extract_agent_response_content(result) -> str:
    """Extract text content from various agent result formats.

    Supports:
    - dict results with a `messages` list of dicts or objects
    - dict results with a top-level `content` key
    - objects with a `content` attribute
    - fallback to str(result)
    """
    content = ""

    if isinstance(result, dict) and "messages" in result:
        messages = result["messages"]
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("content"):
                content = msg.get("content")
                break
            elif hasattr(msg, "content") and getattr(msg, "content"):
                content = msg.content
                break
    elif isinstance(result, dict) and result.get("content"):
        content = result.get("content")
    elif hasattr(result, "content"):
        content = result.content
    else:
        content = str(result)

    return content


def repair_json(text: str) -> str:
    """Attempt to repair common JSON formatting issues.

    Fixes:
    - Unquoted string values (e.g., chart_type: bar_grouped -> chart_type: "bar_grouped")
    """
    chart_types = [
        'line', 'line_smooth', 'line_stacked', 'area', 'area_stacked',
        'bar', 'bar_horizontal', 'bar_stacked', 'bar_grouped',
        'bar_stacked_dual_axis', 'bar_grouped_dual_axis',
        'bar_line', 'bar_line_single_axis',
        'pie', 'boxplot', 'boxplot_horizontal', 'boxplot_dual_axis',
        'heatmap', 'heatmap_time_series', 'heatmap_correlation', 'heatmap_calendar',
        'none'
    ]

    for chart_type in chart_types:
        pattern = rf'("chart_type"\s*:\s*)({chart_type})([,\s\}}])'
        replacement = rf'\1"\2"\3'
        text = re.sub(pattern, replacement, text)

    return text


def parse_plan_steps(text: str) -> List[dict]:
    """Parse plan steps from JSON formatted text."""
    try:
        parsed = json.loads(text)

        if isinstance(parsed, dict) and "plan" in parsed:
            return parsed["plan"]

        if isinstance(parsed, list):
            return parsed

        return [{
            "visualization": False,
            "sql_required": True,
            "task": str(parsed)
        }]

    except json.JSONDecodeError as e:
        try:
            repaired_text = repair_json(text)
            parsed = json.loads(repaired_text)

            print(f" ! JSON repair successful: Fixed invalid JSON")

            if isinstance(parsed, dict) and "plan" in parsed:
                return parsed["plan"]

            if isinstance(parsed, list):
                return parsed

            return [{
                "visualization": False,
                "sql_required": True,
                "task": str(parsed)
            }]

        except json.JSONDecodeError:
            print(f" ! JSON parsing failed even after repair: {e}")
            return [{
                "visualization": False,
                "sql_required": True,
                "task": text.strip()
            }]


def save_query_results(query_key: str = None, save_all: bool = False) -> dict:
    """Save query results from cache to the query_results folder as JSON files."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    query_results_dir = os.path.join(current_dir, "query_results")
    os.makedirs(query_results_dir, exist_ok=True)

    results = {
        "success": True,
        "saved_count": 0,
        "failed_count": 0,
        "errors": []
    }

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


def save_statistical_analysis_to_json(
    stats: dict,
    query_context: str = None
) -> dict:
    """Save statistical analysis results to a separate JSON file.
    
    Args:
        stats: Dictionary containing statistical analysis results
        query_context: Optional query context string for additional context
        
    Returns:
        dict: Result status with file path if successful
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    stats_dir = os.path.join(current_dir, "statistical_analysis")
    os.makedirs(stats_dir, exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"statistical_analysis_{timestamp}.json"
    file_path = os.path.join(stats_dir, filename)
    
    # Build the output structure
    output = {
        "timestamp": datetime.now().isoformat(),
        "query_context": query_context,
        "statistical_analysis": stats
    }
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        return {
            "success": True,
            "file_path": file_path,
            "columns_analyzed": len(stats)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_latest_query_result():
    """Retrieve the most recent query result from cache."""
    if not query_results_cache:
        return None
    latest_key = max(query_results_cache.keys())
    return query_results_cache[latest_key]


def detect_dml_statements(content: str) -> list[dict[str, str]]:
    """Detect forbidden SQL statements (DML, DDL, DCL, TCL)."""
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
                    break

    return found_statements


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
    value_columns = viz_spec.get("value_columns", [])
    x_axis_name = viz_spec.get("x_axis_name")
    y_axis_name = viz_spec.get("y_axis_name")
    x_axis_type = viz_spec.get("x_axis_type")
    y_axis_type = viz_spec.get("y_axis_type")
    series_labels = viz_spec.get("series_labels")
    series_name = viz_spec.get("series_name")

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
        return echarts_bar(x_col, y_col, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name, x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    elif chart_type == "bar_horizontal":
        return echarts_bar_horizontal(x_column=x_col, y_column=y_col, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name, x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    elif chart_type == "bar_stacked":
        category_col = x_col or y_col
        value_columns = ensure_value_columns_list(value_columns, y_col, x_col)
        return echarts_bar_stacked(category_col, value_columns, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name, series_labels=series_labels, x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    elif chart_type == "bar_grouped":
        category_col = x_col or y_col
        value_columns = ensure_value_columns_list(value_columns, y_col, x_col)
        return echarts_bar_grouped(category_col, value_columns, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name, series_labels=series_labels, x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    elif chart_type == "line":
        return echarts_line(x_col, y_col, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name, x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    elif chart_type == "line_smooth":
        return echarts_line_smooth(x_col, y_col, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name, x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    elif chart_type == "line_stacked":
        category_col = x_col or y_col
        value_columns = ensure_value_columns_list(value_columns, y_col, x_col)
        return echarts_line_stacked(category_col, value_columns, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name, series_labels=series_labels, x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    elif chart_type == "area":
        return echarts_area(x_col, y_col, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name, x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    elif chart_type == "area_stacked":
        category_col = x_col or y_col
        value_columns = ensure_value_columns_list(value_columns, y_col, x_col)
        return echarts_area_stacked(category_col, value_columns, query_result=query_result, title=title, x_axis_name=x_axis_name, y_axis_name=y_axis_name, series_labels=series_labels, x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    elif chart_type == "pie":
        return echarts_pie(x_col, y_col, title=title, query_result=query_result, series_name=series_name)
    elif chart_type == "scatter":
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
            x_axis_type=x_axis_type,
            y_axis_type=y_axis_type,
            query_result=query_result
        )
    elif chart_type == "boxplot":
        min_col = viz_spec.get("min_col", "min")
        q1_col = viz_spec.get("q1_col", "q1")
        median_col = viz_spec.get("median_col", "median")
        q3_col = viz_spec.get("q3_col", "q3")
        max_col = viz_spec.get("max_col", "max")
        return echarts_boxplot(x_col, query_result=query_result, title=title,
                               min_col=min_col, q1_col=q1_col, median_col=median_col,
                               q3_col=q3_col, max_col=max_col,
                               x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    elif chart_type == "heatmap":
        value_col = value_columns[0] if isinstance(value_columns, list) and value_columns else value_columns
        if not value_col:
            value_col = "value"
        return echarts_heatmap(x_col, y_col, value_col, title=title, query_result=query_result, x_axis_name=x_axis_name, y_axis_name=y_axis_name, x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    elif chart_type == "heatmap_correlation":
        columns = value_columns if isinstance(value_columns, list) else [value_columns]
        return echarts_heatmap_correlation(columns, title=title, query_result=query_result)
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
            series_labels=series_labels,
            x_axis_type=x_axis_type
        )
    elif chart_type in ("bar_stacked_dual_axis", "bar_grouped_dual_axis", "bar_line_single_axis"):
        bar_columns = viz_spec.get("bar_columns", [])
        line_columns = viz_spec.get("line_columns", [])
        primary_axis_name = viz_spec.get("primary_axis_name", "")
        secondary_axis_name = viz_spec.get("secondary_axis_name", "")
        return echarts_bar_line(
            x_column=x_col,
            bar_columns=bar_columns or ([y_col] if y_col else []),
            line_columns=line_columns or [],
            primary_axis_name=primary_axis_name,
            secondary_axis_name=secondary_axis_name,
            query_result=query_result,
            title=title,
            x_axis_name=x_axis_name,
            series_labels=series_labels,
            x_axis_type=x_axis_type
        )
    elif chart_type in ("boxplot_horizontal", "boxplot_dual_axis"):
        min_col = viz_spec.get("min_col", "min")
        q1_col = viz_spec.get("q1_col", "q1")
        median_col = viz_spec.get("median_col", "median")
        q3_col = viz_spec.get("q3_col", "q3")
        max_col = viz_spec.get("max_col", "max")
        return echarts_boxplot(x_col, query_result=query_result, title=title,
                               min_col=min_col, q1_col=q1_col, median_col=median_col,
                               q3_col=q3_col, max_col=max_col,
                               x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    elif chart_type in ("heatmap_time_series", "heatmap_calendar"):
        value_col = value_columns[0] if isinstance(value_columns, list) and value_columns else value_columns
        if not value_col:
            value_col = "value"
        return echarts_heatmap(x_col, y_col, value_col, title=title, query_result=query_result, x_axis_name=x_axis_name, y_axis_name=y_axis_name, x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    else:
        return {"error": f"Unknown chart type: {chart_type}"}


def compute_statistical_analysis(df: pd.DataFrame, num_rows: int) -> dict:
    """Compute outliers and distribution shape for eligible numeric columns."""
    stats = {}

    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        if df[col].nunique() < 5:
            continue  # Likely categorical/ordinal
        if num_rows < 30:
            continue  # Too small for meaningful analysis

        series = df[col].dropna()
        col_stats = {}

        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = series[(series < lower) | (series > upper)]
        col_stats["outlier_count"] = len(outliers)
        col_stats["outlier_pct"] = round(len(outliers) / len(series) * 100, 2)

        skewness = round(series.skew(), 3)
        kurtosis = round(series.kurtosis(), 3)
        col_stats["skewness"] = skewness
        col_stats["kurtosis"] = kurtosis

        if abs(skewness) < 0.5:
            col_stats["distribution_shape"] = "approximately_normal"
        elif skewness > 0.5:
            col_stats["distribution_shape"] = "right_skewed"
        else:
            col_stats["distribution_shape"] = "left_skewed"

        stats[col] = col_stats

    return stats


# ---------------------------------------------------------------------------
# Agent node functions
# ---------------------------------------------------------------------------

def preprocess_input(state: AgentState):
    """Extract user_query from messages (always use the latest human message) or from direct input."""
    user_query = state.get("user_query", "")
    messages = state.get("messages", [])
    chat_history = state.get("chat_history", [])

    print(chat_history)

    if messages:
        for msg in reversed(messages):
            msg_type = msg.get("type") if isinstance(msg, dict) else getattr(msg, "type", None)
            msg_content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")

            if msg_type == "human" and msg_content:
                user_query = msg_content
                break

    turn_number = state.get("turn_number", 1)

    print(f" ! Preprocessing: Extracted user query: {user_query[:100] if user_query else 'None'}...")

    agent = create_agent(
        intention_agent_model,
        system_prompt=context_resolver_agent_system_prompt()
    )

    formatted_history = []
    for entry in chat_history:
        if "user_input" in entry and "final_response" in entry:
            formatted_history.append({"role": "user", "content": entry["user_input"]})
            formatted_history.append({"role": "assistant", "content": entry["final_response"]})
    
    formatted_history.append({"role": "user", "content": user_query})
    result = invoke_and_save(agent, "context_resolver_agent", formatted_history)
    token_usage = extract_token_usage(result, agent_name="context_resolver_agent", turn_number=turn_number)

    processed_text = extract_agent_response_content(result).strip()
    print(processed_text)

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
    
    result = invoke_and_save(agent, "intention_agent", [{"role": "user", "content": user_query}])
    
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

    result = invoke_and_save(agent, "schema_info_agent", formatted_history)
    
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


def planner_agent(state: AgentState):
    """Custom node that extracts user query from state for the planner."""
    user_query = state.get("user_query", "")
    turn_number = state.get("turn_number", 1)

    agent = create_agent(
        planner_agent_model,
        system_prompt=planner_agent_system_prompt()
    )

    result = invoke_and_save(agent, "planner_agent", [{"role": "user", "content": user_query}])
    print(result)

    token_usage = extract_token_usage(result, agent_name="planner_agent", turn_number=turn_number)

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

    # Increment retry count if there's an error (self-correction loop)
    retry_count = state.get("sql_retry_count", 0)
    if error_log:
        retry_count += 1
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
        # Reset retry count for new SQL generation
        retry_count = 0
        # CONTEXT: The agent is in "Initial Generation Mode"
        # Include the current step being processed
        prompt = f"""
        {generate_sql_system_prompt()}
        """

    agent = create_agent(
        sql_agent_model,
        system_prompt=prompt
    )

    response = invoke_and_save(agent, "text_to_sql_agent", [{"role": "user", "content": current_step}])
    
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
        "sql_retry_count": retry_count,
        "human_decision": "approve",  # Reset human decision for new review
        "messages": [{"type": "ai", "content": review_message}],
    }
    
    if token_usage:
        return_dict["token_usage_log"] = [token_usage]
    print(f" ! SQL Generated for review (retry count: {retry_count}):\n{sql_query}")
    return return_dict


def human_review_node(state: AgentState):
    """Human review checkpoint - pauses execution and waits for user decision.

    Uses LangGraph's interrupt() to pause the graph and wait for the user
    to approve or cancel the SQL query via the frontend.
    """
    sql_query = state.get("generated_sql", "")
    sql_query = parse_sql_query(sql_query)
    current_step_index = state.get("current_step_index", 0)
    plan_steps = state.get("plan_steps", [])
    data_steps = [s for s in plan_steps if s.get("sql_required", True)]
    current_step_dict = data_steps[current_step_index] if current_step_index < len(data_steps) else None
    task = current_step_dict.get("task", state.get("user_query", "")) if current_step_dict else state.get("user_query", "")

    human_decision = interrupt({
        "sql_query": sql_query,
        "task": task,
    })

    if human_decision == "cancel":
        cancel_message = "**Query Cancelled**\n\nThe SQL query execution was cancelled by the user."
        return {
            "human_decision": "cancel",
            "messages": [{"type": "ai", "content": cancel_message}],
        }

    return {"human_decision": "approve"}


def sql_executor(state: AgentState) -> AgentState:
    """Execute a SELECT query and return results with updated state."""
    sql_query = state.get("generated_sql", "")

    if not sql_query:
        error_msg = "No SQL query generated to execute."
        return {
            "error_log": error_msg,
            "messages": [{"type": "ai", "content": f"**SQL Execution Error**\n\n{error_msg}"}]
        }

    sql_query = parse_sql_query(sql_query)

    try:
        forbidden = detect_dml_statements(sql_query)
        if forbidden:
            error_msg = f"Cannot execute SQL. Forbidden statements detected: {', '.join([s['statement'] for s in forbidden])}. Please regenerate the SQL query without these forbidden operations."
            return {
                "error_log": error_msg,
                "messages": [{"type": "ai", "content": f"**SQL Execution Error**\n\n{error_msg}"}]
            }

        conn = get_db_connection()

        cursor = conn.cursor()
        try:
            cursor.execute(sql_query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = pd.DataFrame(rows, columns=columns)
        except Exception as e:
            if not conn.autocommit:
                conn.rollback()
            raise e
        finally:
            cursor.close()

        for col in result.columns:
            if pd.api.types.is_datetime64_any_dtype(result[col]):
                result[col] = result[col].dt.strftime('%Y-%m-%d %H:%M:%S')

        for col in result.columns:
            if result[col].dtype == 'object':
                if len(result[col]) > 0 and isinstance(result[col].iloc[0], Decimal):
                    result[col] = result[col].astype(float)

        for col in result.columns:
            if pd.api.types.is_numeric_dtype(result[col]) and pd.api.types.is_float_dtype(result[col]):
                result[col] = result[col].round(2)

        metadata = {
            "columns": result.columns.to_list(),
            "num_columns": len(result.columns),
            "num_rows": len(result),
            "describe": result.describe().to_dict(orient='split')
        }
        records_json = result.to_dict(orient='records')

        records_json = convert_decimals_to_float(records_json)
        metadata = convert_decimals_to_float(metadata)
        records_json = convert_dates_to_strings(records_json)
        metadata = convert_dates_to_strings(metadata)

        result_json = {
            "sql_query": sql_query,
            "metadata": metadata,
            "data": records_json
        }

        query_key = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        query_results_cache[query_key] = result_json

        success_message = f"The SQL Query executed successfully! Rows returned: {len(result)}. Columns: {', '.join(result.columns)}."

        analysis_entry = {
            "type": "sql_execution",
            "query_key": query_key,
            "sql": sql_query,
            "rows": len(result),
            "columns": result.columns.to_list(),
            "timestamp": datetime.now().isoformat()
        }

        current_index = state.get("current_step_index", 0)
        next_index = current_index + 1

        return {
            "error_log": "",
            "sql_retry_count": 0,  # Reset retry count on successful execution
            "analysis_history": [analysis_entry],
            "current_step_index": next_index,
            "messages": [{"type": "ai", "content": success_message}]
        }

    except Exception as e:
        error_msg = f"Failed to execute SQL query. Error details: {str(e)}"
        error_str = str(e).lower()
        
        # Check if error is about aborted transaction or timeout - don't regenerate for these
        is_aborted_transaction = "transaction is aborted" in error_str
        is_timeout = "timeout" in error_str or "connection timeout" in error_str
        
        if is_aborted_transaction or is_timeout:
            # Don't suggest regeneration for these specific errors
            user_facing_msg = f"""**SQL Execution Error**

{str(e)}

This error is typically environmental and regenerating the query won't help. Please try again."""
        else:
            # For other errors, suggest regeneration
            user_facing_msg = f"""**SQL Execution Error**

{str(e)}

*Attempting to regenerate the query...*"""
        
        return {
            "error_log": error_msg,
            "messages": [{"type": "ai", "content": user_facing_msg}]
        }


def statistical_analysis_node(state: AgentState):
    """Optional node: Compute outliers/distribution for large or exploratory queries."""
    query_result = get_latest_query_result()

    if not query_result or not query_result.get("data"):
        return {}

    num_rows = query_result["metadata"].get("num_rows", 0)

    if num_rows < 30:
        return {}

    df = pd.DataFrame(query_result["data"])
    stats = compute_statistical_analysis(df, num_rows)

    if not stats:
        return {}

    latest_key = max(query_results_cache.keys())
    query_results_cache[latest_key]["statistical_analysis"] = stats
    
    # Get query context from state if available
    query_context = state.get("user_query", None)
    
    # Save statistical analysis to separate JSON file
    save_result = save_statistical_analysis_to_json(stats, query_context)
    
    if save_result.get("success"):
        print(f" ! Statistical analysis saved to: {save_result['file_path']}")
    else:
        print(f" ! Failed to save statistical analysis: {save_result.get('error')}")

    print(f" ! Statistical analysis computed for {len(stats)} columns")
    return {}


def data_visual_agent_node(state: AgentState):
    """Custom node that creates visualizations based on query results."""
    user_input = state.get("user_query", "")
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
        
        analysis_history = state.get("analysis_history", [])
        sql_entries = [e for e in analysis_history if e.get("type") == "sql_execution"]
        if sql_entries:
            query_key = sql_entries[-1].get("query_key")
    else:
        column_names = ["example_column_1", "example_column_2", "example_column_3"]
        row_example = {"example_column_1": "value1", "example_column_2": 123, "example_column_3": 45.67}
        query_metadata = {"columns": column_names, "sample_rows": [row_example]}
    
    agent = create_agent(
        data_visual_agent_model,
        system_prompt=data_vis_system_prompt(
            query_metadata=query_metadata
        )
    )
    
    result = invoke_and_save(agent, "data_visual_agent", [{"role": "user", "content": current_task}])
    
    turn_number = state.get("turn_number", 1)
    token_usage = extract_token_usage(result, agent_name="data_visual_agent", turn_number=turn_number)
    
    viz_content = extract_agent_response_content(result)
    try:
        viz_spec = json.loads(viz_content)
        
        if isinstance(viz_spec, list):
            if viz_spec:
                viz_spec = viz_spec[0]
            else:
                raise ValueError("Empty visualization specification list")
        
        chart_config = map_visualization_spec_to_chart(viz_spec, query_result=query_result)
        
        viz_output = json.dumps({
            "specification": viz_spec,
            "chart_config": chart_config
        }, indent=2)
    except json.JSONDecodeError:
        viz_output = viz_content
    except (ValueError, KeyError) as e:
        print(f"Warning: Invalid visualization specification: {e}")
        viz_output = viz_content

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

def save_agent_response(agent_name: str, response: dict):
    """Save agent responses to a JSON file for logging and debugging."""
    log_dir = "logs/agent_responses"
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_name = f"{agent_name}_{timestamp}.json"
    file_path = os.path.join(log_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(response, f, indent=4, ensure_ascii=False)

# Wrap agent invocation to include saving responses
def invoke_and_save(agent, agent_name: str, messages: list):
    result = agent.invoke({"messages": messages})
    raw_content = extract_agent_response_content(result)
    save_agent_response(agent_name, {"raw_agent_response": raw_content})
    return result

def response_synthesizer_agent_node(state: AgentState):
    """Custom node that synthesizes response with chart specs and minimal data summary.
    
    Only passes:
    - chart_specs: Visualization specifications (spec only, no full chart config)
    - metadata: Minimal summary with key statistics only
    - data_sample: First 5-10 rows only for context
    """
    user_query = state.get("user_query", "")
    viz_output = state.get("final_response", "")

    chart_specs = ""
    if viz_output:
        try:
            viz_output_json = json.loads(viz_output)
            chart_specs = json.dumps({"specification": viz_output_json.get("specification", {})}, indent=2)
        except json.JSONDecodeError:
            chart_specs = viz_output

    query_result = get_latest_query_result()
    metadata = {}
    if query_result and isinstance(query_result, dict):
        original_metadata = query_result.get("metadata", {})

        metadata = {
            "columns": original_metadata.get("columns", []),
            "num_columns": original_metadata.get("num_columns", 0),
            "num_rows": original_metadata.get("num_rows", 0)
        }
        stat_analysis = query_result.get("statistical_analysis", {})
        if stat_analysis:
            metadata["statistical_analysis"] = stat_analysis

        describe_data = original_metadata.get("describe", {})
        if describe_data and "data" in describe_data and "index" in describe_data:
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

        # Include Data Sample with a limit of 30 rows
        if query_result.get("data"):
            toon_data = convert_data_to_toon_format(query_result, data_limit=30)
            metadata["data_sample"] = toon_data

    agent = create_agent(
        general_agent_model,
        system_prompt=response_synthesizer_system_prompt(
            chart_specs=chart_specs, 
            metadata=metadata
        )
    )

    result = invoke_and_save(agent, "response_synthesizer_agent", [{"role": "user", "content": user_query}])

    turn_number = state.get("turn_number", 1)
    token_usage = extract_token_usage(result, agent_name="response_synthesizer_agent", turn_number=turn_number)

    raw_content = extract_agent_response_content(result)
    final_content = extract_agent_response_content(result)
    final_content = re.sub(r'```json\s*\n.*?\n```', '', final_content, flags=re.DOTALL).strip()

    chart_configs = state.get("chart_configs", [])
    if chart_configs and "{chart_json}" in final_content:
        latest_chart_config = chart_configs[-1]

        chart_json_str = json.dumps(latest_chart_config, indent=2, ensure_ascii=False)
        chart_json_block = f"```json\n{chart_json_str}\n```"

        final_content = final_content.replace("{chart_json}", chart_json_block)

    save_query_results(save_all=True)
    print(f" ! Saved {len(query_results_cache)} query results to disk")

    turn_number = state.get("turn_number", 1)
    token_usage_log = state.get("token_usage_log", [])

    complete_log = token_usage_log + ([token_usage] if token_usage else [])
    current_turn_log = [entry for entry in complete_log if entry.get("turn_number") == turn_number]

    if current_turn_log:
        save_result = save_token_usage_to_file(current_turn_log)
        if save_result["success"]:
            print(f" ! Saved token usage to disk: {save_result['totals']['total_tokens']} total tokens")
        else:
            print(f" ! Failed to save token usage: {save_result.get('error', 'Unknown error')}")

    chat_entry = {
        "user_input": user_query,
        "final_response": raw_content,
        "timestamp": datetime.now().isoformat()
    }

    return_dict = {
        "final_response": final_content,
        "chat_history": [chat_entry],
        "turn_number": turn_number + 1,
        "raw_agent_response": raw_content,
        "messages": [{"type": "ai", "content": final_content}]
    }

    if token_usage:
        return_dict["token_usage_log"] = [token_usage]

    # Save raw agent response
    save_agent_response("response_synthesizer_agent", {"raw_agent_response": raw_content})

    print(return_dict)
    return return_dict