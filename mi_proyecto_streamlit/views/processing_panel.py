import streamlit as st


def render_processing_header(title: str, subtitle: str = ""):
    extra = f'<div class="rs-card-subtitle" style="margin:6px 0 0 0;">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div class="rs-process-bar">
        <div class="rs-process-title">{title}</div>
        {extra}
    </div>
    """, unsafe_allow_html=True)


def render_job_progress(current: int, total: int, label: str = ""):
    if total <= 0:
        return
    ratio = min(1.0, max(0.0, current / total))
    st.progress(ratio, text=label or f"Recurso {current} de {total}")


def render_meta_table(placeholder, headers: list, rows_html: str):
    ths = "".join(f"<th>{h}</th>" for h in headers)
    placeholder.markdown(f"""
    <table class="rs-meta-table">
        <thead><tr>{ths}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)


def render_summary_banner(title: str, message: str):
    st.markdown(f"""
    <div class="rs-alert rs-alert-success" role="status">
        <div class="rs-alert-title">{title}</div>
        <div class="rs-alert-body">{message}</div>
    </div>
    """, unsafe_allow_html=True)
