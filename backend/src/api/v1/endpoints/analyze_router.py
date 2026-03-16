"""
Contract Analysis Router - Orchestrates the full legal review pipeline.
"""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from langchain_community.document_loaders import PyPDFLoader
from src.core.config import settings
from src.utils.file_helpers import save_upload_file
from src.llm.agents.pipeline import clauseguard_pipeline
from langsmith import traceable

router = APIRouter()

@router.post("/analyze")
@traceable(name="Contract_Analysis_Workflow", run_type="chain")
async def analyze_contract(file: UploadFile = File(...)):
    """
    Triggers the full multi-agent orchestration for comprehensive contract risk analysis.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    save_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    try:
        # Persistence Layer: Save document for background reference
        save_upload_file(file, save_path)

        # Context Preparation: Extract raw text for initial ingestion
        loader = PyPDFLoader(save_path)
        docs = loader.load()
        contract_text = "\n".join(doc.page_content for doc in docs).strip()

        if not contract_text:
            contract_text = "[Scanned PDF — text extraction pending OCR]"

        # State Initialization: Define the shared context for the Agent Pipeline
        initial_state = {
            "contract_text": contract_text,
            "filename": file.filename,
            "flagged_clauses": "",
            "statute_validity": "",
            "case_law_delta": "",
            "risk_report": None,
        }

        # Execution Phase: Invoke the LangGraph Orchestrator
        final_state = clauseguard_pipeline.invoke(initial_state)

        return {
            "filename": file.filename,
            "flagged_clauses":  final_state.get("flagged_clauses", ""),
            "statute_validity": final_state.get("statute_validity", ""),
            "case_law_delta":   final_state.get("case_law_delta", ""),
            "risk_report":      final_state.get("risk_report", "Risk report unavailable."),
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
