from langgraph.graph import StateGraph, MessagesState, START, END
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from agent.planner_agent_system_prompt import planner_agent_system_prompt
from agent.sql_agent_system_prompt import generate_sql_system_prompt
from agent.general_agent_system_prompt import general_agent_system_prompt
from agent.fix_sql_error_system_prompt import fix_sql_error_prompt
from agent.data_viz_system_prompt import data_vis_system_prompt
from agent.response_synthesizer_system_prompt import response_synthesizer_system_prompt
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
import sqlparse
import pandas as pd
from agent.database_tools import get_db_connection
from datetime import datetime
import json
import os

# Module-level cache to store query results
query_results_cache = {}

general_agent_model_name = "gpt-5-mini-2025-08-07"
general_agent_model = ChatOpenAI(
    model = general_agent_model_name,
    temperature = 0.2,
    max_tokens = 10000
)


def save_query_results(query_key: str = None, save_all: bool = False) -> dict:
    """
    Save query results from cache to the query_results folder as JSON files.
    
    Args:
        query_key (str, optional): Specific key to save. If None and save_all is False, does nothing.
        save_all (bool): If True, saves all cached query results.
    
    Returns:
        dict: Status dictionary with 'success', 'saved_count', 'failed_count', and 'errors' keys.
    """
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

@tool
def generate_sql(user_query: str) -> str:
    """Generate SQL query from natural language."""
    prompt = generate_sql_system_prompt(user_input=user_query)

    response = general_agent_model.invoke(input = prompt)

    # Validate immediately
    forbidden = detect_dml_statements(response.content)
    if forbidden:
        return f"ERROR: Cannot generate this SQL. Forbidden statements detected: {', '.join([s['statement'] for s in forbidden])}"
    else:
        return response.content

@tool
def execute_sql(sql_query: str) -> str:
    """Execute a SELECT query and return results as a string representation of the data."""
    try:
        # Validate first
        forbidden = detect_dml_statements(sql_query)
        if forbidden:
            return f"""ERROR: Cannot execute SQL. Forbidden statements detected: {', '.join([s['statement'] for s in forbidden])}
            
            Please regenerate the SQL query without these forbidden operations."""
        
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
        
        # Store result_json in module-level cache
        query_results_cache[query_key] = result_json
        save_query_results(save_all=True)
        
        success_message = f"The SQL Query {sql_query} executed successfully. Rows returned: {len(result)}. Columns: {', '.join(result.columns)}. Result stored with key: {query_key}"
        
        # Return only the string message for the agent
        return success_message
    
    except Exception as e:
        error_msg = str(e)
        return f"""ERROR: Failed to execute SQL query.

        Error Details: {error_msg}

        Please analyze the error and regenerate a corrected SQL query. Common issues:
        - Invalid table/column names (check schema)
        - Syntax errors
        - Type mismatches
        - Missing JOIN conditions
        """
    
@tool
def fix_sql_error(sql_query: str, error_message: str) -> str:
    """Fix SQL query based on error message using the language model."""
    prompt = fix_sql_error_prompt(sql_query=sql_query, error_message=error_message)

    response = general_agent_model.invoke(input=prompt)
    return response.content.strip()


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

def initialize_db_node(state: MessagesState):
    """Initialize database connection before processing any requests."""
    try:
        conn = get_db_connection()
        print(" ! Database initialization node completed successfully")
    except Exception as e:
        print(f" ! Database initialization failed: {e}")
        raise
    return state

def planner_agent_node(state: MessagesState):
    """Custom node that extracts user input from state for the planner."""
    messages = state.get("messages", [])
    
    # Extract user input (first human message)
    user_input = ""
    for msg in messages:
        if hasattr(msg, 'type') and msg.type == 'human':
            user_input = msg.content
            break
    
    # Create agent with dynamic system prompt
    agent = create_agent(
        general_agent_model,
        system_prompt=planner_agent_system_prompt(user_input=user_input)
    )
    
    return agent.invoke(state)

def text_to_sql_agent_node(state: MessagesState):
    """Custom node that extracts user input and planner output from state."""
    messages = state.get("messages", [])
    
    # Extract user input (first human message)
    user_input = ""
    for msg in messages:
        if hasattr(msg, 'type') and msg.type == 'human':
            user_input = msg.content
            break
    
    # Extract planner output (last AI message before this node)
    to_do_list = ""
    for msg in reversed(messages):
        if hasattr(msg, 'type') and msg.type == 'ai' and hasattr(msg, 'content'):
            to_do_list = msg.content
            break
    
    # Create agent with dynamic system prompt
    agent = create_agent(
        general_agent_model,
        tools=[generate_sql, fix_sql_error, execute_sql],
        system_prompt=general_agent_system_prompt(user_input=user_input, to_do_list=to_do_list)
    )
    
    return agent.invoke(state)

data_visual_agent = create_agent(
    general_agent_model,
    system_prompt=data_vis_system_prompt()
)

response_synthesizer_agent = create_agent(
    general_agent_model,
    system_prompt=response_synthesizer_system_prompt()
)

def route_planner(state: MessagesState):
    """Route from planner to appropriate agent or finish."""
    messages = state.get("messages", [])
    if not messages:
        return "Response_Synthesizer"
    
    last_message = messages[-1]
    content = last_message.content.lower() if hasattr(last_message, 'content') else str(last_message).lower()
    
    # Route to visualization if needed
    if any(word in content for word in ["visualize", "chart", "graph", "plot"]):
        return "Data_Visual_Agent"
    # Default to response synthesizer
    else:
        return "Response_Synthesizer"


graph = StateGraph(MessagesState)

graph.add_node("Initialize_DB", initialize_db_node)
graph.add_node("Planner_Agent", planner_agent_node)
graph.add_node("Text_to_SQL_Agent", text_to_sql_agent_node)
graph.add_node("Data_Visual_Agent", data_visual_agent)
graph.add_node("Response_Synthesizer", response_synthesizer_agent)

graph.add_edge(START, "Initialize_DB")
graph.add_edge("Initialize_DB", "Planner_Agent")
graph.add_edge("Planner_Agent", "Text_to_SQL_Agent")
graph.add_conditional_edges(
    "Text_to_SQL_Agent",
    route_planner,
    {
        "Data_Visual_Agent": "Data_Visual_Agent",
        "Response_Synthesizer": "Response_Synthesizer"
    }
)
graph.add_edge("Data_Visual_Agent", "Response_Synthesizer")
graph.add_edge("Response_Synthesizer", END)

# Compile the graph for LangGraph Studio
app = graph.compile()