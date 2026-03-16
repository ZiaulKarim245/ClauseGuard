"""
ClauseGuard Orchestration Pipeline - Multi-agent workflow for contract intelligence.
"""
from langsmith import traceable
from langgraph.graph import StateGraph, END
import os

from src.core.config import settings
from src.llm.agents.state import ContractAnalysisState
from src.llm.agents.rag_agent import answer_from_documents
from src.llm.agents.statute_agent import fact_check_with_google
from src.llm.agents.research_agent import researcher_agent_invoke
from src.llm.agents.vision_agent import vision_agent_invoke
from src.llm.agents.risk_agent import generate_risk_report
from src.llm.tools.pdf_processor import convert_pdf_to_images
from src.db.vector_store import get_vector_store
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- Node Implementation Logic ---

@traceable(name="Pipeline_Node_Vision_OCR")
def run_vision_ocr_node(state: ContractAnalysisState) -> ContractAnalysisState:
    """
    Vision Node: Performs JIT OCR for scanned documents to enable downstream analysis.
    """
    if state.get("contract_text") == "[Scanned PDF — text extraction pending OCR]":
        pdf_path = os.path.normpath(os.path.join(settings.UPLOAD_DIR, state["filename"]))
        # Limit to 4 pages for stability
        images = convert_pdf_to_images(pdf_path, max_pages=4) 
        
        ocr_docs = []
        ocr_text_parts = []
        for i, img_b64 in enumerate(images):
            ocr_result = vision_agent_invoke(
                query="OCR Request: Transcribe all legal text accurately. No commentary.",
                base64_image=img_b64
            )
            # Support both raw string (old) and dict (new) for robustness
            text = ocr_result.get("reply", "") if isinstance(ocr_result, dict) else ocr_result
            ocr_text_parts.append(f"--- [Page {i+1}] ---\n{text}")
            
            ocr_docs.append(Document(
                page_content=text,
                metadata={"source": state["filename"], "page": i}
            ))
        
        state["contract_text"] = "\n\n".join(ocr_text_parts)

        # Indexing: Populate vector store with newly extracted OCR context
        if ocr_docs:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(ocr_docs)
            vector_store = get_vector_store()
            vector_store.add_documents(chunks)
    return state

@traceable(name="Pipeline_Node_RAG")
def run_rag_node(state: ContractAnalysisState) -> ContractAnalysisState:
    """
    RAG Node: Identifies high-risk clauses via semantic retrieval and LLM analysis.
    """
    result = answer_from_documents(
        query="List all high-risk, unfair, or legally dangerous clauses in this contract. Include page references.",
        chat_history=[],
        filename=state.get("filename")
    )
    state["flagged_clauses"] = result.get("reply", "No clauses found.")
    return state

@traceable(name="Pipeline_Node_Statute_Checker")
def run_fact_check_node(state: ContractAnalysisState) -> ContractAnalysisState:
    """
    Fact Checker Node: Validates statutory references via real-time search grounding.
    """
    query = (
        f"The following contract text references various statutes and laws. "
        f"Verify which statutes are currently active, amended, or repealed:\n\n"
        f"{state['contract_text'][:3000]}"
    )
    result = fact_check_with_google(query)
    state["statute_validity"] = result
    return state

@traceable(name="Pipeline_Node_Precedent_Researcher")
def run_research_node(state: ContractAnalysisState) -> ContractAnalysisState:
    """
    Research Node: Investigates judicial precedents and FTC guidelines via Tavily.
    """
    inputs = {
        "messages": [(
            "user",
            f"Find recent case law and judicial precedents relevant to the following "
            f"contract clauses:\n\n{state['flagged_clauses'][:2000]}"
        )]
    }
    result = researcher_agent_invoke(inputs)
    content = result["messages"][-1].content
    if isinstance(content, list):
        content = content[0].get("text", "")
    state["case_law_delta"] = content
    return state

@traceable(name="Pipeline_Node_Unified_Risk_Engine")
def run_risk_engine_node(state: ContractAnalysisState) -> ContractAnalysisState:
    """
    Risk Engine Node: Synthesizes expert findings into a comprehensive executive report.
    """
    report = generate_risk_report(
        flagged_clauses=state.get("flagged_clauses", "N/A"),
        statute_validity=state.get("statute_validity", "N/A"),
        case_law_delta=state.get("case_law_delta", "N/A")
    )
    state["risk_report"] = report
    return state

# --- Pipeline Orchestration ---

def build_pipeline():
    """
    Constructs and compiles the LangGraph state machine.
    """
    graph = StateGraph(ContractAnalysisState)

    graph.add_node("vision_ocr",  run_vision_ocr_node)
    graph.add_node("rag",         run_rag_node)
    graph.add_node("fact_check",  run_fact_check_node)
    graph.add_node("research",    run_research_node)
    graph.add_node("risk_engine", run_risk_engine_node)

    graph.set_entry_point("vision_ocr")
    graph.add_edge("vision_ocr", "rag")
    graph.add_edge("rag",        "fact_check")
    graph.add_edge("fact_check", "research")
    graph.add_edge("research",   "risk_engine")
    graph.add_edge("risk_engine", END)

    return graph.compile()

# Singleton Pipeline Instance
clauseguard_pipeline = build_pipeline()
