import json
from langchain_core.messages import SystemMessage, HumanMessage
from agents.execution_agents.retriever.tools import semantic_search_tool
from agents.state import AgentState

def Intent_classifier(llm, final_intent_prompt):
    def intent_node(state: AgentState):
        # =====================================================
        # 1. SAFE HIERARCHICAL STATE ACCESS
        # =====================================================
        query = state.get("raw_user_query", "").strip()
        doc_state = state.get("document", {})
        clar_state = state.get("clarification", {})
        exec_state = state.get("execution", {})
        current_workflow = state.get("workflow", {})

        clarification_history = clar_state.get('clarification_history', [])

        # =====================================================
        # 2. PACKAGE CONTEXT FOR INTENT MODEL
        # =====================================================

        #need to send refine doc information...not complete doc object...it is not picking up properly..
        context_payload = (
            f"Raw User Query: {query}\n"
            f"Overall Summary from Document: {doc_state.get('overall_summary', 'None')}\n"
            f"Total number of sections in the document: {doc_state.get('total_no_of_sections', 'None')}\n"
            f"Extracted Sections: {json.dumps(doc_state.get('extracted_sections', []))}\n"
            f"Previous Clarifications: {json.dumps(clarification_history)}"
        )

        payload = [
            SystemMessage(content=final_intent_prompt),
            HumanMessage(content=context_payload)
        ]
        
        response = llm.invoke(payload)
        
        try:
            # =====================================================
            # 3. PARSE JSON OUTPUT SAFELY
            # =====================================================
            raw_content = response.content.strip()
            if raw_content.startswith("```"):
                raw_content = raw_content.split("```json")[-1].split("```")[0].strip()
                
            result = json.loads(raw_content)
            
            target_node = result.get("recommended_routing_node", "BASIC_DATA_INFO")
            clarification_needed = result.get("clarification_needed", False)
            section_clarifications = result.get("section_clarifications", [])

            # =====================================================
            # 4. DECOUPLED CLARIFICATION BRANCH (NO INLINE INTERRUPT)
            # =====================================================
            if clarification_needed:
                print("⚠️ Intent Agent requires clarification. Routing execution to hitl_node...")
                
                # Determine interaction type
                interaction_type = "select"
                placeholder = "Type your response here..."
                
                # Check if any question is text-based or if there are zero options
                has_options = False
                for sc in section_clarifications:
                    if sc.get("options"):
                        has_options = True
                    if sc.get("question_type") == "text":
                        interaction_type = "text"
                
                global_clarifications = result.get("global_clarifications", [])
                for gc in global_clarifications:
                    if gc.get("options"):
                        has_options = True
                    if gc.get("question_type") == "text":
                        interaction_type = "text"
                
                if not has_options:
                    interaction_type = "text"
                
                sections = []
                selection_message = "Clarification required."
                
                if interaction_type == "select":
                    # Format section clarifications as options
                    for idx, sc in enumerate(section_clarifications):
                        question = sc.get("question", "Clarification needed")
                        options = sc.get("options", [])
                        section_name = sc.get("section_name", f"Question {idx+1}")
                        
                        for opt_idx, opt in enumerate(options):
                            sections.append({
                                "section_id": f"opt_{idx}_{opt_idx}",
                                "section_name": opt,
                                "content_type": section_name,
                                "summary": question
                            })
                    
                    # Process global clarifications
                    for idx, gc in enumerate(global_clarifications):
                        question = gc.get("question", "Clarification needed")
                        options = gc.get("options", [])
                        for opt_idx, opt in enumerate(options):
                            sections.append({
                                "section_id": f"glob_{idx}_{opt_idx}",
                                "section_name": opt,
                                "content_type": "Global Setting",
                                "summary": question
                            })
                else:
                    # Provide placeholder example if any
                    if section_clarifications:
                        sc = section_clarifications[0]
                        options = sc.get("options", [])
                        if options:
                            placeholder = f"e.g., {options[0]}"
                    elif global_clarifications:
                        gc = global_clarifications[0]
                        options = gc.get("options", [])
                        if options:
                            placeholder = f"e.g., {options[0]}"
                
                if section_clarifications:
                    selection_message = section_clarifications[0].get("question", selection_message)
                elif global_clarifications:
                    selection_message = global_clarifications[0].get("question", selection_message)

                return {
                    "clarification": {
                        **clar_state,
                        "clarification_needed": True,
                        "section_clarifications": section_clarifications
                    },
                    "workflow": {
                        **current_workflow,
                        "next_step": "HITL_NODE",  # Hands control to your centralized loop node
                        "workflow_stage": "CLASSIFICATION_PENDING"
                    },
                    "pending_clarification": {
                        "selection_message": selection_message,
                        "document_type": doc_state.get("document_type"),
                        "interaction_type": interaction_type,
                        "placeholder": placeholder,
                        "sections": sections,
                        "missing_fields": []
                    }
                }

            # =====================================================
            # 5. SUCCESS PATH -> DDL SCHEMA LOOKUP & EXECUTION HANDOFF
            # =====================================================
            fetched_schema = ""
            refined_plan = result.get("refined_execution_plan", query)
            # Fall back to reasoning_summary if the LLM generated SQL code instead of a plain-text plan
            if "SELECT" in refined_plan.upper() and "FROM" in refined_plan.upper():
                refined_plan = result.get("reasoning_summary", query)
            
            if target_node in ("SQL_GENERATOR", "SQL_GENERATOR_NODE"):
                print(f"🔍 Fetching semantic DDL embeddings for plan: '{refined_plan}'")
                # Semantic search tool queries vector space using the refined business plan
                matched_ddl_list = semantic_search_tool.func(refined_plan)
                fetched_schema = matched_ddl_list

            return {
                "document": {
                    **doc_state,
                    "relevant_schema": fetched_schema
                },
                "clarification": {
                    **clar_state,
                    "clarification_needed": False
                },
                "execution": {
                    **exec_state,
                    "refined_execution_plan": refined_plan,
                    "reasoning_summary": result.get("reasoning_summary", "")
                },
                "workflow": {
                    **current_workflow,
                    "next_step": target_node, 
                    "workflow_stage": "INTENT_LOCKED",
                    "primary_intent": result.get("primary_intent", "N/A")
                }
            }

        except Exception as e:
            print(f"Error parsing intent response: {e}")
            attempts = clar_state.get("classification_attempts", 0)
            if attempts < 3:
                print(f"🔄 Retrying Intent Classification (Attempt {attempts + 1}/3)...")
                return {
                    "messages": [
                        response, 
                        SystemMessage(content=f"Error parsing response or running tool: {str(e)}. Please retry and output strictly valid JSON conforming to the schema.")
                    ],
                    "clarification": {
                        **clar_state,
                        "classification_attempts": attempts + 1
                    },
                    "workflow": {
                        **current_workflow,
                        "next_step": "INTENT_CLASSIFIER_NODE",
                        "workflow_stage": "INTENT_CLASSIFIER_SELF_HEAL"
                    }
                }
            else:
                print("❌ Intent Classification failed after maximum retries. Routing to HITL_NODE...")
                return {
                    "clarification": {
                        **clar_state,
                        "clarification_needed": True,
                        "classification_attempts": 0  # Reset for next run
                    },
                    "workflow": {
                        **current_workflow,
                        "next_step": "HITL_NODE",
                        "workflow_stage": "INTENT_CLASSIFICATION_FAILED",
                        "status": "failed"
                    },
                    "pending_clarification": {
                        "selection_message": f"Intent classification failed after multiple retries. System error: {str(e)}. Please clarify your instruction.",
                        "document_type": doc_state.get("document_type"),
                        "sections": doc_state.get("extracted_sections", [])
                    }
                }
            
    return intent_node