import requests
from typing import Optional, List
from core.config import BASE_URL

def send_chat_message(query: str, agent_type: str, image_base64: Optional[str] = None, chat_history: Optional[list] = None, filename: Optional[str] = None) -> dict:
    """
    Dispatches a user query to the backend orchestration router.
    Supports multimodal inputs (base64 images) and contextual conversation history.
    """
    payload = {"query": query, "agent_type": agent_type}
    if image_base64:
        payload["image_base64"] = image_base64

    if chat_history:
        payload["chat_history"] = chat_history
    
    if filename:
        payload["filename"] = filename
        
    try:
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = response.text if 'response' in locals() and response else str(e)
        return {"agent": "System", "reply": f"Backend Crash Details: {error_msg}", "citations": []}

def upload_document(file_bytes: bytes, filename: str, task: str) -> dict:
    """
    Uploads document assets to the ingestion server.
    MIME type detection is strictly enforced for PDF and imagery.
    """
    mime_type = "application/pdf" if filename.lower().endswith(".pdf") else "image/jpeg"
    
    files = {"file": (filename, file_bytes, mime_type)}
    data = {"task": task}
    
    try:
        response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = response.text if 'response' in locals() and response else str(e)
        return {"error": f"Upload Failed: {error_msg}"}

def analyze_contract(file_bytes: bytes, filename: str) -> dict:
    """
    Invokes the high-latency Automated Legal Risk Pipeline.
    Triggers the sequential coordination of all ClauseGuard specialized agents.
    """
    files = {"file": (filename, file_bytes, "application/pdf")}
    try:
        response = requests.post(f"{BASE_URL}/analyze", files=files, timeout=300)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = response.text if 'response' in locals() and response else str(e)
        return {"error": f"Analysis Failed: {error_msg}"}
