from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END, add_messages
from IPython.display import Image, display
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from typing_extensions import Annotated
from langgraph.prebuilt import ToolNode, tools_condition
import os
from langgraph.checkpoint.memory import MemorySaver
from typing import List
from agents.retriever.logic import scheme_retriever_agent
from agents.sql_generator.logic import sql_generator_agent
from agents.retriever.tools import semantic_search_tool
from agents.sql_generator.tools import execute_sql_query_tool
from agents.common_tool import db_config_tool
from agents.routers import sql_generator_conditions,htil_router,route_after_tools,retriever_router
from agents.hitl import hitl_agent



class AgentState(TypedDict):
    # 'add_messages' means this list only grows, it never gets erased
    messages: Annotated[List, add_messages]
    
    # These strings will be REPLACED every time a node returns them
    user_requirement: str
    relevant_schema: str
    generated_sql: str
    
    is_valid: bool
    sql_error: str
    retry_count: int  # You'll increment this in your nodes: state['retry_count'] + 1
    
    final_insights: str



llm = init_chat_model('llama-3.1-8b-instant', model_provider='groq')

workflow = StateGraph(AgentState)
tools = ToolNode([semantic_search_tool,db_config_tool,execute_sql_query_tool])


# Graph nodes
workflow.add_node("tools",tools)
workflow.add_node("retriever_node",scheme_retriever_agent(llm))
workflow.add_node("sql_generator_node",sql_generator_agent(llm))
workflow.add_node("hitl_node",hitl_agent(llm))

# Define edges between the nodes
workflow.add_edge(START,"retriever_node")
workflow.add_conditional_edges("retriever_node", retriever_router, # Standard LangGraph tool check
    {
        "tools": "tools",
        "retriever_node": "retriever_node",
        "__end__": "sql_generator_node" # If no tools called, go to SQL Gen
    })
workflow.add_conditional_edges("tools", route_after_tools)
workflow.add_conditional_edges("sql_generator_node",sql_generator_conditions,{
    "tools":"tools",
    "retry":"sql_generator_node",
    "fail":"hitl_node",
    "success":END
})

workflow.add_conditional_edges("hitl_node",htil_router,{
    "continue":"sql_generator_node",
    "end":END
})


#compile the workflow to actually run
orchestrator_agent = workflow.compile()

