"""
Text Cleaning Utilities - Sanitizes and normalizes extracted legal text for consistency.
"""
import re

def clean_legal_text(text: str) -> str:
    """
    Normalizes legal text by consolidating fragmented whitespace and newlines.
    Crucial for maintaining structural integrity after PDF processing.
    """
    if not text:
        return ""
    
    # Normalization: Collapse multi-line fragments and redundant spacing
    text = re.sub(r"\n+", " ", text)
    return re.sub(r"\s{2,}", " ", text).strip()
