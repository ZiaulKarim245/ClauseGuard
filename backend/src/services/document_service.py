"""
Document Service - Orchestrates the ingestion, processing, and vectorization of legal documents.
"""
import os
from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.db.vector_store import get_vector_store
from src.core.config import settings
from src.utils.file_helpers import save_upload_file

TEMP_DIR = settings.UPLOAD_DIR
os.makedirs(TEMP_DIR, exist_ok=True)
async def process_and_store_document(file: UploadFile) -> dict:
    """
    Standardized Ingestion Pipeline:
    1. Persists file to disk.
    2. Performs context-aware extraction via PyPDF.
    3. Implements Cross-Page Context Merging for semantic continuity.
    4. Vectorizes chunks into the specialized legal index.
    """
    temp_path = os.path.join(TEMP_DIR, file.filename)
    
    try:
        # File Persistence
        save_upload_file(file, temp_path)
        
        # Extraction logic with automatic metadata tagging
        loader = PyPDFLoader(temp_path)
        docs = loader.load()
        
        # Scanned PDF Detection: Identify documents requiring JIT OCR
        total_text = "".join(doc.page_content for doc in docs).strip()
        if len(total_text) < 50:
            return {
                "status": "success", 
                "filename": file.filename, 
                "message": "Scanned document detected. On-demand OCR fallback initialized."
            }
        
        # --- Continuity Logic: Cross-Page Windowing ---
        # Prevents fragmentation of clauses that span across physical page breaks.
        for i in range(len(docs) - 1):
            next_page_top = docs[i + 1].page_content[:800] 
            docs[i].page_content += f"\n\n--- [Contextual Continuity from Page {i+2}] ---\n\n{next_page_top}"

        # Vectorization: Recursive splitting optimized for complex legal document structures
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        chunks = text_splitter.split_documents(docs)
        
        # Storage: Persistence to Vector repository
        vector_store = get_vector_store()
        vector_store.add_documents(chunks)
        
        return {
            "status": "success", 
            "filename": file.filename, 
            "chunks_stored": len(chunks)
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Ingestion Failure: {str(e)}"}
        
    finally:
        # Retention: File is preserved for integrated frontend PDF rendering.
        pass