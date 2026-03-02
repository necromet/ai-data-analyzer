def context_resolver_agent_system_prompt():
    """
    System prompt for Context Resolver agent that combines user queries and history.
    """
    
    system_prompt = f"""Given the following conversation history and the users next question,rephrase the question to be a stand alone question.
If the conversation is irrelevant or empty, just restate the original question.
Do not add more details than necessary to the question.

Standalone Question:
"""
    
    return system_prompt
