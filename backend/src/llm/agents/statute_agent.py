"""
Statute Agent - Validates legal statutory references via real-time Google Search grounding.
"""
from google import genai
from google.genai import types
from langsmith import traceable
from src.core.config import settings

@traceable(name="Statute_Checker_Agent")
def fact_check_with_google(query: str) -> str:
    """
    Leverages Gemini 2.0 Flash with Search Grounding to verify the current standing of laws.
    Identifies whether statutes are active, repealed, or superseded.
    """
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    
    config = types.GenerateContentConfig(
        tools=[{"google_search": {}}],
        temperature=0,
        system_instruction="You are an elite Legal Statute Checker. Find authoritative government databases to verify if the mentioned statutes, laws, or guidelines are currently active, repealed, or superseded."
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=query,
            config=config,
        )
        
        answer = response.text or "No verifiable information found."
        
        # Grounding Metadata: Extract verified web sources for transparency
        metadata = getattr(response.candidates[0], "grounding_metadata", None)
        if metadata and getattr(metadata, "grounding_chunks", None):
            answer += "\n\n**Verified Sources:**\n"
            for chunk in metadata.grounding_chunks:
                if getattr(chunk, "web", None):
                    answer += f"- [{chunk.web.title}]({chunk.web.uri})\n"
        return answer
        
    except Exception as e:
        return f"Legal Statute Verification Error: {str(e)}"