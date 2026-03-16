"""
Chat Router - Handles conversational interactions with various legal agents.
"""
from fastapi import APIRouter, HTTPException
import traceback
from src.services.chat_service import ChatService
from src.api.v1.schemas.chat import ChatRequest

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Primary chat entry point. Routes queries to specialized agents based on user selection.
    """
    try:
        # Service Invocation: Process the chat request with session history and optional context
        result = await ChatService.process_chat(
            query=request.query,
            agent_type=request.agent_type,
            image_base64=request.image_base64,
            chat_history=request.chat_history,
            filename=request.filename
        )
        return result
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = str(e)
        
        # Resiliency: Handle common provider-level rate limits with professional feedback
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return {
                "agent": "System", 
                "reply": "**API Rate Limit Exceeded:** We are receiving too many requests. Please wait 1 minute and try again.", 
                "citations": []
            }
            
        # Logging: Capture critical failures for backend observability
        print("\n --- CRITICAL CRASH REPORT --- ")
        traceback.print_exc() 
        print(" ----------------------------- \n")
        raise HTTPException(status_code=500, detail=str(e))
