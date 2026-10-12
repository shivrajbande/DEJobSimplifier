from langgraph.types import interrupt
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agents.execution_agents.retriever.tools import semantic_search_tool


def hitl_classifier_node():
    """
    Dedicated Human-in-the-loop interruption node. 
    Pauses execution, captures feedback, updates state history, and loops back.
    """
    def node(state):
        clar_state = state.get("clarification", {})
        clarification_history = clar_state.get('clarification_history', [])
        clarification_attempt = clar_state.get('clarification_attempt', 0)
        
        # Pull the staged data from the previous node
        pending = state.get("pending_clarification", {})
        selection_message = pending.get("selection_message", "Clarification required.")
        
        # 1. TRIGGER INTERRUPT (Execution halts completely here until resumed)
        user_response = interrupt({
            "status": "requires_selection",
            "document_type": pending.get("document_type"),
            "requires_selection": True,
            "message": selection_message,
            "sections": pending.get("sections", [])
        })

        # 2. PROCESS USER RESPONSE
        updated_history = list(clarification_history)
        updated_history.append({
            "question": selection_message,
            "answer": user_response.get("user_reply")
        })

        # 3. WRITE BACK STATE & LOOP BACK
        return {
            "intent_classified": False,
            "clarification": {
                "clarification_needed": True,
                "clarification_attempt": clarification_attempt + 1,
                "clarification_history": updated_history,
                "missing_fields": pending.get("missing_fields", [])
            },
            "document": {
                "document_type": pending.get("document_type"),
                "extracted_sections": pending.get("sections", []),
                "detected_entities": [],
                "detected_usecases": []
            },
            "workflow": {
                **state.get("workflow", {}),
                "next_step": "DOCUMENT_ANALYZER",  # Directing loop-back behavior
                "workflow_stage": "USER_CLARIFICATION_RECEIVED"
            },
            "pending_clarification": None  # Flush staged data
        }

    return node