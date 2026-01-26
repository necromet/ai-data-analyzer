from typing_extensions import TypedDict
from typing import List
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
from agent.text_to_sql_system_prompt import TEXT_TO_SQL_SYSTEM_PROMPT
from agent.general_agent_system_prompt import GENERAL_AGENT_SYSTEM_PROMPT
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from pydantic import BaseModel, Field
from typing_extensions import Literal
from langchain_openai import ChatOpenAI
from IPython.display import Image, display
import sqlparse


model_name = "gpt-4o-mini-2024-07-18"
model = ChatOpenAI(
    model = model_name,
    temperature = 0.2,
    max_tokens = 5000
)

class AgentState(TypedDict):
    messages: List[BaseMessage]
    category: str

@tool
def generate_sql(query: str) -> str:
    """Generate SQL query from natural language."""
    prompt = f"""
    User Query = {query}

    System Prompt:
    {TEXT_TO_SQL_SYSTEM_PROMPT}
    """
    response = model.invoke(input = prompt)
    return response.content

def detect_dml_statements(content: str) -> list[dict[str, str]]:
    """Detect forbidden SQL statements (DML, DDL, DCL, TCL)."""
    # This list covers DDL, DML, DCL, and TCL
    forbidden_types = {
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 
        'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE', 'MERGE', 
        'COMMIT'
    }
    
    found_statements = []
    
    # Split string into individual SQL statements
    parsed = sqlparse.parse(content)
    
    for statement in parsed:
        # Get the first real token (e.g., 'SELECT', 'UPDATE', etc.)
        # sqlparse ignores comments and whitespace automatically
        root_keyword = statement.get_type()
        
        # Check if the main command is in our list
        if root_keyword in forbidden_types:
            found_statements.append({
                "statement": root_keyword,
                "full_query": str(statement).strip()
            })
            
        # Also check for sub-commands (like a DELETE inside a TRIGGER or a block)
        # We can iterate through tokens to find keywords inside the query
        else:
            for token in statement.flatten():
                if token.is_keyword and token.value.upper() in forbidden_types:
                    found_statements.append({
                        "statement": token.value.upper(),
                        "full_query": "Detected inside sub-query or block"
                    })
                    break # Avoid duplicate entries for the same query

    return found_statements

def validate_sql_node(state: MessagesState) -> MessagesState:
    """Validate SQL queries for forbidden DML/DDL statements."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if the last message is a tool message from generate_sql
    if isinstance(last_message, ToolMessage) and last_message.name == "generate_sql":
        sql_content = last_message.content
        
        # Detect forbidden statements
        forbidden = detect_dml_statements(sql_content)
        
        if forbidden:
            # Block the query and return error message
            error_msg = f"BLOCKED: Forbidden SQL statements detected: {', '.join([s['statement'] for s in forbidden])}"
            # Replace the tool message with an error message
            messages[-1] = ToolMessage(
                content=error_msg,
                tool_call_id=last_message.tool_call_id,
                name="generate_sql"
            )
    
    return {"messages": messages}

def should_validate(state: MessagesState) -> str:
    """Determine if we need to validate SQL."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if last message is a tool message from generate_sql
    if isinstance(last_message, ToolMessage) and last_message.name == "generate_sql":
        return "validate"
    return "end"


agent = create_agent(
    model, 
    tools=[generate_sql],
    system_prompt=GENERAL_AGENT_SYSTEM_PROMPT
)

graph = StateGraph(MessagesState)

graph.add_node("Agent", agent)
graph.add_node("validate_sql", validate_sql_node)

graph.add_edge(START, "Agent")
graph.add_conditional_edges(
    "Agent",
    should_validate,
    {
        "validate": "validate_sql",
        "end": END
    }
)
graph.add_edge("validate_sql", END)