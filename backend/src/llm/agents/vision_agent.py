"""
Vision Agent - Multimodal legal document analysis using Llama-4 Vision models.
"""
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langsmith import traceable
from src.core.config import settings

@traceable(name="Tool_Vision_Payload_Encoder", run_type="tool")
def prepare_vision_payload(query: str, base64_image: str) -> HumanMessage:
    """
    Constructs a multimodal message payload with interleaved text and image data.
    """
    return HumanMessage(
        content=[
            {
                "type": "text", 
                "text": (
                    "You are an expert legal analyst. Analyze this document image and "
                    "answer the user's query in clean Markdown format. "
                    f"Query: {query}"
                )
            },
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    )

@traceable(name="Vision_Analysis_Agent")
def vision_agent_invoke(query: str, base64_image: str) -> dict:
    """
    Orchestrates OCR and visual intelligence for scanned documents or image-based legal queries.
    """
    llm = ChatGroq(
        model="meta-llama/llama-4-scout-17b-16e-instruct", 
        api_key=settings.GROQ_API_KEY,
        temperature=0.1
    )
    
    # Execution: Prepare payload and invoke multimodal model
    message = prepare_vision_payload(query, base64_image)
    response = llm.invoke([message])
    
    return {
        "reply": response.content,
        "citations": [{
            "source": "Visual_Context_Analysis",
            "page": 1,
            "type": "image"
        }]
    }
