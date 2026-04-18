from langchain_core.messages import SystemMessage
from agents.insights_generator.prompt import system_prompt
def insights_generator_agent(llm):
    # We will build the template inside the node to ensure it's fresh
    def node(state):
        # 1. Manually format the system prompt string with the state variables
        # This forces Python to do the work before LangChain even sees it
        raw_schema = state.get('relevant_schema', "N/A")
        short_schema = str(raw_schema)[:500] + "..." if len(str(raw_schema)) > 500 else raw_schema
        try:
            full_system_message = system_prompt.format(
                generated_sql=state.get('generated_sql', "N/A"),
                sql_results=state.get('sql_results', "N/A"),
                relevant_schema=short_schema,
                user_requirement=state.get('user_requirement', "N/A")
            )
        except KeyError as e:
            # This happens if your system_prompt has { } that aren't variables
            print(f"❌ Formatting Error: Missing key {e}")
            full_system_message = system_prompt 


        # 2. Create the message list manually
        user_query = state.get("messages", [])[0]
        messages = [

            SystemMessage(content=full_system_message),
            user_query 
        ]

        # 3. Invoke the LLM directly with the message list
        # This bypasses 'prompt.invoke' and goes straight to the brain
        print(f"--- 🚀 Sending Isolated Prompt (Length: {len(full_system_message)}) ---")
        
        response = llm.invoke(messages)

        print(f"response generated is{response.content}")

        if not response.content:
            print("⚠️ Warning: LLM still returned empty content!")

        return {
            "messages": [response],
            "final_insights": response.content or "Error: No insights generated."
        }

    return node