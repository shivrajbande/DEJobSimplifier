from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from utils.embedding_text import all_table_texts

# 1. Initialize the embedding model
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Initialize the Chroma database instance
vector_db = Chroma(
    collection_name="sql_schema",
    embedding_function=embedding_model,
    persist_directory="./embedding_memory"
)

# 3. Convert your text descriptions into LangChain Documents with Table Metadata
documents_to_embed = []

# Assuming all_table_texts is a dictionary like: 
# {"movies": movies_table_text, "persons": persons_table_text, ...}
for table_name, table_text in all_table_texts.items():
    doc = Document(
        page_content=table_text.strip(),
        metadata={"table_name": table_name}  # Useful for downstream filtering
    )
    documents_to_embed.append(doc)

# 4. Generate embeddings and persist them to your local directory only if empty
try:
    existing_count = vector_db._collection.count()
except Exception:
    existing_count = 0

if existing_count == 0:
    print(f"Embedding {len(documents_to_embed)} table schemas into Chroma DB...")
    vector_db.add_documents(documents_to_embed)
    print("Embeddings successfully created and stored locally in './embedding_memory'!")
else:
    print(f"Chroma DB already contains {existing_count} documents. Skipping duplicate insertion.")