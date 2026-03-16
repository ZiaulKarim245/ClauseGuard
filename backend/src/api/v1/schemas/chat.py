"""
Chat API Schemas - Defines the request structure for conversational legal analysis.
"""
from pydantic import BaseModel
from enum import Enum
from typing import Optional, List

class AgentType(str, Enum):
    """Supported specialist agent personas."""
    RESEACHER = "researcher"      # Legal Precedent Researcher
    FACT_CHECKER = "fact_checker" # Statute & Fact Validator
    RAG_AGENT = "rag_agent"       # Contextual Contract Risk Analyst
    VISION_AGENT = "vision_agent" # Multi-modal OCR & Document Analyst

class ChatRequest(BaseModel):
    """
    Schema for incoming chat messages.
    Supports multi-modal context (images) and session consistency (chat history).
    """
    query: str
    agent_type: AgentType
    image_base64: Optional[str] = None
    chat_history: Optional[List] = []
    filename: Optional[str] = None
