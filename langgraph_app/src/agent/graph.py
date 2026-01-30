from typing_extensions import TypedDict
from typing import List, Union
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
from agent.text_to_sql_system_prompt import TEXT_TO_SQL_SYSTEM_PROMPT
from agent.general_agent_system_prompt import GENERAL_AGENT_SYSTEM_PROMPT
from agent.data_viz_system_prompt import DATA_VIZ_SYSTEM_PROMPT
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
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
    max_tokens = 5000
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
    
def execute_sql(sql_query: str) -> Union[pd.DataFrame, str]:
    """Execute a SELECT query and return results as pandas DataFrame."""
    try:
        # Validate first
        forbidden = detect_dml_statements(sql_query)
        if forbidden:
            return f"ERROR: Cannot execute. Forbidden statements: {', '.join([s['statement'] for s in forbidden])}"
        
        # Get thread-safe connection
        conn = get_db_connection()
        
        # Execute and immediately materialize to DataFrame
        result = conn.execute(sql_query)
        df = result.fetchdf()
        
        return df
    except Exception as e:
        return f"ERROR: Failed to execute SQL: {str(e)}"

@tool
def create_chartjs_render(user_query: str, sql_query: str) -> str:
    """Create a chartjs render from data. chart_type: 'bar', 'line', 'pie', etc."""
    df = execute_sql(sql_query)
    
    # Check if we got an error message
    if isinstance(df, str) and df.startswith("ERROR"):
        return df

    prompt = f"""
    User Query = {user_query}

    SQL Query = {sql_query}

    Data Returned = {df.to_string()}

    System Prompt:
    {DATA_VIZ_SYSTEM_PROMPT}
    """
    response = general_agent_model.invoke(input=prompt)
    return response.content


# def generate_todo_list(query: str) -> str:
#     """Generate a todo list from natural language query."""
#     prompt = f"""
#     User Query = {query}

#     System Prompt:
#     {TODO_LIST_SYSTEM_PROMPT}
#     """
#     response = model.invoke(input=prompt)
#     return response.content


# def todo_node(state: MessagesState) -> MessagesState:
#     """Generate a todo list based on the user's query."""
#     messages = state["messages"]
#     last_user_message = None
#     for msg in reversed(messages):
#         if msg.type == "human":
#             last_user_message = msg.content
#             break
#     if last_user_message:
#         todo = generate_todo_list(last_user_message)
#         new_messages = messages + [AIMessage(content=f"Todo List:\n{todo}")]
#         return {"messages": new_messages}
#     return state

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


def should_validate(state: MessagesState) -> str:
    """Determine if we need to validate SQL."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if last message is a tool message from generate_sql
    if isinstance(last_message, ToolMessage) and last_message.name == "generate_sql":
        return "validate"
    return "end"


agent = create_agent(
    general_agent_model, 
    tools=[generate_sql, create_chartjs_render],
    system_prompt=GENERAL_AGENT_SYSTEM_PROMPT
)

graph = StateGraph(MessagesState)

graph.add_node("Agent", agent)

graph.add_edge(START, "Agent")
graph.add_edge("Agent", END)