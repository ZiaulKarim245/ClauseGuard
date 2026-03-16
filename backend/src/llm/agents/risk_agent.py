"""
Risk Engine Agent - Synthesizes expert agent outputs into a unified risk report.
"""
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langsmith import traceable
from src.core.config import settings

# --- Engine Configuration ---
_risk_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=settings.GROQ_API_KEY,
    temperature=0,
    max_retries=2,
)

RISK_ENGINE_PROMPT = PromptTemplate.from_template("""
You are the ClauseGuard Risk Engine. You receive the outputs from several
specialist legal AI agents and must synthesize a single, authoritative
Contract Risk Report.

=== FLAGGED CLAUSES (from RAG Agent) ===
{flagged_clauses}

=== STATUTE VALIDITY (from Fact Checker) ===
{statute_validity}

=== CASE LAW DELTA (from Research Agent) ===
{case_law_delta}

---
Your task:
1. Produce an **Overall Risk Rating**: HIGH / MEDIUM / LOW with a 2-sentence justification.
2. List the top dangerous clauses with a risk label: 🔴 HIGH | 🟡 MEDIUM | 🟢 LOW.
3. Highlight any outdated statutes and their replacements.
4. Summarise the most relevant recent case law and how it affects enforceability.
5. Provide concise suggested redlines for the highest-risk items.

Format your output using clear markdown headers.
""")

risk_engine_chain = RISK_ENGINE_PROMPT | _risk_llm

@traceable(name="Risk_Engine_Agent")
def generate_risk_report(flagged_clauses: str, statute_validity: str, case_law_delta: str) -> str:
    """
    Synthesizes diverse agent findings into an executive-level legal risk assessment.
    """
    response = risk_engine_chain.invoke({
        "flagged_clauses":  flagged_clauses or "N/A",
        "statute_validity": statute_validity or "N/A",
        "case_law_delta":   case_law_delta or "N/A",
    })
    return response.content
