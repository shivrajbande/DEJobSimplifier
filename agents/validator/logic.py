from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agents.retriever.tools import semantic_search_tool
from agents.retriever.prompt import system_prompt

def sql_validator_agent(llm):
    '''
        This function will create the classifier agent.
        1. Bind the schema_search tool to the node.
        2. Create a scheme_retriver agent(node) using the prompt and llm_with_tools.
        3. Return the agent/node which will be used by langgraph.
    '''
    # 1. Bind the tools to the llm.
    llm_with_tools = llm.bind_tools(semantic_search_tool)

    # 2. Create a prompt for the classifier agent.
    prompt = ChatPromptTemplate.from_messages([
        ("system",system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])

    # 3. Create a classofoer agent(node) using the prompt and llm_with_tools.
    def node(state):

        chain = prompt | llm_with_tools
        response =  chain.invoke({'messages':state['messages']})
        return {'messages': [response]}

    # 4. Return the classifier agent/node which will be used by langgraph.
    return node


    


