from langgraph.graph import StateGraph, MessagesState, START, END
from langchain.agents import create_agent
from agent.system_prompt import SYSTEM_PROMPT

agent = create_agent(
    "gpt-4o-mini-2024-07-18",
    # tools=[send_email],
    system_prompt=SYSTEM_PROMPT,
)

graph = StateGraph(MessagesState)
graph.add_node("agent", agent)

graph.add_edge(START, "agent")
graph.add_edge("agent", END)
graph = graph.compile()