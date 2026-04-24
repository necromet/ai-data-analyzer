from langgraph.graph import StateGraph, START, END
from agent.agents import (
    AgentState,
    preprocess_input,
    intention_agent,
    schema_info_agent,
    planner_agent,
    text_to_sql_agent,
    human_review_node,
    sql_executor,
    statistical_analysis_node,
    data_visual_agent_node,
    response_synthesizer_agent_node,
)
from agent.graph_routes import (
    route_intention,
    route_after_exec,
    route_after_visualization,
    route_after_statistical,
    route_human_review,
)

graph = StateGraph(AgentState)
graph.add_node("Preprocess_Input", preprocess_input)
graph.add_node("Intention_Agent", intention_agent)
graph.add_node("Schema_Info_Agent", schema_info_agent)
graph.add_node("Planner_Agent", planner_agent)
graph.add_node("Text_to_SQL_Agent", text_to_sql_agent)
graph.add_node("Human_Review", human_review_node)
graph.add_node("SQL_Executor", sql_executor)
graph.add_node("Statistical_Analysis", statistical_analysis_node)
graph.add_node("Data_Visual_Agent", data_visual_agent_node)
graph.add_node("Response_Synthesizer", response_synthesizer_agent_node)

# 0. Start with input preprocessing to extract user_query from messages
graph.add_edge(START, "Preprocess_Input")

# 1. Continue with Intention Classification
graph.add_edge("Preprocess_Input", "Intention_Agent")

# 2. Route based on intention
graph.add_conditional_edges(
    "Intention_Agent",
    route_intention,
    {
        "Schema_Info_Agent": "Schema_Info_Agent",
        "Planner_Agent": "Planner_Agent"
    }
)

# Schema Info path goes directly to END
graph.add_edge("Schema_Info_Agent", END)

# 3. Planning -> Human (Optional: Clarification)
graph.add_edge("Planner_Agent", "Text_to_SQL_Agent")

# 4. Pause Point: Let human see the SQL before execution
graph.add_edge("Text_to_SQL_Agent", "Human_Review")

# 4.1. Human can approve (continue to SQL_Executor) or cancel (go to END)
graph.add_conditional_edges(
    "Human_Review",
    route_human_review,
    {
        "SQL_Executor": "SQL_Executor",
        "END": END
    }
)

# 5. After SQL execution, route based on errors, remaining steps, and visualization needs
graph.add_conditional_edges(
    "SQL_Executor",
    route_after_exec,
    {
        "Text_to_SQL_Agent": "Text_to_SQL_Agent",
        "Statistical_Analysis": "Statistical_Analysis",
        "Response_Synthesizer": "Response_Synthesizer"
    }
)

# 5.1. After statistical analysis, check if visualization is needed
graph.add_conditional_edges(
    "Statistical_Analysis",
    route_after_statistical,
    {
        "Data_Visual_Agent": "Data_Visual_Agent",
        "Response_Synthesizer": "Response_Synthesizer"
    }
)

graph.add_conditional_edges(
    "Data_Visual_Agent",
    route_after_visualization,
    {
        "Text_to_SQL_Agent": "Text_to_SQL_Agent",
        "Response_Synthesizer": "Response_Synthesizer"
    }
)

# 6. Final response synthesis with visualization specs and data summary
graph.add_edge("Response_Synthesizer", END)

app = graph.compile()
