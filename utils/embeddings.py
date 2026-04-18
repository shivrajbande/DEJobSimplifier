from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from utils.embedding_text import all_table_texts

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_db = Chroma(
    collection_name="sql_schema",
    embedding_function=embedding_model,
    persist_directory="./embedding_memory"
)


