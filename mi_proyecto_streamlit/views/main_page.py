import streamlit as st
from views.status_alert import render_status_alert


def render_main_page(base_url: str = "", has_secrets: bool = True) -> bool:
    """Entrada de conexión: estado de credenciales y modos disponibles."""
    st.markdown("""
    <div class="rs-hero-banner">
        <div class="rs-hero-pill">
            <h2>Organice sus materiales de video con IA</h2>
            <p>Conéctese a ByteBox para catalogar fotogramas con BLIP o buscar escenas en lenguaje natural con CLIP.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not has_secrets:
        render_status_alert(
            "error",
            "Faltan credenciales de ByteBox",
            "Cree mi_proyecto_streamlit/.streamlit/secrets.toml con base_url, user y private_key.",
        )
    elif base_url:
        render_status_alert(
            "info",
            "Listo para autenticar",
            "La conexión usa las credenciales locales. No se muestran claves en pantalla.",
        )

    st.markdown("""
    <div class="rs-card">
        <div class="rs-card-header">Conexión con el repositorio MAM</div>
        <div class="rs-card-subtitle">
            Tras conectar podrá: 1) seleccionar una colección, 2) catalogar videos con BLIP
            o 3) buscar fotogramas con CLIP. Ambos modos reutilizan la misma sesión.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        return st.button(
            "Iniciar conexión con ByteBox",
            type="primary",
            use_container_width=True,
            disabled=not has_secrets,
        )
