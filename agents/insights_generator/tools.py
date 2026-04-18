from utils.embeddings import vector_db
from langchain_core.tools import tool

@tool
def semantic_search_tool(query):
    """
    This fun do sematic serach of the user query and return top 5 (K=5) information
    """
    results = vector_db.similarity_search(query=query,k=5)
    print(f"results are ${results}")
    
    docs = []
    for doc in results:
        print(f"found match:{doc.page_content}")
        docs.append(doc.page_content)
    
    return docs