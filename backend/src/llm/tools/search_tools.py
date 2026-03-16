"""
Search Tools - Specialized legal search interfaces for judicial research.
"""
from langchain_tavily import TavilySearch  
from src.core.config import settings

def get_internet_search_tool() -> TavilySearch:
    """
    Initializes a high-precision Tavily Search engine tuned for legal precedence research.
    """
    search_tool = TavilySearch(
        tavily_api_key=settings.TAVILY_API_KEY,  
        max_results=5,               
        search_depth="advanced", 
        topic="general",   
        include_answer=True,
        include_raw_content=False       
    )
    
    # Tool Metadata: Defined for ReAct agent understanding
    search_tool.name = "tavily_legal_search"
    search_tool.description = (
        "Advanced search for case law, judicial precedents, FTC rulings, and modern statutes. "
        "Provides exact source URLs. Append these URLs to validate factual claims."    
    )
    
    return search_tool
