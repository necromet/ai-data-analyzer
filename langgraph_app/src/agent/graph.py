from typing_extensions import TypedDict
from typing import List
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
from agent.text_to_sql_system_prompt import TEXT_TO_SQL_SYSTEM_PROMPT
from agent.general_agent_system_prompt import GENERAL_AGENT_SYSTEM_PROMPT
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from pydantic import BaseModel, Field
from typing_extensions import Literal
from langchain_openai import ChatOpenAI
from IPython.display import Image, display


model_name = "gpt-4o-mini-2024-07-18"
model = ChatOpenAI(
    model = model_name,
    temperature = 0.2,
    max_tokens = 5000
)

class AgentState(TypedDict):
    messages = List[BaseMessage]
    category = str

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


agent = create_agent(model, tools=[generate_sql], system_prompt=GENERAL_AGENT_SYSTEM_PROMPT)

graph = StateGraph(MessagesState)

graph.add_node("Agent", agent)

graph.add_edge(START, "Agent")
graph.add_edge("Agent", END)