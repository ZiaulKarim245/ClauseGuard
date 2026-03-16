import streamlit as st
import re

def open_citation(citation_data: dict) -> None:
    """
    Synchronizes the global UI reference state based on selected citation metadata.
    Enables side-by-side document visualization and quote highlights.
    """
    if citation_data.get("type") == "image":
        st.session_state.pdf_ref.update({
            "show_image": True,
            "show": False,
            "filename": "Image Analyst View"
        })
    else:
        st.session_state.pdf_ref.update({
            "page":     citation_data["page"],
            "filename": citation_data.get("source", st.session_state.pdf_ref.get("filename")),
            "quote":    citation_data.get("quote", ""),
            "show":     True,
            "show_image": False
        })

def format_response(text: str, citations: list) -> str:
    """
    Sanitizes and stylizes AI-generated responses.
    Converts raw markdown citation markers into stylized UI badges for consistency.
    """
    styled = text
    for c in citations:
        p = str(c["page"])
        pill = f'<span class="cg-cite">Page {p}</span>'
        styled = re.sub(rf'\[🔗 Page {p}\]', pill, styled)
    styled = re.sub(r'\[🔗 Page (\d+)\]', r'<span class="cg-cite">Page \1</span>', styled)
    return styled
