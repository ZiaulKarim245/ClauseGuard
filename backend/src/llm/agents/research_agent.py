"""
Research Agent - Investigates judicial precedents and legal case law via search tools.
"""
from langsmith import traceable
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from src.core.config import settings
from src.llm.tools.search_tools import get_internet_search_tool

# --- Model Configuration ---
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=settings.GROQ_API_KEY,
    temperature=0.1,  # Balanced for diversity in search synthesis
    max_retries=2 
)

# --- Agent Definition ---
tools = [get_internet_search_tool()]

SYSTEM_PROMPT = """
You are a professional Legal Precedent Researcher.

Mandatory Workflow:
1. ALWAYS use the `tavily_legal_search` tool to find recent case law, FTC rulings, and modern judicial precedent.
2. Provide deep analysis: explain how the recent legal decisions impact the enforceability of standard contract clauses today.
3. Structure your response with professional markdown headers (e.g., Executive Summary, Recent Precedents, Clause Impact).
4. STRICT CITATION RULE: You MUST append reference links to every factual legal claim you make using inline markdown: [Source Name](URL). Only use exact URLs provided by the search tool. Do not hallucinate links.
"""

# ReAct Orchestrator for tool-use cycles
researcher_internal = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT,
    name="Researcher_Internal_Logic"
)

@traceable(name="Legal_Precedent_Researcher_Agent")
def researcher_agent_invoke(inputs: dict) -> dict:
    """
    Orchestrates search-based judicial research for a given set of contract clauses.
    """
    return researcher_internal.invoke(inputs)