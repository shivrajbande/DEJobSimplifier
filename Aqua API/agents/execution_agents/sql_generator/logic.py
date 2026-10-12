from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from agents.state import AgentState

def sql_generator_agent(llm, system_prompt: str):
    """
    Translates the refined execution plan and retrieved schema into clean SQL.
    Accepts feedback from the validator node if errors are caught.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])

    def node(state: AgentState):
        # 1. Safe Hierarchical State Access
        query = state.get("raw_user_query", "")
        doc_state = state.get("document", {})
        exec_state = state.get("execution", {})
        clar_state = state.get("clarification", {})

        relevant_schema = doc_state.get("relevant_schema", "No schema provided.")
        refined_plan = exec_state.get("refined_execution_plan", query)
        sql_error = exec_state.get("sql_error", "")
        message_history = state.get("messages", [])

        # =====================================================
        # 🧠 INLINE INJECTION FOR SELF-HEALING HISTORY
        # =====================================================
        # To ensure the LLM perfectly parses our variables without template 
        # dictionary errors, we structure the current turn context as a rich 
        # HumanMessage payload appended to the conversation tracking thread.
        context_instruction = (
            f"### CURRENT EXECUTION CONTEXT\n"
            f"- Analytical Goal: {query}\n"
            f"- Refined Execution Plan: {refined_plan}\n"
            f"- Document Type: {doc_state.get('document_type', 'Unknown')}\n\n"
            f"### SURGICALLY RETRIEVED SCHEMA TRUTH\n"
            f"{relevant_schema}\n\n"
        )
        
        # If the validator node dropped an error, forcefully append it here
        if sql_error:
            context_instruction += (
                f"⚠️ ### PREVIOUS VALIDATION REJECTION ERROR\n"
                f"Your last query failed compilation with the following error:\n"
                f"{sql_error}\n"
                f"Please inspect your table aliases, join hooks, and column mappings to fix this issue."
            )

        # Assemble the input dictionary matching the variable requirements
        # We append the context instruction message directly to feed the placeholder safely
        active_messages = list(message_history)
        active_messages.append(HumanMessage(content=context_instruction))

        input_data = {
            "messages": active_messages,
            "relevant_schema": relevant_schema,
            "user_requirement": refined_plan,
            "sql_error": sql_error 
        }
        
        # 2. Invoke LLM
        chain = prompt | llm
        response = chain.invoke(input_data)

        # 3. Clean up Markdown Code Block Wrappers safely
        generated_query_text = response.content.strip()
        if generated_query_text.startswith("```"):
            generated_query_text = generated_query_text.split("```sql")[-1].split("```")[0].strip()
            if generated_query_text.startswith("```"):
                generated_query_text = generated_query_text.split("```")[-1].strip()

        # =====================================================
        # 4. NESTED STATE RETURN
        # =====================================================
        return {
            "messages": [response],
            "execution": {
                **exec_state,
                "generated_sql": generated_query_text
            },
            "workflow": {
                **state.get("workflow", {}),
                # 💡 FIXED: Match case lowercase registration named in orchestrator file!
                "next_step": "SQL_VALIDATOR_NODE", 
                "workflow_stage": "SQL_QUERY_GENERATED"
            }
        }

    return node