from typing_extensions import TypedDict
from typing import List
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain.agents import create_agent
from langchain.tools import tool
from agent.text_to_sql_system_prompt import TEXT_TO_SQL_SYSTEM_PROMPT
from agent.general_agent_system_prompt import GENERAL_AGENT_SYSTEM_PROMPT
from agent.categorizer_system_prompt import CATEGORIZER_SYSTEM_PROMPT
from openai import OpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from pydantic import BaseModel, Field
from typing_extensions import Literal
from langchain_openai import ChatOpenAI
from IPython.display import Image, display


# class State(TypedDict):
#     joke: str
#     topic: str
#     feedback: str
#     funny_or_not: str

# # Configurations
# llm = OpenAI()


model_name = "gpt-4o-mini-2024-07-18"
llm = ChatOpenAI(model=model_name)

class AgentState(TypedDict):
    messages: List[BaseMessage]
    category: str

def categorize_input(state: AgentState):
    """
    Analyzes the user's last message and decides if it's 'Math' or 'General'.
    """
    last_message = state["messages"][-1].content
    
    # We ask the LLM to classify strictly.
    prompt = f"""
    {CATEGORIZER_SYSTEM_PROMPT}
    
    Input: {last_message}
    """
    response = llm.invoke(prompt)
    category = response.content.strip()
    
    # Update the state with the category
    return {"category": category}

def routing_logic(state: AgentState):
    if state["category"] == "SQL":
        return "text_to_sql_node"
    elif state["category"] == "GENERAL":
        return "general_node"
    
def text_to_sql_call(state: AgentState):
    # if state.get("feedback"):
    #     msg = llm.responses.create(
    #         model="gpt-4o-mini-2024-07-18",
    #         input=f"Provide feedback on the joke: {state['joke']} about {state['topic']}. User feedback: {state['feedback']}"
    #     )
    # else:
    #     msg = llm.responses.create(
    #         model="gpt-4o-mini-2024-07-18",
    #         input=TEXT_TO_SQL_SYSTEM_PROMPT
    #     )
    last_message = state["messages"][-1].content
    prompt = f"""
    Input: {last_message}

    {TEXT_TO_SQL_SYSTEM_PROMPT}
    """
    response = llm.invoke(prompt)
    return {"messages": [response]}

def general_llm_call(state: AgentState):
    last_message = state["messages"][-1].content

    prompt = f"""
    {GENERAL_AGENT_SYSTEM_PROMPT}
    
    Input: {last_message}
    """
    response = llm.invoke(prompt)
    return {"messages": [response]}
    
sql_agent = StateGraph(MessagesState)

# Nodes
sql_agent.add_node("categorizer", categorize_input)
sql_agent.add_node("text_to_sql_node", text_to_sql_call)
sql_agent.add_node("general_node", general_llm_call)


# Edges to connect nodes
sql_agent.add_edge(START, "categorizer")
sql_agent.add_conditional_edges(
    "categorizer", 
    routing_logic,
    {  # Name returned by route_joke : Name of next node to visit
        "text_to_sql_node": "text_to_sql_node",
        "general_node": "general_node"
    }
)
sql_agent.add_edge("text_to_sql_node", END)
sql_agent.add_edge("general_node", END)

# Compiler
graph = sql_agent.compile()



# # Graph state
# class State(TypedDict):
#     joke: str
#     topic: str
#     feedback: str
#     funny_or_not: str


# # Schema for structured output to use in evaluation
# class Feedback(BaseModel):
#     grade: Literal["funny", "not funny"] = Field(
#         description="Decide if the joke is funny or not.",
#     )
#     feedback: str = Field(
#         description="If the joke is not funny, provide feedback on how to improve it.",
#     )

# # Augment the LLM with schema for structured output
# evaluator = llm.with_structured_output(Feedback)


# # Nodes
# def llm_call_generator(state: State):
#     """LLM generates a joke"""

#     if state.get("feedback"):
#         msg = llm.invoke(
#             f"Write a joke about {state['topic']} but take into account the feedback: {state['feedback']}"
#         )
#     else:
#         msg = llm.invoke(f"Write a joke about {state['topic']}")
#     return {"joke": msg.content}


# def llm_call_evaluator(state: State):
#     """LLM evaluates the joke"""

#     grade = evaluator.invoke(f"Grade the joke {state['joke']}")
#     return {"funny_or_not": grade.grade, "feedback": grade.feedback}


# # Conditional edge function to route back to joke generator or end based upon feedback from the evaluator
# def route_joke(state: State):
#     """Route back to joke generator or end based upon feedback from the evaluator"""

#     if state["funny_or_not"] == "funny":
#         return "Accepted"
#     elif state["funny_or_not"] == "not funny":
#         return "Rejected + Feedback"


# # Build workflow
# optimizer_builder = StateGraph(State)

# # Add the nodes
# optimizer_builder.add_node("Agent", agent)
# optimizer_builder.add_node("llm_call_generator", llm_call_generator)
# optimizer_builder.add_node("llm_call_evaluator", llm_call_evaluator)

# # Add edges to connect nodes
# optimizer_builder.add_edge(START, "Agent")
# optimizer_builder.add_edge("Agent", "llm_call_generator")
# optimizer_builder.add_edge("llm_call_generator", "llm_call_evaluator")
# optimizer_builder.add_conditional_edges(
#     "llm_call_evaluator",
#     route_joke,
#     {  # Name returned by route_joke : Name of next node to visit
#         "Accepted": END,
#         "Rejected + Feedback": "llm_call_generator",
#     },
# )

# # Compile the workflow
# graph = optimizer_builder.compile()

# # Show the workflow (only when running directly)
# if __name__ == "__main__":
#     display(Image(graph.get_graph().draw_mermaid_png()))
    
#     # Invoke
#     state = graph.invoke({"topic": "Cats"})
#     print(state["joke"])