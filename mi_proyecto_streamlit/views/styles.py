import streamlit as st

def apply_bytebox_styles():
    """
    Inyecta la hoja de estilos CSS personalizada que recrea la identidad visual,
    paleta de colores, tipografía y componentes de ByteBox DAM.
    """
    st.markdown("""
    <style>
    /* Google Fonts para tipografía limpia */
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Open Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }

    /* Reducir padding superior por defecto de Streamlit */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }

    /* =========================================================================
       1. TOP NAVBAR / HEADER (Estilo ResourceSpace)
       ========================================================================= */
    .rs-header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: #ffffff;
        border-bottom: 1px solid #e2e8f0;
        padding: 10px 20px;
        margin: -1.2rem -2rem 1.5rem -2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    .rs-logo-link {
        display: flex;
        align-items: center;
        gap: 12px;
        text-decoration: none;
        color: inherit;
    }

    .rs-logo-link:hover {
        opacity: 0.9;
        text-decoration: none;
    }

    .rs-logo-title {
        font-weight: 700;
        font-size: 1.35rem;
        color: #3b2a59;
        line-height: 1.1;
        letter-spacing: -0.5px;
    }

    .rs-logo-sub {
        font-size: 0.72rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
    }

    .rs-badge-system {
        background: #edf2f7;
        color: #4a5568;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid #cbd5e0;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    /* =========================================================================
       2. BREADCRUMBS (Migas de Pan)
       ========================================================================= */
    .rs-breadcrumbs {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.88rem;
        color: #718096;
        margin-bottom: 1rem;
    }

    .rs-breadcrumbs a {
        color: #1b75bb;
        text-decoration: none;
    }

    .rs-breadcrumbs a:hover {
        text-decoration: underline;
    }

    .rs-breadcrumbs .active {
        color: #2d3748;
        font-weight: 600;
    }

    /* =========================================================================
       3. SIDEBAR OSCURO (Panel de Búsqueda / Configuración de ResourceSpace)
       ========================================================================= */
    [data-testid="stSidebar"] {
        background-color: #33373b !important;
        color: #f7fafc !important;
        border-right: 1px solid #222629;
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #e2e8f0 !important;
    }

    .rs-sidebar-section-title {
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        color: #cbd5e0 !important;
        margin-top: 1.2rem !important;
        margin-bottom: 0.4rem !important;
        padding-bottom: 4px;
        border-bottom: 1px solid #4a5568;
    }

    /* Inputs en sidebar */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] .stSelectbox > div,
    [data-testid="stSidebar"] .stNumberInput input {
        background-color: #ffffff !important;
        color: #1a202c !important;
        border-radius: 3px !important;
        border: 1px solid #4a5568 !important;
    }

    /* Sliders y Controles en sidebar */
    [data-testid="stSidebar"] .stSlider label {
        font-size: 0.82rem;
    }

    /* =========================================================================
       4. BOTONES ESTILO BYTEBOX
       ========================================================================= */
    button[kind="primary"], .stButton > button[type="primary"] {
        background-color: #1b75bb !important;
        color: #ffffff !important;
        border: 1px solid #145d94 !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        padding: 0.45rem 1.2rem !important;
        font-size: 0.92rem !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
    }

    button[kind="primary"]:not(:disabled), .stButton > button[type="primary"]:not(:disabled),
    button[kind="primary"]:not(:disabled):hover, .stButton > button[type="primary"]:not(:disabled):hover,
    button[kind="primary"]:not(:disabled):focus, .stButton > button[type="primary"]:not(:disabled):focus,
    button[kind="primary"]:not(:disabled):active, .stButton > button[type="primary"]:not(:disabled):active {
        color: #ffffff !important;
    }

    button[kind="primary"]:not(:disabled), .stButton > button[type="primary"]:not(:disabled) {
        background: linear-gradient(135deg, #1b75bb 0%, #145d94 100%) !important;
        border-color: #0e446d !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 6px rgba(27, 117, 187, 0.2) !important;
    }

    button[kind="primary"]:not(:disabled):hover, .stButton > button[type="primary"]:not(:disabled):hover {
        background: linear-gradient(135deg, #145d94 0%, #0e446d 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(27, 117, 187, 0.35) !important;
    }

    /* Botones deshabilitados (Streamlit) */
    button:disabled, button[disabled], .stButton > button:disabled, .stButton > button[disabled] {
        background: #e2e8f0 !important;
        color: #94a3b8 !important;
        border-color: #cbd5e1 !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: none !important;
        opacity: 0.7 !important;
    }

    button[kind="secondary"], .stButton > button:not([type="primary"]) {
        background-color: #f8fafc !important;
        color: #2d3748 !important;
        border: 1px solid #cbd5e0 !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }

    button[kind="secondary"]:not(:disabled):hover, .stButton > button:not([type="primary"]):not(:disabled):hover {
        background-color: #edf2f7 !important;
        border-color: #a0aec0 !important;
    }

    /* =========================================================================
       5. TARJETAS Y CONTENEDORES (Estilo DAM Clean UI)
       ========================================================================= */
    .rs-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    .rs-card-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .rs-card-subtitle {
        font-size: 0.85rem;
        color: #718096;
        margin-bottom: 16px;
    }

    /* Hero Banner de ResourceSpace */
    .rs-hero-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%);
        border-radius: 8px;
        padding: 30px 40px;
        color: #ffffff;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }

    .rs-hero-pill {
        background: rgba(0, 0, 0, 0.45);
        backdrop-filter: blur(8px);
        padding: 16px 24px;
        border-radius: 8px;
        max-width: 480px;
        border: 1px solid rgba(255,255,255,0.15);
    }

    .rs-hero-pill h2 {
        font-size: 1.3rem;
        font-weight: 700;
        margin: 0;
        color: #ffffff !important;
    }

    .rs-hero-pill p {
        font-size: 0.85rem;
        margin: 6px 0 0 0;
        color: #e2e8f0 !important;
    }

    /* =========================================================================
       6. BANDEJA DE COLECCIÓN INFERIOR (Bottom Collection Tray)
       ========================================================================= */
    .rs-collection-tray {
        background-color: #26292c;
        border: 1px solid #1a1c1e;
        border-radius: 6px;
        padding: 14px 18px;
        color: #e2e8f0;
        margin-top: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }

    .rs-tray-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #3a3e43;
        padding-bottom: 8px;
        margin-bottom: 12px;
    }

    .rs-tray-title {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #a0aec0;
    }

    .rs-tray-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
        gap: 12px;
        max-height: 320px;
        overflow-y: auto;
        padding: 4px;
    }

    .rs-frame-card {
        background: #33373b;
        border: 1px solid #4a5056;
        border-radius: 4px;
        overflow: hidden;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }

    .rs-frame-card:hover {
        transform: translateY(-2px);
        border-color: #1b75bb;
    }

    .rs-frame-info {
        padding: 8px;
        font-size: 0.75rem;
    }

    .rs-frame-badge {
        background: #1b75bb;
        color: white;
        padding: 2px 6px;
        border-radius: 3px;
        font-weight: 700;
        font-size: 0.7rem;
        display: inline-block;
        margin-bottom: 4px;
    }

    .rs-frame-desc {
        color: #cbd5e0;
        line-height: 1.25;
        font-size: 0.74rem;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
    }

    /* Tabla de metadatos de resultados */
    .rs-meta-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
        margin-top: 10px;
    }

    .rs-meta-table th {
        background: #f1f5f9;
        color: #475569;
        font-weight: 600;
        padding: 8px 12px;
        text-align: left;
        border-bottom: 2px solid #cbd5e1;
    }

    .rs-meta-table td {
        padding: 8px 12px;
        border-bottom: 1px solid #e2e8f0;
        color: #1e293b;
    }

    .rs-meta-table tr:hover {
        background: #f8fafc;
    }

    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #2d3748;
    }
    ::-webkit-scrollbar-thumb {
        background: #4a5568;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #718096;
    }
    </style>
    """, unsafe_allow_html=True)
