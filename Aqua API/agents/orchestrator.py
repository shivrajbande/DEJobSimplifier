from typing import Optional, TypedDict, Literal, List, Dict, Any, Annotated
from langgraph.graph import StateGraph, START, END, add_messages
from IPython.display import Image, display
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode
import os
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver


# Import custom nodes
from agents.main_agent.logic import supervisor_agent
from agents.intent_classification.document_analyser.logic import document_classifier
from agents.intent_classification.intent_classifier.logic import Intent_classifier
from agents.execution_agents.sql_generator.logic import sql_generator_agent
from agents.execution_agents.sql_generator.prompt import system_prompt as sql_system_prompt

from agents.execution_agents.sql_generator.sql_validator import sql_validator_node
from agents.execution_agents.insights_generator.logic import insights_generator_agent
from agents.hitl import hitl_classifier_node

# Import prompts
from agents.intent_classification.intent_classifier.prompt import final_intent

# Import custom conditional router handlers
from agents.routers import supervisor_router, intent_router, router_after_validation, hitl_router

# =====================================================================
# 1. HIERARCHICAL STATE SCHEMAS (Synced with new architecture)
# =====================================================================

from agents.state import AgentState, ClarificationState, DocumentState, WorkflowState, ExecutionState


# =====================================================================
# 2. LLM CONNECTIONS (Groq Configuration)
# =====================================================================

triage_llm = init_chat_model('llama-3.1-8b-instant', model_provider='groq', temperature=0.1)
vision_llm = init_chat_model('meta-llama/llama-4-scout-17b-16e-instruct', model_provider='groq', temperature=0.1)
sql_llm = init_chat_model("llama-3.3-70b-versatile", model_provider="groq", temperature=0)
insights_llm = init_chat_model('llama-3.3-70b-versatile', model_provider='groq', temperature=0.5)

# =====================================================================
# 3. GRAPH INITIALIZATION & NODE REGISTRATION
# =====================================================================

workflow = StateGraph(AgentState)

# Phase 1: Intake & Discovery Nodes (Registered UPPERCASE)
workflow.add_node("SUPERVISOUR_NODE", supervisor_agent(llm=triage_llm))
workflow.add_node("DOCUMENT_ANALYZER_NODE", document_classifier(vision_llm))
workflow.add_node("INTENT_CLASSIFIER_NODE", Intent_classifier(triage_llm, final_intent))

# Phase 2: Generation, Validation & Analytical Blueprint Nodes
workflow.add_node("SQL_GENERATOR_NODE", sql_generator_agent(sql_llm, sql_system_prompt))
workflow.add_node("SQL_VALIDATOR_NODE", sql_validator_node)
workflow.add_node("INSIGHTS_GENERATOR_NODE", insights_generator_agent(insights_llm))

# Phase 3: Centralized Human-in-the-Loop Interruption Loop
workflow.add_node("HITL_NODE", hitl_classifier_node())

# =====================================================================
# 4. DETERMINISTIC & CONDITIONAL ROUTING EDGES
# =====================================================================

# 1. Entry Point -> Routes to UPPERCASE Supervisor node configuration
workflow.add_edge(START, "SUPERVISOUR_NODE")

workflow.add_conditional_edges(
    "SUPERVISOUR_NODE",
    supervisor_router,
    {
        "document_analyzer_node": "DOCUMENT_ANALYZER_NODE",
        "intent_classifier_node": "INTENT_CLASSIFIER_NODE"
    }
)



# 3. Document Analysis -> Drops sequentially into uppercase Intent Layer
workflow.add_edge("DOCUMENT_ANALYZER_NODE", "INTENT_CLASSIFIER_NODE")

# 4. Intent Router -> Corrected mapping points to match structural node bindings
workflow.add_conditional_edges(
    "INTENT_CLASSIFIER_NODE", 
    intent_router, 
    {
        "sql_generator_node": "SQL_GENERATOR_NODE",
        "insights_generator_node": "INSIGHTS_GENERATOR_NODE", 
        "hitl_node": "HITL_NODE",
        "intent_classifier_node": "INTENT_CLASSIFIER_NODE"
    }
)

# 5. Code Engine -> Drops directly into programmatic validation block
workflow.add_edge("SQL_GENERATOR_NODE", "SQL_VALIDATOR_NODE")

# 6. SQL Validator -> Fixed target mappings to match state machine requirements
workflow.add_conditional_edges(
    "SQL_VALIDATOR_NODE", 
    router_after_validation, 
    {
        "sql_generator_node": "SQL_GENERATOR_NODE",         
        "insights_generator_node": "INSIGHTS_GENERATOR_NODE", 
        "hitl_node": "HITL_NODE"                             
    }
)

# 7. Human Loop Correction Router -> Re-entry target strings synchronized with upper cases
workflow.add_conditional_edges(
    "HITL_NODE", 
    hitl_router, 
    {
        "supervisor_node": "SUPERVISOUR_NODE",     
        "sql_generator_node": "SQL_GENERATOR_NODE", 
        "END": "__end__"
    }
)

# 8. Terminal Paths
workflow.add_edge("INSIGHTS_GENERATOR_NODE", END)

# =====================================================================
# 5. COMPILE ENGINE
# =====================================================================
conn = sqlite3.connect("state_db.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

orchestrator_agent = workflow.compile(checkpointer=memory)