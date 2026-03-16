import streamlit as st
from core.api_client import analyze_contract

def render_analyze_tab() -> None:
    """
    Renders the Full Automated Contract Analysis report view.
    Orchestrates the sequential agent pipeline and displays the unified risk matrix.
    """
    st.markdown("## Automated Contract Review")
    st.caption("Standardized pipeline: Vision → RAG → Fact Check → Research → Synthesis")
    
    a_file = st.file_uploader("Contract PDF for Analysis", type=["pdf"])
    if a_file and st.button("Generate Risk Report", type="primary", use_container_width=True):
        with st.spinner("Orchestrating Agents..."):
            res = analyze_contract(a_file.getvalue(), a_file.name)
            if "error" in res: st.error(res["error"])
            else:
                st.session_state.analysis_result = res
                st.session_state.pdf_ref["filename"] = a_file.name

    if st.session_state.analysis_result:
        res = st.session_state.analysis_result
        st.markdown("### Risk Report Summary")
        st.info(res.get("risk_report", "No report"))
        
        c1, c2, c3 = st.columns(3)
        with c1:
            with st.expander("RAG Flags"): st.markdown(res.get("flagged_clauses", ""))
        with c2:
            with st.expander("Statutes"): st.markdown(res.get("statute_validity", ""))
        with c3:
            with st.expander("Case Law"): st.markdown(res.get("case_law_delta", ""))
