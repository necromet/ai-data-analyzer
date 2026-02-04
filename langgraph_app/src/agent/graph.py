from langgraph.graph import StateGraph, MessagesState, START, END
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from agent.planner_agent_system_prompt import planner_agent_system_prompt
from agent.sql_agent_system_prompt import generate_sql_system_prompt
from agent.general_agent_system_prompt import general_agent_system_prompt
from agent.fix_sql_error_system_prompt import fix_sql_error_prompt
from agent.data_viz_system_prompt import data_vis_system_prompt
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
import sqlparse
import pandas as pd
from agent.database_tools import get_db_connection

general_agent_model_name = "gpt-4o-mini-2024-07-18"
general_agent_model = ChatOpenAI(
    model = general_agent_model_name,
    temperature = 0.2,
    max_tokens = 10000
)

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
            Problematic SQL:
            {sql_query}
            
            Please regenerate the SQL query without these forbidden operations."""
        
        # Get thread-safe connection
        conn = get_db_connection()
        
        # Execute and immediately materialize to DataFrame
        result = conn.execute(sql_query).fetchdf()
        
        # Store metadata in JSON format
        metadata = {
            "columns": result.columns,
            "num_columns": len(result.columns),
            "num_rows": len(result),
            "describe": result.describe().to_json(orient='records', indent=2)
        }
        result_json = result.to_json(orient='records', indent=2)

        success_message = f"SQL executed successfully. Rows returned: {len(result)}. Columns: {', '.join(result.columns)}."
        # Return string representation for tool output
        return success_message
    
    except Exception as e:
        error_msg = str(e)
        return f"""ERROR: Failed to execute SQL query.

        Error Details: {error_msg}

        Problematic SQL:
        {sql_query}

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
    tools=[generate_sql, execute_sql],
    system_prompt=data_vis_system_prompt()
)

response_synthesizer_agent = create_agent(
    general_agent_model,
    system_prompt=data_vis_system_prompt()
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
graph.add_edge("Data_Visual_Agent", END)

# Compile the graph for LangGraph Studio
app = graph.compile()