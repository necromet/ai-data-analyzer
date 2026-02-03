from langgraph.graph import StateGraph, MessagesState, START, END
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
from agent.text_to_sql_system_prompt import TEXT_TO_SQL_SYSTEM_PROMPT
from agent.general_agent_system_prompt import GENERAL_AGENT_SYSTEM_PROMPT
from langchain_openai import ChatOpenAI
import sqlparse
import duckdb
import pandas as pd
import threading

general_agent_name = "gpt-4o-mini-2024-07-18"
general_agent_model = ChatOpenAI(
    model = general_agent_name,
    temperature = 0.2,
    max_tokens = 5000
)

sql_tool_name = "gpt-4o-2024-08-06"
sql_tool_model = ChatOpenAI(
    model = sql_tool_name,
    temperature = 0.2,
    max_tokens = 10000
)

# Database paths (try in order)
DB_PATHS = [
    "C:\\Users\\OSVALDO-SOFTENG\\Documents\\edward-portfolio\\GIT\\ai-data-analyzer\\olist.db",
    "/media/edward/SSD-Data/My Folder/ai-data-analyzer/olist.db"
]

# Thread-local storage for database connections
thread_local = threading.local()

def get_db_connection():
    """Get a thread-safe database connection."""
    if not hasattr(thread_local, "conn") or thread_local.conn is None:
        for db_path in DB_PATHS:
            try:
                conn = duckdb.connect(database=db_path, read_only=False)
                thread_local.conn = conn
                thread_local.db_path = db_path
                print(f" ! Database connected: {db_path}")
                conn.execute("LOAD spatial;")
                conn.execute("LOAD httpfs;")
                conn.execute("LOAD fts;")
                conn.execute("LOAD icu;")
                print(f" ! Spatial, HTTP, FTS, ICU loaded in database: {db_path}")
                break
            except Exception as e:
                print(f" ! Failed to connect to {db_path}: {e}")
                continue
        else:
            raise Exception("Failed to connect to any database path")
    return thread_local.conn

@tool
def generate_sql(query: str) -> str:
    """Generate SQL query from natural language."""
    prompt = f"""
    User Query = {query}

    System Prompt:
    {TEXT_TO_SQL_SYSTEM_PROMPT}
    """
    response = sql_tool_model.invoke(input = prompt)

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
        result = conn.execute(sql_query)
        df = result.fetchdf()
        
        # Return string representation for tool output
        return df.to_string()
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


planner_agent = create_agent(
    general_agent_model, 
    tools=[generate_sql, execute_sql],
    system_prompt=GENERAL_AGENT_SYSTEM_PROMPT
)

text_to_sql_agent = create_agent(
    general_agent_model, 
    tools=[generate_sql, execute_sql],
    system_prompt=GENERAL_AGENT_SYSTEM_PROMPT
)

data_visual_agent = create_agent(
    general_agent_model,
    tools=[generate_sql, execute_sql],
    system_prompt=GENERAL_AGENT_SYSTEM_PROMPT
)




def route_planner(state: MessagesState):
    """Route from planner to appropriate agent or finish."""
    messages = state.get("messages", [])
    if not messages:
        return "Text_to_SQL_Agent"
    
    last_message = messages[-1]
    content = last_message.content.lower() if hasattr(last_message, 'content') else str(last_message).lower()
    
    # Check if planner wants to finish
    if any(phrase in content for phrase in ["task complete", "finished", "done", "final answer"]):
        return END
    # Route to visualization if needed
    elif any(word in content for word in ["visualiz", "chart", "graph", "plot"]):
        return "Data_Visual_Agent"
    # Default to SQL agent
    else:
        return "Text_to_SQL_Agent"


graph = StateGraph(MessagesState)

graph.add_node("Planner_Agent", planner_agent)
graph.add_node("Text_to_SQL_Agent", text_to_sql_agent)
graph.add_node("Data_Visual_Agent", data_visual_agent)

graph.add_edge(START, "Planner_Agent")
graph.add_conditional_edges(
    "Planner_Agent",
    route_planner,
    {
        "Text_to_SQL_Agent": "Text_to_SQL_Agent",
        "Data_Visual_Agent": "Data_Visual_Agent",
        END: END
    }
)
graph.add_edge("Text_to_SQL_Agent", "Planner_Agent")
graph.add_edge("Data_Visual_Agent", "Planner_Agent")

# Compile the graph for LangGraph Studio
app = graph.compile()