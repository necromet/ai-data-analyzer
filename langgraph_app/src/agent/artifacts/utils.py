import json
import os
import re
from typing import List
from decimal import Decimal
from datetime import datetime, date, time

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
    
    cleaned = re.sub(r'^\s*```(?:sql)?\s*\n?|\n?\s*```\s*$', '', sql_text.strip(), flags=re.IGNORECASE)
    return cleaned.strip()


def print_and_save_config(config: dict, name: str = None) -> None:
    """Print chart config to stdout and optionally save to JSON.

    Behavior:
    - Always prints a pretty JSON representation of the config.
    - If environment variable `ARTIFACTS_SAVE_CONFIG` is set and non-empty,
      its value is treated as a directory path (relative to this file when not absolute)
      where a timestamped JSON file will be written.

    Args:
        config: The chart configuration dictionary.
        name: Optional base name for the saved file.
    """
    try:
        cfg = convert_decimals_to_float(config)
        cfg = convert_dates_to_strings(cfg)

        header = f"Chart config{(' - ' + name) if name else ''}:"
        print(header)
        print(json.dumps(cfg, indent=2, ensure_ascii=False))

        save_flag = os.environ.get("ARTIFACTS_SAVE_CONFIG", "").strip()
        if save_flag:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            out_dir = save_flag if os.path.isabs(save_flag) else os.path.join(current_dir, save_flag)
            os.makedirs(out_dir, exist_ok=True)
            filename = f"{(name or 'chart')}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
            file_path = os.path.join(out_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            print(f"Saved chart config to {file_path}")
    except Exception as e:
        print(f"Error printing/saving chart config: {e}")