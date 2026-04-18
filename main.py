from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage
from agents.orchestrator import orchestrator_agent


app = FastAPI()

def response_generator():
    try:
        # 1. Initialize input
        user_query = "no of customer with highest no of orders"
        inputs = {"messages": [HumanMessage(content=user_query)]}
        final_response = None

        # 2. Iterate through the stream
        # Using stream_mode="updates" is often clearer for node tracking
        for event in orchestrator_agent.stream(inputs, stream_mode="updates"):
            for node_name, state_update in event.items():
                
                # Ensure messages exist in the update to avoid KeyErrors
                if "messages" not in state_update:
                    continue
                    
                last_msg = state_update["messages"][-1]
                
                # Logic for specific nodes
                if node_name == "retriever_node":
                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                        print("--- 🔍 Retriever is searching the Vector DB... ---")
                    else:
                        print(f"--- ✅ Plan Generated ---")
                        # Don't return yet! The graph might need to move to the next node.
                        final_response = last_msg.content
                
                elif node_name == "tools":
                    print("--- 🛠️ Tool Execution complete. Results found. ---")
                    final_response = last_msg.content
                elif node_name == "sql_generator_node":
                    if hasattr(last_msg,'tool_calls') and last_msg.tool_calls:
                        print("--- 🔍 Retriever is searching the Vector DB... ---")
                    else:
                        print(f"sql generated {last_msg.content}")
                        final_response = last_msg.content
                if node_name == "insights_generator_node":
                    print(f"sql generated {last_msg.content}")
                    # This is the final step, grab the insights!
                    raw_insights = state_update.get("final_insights")
    
                    # 2. Check if it's that list format you just showed me
                    if isinstance(raw_insights, list) and len(raw_insights) > 0:
                        # Extract the 'text' field from the first dictionary
                        final_response = raw_insights[0].get("text")
                    else:
                        # Otherwise, assume it's a standard string
                        final_response = raw_insights
                    print("--- ✨ Insights Generated ---")
                        
        # 3. Return the final content after the graph finishes execution
        if final_response:
            return {"response": final_response}
        else:
            raise HTTPException(status_code=500, detail="Graph failed to produce a response.")

    except Exception as e:
        # Provide a more useful error message for debugging
        print(f"Error: {e}")
        return {"error": str(e)}


response_generator()

@app.post("/query")
async def response_generator(user_query: str):
    try:
        # 1. Initialize input
        inputs = {"messages": [HumanMessage(content=user_query)]}
        final_response = None

        # 2. Iterate through the stream
        # Using stream_mode="updates" is often clearer for node tracking
        for event in orchestrator_agent.stream(inputs, stream_mode="updates"):
            for node_name, state_update in event.items():
                
                # Ensure messages exist in the update to avoid KeyErrors
                if "messages" not in state_update:
                    continue
                    
                last_msg = state_update["messages"][-1]
                
                # Logic for specific nodes
                if node_name == "retriever":
                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                        print("--- 🔍 Retriever is searching the Vector DB... ---")
                    else:
                        print(f"--- ✅ Plan Generated ---")
                        # Don't return yet! The graph might need to move to the next node.
                        final_response = last_msg.content
                
                elif node_name == "execute_tools":
                    print("--- 🛠️ Tool Execution complete. Results found. ---")
                    final_response = last_msg.content

        # 3. Return the final content after the graph finishes execution
        if final_response:
            return {"response": final_response}
        else:
            raise HTTPException(status_code=500, detail="Graph failed to produce a response.")

    except Exception as e:
        # Provide a more useful error message for debugging
        print(f"Error: {e}")
        return {"error": str(e)}







