from utils.embeddings import vector_db
from langchain_core.tools import tool

@tool
def semantic_search_tool(query: str):
    """
    Performs semantic search for schema info.
    Returns a single string of unique table definitions.
    """
    results = vector_db.similarity_search(query=query, k=4) 
    
    unique_tables_list = []
    seen = set()

    for doc in results:
        # Better heuristic: find the actual "Table Name:" line
        content = doc.page_content
        table_name_line = [l for l in content.split('\n') if "Table Name:" in l]
        table_id = table_name_line[0] if table_name_line else content[:50]

        if table_id not in seen:
            unique_tables_list.append(content)
            seen.add(table_id)
            print(f"✅ Added unique match: {table_id}")

    # Return the list joined as a string to keep the message block clean
    return "\n\n".join(unique_tables_list)