def intention_agent(state: AgentState):
    """Classify user intention: GENERAL_SCHEMA or ANALYZE."""
    user_query = state.get("user_query", "")
    turn_number = state.get("turn_number", 1)
    
    agent = create_agent(
        intention_agent_model,
        system_prompt=intention_agent_system_prompt()
    )
    
    result = agent.invoke({"messages": [{"role": "user", "content": user_query}]})
    
    # Extract token usage
    token_usage = extract_token_usage(result, agent_name="intention_agent", turn_number=turn_number)
    
    # Extract intention (should be "SCHEMA_INFO" or "ANALYZE")
    intention_text = extract_agent_response_content(result).strip().upper()
    print(intention_text)
    # Validate intention
    if "GENERAL_SCHEMA" in intention_text:
        intention = "GENERAL_SCHEMA"
    elif "ANALYZE" in intention_text:
        intention = "ANALYZE"
    else:
        # Default to ANALYZE if unclear
        intention = "ANALYZE"

    print(f" ! Intention Agent classified query as: {intention}")
    
    return_dict = {
        "intention": intention,
        "turn_number": turn_number
    }
    
    if token_usage:
        return_dict["token_usage_log"] = [token_usage]
    
    return return_dict


def schema_info_agent(state: AgentState):
    """Answer general questions about database schema without executing queries."""
    user_query = state.get("user_query", "")
    turn_number = state.get("turn_number", 1)
    
    agent = create_agent(
        schema_agent_model,
        system_prompt=schema_info_agent_system_prompt()
    )

    # Convert chat_history entries {user_input, final_response} to {role, content} format
    formatted_history = []
    for entry in state.get("chat_history", []):
        if "user_input" in entry and "final_response" in entry:
            formatted_history.append({"role": "user", "content": entry["user_input"]})
            formatted_history.append({"role": "assistant", "content": entry["final_response"]})
    formatted_history.append({"role": "user", "content": user_query})

    result = agent.invoke({"messages": formatted_history})
    
    # Extract token usage
    token_usage = extract_token_usage(result, agent_name="schema_info_agent", turn_number=turn_number)
    
    # Extract response
    response = extract_agent_response_content(result)
    
    print(" ! Schema Info Agent completed response")
    
    # Create chat history entry
    chat_entry = {
        "user_input": user_query,
        "final_response": response,
        "timestamp": datetime.now().isoformat()
    }
    
    return_dict = {
        "final_response": response,
        "chat_history": [chat_entry],
        "turn_number": turn_number + 1,
        "messages": [{"type": "ai", "content": response}]
    }
    
    if token_usage:
        return_dict["token_usage_log"] = [token_usage]
    
    print(return_dict)
    return return_dict

def text_to_sql_agent(state: AgentState):
    """Generate or fix SQL query based on user request and any previous errors."""
    user_query = state.get("user_query", "")
    error_log = state.get("error_log", "")
    last_sql = state.get("generated_sql", "")
    
    # Get current plan step context
    current_step_index = state.get("current_step_index", 0)
    plan_steps = state.get("plan_steps", [])
    
    # Filter out steps that don't require SQL or are visualization-only
    data_steps = [s for s in plan_steps if s.get("sql_required", True)]
    current_step_dict = data_steps[current_step_index] if current_step_index < len(data_steps) else None
    current_step = current_step_dict.get("task", user_query) if current_step_dict else user_query

    if error_log:
        # CONTEXT: The agent is now in "Fix Mode"
        prompt = f"""
        The user asked: {user_query}
        Your previous SQL: {last_sql}
        It failed with this error: {error_log}
        Please provide a corrected PostgreSQL SQL query. Do not include any explanations or additional text, just SQL.

        System Prompt:
        {generate_sql_system_prompt()}
        """
    else:
        # CONTEXT: The agent is in "Initial Generation Mode"
        # Include the current step being processed
        prompt = f"""
        {generate_sql_system_prompt()}
        """

    agent = create_agent(
        sql_agent_model,
        system_prompt=prompt
    )

    response = agent.invoke({"messages": [{"role": "user", "content": current_step}]})
    
    # Extract token usage with turn number
    turn_number = state.get("turn_number", 1)
    token_usage = extract_token_usage(response, agent_name="text_to_sql_agent", turn_number=turn_number)
    
    # Get text content from agent response (supports dict or object results)
    response_text = extract_agent_response_content(response)
    
    # Parse and clean the SQL query for display
    sql_query = parse_sql_query(response_text)
    
    # Create a formatted review message for the frontend (since interrupt_before stops before Human_Review node)
    review_message = f"""**SQL Query Ready for Review**

**Task:** {current_step}

**Generated SQL:**
```sql
{sql_query}
```

Please review the SQL query above. Click **Continue** to execute it, or provide feedback to regenerate it."""
    
    return_dict = {
        "generated_sql": response_text,
        "error_log": "",  # Clear the error once we retry
        "messages": [{"type": "ai", "content": review_message}],
    }
    
    if token_usage:
        return_dict["token_usage_log"] = [token_usage]
    print(f" ! SQL Generated for review:\n{sql_query}")
    return return_dict

