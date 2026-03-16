import streamlit as st
import base64
import requests
from core.config import BASE_URL
from core.api_client import upload_document

def render_sidebar() -> str:
    """
    Renders the ClauseGuard Sidebar for agent selection and document context management.
    @return: The identifier of the selected agent mode.
    """
    with st.sidebar:
        st.title("ClauseGuard")
        st.caption("Legal Contract Intelligence")
        st.divider()

        agent_options = {
            "Contract Risk Analysis": "rag_agent",
            "Legal Precedent":        "researcher",
            "Statute Checker":        "fact_checker",
            "Vision Scan":            "vision_agent",
        }
        
        # We return the selected agent type so app.py can use it
        selected_label = st.selectbox("Active Agent Mode", list(agent_options.keys()))
        current_agent_type = agent_options[selected_label]

        st.markdown("### Context")
        if current_agent_type == "vision_agent":
            if st.session_state.vision_base64:
                 st.info("Active: Vision Context Image")
            vision_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])
            if vision_file:
                st.session_state.vision_base64 = base64.b64encode(vision_file.read()).decode("utf-8")
                st.success("Image Ready")

        elif current_agent_type == "rag_agent":
            if st.session_state.pdf_ref.get("filename"):
                st.info(f"Active: {st.session_state.pdf_ref['filename'][:20]}...")
            uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
            if uploaded_file and st.button("Ingest Document", use_container_width=True):
                with st.spinner("Processing..."):
                    res = upload_document(uploaded_file.getvalue(), uploaded_file.name, task="rag")
                    if "error" in res: st.error(res["error"])
                    else: 
                        st.success("Ready")
                        st.session_state.pdf_ref["filename"] = uploaded_file.name
        else:
            st.caption("Web search enabled. No upload required.")

        st.divider()
        if st.button("Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.vision_base64 = None
            st.session_state.analysis_result = None
            st.session_state.pdf_ref = {"filename": None, "page": 1, "show": False, "quote": "", "show_image": False}
            try:
                requests.delete(f"{BASE_URL}/reset", timeout=5)
                st.rerun()
            except:
                st.rerun()
        
        return current_agent_type
