from agents.intent_classification.document_analyser.prompt import image_system_promt
import json
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import interrupt


def document_classifier(llm):
    def document_node(state):
        query = state.get("raw_user_query", "").strip()
        image = state.get("uploaded_image")
        
        clar_state = state.get("clarification", {})
        clarification_history = clar_state.get('clarification_history', [])
        clarification_attempt = clar_state.get('clarification_attempt', 0)
        
        if not image:
            return {
                "workflow": {
                    **state.get("workflow", {}),
                    "next_step": "INTENT_CLASSIFIER_NODE"
                }
            }
            
        # Normalize: wrap raw base64 in a data URI if not already prefixed
        if image and not image.startswith("data:"):
            image = f"data:image/jpeg;base64,{image}"

        payload = [
            SystemMessage(content=image_system_promt),
            HumanMessage(content=[
                {"type": "image_url", "image_url": {"url": image}},
                {
                    "type": "text", 
                    "text": f"Original Query: {query}\nHistory:\n{json.dumps(clarification_history)}"
                }
            ])
        ] 
        
        try:
            response = llm.invoke(payload)
            raw_content = response.content.strip()
            
            # Clean Markdown wrapping if present
            if raw_content.startswith("```json"):
                raw_content = raw_content.split("\n```json")[1].split("```")[0].strip()
            elif raw_content.startswith("```"):
                raw_content = raw_content.split("\n```")[1].split("```")[0].strip()
            
            result = json.loads(raw_content)
            
            interaction = result.get("recommended_user_interaction", {}) or {}
            selection_message = interaction.get("selection_message", "Clarification required.")
            
            should_interrupt = (
                result.get("clarification_needed", False)
                and clarification_attempt < 3
            )
            
            if should_interrupt:
                # Instead of interrupting here, stage the data and route to the HITL node
                return {
                    "intent_classified": False,
                    "workflow": {
                        **state.get("workflow", {}),
                        "next_step": "HITL_NODE", # Dynamic router targets this
                        "workflow_stage": "DOCUMENT_ANALYZING_PENDING"
                    },
                    # Hold onto this payload so the HITL node knows what to ask
                    "pending_clarification": {
                        "selection_message": selection_message,
                        "document_type": result.get("document_type"),
                        "sections": result.get("sections", []),
                        "missing_fields": result.get("missing_fields", [])
                    }
                }
                
            # Direct path: No clarification needed
            return {
                "intent_classified": False,
                "clarification": {
                    **clar_state,
                    "clarification_needed": False
                },
                "document": {
                    "document_type": result.get("document_type"),
                    "extracted_sections": result.get("sections", []),
                    "detected_entities": result.get("detected_entities", []),
                    "detected_usecases": result.get("detected_usecases", []),
                    "overall_summary":result.get("overall_summary","N/A"),
                    "total_no_of_sections":result.get("total_no_of_sections",0),
                },
                "workflow": {
                    **state.get("workflow", {}),
                    "next_step": "INTENT_CLASSIFIER_NODE",
                    "workflow_stage": "IMAGE_PROCESSED"
                }
            }

        except Exception as e:
            print(f"Parsing Exception in Document Node: {e}")
            return {
                "workflow": {
                    **state.get("workflow", {}),
                    "next_step": "INTENT_CLASSIFIER_NODE",
                    "workflow_stage": "FALLBACK_TRIGGERED"
                }
            }
            
    return document_node
    # def document_node(state):
    #     # 1. READ safely from nested dictionary paths
    #     query = state.get("raw_user_query", "").strip()
    #     image = state.get("uploaded_image")
        
    #     # Access nested sub-states safely with defaults
    #     clar_state = state.get("clarification", {})
    #     clarification_history = clar_state.get('clarification_history', [])
    #     clarification_attempt = clar_state.get('clarification_attempt', 0)
        
    #     if not image:
    #         return {
    #             "workflow": {
    #                 **state.get("workflow", {}),
    #                 "next_step": "INTENT_CLASSIFIER"
    #             }
    #         }
            
    #     # Assemble payload for your JSON Multimodal engine
    #     payload = [
    #         SystemMessage(content=image_system_promt),
    #         HumanMessage(content=[
    #             {"type": "image_url", "image_url": {"url": image}},
    #             {
    #                 "type": "text", 
    #                 "text": f"Original Query: {query}\nHistory:\n{json.dumps(clarification_history)}"
    #             }
    #         ])
    #     ] 
        
    #     response = llm.invoke(payload)
        
    #     try:
    #         raw_content = response.content.strip()
    #         # Strip markdown code block wrappers if present
    #         if raw_content.startswith("```json"):
    #             raw_content = raw_content.split("```json")[1].split("```")[0].strip()
    #         elif raw_content.startswith("```"):
    #             raw_content = raw_content.split("```")[1].split("```")[0].strip()
            
    #         result = json.loads(raw_content)
            
    #         interaction = result.get("recommended_user_interaction", {}) or {}
    #         selection_message = interaction.get("selection_message", "Clarification required.")
            
    #         # CRITICAL FIX: Removed "overall_confidence" dependency since confidence scoring was removed from prompt.
    #         # We now rely cleanly on the explicit clarification_needed boolean flag and retry count safety limits.
    #         should_interrupt = (
    #             result.get("clarification_needed", False)
    #             and clarification_attempt < 3
    #         )
            
    #         if should_interrupt:
    #             # Trigger the Human-In-The-Loop break
    #             user_response = interrupt({
    #                 "status": "requires_selection",
    #                 "document_type": result.get("document_type"),
    #                 "requires_selection": True,
    #                 "message": selection_message,
    #                 "sections": result.get("sections", [])
    #             })

    #             # Append the new conversation slice to the history list
    #             updated_history = list(clarification_history)
    #             updated_history.append({
    #                 "question": selection_message,
    #                 "answer": user_response.get("user_reply")
    #             })

    #             # 2. WRITE back to specific nested sub-states safely preserving other keys
    #             return {
    #                 "intent_classified": False,
    #                 "clarification": {
    #                     "clarification_needed": True,
    #                     "clarification_attempt": clarification_attempt + 1,
    #                     "clarification_history": updated_history,
    #                     "missing_fields": result.get("missing_fields", [])
    #                 },
    #                 "document": {
    #                     "document_type": result.get("document_type"),
    #                     "extracted_sections": result.get("sections", []),
    #                     "detected_entities": [],
    #                     "detected_usecases": []
    #                 },
    #                 "workflow": {
    #                     **state.get("workflow", {}),
    #                     "next_step": "DOCUMENT_ANALYZER",
    #                     "workflow_stage": "DOCUMENT_ANALYZING_PENDING"
    #                 }
    #             }
                
    #         # No interruption needed -> Push straight through to intent classifier processing
    #         return {
    #             "intent_classified": False,
    #             "clarification": {
    #                 **clar_state,
    #                 "clarification_needed": False
    #             },
    #             "document": {
    #                 "document_type": result.get("document_type"),
    #                 "extracted_sections": result.get("sections", []),
    #                 "detected_entities": result.get("detected_entities", []),
    #                 "detected_usecases": result.get("detected_usecases", [])
    #             },
    #             "workflow": {
    #                 **state.get("workflow", {}),
    #                 "next_step": "INTENT_CLASSIFIER",
    #                 "workflow_stage": "IMAGE_PROCESSED"
    #             }
    #         }

    #     except Exception as e:
    #         print(f"Parsing Exception in Document Node: {e}")
    #         return {
    #             "workflow": {
    #                 **state.get("workflow", {}),
    #                 "next_step": "INTENT_CLASSIFIER",
    #                 "workflow_stage": "FALLBACK_TRIGGERED"
    #             }
    #         }
            
    # return document_node