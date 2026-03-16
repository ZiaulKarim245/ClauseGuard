import streamlit as st
import base64
import requests
import urllib.parse
from streamlit_pdf_viewer import pdf_viewer
from core.config import BASE_URL
from core.api_client import send_chat_message
from utils.helpers import format_response, open_citation

def render_chat_tab(current_agent_type: str) -> None:
    """
    Renders the interactive chat interface and document previewer.
    Handles the split layout for conversation and document context visualization.
    """
    show_preview = st.session_state.pdf_ref["show"] or st.session_state.pdf_ref.get("show_image", False)
    col_c, col_p = st.columns([1, 1] if show_preview else [1, 0.01])

    with col_c:
        if not st.session_state.messages:
            st.markdown("""
            <div style="height:50vh; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; color:#5f6368">
                <div style="font-size:2rem; font-weight:700; color:#202124; margin-bottom:1rem">Enterprise Legal Assistant</div>
                <p style="max-width:400px">Upload a contract or ask about case law. I can find risks, verify statutes, and research precedents.</p>
            </div>
            """, unsafe_allow_html=True)

        for m_idx, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant":
                    st.markdown(f'<div class="cg-agent-header">{current_agent_type.replace("_", " ")}</div>', unsafe_allow_html=True)
                
                content = format_response(msg["content"], msg.get("citations", []))
                st.markdown(content, unsafe_allow_html=True)

                if msg.get("citations"):
                    c_list = list({c["page"]: c for c in msg["citations"]}.values())
                    st.markdown("---")
                    
                    if current_agent_type == "rag_agent":
                        with st.popover("Sources"):
                            for idx, c in enumerate(c_list):
                                btn_label = f"Page {c['page']}"
                                if st.button(btn_label, key=f"chat_{m_idx}_{c['page']}", use_container_width=True):
                                    open_citation(c)
                                    st.rerun()
                    else:
                        cols = st.columns(min(len(c_list), 4)) 
                        for idx, c in enumerate(c_list):
                            if st.button("Source", key=f"chat_{m_idx}_v_{idx}", use_container_width=True):
                                open_citation(c)
                                st.rerun()

        if prompt := st.chat_input("Ask ClauseGuard..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner(" "):
                    res = send_chat_message(
                        query=prompt, agent_type=current_agent_type,
                        image_base64=st.session_state.vision_base64,
                        chat_history=st.session_state.messages[:-1],
                        filename=st.session_state.pdf_ref.get("filename")
                    )
                agent_name = res.get("agent", "AI")
                reply = res.get("reply", "")
                st.markdown(f'<div class="cg-agent-header">{agent_name}</div>', unsafe_allow_html=True)
                st.markdown(format_response(reply, res.get("citations", [])), unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": reply, "citations": res.get("citations", [])})
            st.rerun()

    with col_p:
        ref = st.session_state.pdf_ref
        
        if ref.get("show_image") and st.session_state.vision_base64:
            st.markdown("### Vision Detail View")
            if st.button("Close Image", use_container_width=True):
                st.session_state.pdf_ref["show_image"] = False
                st.rerun()
            img_data = base64.b64decode(st.session_state.vision_base64)
            st.image(img_data, use_container_width=True)
            st.caption("Visual Evidence inspected by Llama-4 Analyst")

        elif ref["show"] and ref["filename"]:
            st.markdown(f"### {ref['filename']} — Page {ref['page']}")
            if st.button("Close Viewer", use_container_width=True):
                st.session_state.pdf_ref["show"] = False
                st.rerun()

            enc_name = urllib.parse.quote(ref["filename"])
            enc_quote = urllib.parse.quote(ref.get("quote", ""))
            api_url = f"{BASE_URL}/download/{enc_name}?quote={enc_quote}"
            try:
                resp = requests.get(api_url)
                if resp.status_code == 200:
                    pdf_viewer(input=resp.content, width=700, pages_to_render=[ref["page"]])
                else: st.error("Sync Error")
            except: st.error("Connection Error")
