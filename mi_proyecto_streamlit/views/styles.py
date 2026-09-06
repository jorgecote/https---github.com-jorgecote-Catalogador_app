import streamlit as st


def apply_bytebox_styles():
    """
    Identidad visual ByteBox / ResourceSpace: tokens, contraste WCAG AA
    y estados de controles/avisos sobre fondo claro y sidebar oscuro.
    """
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');

    :root {
        --rs-blue: #1b75bb;
        --rs-blue-dark: #145d94;
        --rs-navy: #0e446d;
        --rs-violet: #3b2a59;
        --rs-sidebar: #33373b;
        --rs-sidebar-deep: #26292c;
        --rs-bg: #f8f9fa;
        --rs-text: #1a202c;
        --rs-muted: #4a5568;
        --rs-border: #cbd5e0;
        --rs-white: #ffffff;
        --rs-error-bg: #7f1d1d;
        --rs-warn-bg: #78350f;
        --rs-ok-bg: #14532d;
        --rs-info-bg: #1e3a5f;
    }

    html, body, [class*="css"] {
        font-family: 'Open Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 4rem !important;
        padding-left: 1.6rem !important;
        padding-right: 1.6rem !important;
        max-width: 100% !important;
    }

    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* Header */
    .rs-header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: var(--rs-white);
        border-bottom: 1px solid #e2e8f0;
        padding: 10px 20px;
        margin: -1rem -1.6rem 0.8rem -1.6rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        gap: 16px;
        flex-wrap: wrap;
    }

    .rs-logo-link {
        display: flex;
        align-items: center;
        gap: 12px;
        text-decoration: none;
        color: inherit;
    }

    .rs-logo-link:hover { opacity: 0.92; text-decoration: none; }

    .rs-logo-title {
        font-weight: 700;
        font-size: 1.3rem;
        color: var(--rs-violet);
        line-height: 1.1;
        letter-spacing: -0.4px;
    }

    .rs-logo-sub {
        font-size: 0.72rem;
        color: var(--rs-muted);
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
    }

    .rs-header-meta {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }

    .rs-badge-system {
        background: #edf2f7;
        color: #2d3748;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid var(--rs-border);
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    .rs-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    .rs-dot-on { background: #15803d; }
    .rs-dot-off { background: #b45309; }

    /* Breadcrumbs + subnav */
    .rs-breadcrumbs {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.86rem;
        color: var(--rs-muted);
        margin-bottom: 0.7rem;
        flex-wrap: wrap;
    }

    .rs-breadcrumbs .active { color: var(--rs-text); font-weight: 700; }
    .rs-breadcrumbs .rs-crumb-link { color: var(--rs-blue); font-weight: 600; }

    .rs-subnav {
        display: flex;
        gap: 8px;
        margin-bottom: 1rem;
        padding-bottom: 10px;
        border-bottom: 1px solid #e2e8f0;
    }

    /* Stepper */
    .rs-stepper {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin: 0 0 16px 0;
    }

    .rs-step {
        display: flex;
        align-items: center;
        gap: 8px;
        background: #edf2f7;
        color: #2d3748;
        border: 1px solid var(--rs-border);
        border-radius: 999px;
        padding: 5px 12px;
        font-size: 0.78rem;
        font-weight: 700;
    }

    .rs-step-num {
        width: 18px; height: 18px;
        border-radius: 50%;
        background: #4a5568;
        color: #fff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
    }

    .rs-step-active {
        background: #e8f3fb;
        border-color: var(--rs-blue);
        color: var(--rs-navy);
    }

    .rs-step-active .rs-step-num { background: var(--rs-blue); }

    .rs-step-done {
        background: #e8f5ee;
        border-color: #15803d;
        color: #14532d;
    }

    .rs-step-done .rs-step-num { background: #15803d; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--rs-sidebar) !important;
        color: #f7fafc !important;
        border-right: 1px solid #222629;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] small {
        color: #edf2f7 !important;
    }

    .rs-sidebar-section-title {
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        color: #e2e8f0 !important;
        margin-top: 1.1rem !important;
        margin-bottom: 0.4rem !important;
        padding-bottom: 4px;
        border-bottom: 1px solid #4a5568;
    }

    .rs-sidebar-note {
        font-size: 0.8rem;
        line-height: 1.4;
        color: #e2e8f0;
        background: #2b2f33;
        border: 1px solid #4a5056;
        border-radius: 4px;
        padding: 8px 10px;
        margin: 6px 0 10px 0;
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] .stSelectbox > div,
    [data-testid="stSidebar"] .stNumberInput input {
        background-color: #ffffff !important;
        color: #1a202c !important;
        border-radius: 3px !important;
        border: 1px solid #94a3b8 !important;
    }

    /* Área principal: Streamlit reutiliza secondaryBackgroundColor (#33373b) en
       textareas e inputs. Forzar fondo claro y texto oscuro para que se lea. */
    [data-testid="stMain"] textarea,
    [data-testid="stMain"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stTextInput"] input,
    section.main textarea,
    section.main input {
        background-color: #ffffff !important;
        color: #1a202c !important;
        caret-color: #1a202c !important;
        border: 1px solid #94a3b8 !important;
        -webkit-text-fill-color: #1a202c !important;
    }

    [data-testid="stMain"] textarea::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {
        color: #4a5568 !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #4a5568 !important;
    }

    [data-testid="stSidebar"] [data-testid="stAlert"] {
        color: #ffffff !important;
        border: 1px solid transparent !important;
    }

    /* Buttons */
    button[kind="primary"], .stButton > button[type="primary"] {
        background: linear-gradient(135deg, #1b75bb 0%, #145d94 100%) !important;
        color: #ffffff !important;
        border: 1px solid #0e446d !important;
        border-radius: 4px !important;
        font-weight: 700 !important;
        padding: 0.45rem 1.1rem !important;
        box-shadow: 0 2px 6px rgba(27, 117, 187, 0.25) !important;
    }

    button[kind="primary"]:not(:disabled):hover {
        background: linear-gradient(135deg, #145d94 0%, #0e446d 100%) !important;
        color: #ffffff !important;
    }

    button[kind="primary"]:focus-visible,
    .stButton > button:focus-visible {
        outline: 3px solid #fbbf24 !important;
        outline-offset: 2px !important;
    }

    button:disabled, .stButton > button:disabled {
        background: #cbd5e1 !important;
        color: #1e293b !important;
        border-color: #94a3b8 !important;
        cursor: not-allowed !important;
        opacity: 1 !important;
        box-shadow: none !important;
    }

    button[kind="secondary"], .stButton > button:not([type="primary"]) {
        background-color: #f8fafc !important;
        color: #1a202c !important;
        border: 1px solid #94a3b8 !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
    }

    /* Cards */
    .rs-card {
        background: var(--rs-white);
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    }

    .rs-card-header {
        font-size: 1.08rem;
        font-weight: 700;
        color: var(--rs-text);
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .rs-card-subtitle {
        font-size: 0.86rem;
        color: var(--rs-muted);
        margin-bottom: 12px;
        line-height: 1.45;
    }

    .rs-hero-banner {
        background: linear-gradient(135deg, #3b2a59 0%, #0e446d 48%, #1b75bb 100%);
        border-radius: 8px;
        padding: 28px 32px;
        color: #ffffff;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(14, 68, 109, 0.25);
    }

    .rs-hero-pill {
        background: rgba(0, 0, 0, 0.35);
        padding: 16px 22px;
        border-radius: 8px;
        max-width: 540px;
        border: 1px solid rgba(255,255,255,0.18);
    }

    .rs-hero-pill h2 {
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0;
        color: #ffffff !important;
    }

    .rs-hero-pill p {
        font-size: 0.88rem;
        margin: 8px 0 0 0;
        color: #e2e8f0 !important;
        line-height: 1.45;
    }

    /* Alerts */
    .rs-alert {
        border-radius: 6px;
        padding: 12px 14px;
        margin: 10px 0 16px 0;
        color: #ffffff;
        border: 1px solid transparent;
    }

    .rs-alert-title { font-weight: 700; font-size: 0.95rem; margin-bottom: 4px; }
    .rs-alert-body { font-size: 0.86rem; line-height: 1.4; color: #f8fafc; }
    .rs-alert-info { background: var(--rs-info-bg); border-color: #93c5fd; }
    .rs-alert-success { background: var(--rs-ok-bg); border-color: #86efac; }
    .rs-alert-warning { background: var(--rs-warn-bg); border-color: #fcd34d; }
    .rs-alert-error { background: var(--rs-error-bg); border-color: #fca5a5; }

    /* Processing */
    .rs-process-bar {
        background: var(--rs-white);
        border: 1px solid #e2e8f0;
        border-left: 4px solid var(--rs-blue);
        border-radius: 6px;
        padding: 14px 16px;
        margin: 12px 0 16px 0;
    }

    .rs-process-title { font-weight: 700; color: var(--rs-navy); }

    /* Tray */
    .rs-collection-tray {
        background-color: var(--rs-sidebar-deep);
        border: 1px solid #1a1c1e;
        border-radius: 6px;
        padding: 14px 16px 8px 16px;
        color: #e2e8f0;
        margin-top: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        position: sticky;
        bottom: 0;
        z-index: 4;
    }

    .rs-tray-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #3a3e43;
        padding-bottom: 8px;
        margin-bottom: 12px;
        gap: 10px;
        flex-wrap: wrap;
    }

    .rs-tray-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #e2e8f0;
    }

    .rs-tray-empty {
        background-color: #2b2f33;
        border: 1px dashed #718096;
        border-radius: 4px;
        padding: 22px;
        text-align: center;
        color: #e2e8f0;
        font-size: 0.85rem;
        margin-bottom: 8px;
    }

    .bb-tray-card {
        background-color: #ffffff;
        border: 1px solid #94a3b8;
        border-radius: 4px;
        padding: 8px;
        margin-bottom: 12px;
    }

    .bb-tray-card-match {
        border: 2px solid #15803d;
        box-shadow: 0 2px 8px rgba(21, 128, 61, 0.25);
    }

    .bb-tray-score-match {
        background-color: #14532d;
        color: #ffffff;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 3px;
    }

    .bb-tray-badge {
        background-color: var(--rs-blue);
        color: #ffffff;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 3px;
    }

    .bb-tray-desc {
        color: #1a202c;
        font-size: 0.74rem;
        line-height: 1.25;
        height: 3.2rem;
        overflow-y: auto;
        margin-top: 6px;
        font-weight: 600;
    }

    .rs-meta-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
        margin-top: 10px;
    }

    .rs-meta-table th {
        background: #e2e8f0;
        color: #1e293b;
        font-weight: 700;
        padding: 8px 12px;
        text-align: left;
        border-bottom: 2px solid #94a3b8;
    }

    .rs-meta-table td {
        padding: 8px 12px;
        border-bottom: 1px solid #e2e8f0;
        color: #1a202c;
    }

    .rs-time-badge, .rs-score-badge {
        color: white;
        padding: 2px 7px;
        border-radius: 3px;
        font-weight: 700;
    }

    .rs-time-badge { background: var(--rs-blue); }
    .rs-score-badge { background: var(--rs-navy); }

    .rs-scope-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #e8f3fb;
        color: var(--rs-navy);
        border: 1px solid #93c5fd;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .stExpander {
        border: 1px solid #cbd5e0 !important;
        background: #ffffff !important;
    }

    [data-testid="stMain"] ::-webkit-scrollbar { width: 8px; height: 8px; }
    [data-testid="stMain"] ::-webkit-scrollbar-track { background: #e2e8f0; }
    [data-testid="stMain"] ::-webkit-scrollbar-thumb { background: #94a3b8; border-radius: 4px; }

    [data-testid="stSidebar"] ::-webkit-scrollbar-track { background: #2d3748; }
    [data-testid="stSidebar"] ::-webkit-scrollbar-thumb { background: #718096; border-radius: 4px; }

    .rs-collection-tray ::-webkit-scrollbar-track { background: #1a1c1e; }
    .rs-collection-tray ::-webkit-scrollbar-thumb { background: #718096; }
    </style>
    """, unsafe_allow_html=True)
