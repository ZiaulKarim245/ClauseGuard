"""
PDF Processing Tools - Handles document-to-image conversions for multimodal analysis.
"""
import base64
import fitz  # PyMuPDF
from langsmith import traceable

@traceable(name="Tool_PDF_to_Image_Converter", run_type="tool")
def convert_pdf_to_images(pdf_path: str, max_pages: int = 5) -> list[str]:
    """
    Converts PDF pages into base64-encoded JPEG strings for Vision/OCR processing.
    Includes high-resolution scaling (2.0x) to optimize legal text readability.
    """
    base64_images = []
    try:
        doc = fitz.open(pdf_path)
        # Limit processing for performance and stability
        for i in range(min(len(doc), max_pages)):
            page = doc.load_page(i)
            # Scaling: 2.0x zoom provides significant clarity for fine legal print
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
            img_data = pix.tobytes("jpeg")
            base64_images.append(base64.b64encode(img_data).decode('utf-8'))
        doc.close()
    except Exception as e:
        print(f"Subsystem Error (PDF Component): {str(e)}")
    return base64_images