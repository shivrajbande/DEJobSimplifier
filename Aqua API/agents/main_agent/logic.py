import json
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import interrupt


def supervisor_agent(llm):
    def supervisor_node(state):

        query = state.get("raw_user_query")
        image = state.get("uploaded_image")

        has_query = bool(query and query.strip())
        has_image = bool(image)
        current_workflow = state.get("workflow",{})
    # =====================================================
    # INITIAL TRIAGE
    # =====================================================
        if has_image:

            return {
                "workflow": {
                    **current_workflow,
                    "workflow_stage": "INPUT_CLASSIFIED",
                    "next_step": "DOCUMENT_ANALYZER_NODE"
                }
            }

        return {
            "workflow": {
                **current_workflow,
                "workflow_stage": "INPUT_CLASSIFIED",
                "next_step": "INTENT_CLASSIFIER_NODE"
            }
        }

      
        
        
        
    return supervisor_node