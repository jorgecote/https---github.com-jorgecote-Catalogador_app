import streamlit as st


def render_status_alert(kind: str, title: str, message: str = ""):
    """Aviso persistente de alto contraste. kind: info | success | warning | error."""
    allowed = {"info", "success", "warning", "error"}
    variant = kind if kind in allowed else "info"
    extra = f'<div class="rs-alert-body">{message}</div>' if message else ""
    st.markdown(f"""
    <div class="rs-alert rs-alert-{variant}" role="status">
        <div class="rs-alert-title">{title}</div>
        {extra}
    </div>
    """, unsafe_allow_html=True)