def data_visual_agent_node(state: AgentState):
    """Custom node that creates visualizations based on query results."""
    user_input = state.get("user_query", "")
    query_result = get_latest_query_result()
    
    # Get the task description for the current visualization
    current_step_index = state.get("current_step_index", 0)
    plan_steps = state.get("plan_steps", [])
    data_steps = [s for s in plan_steps if s.get("sql_required", True)]
    
    # Get the step we just completed (current_step_index was already incremented)
    last_step_index = current_step_index - 1
    current_task = user_input
    if 0 <= last_step_index < len(data_steps):
        current_task = data_steps[last_step_index].get("task", user_input)
    
    query_key = None
    if query_result and isinstance(query_result, dict) and query_result.get("data"):
        metadata = query_result["metadata"]
        column_names = metadata["columns"]
        row_example = query_result["data"][0] if query_result["data"] else {}
        query_metadata = {
            "columns": column_names,
            "num_rows": metadata.get("num_rows", len(query_result["data"])),
            "num_columns": metadata.get("num_columns", len(column_names)),
            "sample_rows": query_result["data"][:3]
        }
        
        analysis_history = state.get("analysis_history", [])
        sql_entries = [e for e in analysis_history if e.get("type") == "sql_execution"]
        if sql_entries:
            query_key = sql_entries[-1].get("query_key")
    else:
        column_names = ["example_column_1", "example_column_2", "example_column_3"]
        row_example = {"example_column_1": "value1", "example_column_2": 123, "example_column_3": 45.67}
        query_metadata = {"columns": column_names, "sample_rows": [row_example]}
    
    agent = create_agent(
        data_visual_agent_model,
        system_prompt=data_vis_system_prompt(
            query_metadata=query_metadata
        )
    )
    
    result = agent.invoke({"messages": [{"role": "user", "content": current_task}]})
    
    turn_number = state.get("turn_number", 1)
    token_usage = extract_token_usage(result, agent_name="data_visual_agent", turn_number=turn_number)
    
    viz_content = extract_agent_response_content(result)
    try:
        viz_spec = json.loads(viz_content)
        
        if isinstance(viz_spec, list):
            if viz_spec:
                viz_spec = viz_spec[0]
            else:
                raise ValueError("Empty visualization specification list")
        
        chart_config = map_visualization_spec_to_chart(viz_spec, query_result=query_result)
        
        viz_output = json.dumps({
            "specification": viz_spec,
            "chart_config": chart_config
        }, indent=2)
    except json.JSONDecodeError:
        viz_output = viz_content
    except (ValueError, KeyError) as e:
        print(f"Warning: Invalid visualization specification: {e}")
        viz_output = viz_content

    viz_entry = {
        "type": "visualization",
        "query_key": query_key,
        "visualization_content": viz_output,
        "timestamp": datetime.now().isoformat()
    }
    
    return_dict = {
        "final_response": viz_output,
        "analysis_history": [viz_entry],
        "chart_configs": [chart_config]  # Save chart config for later use
    }
    
    if token_usage:
        return_dict["token_usage_log"] = [token_usage]
    
    return return_dict

