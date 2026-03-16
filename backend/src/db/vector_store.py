"""
Vector Database Interface - Manages local ChromaDB storage and semantic retrieval logic.
"""
import os
import logging 
from langchain_chroma import Chroma 
from langchain_huggingface import HuggingFaceEmbeddings
from langsmith import traceable
from src.core.config import settings

# --- Initialize Subsystem Logging ---
logging.getLogger("transformers").setLevel(logging.ERROR)

# --- Configuration Constants ---
DB_DIR = os.path.join(settings.DATA_DIR, "clauseguard_db")

def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Initializes the embedding engine using a high-performance transformer model.
    Model: sentence-transformers/multi-qa-MiniLM-L6-cos-v1 (Targeted for Q&A tasks)
    """
    return HuggingFaceEmbeddings(model_name="sentence-transformers/multi-qa-MiniLM-L6-cos-v1")

def get_vector_store() -> Chroma:
    """
    Connects to the persistent ChromaDB local storage layer.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    return Chroma(
        persist_directory=DB_DIR,
        embedding_function=get_embedding_model(),
        collection_name="legal_docs"
    )

@traceable(name="Tool_Vector_Database_Search", run_type="retriever")
def semantic_search(query: str, k: int = 15):
    """
    Performs a semantic similarity search across the indexed legal knowledge base.
    """
    store = get_vector_store()
    return store.similarity_search(query, k=k)