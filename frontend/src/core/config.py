import streamlit as st

BASE_URL = "http://127.0.0.1:8000/api/v1"

def init_session_state() -> None:
    """
    Initializes the primary session state containers for the ClauseGuard ecosystem.
    Ensures persistent storage for chat history, document context, and analysis results.
    """
    if "messages"        not in st.session_state: st.session_state.messages = []
    if "pdf_ref"         not in st.session_state: st.session_state.pdf_ref = {
        "filename": None, 
        "page": 1, 
        "show": False, 
        "quote": "", 
        "show_image": False
    }
    if "vision_base64"   not in st.session_state: st.session_state.vision_base64 = None
    if "analysis_result" not in st.session_state: st.session_state.analysis_result = None
