"""
ClauseGuard Frontend - Entry point for the Streamlit-based Legal AI interface.
"""
import streamlit as st
import os

from core.config import init_session_state
from modules.sidebar import render_sidebar
from modules.chat import render_chat_tab
from modules.analyze import render_analyze_tab

# Initialize global application state
init_session_state()

# --- Page Orchestration ---
st.set_page_config(
    page_title="ClauseGuard Legal AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Design System Implementation ---
style_path = os.path.join(os.path.dirname(__file__), "styles", "main.css")
with open(style_path, "r") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Sidebar: Selection and context management
current_agent_type = render_sidebar()

# Main Interface: Tabbed orchestration
tab_chat, tab_analyze = st.tabs(["Chat Interface", "Automated Report"])

with tab_chat:
    render_chat_tab(current_agent_type)

with tab_analyze:
    render_analyze_tab()