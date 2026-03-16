"""
RAG Agent - Specialized legal assistant for document-based retrieval and risk analysis.
"""
import os
from typing import Optional, List
import re
import time 
import numpy as np
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langsmith import traceable
from src.core.config import settings
from src.core.exceptions import QuotaExhaustedError
from src.db.vector_store import get_vector_store, semantic_search
from sentence_transformers import CrossEncoder
from src.utils.text_cleaner import clean_legal_text

# --- Shared Utilities & Models ---
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)

@traceable(name="Tool_Text_Cleaner", run_type="tool")
def clean_text(text: str) -> str:
    """Standardized legal text cleaning utility."""
    return clean_legal_text(text)

@traceable(name="Tool_Cross_Encoder_Reranker", run_type="tool")
def rerank_documents(query: str, documents: list) -> list:
    """
    Reranks document chunks using a Cross-Encoder for high-accuracy relevance scoring.
    """
    pairs = [[query, doc.page_content] for doc in documents]
    scores = reranker.predict(pairs)
    ranked_indices = np.argsort(scores)[::-1]
    
    top_docs = [documents[i] for i in ranked_indices[:6]] 
    top_scores = [scores[i] for i in ranked_indices[:6]]
    return top_docs, top_scores

# --- LLM Interface Configuration ---
llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    api_key=settings.GROQ_API_KEY, 
    temperature=0
)

# Prompts & Chains
CONDENSE_PROMPT = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question. 
Chat History: {chat_history}
Follow Up Question: {question}
Standalone:"""
condense_chain = PromptTemplate.from_template(CONDENSE_PROMPT) | llm

RAG_PROMPT = """You are an expert Legal AI Assistant reviewing contracts. Use ONLY the provided context to answer. 
CRITICAL RULE: For every single paragraph, risk item, or clause you extract, you MUST add exactly ONE inline citation at the very end of the paragraph/block, formatted exactly like this: [🔗 Page X].

Context: {context}
Question: {question}"""
rag_chain = PromptTemplate.from_template(RAG_PROMPT) | llm

def safe_invoke(chain, payload):
    """Executes a chain with exponential backoff on rate limits."""
    try:
        return chain.invoke(payload).content
    except Exception as e:
        if QuotaExhaustedError.is_quota_error(e):
            time.sleep(30)
            return chain.invoke(payload).content
        raise e

# --- Core Logic ---

@traceable(name="OCR_Fallback", run_type="tool")
def fallback_ocr(filename: str) -> List:
    """
    Performs on-demand OCR (Lazy Ingestion) when a document is identified as scanned/empty.
    """
    from src.llm.agents.vision_agent import vision_agent_invoke
    from src.llm.tools.pdf_processor import convert_pdf_to_images
    from src.db.vector_store import get_vector_store
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    pdf_path = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.exists(pdf_path): return []
    
    images = convert_pdf_to_images(pdf_path, max_pages=4)
    ocr_docs = []
    for i, img_b64 in enumerate(images):
        res = vision_agent_invoke("OCR Request: Transcribe all legal text accurately.", img_b64)
        text = res.get("reply", "") if isinstance(res, dict) else res
        ocr_docs.append(Document(page_content=text, metadata={"source": filename, "page": i}))
    
    if ocr_docs:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(ocr_docs)
        get_vector_store().add_documents(chunks)
    return ocr_docs

@traceable(name="RAG_Analysis_Agent")
def answer_from_documents(query: str, chat_history: Optional[list] = None, filename: Optional[str] = None) -> dict:
    """
    Orchestrates the RAG lifecycle: Retrieval, Reranking, Context Synthesis, and Citations.
    """
    try:
        search_query = query
        if chat_history and len(chat_history) > 0:
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history[-4:]])
            search_query = safe_invoke(condense_chain, {"chat_history": history_str, "question": query})
            
        # Retrieval Phase
        initial_results = semantic_search(search_query, k=15)
        
        # JIT Fallback logic for scanned documents
        is_empty = not initial_results or not any(doc.page_content.strip() for doc in initial_results)
        if is_empty and filename:
            ocr_docs = fallback_ocr(filename)
            if ocr_docs:
                initial_results = semantic_search(search_query, k=15)

        if not initial_results:
            return {"agent": "RAG", "reply": "No documents found. Please ensure the file contains extractable text or use the Vision analyst.", "citations": []}

        # Reranking Phase
        top_docs, top_scores = rerank_documents(search_query, initial_results)

        # Synthesis Phase
        context_parts = []
        for doc in top_docs:
            p_num = int(doc.metadata.get("page", 0)) + 1
            context_parts.append(f"--- [Source: Page {p_num}] ---\n{clean_text(doc.page_content)}")
        clean_context = "\n\n".join(context_parts)
        
        reply_text = safe_invoke(rag_chain, {"context": clean_context, "question": search_query})

        if "I cannot find the answer" in reply_text:
            return {"agent": "RAG", "reply": reply_text, "citations": []}

        # Post-Processing: Citation validation and Confidence scoring
        cited_pages = {int(m.group(1)) for m in re.finditer(r'\[🔗 Page (\d+)\]', reply_text)}
        valid_citations = []
        seen_pages = set()
        
        for doc, raw_score in zip(top_docs, top_scores):
            page_num = int(doc.metadata.get("page", 0)) + 1
            if page_num in cited_pages and page_num not in seen_pages:
                # Bayesian-style confidence mapping for Cross-Encoder log-odds
                scaled_score = (float(raw_score) + 3.0) / 2.5
                confidence = round(100 / (1 + np.exp(-scaled_score)), 1)
                valid_citations.append({
                    "source": os.path.basename(str(doc.metadata.get("source", "Document.pdf"))),
                    "page": page_num, 
                    "quote": doc.page_content,
                    "confidence": confidence
                })
                seen_pages.add(page_num)

        return {"agent": "ClauseGuard RAG", "reply": reply_text, "citations": valid_citations}

    except Exception as e:
        return {"agent": "System", "reply": f"Process Interrupted: {str(e)}", "citations": []}