from typing import Literal
def sql_generator_conditions(state) -> Literal["tools", "retry", "fail", "success"]:
    last_msg = state['messages'][-1]

    # 1. If the AI wants to use a tool (db_config or execute_sql)
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    
    # 2. Check for Database Errors
    if "DB_ERROR" in last_msg.content or "MYSQL_ERROR" in last_msg.content:
        # We only check the count here; we don't increment it here
        if state.get('retry_count', 0) < 3:
            return "retry"
        else:
            return "fail"
            
    return "success"

def route_after_tools(state):
    # If we already have the schema, don't go back to the retriever!
    # Go straight to the SQL Generator to attempt the fix.
    if any(call['name'] == 'execute_sql_query_tool' for call in state['messages'][-2].tool_calls):
        return "sql_generator_node"
        
    return "retriever_node"

def htil_router(state):
    """
    Called after 3 failed retries.
    Returns 'continue' to retry or 'end' to stop.
    """
    user_input = state['messages'][-1].content.lower()
    if "continue" in user_input:
        return "continue"
    else:
        return "end"


def retriever_router(state):
    last_message = state["messages"][-1]
    
    # 1. If the LLM called a tool, go to tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # 2. If the LLM output tags, we are done with retrieval
    if state.get("relevant_schema") and state.get("user_requirement"):
        return "__end__" # This maps to sql_generator_node in your config
    
    # 3. Fallback: if it didn't call a tool and didn't provide tags, 
    # the 'node' added a HumanMessage, so we loop back to retriever_node to try again.
    return "retriever_node"
    