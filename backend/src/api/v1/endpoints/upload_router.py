"""
Upload Router - Manages document ingestion, retrieval, and environment resets.
"""
import os, shutil, urllib.parse, traceback
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import Optional 
from src.core.config import settings
from src.utils.file_helpers import encode_image, save_upload_file
from src.llm.agents.vision_agent import vision_agent_invoke
from src.services.document_service import process_and_store_document
from src.db.vector_store import get_vector_store
from src.api.v1.schemas.upload import UploadTask

router = APIRouter()
UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/download/{filename}")
async def get_pdf(filename: str, quote: Optional[str] = None):
    """
    Serves uploaded PDF documents for the frontend viewer.
    """
    clean_name = urllib.parse.unquote(filename)
    file_path = os.path.normpath(os.path.join(UPLOAD_DIR, clean_name))
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing.")
    return FileResponse(file_path, media_type="application/pdf")

@router.post("/upload")
async def handle_document_upload(
    task: UploadTask = Form(...),
    file: UploadFile = File(...),
    query: str = Form("What is in this document?")
):
    """
    Ingests documents into the system. Supports RAG (vector indexing) or direct OCR analysis.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        # File Storage: Persist the raw file to the local upload directory
        save_upload_file(file, file_path)
            
        if task == UploadTask.RAG_INDEX:
            # RAG Branch: Process PDF for Vector Database storage
            if not file.filename.lower().endswith('.pdf'):
                raise ValueError("RAG requires PDFs.")
            file.file.seek(0)
            result = await process_and_store_document(file)
            return {"agent": "RAG Database", "result": result}
            
        elif task == UploadTask.VISION_OCR:
            # OCR Branch: Dynamic analysis of images/scans via Vision Agent
            base64_str = encode_image(file_path)
            analysis = vision_agent_invoke(query=query, base64_image=base64_str)
            
            # Post-processing: Image analysis files are temporary and cleaned up immediately
            if os.path.exists(file_path): os.remove(file_path) 
            return {"agent": "OCR Analyst", "result": analysis}
            
    except Exception as e:
        traceback.print_exc()
        if os.path.exists(file_path): os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reset")
async def reset_system():
    """
    Wipes the Vector Database and clears all persistent file storage. Used for environment cleanup.
    """
    try:
        # Step 1: Purge Vector Store Collection
        try:
            vector_store = get_vector_store()
            vector_store.delete_collection()
        except Exception as db_err:
            print(f"Warning: Could not wipe vector DB: {db_err}")
            
        # Step 2: Clear Disk Storage (Uploads)
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.normpath(os.path.join(UPLOAD_DIR, filename))
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as file_err:
                    print(f"Warning: Could not delete {file_path}: {file_err}")
                
        return {"status": "success", "message": "System purged successfully."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Reset aborted: {str(e)}")