def response_synthesizer_agent_node(state: AgentState):
    """Custom node that synthesizes response with chart specs and minimal data summary.
    
    Only passes:
    - chart_specs: Visualization specifications (spec only, no full chart config)
    - metadata: Minimal summary with key statistics only
    - data_sample: First 5-10 rows only for context
    """
    user_query = state.get("user_query", "")
    viz_output = state.get("final_response", "")
    
    chart_specs = ""
    if viz_output:
        try:
            viz_output_json = json.loads(viz_output)
            chart_specs = json.dumps({"specification": viz_output_json.get("specification", {})}, indent=2)
        except json.JSONDecodeError:
            chart_specs = viz_output
    
    query_result = get_latest_query_result()
    metadata = {}
    if query_result and isinstance(query_result, dict):
        original_metadata = query_result.get("metadata", {})
        
        metadata = {
            "columns": original_metadata.get("columns", []),
            "num_columns": original_metadata.get("num_columns", 0),
            "num_rows": original_metadata.get("num_rows", 0)
        }
        stat_analysis = query_result.get("statistical_analysis", {})
        if stat_analysis:
            metadata["statistical_analysis"] = stat_analysis

        describe_data = original_metadata.get("describe", {})
        if describe_data and "data" in describe_data and "index" in describe_data:
            stats_summary = {}
            index_labels = describe_data["index"]
            for col_idx, col_name in enumerate(describe_data.get("columns", [])):
                if col_idx < len(describe_data["data"][0]):
                    stats_summary[col_name] = {
                        label: describe_data["data"][idx][col_idx] 
                        for idx, label in enumerate(index_labels)
                        if label in ["count", "mean", "min", "max", "25%", "50%", "75%"]
                    }
            metadata["summary_statistics"] = stats_summary

        # Include Data Sample
        if query_result.get("data"):
            metadata["data_sample"] = query_result["data"][:30]  # First 30 rows only
    
    agent = create_agent(
        general_agent_model,
        system_prompt=response_synthesizer_system_prompt(
            chart_specs=chart_specs, 
            metadata=metadata
        )
    )
    
    result = agent.invoke(  {"messages": [{"role": "user", "content": user_query}]} )
    
    turn_number = state.get("turn_number", 1)
    token_usage = extract_token_usage(result, agent_name="response_synthesizer_agent", turn_number=turn_number)
    
    raw_content = extract_agent_response_content(result)
    final_content = extract_agent_response_content(result)
    final_content = re.sub(r'```json\s*\n.*?\n```', '', final_content, flags=re.DOTALL).strip()

    chart_configs = state.get("chart_configs", [])
    if chart_configs and "{chart_json}" in final_content:
        latest_chart_config = chart_configs[-1]
        
        chart_json_str = json.dumps(latest_chart_config, indent=2, ensure_ascii=False)
        chart_json_block = f"```json\n{chart_json_str}\n```"
        
        final_content = final_content.replace("{chart_json}", chart_json_block)
    
    save_query_results(save_all=True)
    print(f" ! Saved {len(query_results_cache)} query results to disk")
    
    turn_number = state.get("turn_number", 1)
    token_usage_log = state.get("token_usage_log", [])
    
    complete_log = token_usage_log + ([token_usage] if token_usage else [])
    current_turn_log = [entry for entry in complete_log if entry.get("turn_number") == turn_number]
    
    if current_turn_log:
        save_result = save_token_usage_to_file(current_turn_log)
        if save_result["success"]:
            print(f" ! Saved token usage to disk: {save_result['totals']['total_tokens']} total tokens")
        else:
            print(f" ! Failed to save token usage: {save_result.get('error', 'Unknown error')}")
    
    chat_entry = {
        "user_input": user_query,
        "final_response": raw_content,
        "timestamp": datetime.now().isoformat()
    }
    
    return_dict = {
        "final_response": final_content,
        "chat_history": [chat_entry],
        "turn_number": turn_number + 1,
        "raw_agent_response": raw_content,
        "messages": [{"type": "ai", "content": final_content}]
    }
    
    if token_usage:
        return_dict["token_usage_log"] = [token_usage]
    print(return_dict)
    return return_dict