# ============================================================
# graph_routes.py
# Contains: routing functions for the LangGraph state machine.
# ============================================================

from agent.agents import AgentState


def route_intention(state: AgentState):
    """Route based on user intention classification."""
    intention = state.get("intention", "ANALYZE")
    
    if intention == "GENERAL_SCHEMA":
        return "Schema_Info_Agent"
    else:
        return "Planner_Agent"

# This route was created to handle multiple tasks from Planner Agent
def route_after_exec(state: AgentState):
    """Route after SQL execution based on error status, plan completion, and visualization needs."""
    if state.get("error_log", ""):
        return "Text_to_SQL_Agent"  # Loop back for self-correction
    
    current_step = state.get("current_step_index", 0)
    plan_steps = state.get("plan_steps", [])
    data_steps = [s for s in plan_steps if s.get("sql_required", True)]
    total_data_steps = len(data_steps)
    
    # Check if the step we just completed needs visualization
    last_executed_step_index = current_step - 1
    if last_executed_step_index >= 0 and last_executed_step_index < len(data_steps):
        last_executed_step = data_steps[last_executed_step_index]
        if last_executed_step.get("visualization", False):
            return "Statistical_Analysis"
    
    if current_step < total_data_steps:
        return "Text_to_SQL_Agent"
    
    return "Response_Synthesizer"

def route_after_visualization(state: AgentState):
    """Route after visualization to check if more SQL steps or visualizations are needed."""
    current_step = state.get("current_step_index", 0)
    plan_steps = state.get("plan_steps", [])
    
    data_steps = [s for s in plan_steps if s.get("sql_required", True)]
    total_data_steps = len(data_steps)
    
    if current_step < total_data_steps:
        return "Text_to_SQL_Agent"
    
    return "Response_Synthesizer"
