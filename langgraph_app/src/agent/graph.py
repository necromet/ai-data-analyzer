from langgraph.graph import StateGraph, MessagesState, START, END
from langchain.agents import create_agent
from agent.system_prompt import SYSTEM_PROMPT

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
    "gpt-4o-mini-2024-07-18",
    # tools=[send_email],
    system_prompt=SYSTEM_PROMPT,
)

graph = StateGraph(MessagesState)
graph.add_node("agent", agent)

graph.add_edge(START, "agent")
graph.add_edge("agent", END)
graph = graph.compile()

# Run the graph and capture response
response = graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})

# Extract and display token usage
if response and "messages" in response:
    last_message = response["messages"][-1]
    
    # Check for usage stats in message metadata
    if hasattr(last_message, "usage_metadata") and last_message.usage_metadata:
        usage = last_message.usage_metadata
        print("\n" + "="*50)
        print("TOKEN USAGE STATISTICS")
        print("="*50)
        print(f"Input tokens:  {usage.get('input_tokens', 0)}")
        print(f"Output tokens: {usage.get('output_tokens', 0)}")
        print(f"Total tokens:  {usage.get('total_tokens', 0)}")
        print("="*50 + "\n")
    elif hasattr(last_message, "response_metadata") and last_message.response_metadata:
        metadata = last_message.response_metadata
        if "token_usage" in metadata:
            usage = metadata["token_usage"]
            print("\n" + "="*50)
            print("TOKEN USAGE STATISTICS")
            print("="*50)
            print(f"Prompt tokens:     {usage.get('prompt_tokens', 0)}")
            print(f"Completion tokens: {usage.get('completion_tokens', 0)}")
            print(f"Total tokens:      {usage.get('total_tokens', 0)}")
            print("="*50 + "\n")