from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agents.sql_generator.prompt import system_prompt
from agents.common_tool import db_config_tool
from langchain_core.messages import HumanMessage

def sql_generator_agent(llm):
    '''
        This function will generate the sql
        1. This agent take schema_requirements and plan to generate sql query
        2. after generating sql query it will use db_config_tool to get the db config
        3. then it will execute the sql query and return the result if no error, else regenerate the sql query by trying again
        4. if max retry count is reached then return the error message
    '''
    # 1. Bind the tools to the llm.
    llm_with_tools = llm.bind_tools([db_config_tool])

    # 2. Create a prompt for the classifier agent.
    prompt = ChatPromptTemplate.from_messages([
        ("system",system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])


    def node(state):
        # 1. TOKEN SAVING: Only send the last 3-5 messages to LLM
        # This prevents the 413 error by cutting out old, bulky tool results
        recent_messages = state['messages'][-3:] 

        input_data = {
            "messages": recent_messages,
            "relevant_schema": state.get('relevant_schema', "No schema provided"),
            "user_requirement": state.get('user_requirement', "No plan provided"),
            "sql_error": state.get('sql_error', "") 
        }
        
        # 2. Invoke LLM
        chain = prompt | llm_with_tools
        response = chain.invoke(input_data)

        current_retry = state.get('retry_count', 0)
        update = {'messages': [response]}
        
        # 3. Always increment retry count when the LLM makes an attempt
        update['retry_count'] = current_retry + 1

        # 4. Handle Tool Calls or Parsing
        if response.tool_calls:
            # If it's calling a tool, just pass it through to the "tools" node
            return update
        
        content = response.content or ""
        
        # 5. Parsing & Logic Check
        if "<SQL_QUERY>" not in content or "<SQL_RESULTS>" not in content:
            # Check if the content contains an error message from a tool execution
            if "MYSQL_ERROR" in content or "DB_ERROR" in content:
                update['sql_error'] = content # Save error for the HITL agent
            else:
                # Nagging the AI for formatting
                update["messages"].append(
                    HumanMessage(content="Error: Please provide the final output inside <SQL_QUERY> and <SQL_RESULTS> tags.")
                )
        else:
            # Success Path: Extract data
            try:
                sql_query = content.split("<SQL_QUERY>")[1].split("</SQL_QUERY>")[0].strip()
                sql_results = content.split("<SQL_RESULTS>")[1].split("</SQL_RESULTS>")[0].strip()
                
                update['generated_sql'] = sql_query
                # We don't need to update sql_error here as it's a success
            except IndexError:
                # Fallback for poorly formatted tags
                update["messages"].append(HumanMessage(content="Tag parsing failed. Please use strict <SQL_QUERY>...</SQL_QUERY> format."))

        return update
    # 4. Return the classifier agent/node which will be used by langgraph.
    return node


    


