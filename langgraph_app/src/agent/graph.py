from typing_extensions import TypedDict
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain.agents import create_agent
from agent.text_to_sql_system_prompt import TEXT_TO_SQL_SYSTEM_PROMPT
from agent.general_agent_system_prompt import GENERAL_AGENT_SYSTEM_PROMPT
from openai import OpenAI

class State(TypedDict):
    joke: str
    topic: str
    feedback: str
    funny_or_not: str

# Configurations
llm = OpenAI()


def llm_call(state: State):
    if state.get("feedback"):
        msg = llm.responses.create(
            model="gpt-4o-mini-2024-07-18"
            input=f"Provide feedback on the joke: {state['joke']} about {state['topic']}. User feedback: {state['feedback']}"
        )
    else:
        msg = llm.responses.create(
            model="gpt-4o-mini-2024-07-18"
            input=f"Provide feedback on the joke: {state['joke']} about {state['topic']}. User feedback: {state['feedback']}"
        )

agent = create_agent(
    "gpt-4o-mini-2024-07-18",
    system_prompt=GENERAL_AGENT_SYSTEM_PROMPT,
)


graph = StateGraph(MessagesState)

# Nodes
graph.add_node("agent", agent)
graph.add_node("text_to_sql", text_to_sql_calls)

# Edges to connect nodes
graph.add_edge(START, "agent")
# graph.add_edge("agent", "text_to_sql")
graph.add_edge("agent", END)
# graph.add_edge("text_to_sql", "agent")

# Compiler
graph = graph.compile()