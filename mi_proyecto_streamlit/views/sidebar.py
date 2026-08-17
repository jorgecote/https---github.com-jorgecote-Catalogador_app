import streamlit as st

def render_sidebar(is_connected: bool, total_videos: int = 0):
    """
    Renderiza el panel lateral oscuro de ByteBox con controles
    de configuración de IA BLIP y filtros.
    """
    with st.sidebar:
        # 1. Estado de Conexión
        st.markdown('<div class="rs-sidebar-section-title">CONEXIÓN BYTEBOX</div>', unsafe_allow_html=True)
        if is_connected:
            st.success(f"● Conectado ({total_videos} videos disponibles)")
        else:
            st.warning("○ Sin conexión activa")

        # 2. Configuración de Inferencia y Muestreo IA
        st.markdown('<div class="rs-sidebar-section-title">CONFIGURACIÓN IA (BLIP)</div>', unsafe_allow_html=True)
        
        sample_rate = st.slider(
            "Tasa de muestreo (segundos/frame)", 
            min_value=1, 
            max_value=30, 
            value=5, 
            step=1,
            help="Menor número extrae más fotogramas para catalogar con mayor detalle."
        )

        strategy = st.selectbox(
            "Estrategia de Inferencia",
            [
                "Greedy Search (Rápida, Óptima CPU)",
                "Beam Search (Mayor Calidad)",
                "Sampling (Creativa / Descriptiva)"
            ],
            key="rs_ai_strategy"
        )

        generation_config = {"num_beams": 1, "do_sample": False}

        if "Greedy Search" in strategy:
            st.caption("ℹ️ **Greedy Search:** Genera el descriptor más probable en cada paso. Muy rápida y recomendada para CPU.")
        elif "Beam Search" in strategy:
            num_beams = st.slider("Ramas (num_beams)", min_value=2, max_value=8, value=3, step=1)
            generation_config = {"num_beams": num_beams, "do_sample": False}
            st.caption("ℹ️ **Beam Search:** Evalúa múltiples alternativas en paralelo. Más ramas mejoran la descripción pero consumen más CPU.")
        elif "Sampling" in strategy:
            temperature = st.slider("Temperatura", min_value=0.2, max_value=1.5, value=0.9, step=0.1)
            top_p = st.slider("Top-P", min_value=0.5, max_value=1.0, value=0.9, step=0.05)
            generation_config = {"do_sample": True, "temperature": temperature, "top_p": top_p, "num_beams": 1}
            st.caption("ℹ️ **Sampling:** Muestreo probabilístico. La temperatura controla la creatividad y el Top-P filtra palabras de baja probabilidad.")

        # 3. Filtro de búsqueda rápida
        st.markdown('<div class="rs-sidebar-section-title">FILTRAR RECURSOS</div>', unsafe_allow_html=True)
        search_filter = st.text_input(
            "Filtrar por ID de video", 
            placeholder="Buscar ID...", 
            label_visibility="collapsed",
            key="rs_video_filter"
        )

        # 4. Información del Sistema
        st.markdown('<div class="rs-sidebar-section-title">SISTEMA</div>', unsafe_allow_html=True)
        st.caption("⚡ Inferencia CPU optimizada con PyTorch & Transformers.")
        st.caption("🔒 Autenticación API segura mediante SHA-256.")

        return {
            "sample_rate": sample_rate,
            "generation_config": generation_config,
            "search_filter": search_filter
        }
