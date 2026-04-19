from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agents.retriever.tools import semantic_search_tool
from agents.retriever.prompt import system_prompt

def hitl_agent(llm):
    """
    Wrapper function to inject the LLM and return the node for LangGraph.
    """
    def node(state):
        # 1. Get the last error from state
        # Ensure 'sql_error' is what your SQL agent actually populates!
        error_message = state.get('sql_error', 'Max retries reached with an unknown database error.')
        
        # 2. Simple explanation prompt
        explanation_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful Data Engineering Assistant. A SQL query failed after 3 attempts. "
                       "Explain the error simply to the user and ask if they want to 'Continue' or 'End'."),
            ("human", f"Latest DB Error: {error_message}")
        ])
        
        chain = explanation_prompt | llm
        response = chain.invoke({})
        
        # 3. Return the messages and clear the error for the next potential run
        return {
            "messages": [response],
            "sql_error": response.content,
            "final_insights":[response]
        }

    return node

