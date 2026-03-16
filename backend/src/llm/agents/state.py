"""
Pipeline State Definition - Shared context for the LangGraph orchestration.
"""
from typing import TypedDict, Optional

class ContractAnalysisState(TypedDict):
    """
    Represents the shared memory and contextual state across the agent pipeline.
    """
    # Context Ingestion
    contract_text: str          # Raw text context (extracted via PDFLoader or Vision OCR)
    filename: str               # Canonical filename for citation mapping

    # Expert Agent Findings
    flagged_clauses: str        # Contextual risk clauses identified via RAG
    statute_validity: str       # Real-time search-grounded status of cited laws
    case_law_delta: str         # Research findings on judicial precedents

    # Executive Synthesis
    risk_report: Optional[str]  # Unified multi-agent intelligence report
