from agents.state import AgentState
from typing import Literal

def intent_router(state):
    workflow_state = state.get("workflow",{})
   
    next_step = workflow_state.get("next_step","")
    if next_step in ("SQL_GENERATOR", "SQL_GENERATOR_NODE"):
        return "sql_generator_node"
    elif next_step in ("INSIGHTS_GENERATOR", "INSIGHTS_GENERATOR_NODE"):
        return "insights_generator_node"
    elif next_step in ("HITL", "HITL_NODE"):
        return "hitl_node"
    elif next_step in ("INTENT_CLASSIFIER", "INTENT_CLASSIFIER_NODE"):
        return "intent_classifier_node"

def router_after_validation(state):
    workflow_state = state.get("workflow",{})
    
    next_step = workflow_state.get("next_step","")
    if next_step in ("SQL_GENERATOR", "SQL_GENERATOR_NODE"):
        return "sql_generator_node"
    elif next_step in ("INSIGHTS_GENERATOR", "INSIGHTS_GENERATOR_NODE"):
        return "insights_generator_node"
    elif next_step in ("HITL", "HITL_NODE"):
        return "hitl_node"

def supervisor_router(state):
    workflow_state = state.get("workflow", {})
    next_step = workflow_state.get("next_step", "")
    if next_step == "DOCUMENT_ANALYZER_NODE":
        return "document_analyzer_node"
    else:
        return "intent_classifier_node"

def hitl_router(state):
    """
    Evaluates the user's human-in-the-loop decision and dynamically routes 
    the graph back to the calling node, or cleanly terminates.
    """
    # 1. Look at what the user said (adapting to your message structure)
    user_input = state['messages'][-1].content.lower()
    
    # 2. Extract the return destination breadcrumb safely
    workflow_state = state.get("workflow", {})
    return_destination = workflow_state.get("return_to", "supervisor_node")

    # 3. Route based on their intent
    if "continue" in user_input or "yes" in user_input:
        # Dynamically returns the node identifier they came from!
        return return_destination 
    else:
        return "END"

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
    
