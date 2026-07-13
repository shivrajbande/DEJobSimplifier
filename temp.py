# Create a retriever from your vector database
from utils.embeddings import vector_db
retriever = vector_db.as_retriever(search_kwargs={"k": 2})

# Test Query
query = "Which actor made the highest salary in a movie?"
retrieved_docs = retriever.invoke(query)

print("\n--- Top Relevant Tables Retrieved ---")
for idx, doc in enumerate(retrieved_docs):
    print(f"\nResult {idx + 1} (Table: {doc.metadata['table_name']}):")
    print(doc.page_content[:300] + "...\n")  # Prints the beginning of the text block