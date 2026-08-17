import streamlit as st

def render_main_page(base_url: str = "") -> bool:
    """
    VISTA: Dibuja la página principal y el botón de conexión con estilo ByteBox.
    No maneja lógica interna, devuelve True si se presiona el botón de conexión.
    """
    # 1. Hero Banner de ByteBox
    st.markdown("""
    <div class="rs-hero-banner">
        <div class="rs-hero-pill">
            <h2>La mejor forma de organizar sus materiales digitales</h2>
            <p>Catalogador Automatizado de Recursos Multimedia con Inteligencia Artificial (BLIP-base).</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Tarjeta de Conexión estilo Panel de Control ByteBox
    st.markdown("""
    <div class="rs-card">
        <div class="rs-card-header">
            <span>🔌</span> Conexión con Repositorio MAM ByteBox
        </div>
        <div class="rs-card-subtitle">
            Haga clic en el botón inferior para autenticar contra la API de ByteBox y cargar los recursos de video disponibles para catalogación.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        boton_conectar = st.button("🔗 Iniciar Conexión con ByteBox", type="primary", use_container_width=True)

    return boton_conectar