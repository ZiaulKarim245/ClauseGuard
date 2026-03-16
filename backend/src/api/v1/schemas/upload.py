"""
Upload API Schemas - Defines the types of document ingestion tasks.
"""
from enum import Enum

class UploadTask(str, Enum):
    """Enumeration of specialized document processing tasks."""
    VISION_OCR = "ocr"  # Direct Vision/OCR analysis of a single image/page
    RAG_INDEX = "rag"   # Multi-page PDF indexing for vector search
