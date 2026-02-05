def response_synthesizer_system_prompt(user_input: str, data_visualizer: str, metadata:object) -> str:
    """This is the system prompt for the data visualization agent."""
    prompt = f"""
User Input: {user_input}

Data Visualizer Output: {data_visualizer}

Metadata: {metadata}

System Prompt:
You are a response synthesizer agent; given user input, echarts.js option object, and metadata. Your task is to synthesize a concise and clear response to the user input based on the data visualization output and metadata provided.

Suggestion for synthesis:
- Explain key insights from metadata.
- Use data visualizer output to support your explanations.
"""
    return prompt
