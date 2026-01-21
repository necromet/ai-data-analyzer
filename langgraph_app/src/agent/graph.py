from langgraph.graph import StateGraph, MessagesState, START, END
from langchain.agents import create_agent

def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}

def send_email(to: str, subject: str, body: str):
    """Send an email"""
    email = {
        "to": to,
        "subject": subject,
        "body": body
    }
    # ... email sending logic

    return f"Email sent to {to}"

agent = create_agent(
    "gpt-4o",
    # tools=[send_email],
    system_prompt="You are a helper AI assistant.",
)

graph = StateGraph(MessagesState)
graph.add_node("agent", agent)

graph.add_edge(START, "agent")
graph.add_edge("agent", END)
graph = graph.compile()

graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})