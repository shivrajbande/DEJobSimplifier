from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langgraph.graph import END  # Explicitly importing END token boundary
from agents.execution_agents.insights_generator.prompt import system_prompt
from agents.state import AgentState

def insights_generator_agent(llm):
    """
    This agent takes the successfully validated SQL/View syntax and breaks down
    the structural logic, join linkages, and architectural data flow for the end-user.
    """
    # 1. Initialize the Chat Prompt Template with consistent history bindings
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])

    def node(state: AgentState):
        # Safely capture nested structural states
        doc_state = state.get("document",{})
        exec_state = state.get("execution", {})
        current_workflow = state.get("workflow", {})
        message_history = state.get("messages", [])

        raw_sql = exec_state.get("generated_sql")
        generated_sql = raw_sql.strip() if (raw_sql and isinstance(raw_sql, str)) else "N/A"
        if not generated_sql:
            generated_sql = "N/A"

        user_query = state.get("raw_user_query", "N/A")
        reasoning_summary = exec_state.get("reasoning_summary", "N/A")
        relevant_schema = state.get("document", {}).get("relevant_schema", "No schema provided.")
        query_results = exec_state.get("query_results", None)

        # Format query results for the prompt
        import json
        if query_results:
            results_block = json.dumps(query_results, indent=2, default=str)
        else:
            results_block = "N/A"

        # =====================================================
        # 🧠 STRUCTURAL CONTEXT INJECTION
        # =====================================================
        # We isolate the exact template string rendering payload so it doesn't 
        # collide with LangChain's strict MessagesPlaceholder layout validation checks.
        context_instruction = (
            f"### INPUT METADATA FOR COMPILATION REVIEW\n"
            f"- Analytical Goal: {user_query}\n"
            f"- Reasoning Summary: {reasoning_summary}\n\n"
            f"### RETRIEVED SCHEMA EMBEDDINGS (Matched Tables)\n"
            f"{relevant_schema}\n\n"
            f"### VERIFIED DATABASE BLUEPRINT SCRIPT\n"
            f"```sql\n{generated_sql}\n```\n\n"
            f"### QUERY EXECUTION RESULT (Actual data, max 10 rows)\n"
            f"```json\n{results_block}\n```"
        )

        # Assemble input payload safely
        active_messages = list(message_history)
        active_messages.append(HumanMessage(content=context_instruction))

        payload = {
            "messages": active_messages,
            "generated_sql": generated_sql,
            "user_requirement": user_query,
            "refined_execution_plan": reasoning_summary
        }
        
        # 2. Invoke our analysis chain
        chain = prompt | llm
        response = chain.invoke(payload)

        if not response.content:
            print("⚠️ Warning: Insights Generator LLM returned empty content!")

        # =====================================================
        # 3. RETURN HIERARCHICAL UPDATES
        # =====================================================
        return {
            "messages": [response],
            "execution": {
                **exec_state,
                # Store the complete architectural explanation block safely
                "generated_insights": response.content or "Error: No analytical blueprint generated."
            },
            "workflow": {
                **current_workflow,
                "workflow_stage": "BLUEPRINT_EXPLAINED",
                # 💡 FIXED: Uses standard string literal token matching your orchestrator configuration!
                "next_step": "__end__"  
            }
        }

    return node