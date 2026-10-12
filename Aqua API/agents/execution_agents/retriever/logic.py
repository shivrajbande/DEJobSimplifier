from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agents.execution_agents.retriever.tools import semantic_search_tool
from agents.execution_agents.retriever.prompt import system_prompt
from langchain_core.messages import HumanMessage
def scheme_retriever_agent(llm):
    '''
        This function will create the classifier agent.
        1. Bind the schema_search tool to the node.
        2. Create a scheme_retriver agent(node) using the prompt and llm_with_tools.
        3. Return the agent/node which will be used by langgraph.
    '''
    # 1. Bind the tools to the llm.
    llm_with_tools = llm.bind_tools([semantic_search_tool])

    # 2. Create a prompt for the classifier agent.
    prompt = ChatPromptTemplate.from_messages([
        ("system",system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])

    # 3. Create a classofoer agent(node) using the prompt and llm_with_tools.
    def node(state):
        messages = state['messages']
        chain = prompt | llm_with_tools
        response = chain.invoke({'messages': messages})
        
        # 1. Default update: always track the latest message
        update = {'messages': [response]}
        
        # 2. Check if the AI is FINISHED with tools but MISSED the tags
        # We only nag the AI if it is NOT calling a tool and NOT providing the plan.
        if not response.tool_calls:
            content = response.content or ""
            
            if "<PLAN>" not in content:
                # Inject a 'correction' message to force the AI to follow the template
                update["messages"].append(
                    HumanMessage(content="Error: I see the tool results, but you haven't provided the structured <SCHEMA> and <PLAN>. Please provide them now.")
                )
            
            # 3. If it IS finished and HAS the tags, extract them for Agent 2
            elif "<SCHEMA>" in content and "<PLAN>" in content:
                print(f"schema and ai resposne includes below info,{content}")
                schema_part = content.split("<SCHEMA>")[1].split("<PLAN>")[0].strip()
                plan_part = content.split("<PLAN>")[1].strip()
                
                update['relevant_schema'] = schema_part
                update['user_requirement'] = plan_part
                
        return update


    return node
    


