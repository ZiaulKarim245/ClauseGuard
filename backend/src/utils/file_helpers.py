"""
File Helpers - Specialized utilities for file encryption and storage management.
"""
import os
import base64
import shutil
from fastapi import UploadFile

def encode_image(image_path: str) -> str:
    """
    Encodes a local image file to a base64 string for multimodal LLM processing.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Source image missing: {image_path}")
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def save_upload_file(upload_file: UploadFile, destination_path: str) -> None:
    """
    Efficiently streams a FastAPI UploadFile to a specified persistent storage path.
    """
    try:
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        with open(destination_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    except Exception as e:
        raise IOError(f"Filesystem Persistence Failure: {str(e)}")
