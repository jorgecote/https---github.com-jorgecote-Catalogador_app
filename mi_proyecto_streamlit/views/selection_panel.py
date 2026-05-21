import streamlit as st

def render_selection_panel(video_ids: list):
    """
    Renderiza el panel donde el usuario selecciona qué videos procesar
    y configura los parámetros del modelo.
    """
    st.markdown("---")
    st.markdown("## ⚙️ Configuración de Procesamiento")
    
    if not video_ids:
        st.info("No se encontraron videos disponibles para procesar.")
        return [], 0, False
        
    col1, col2 = st.columns([2, 1], gap="large")
    
    with col1:
        st.markdown("### 🎞️ Selecciona los Videos")
        st.markdown("Elige qué recursos deseas enviar al modelo de IA para generar descriptores.")
        
        # Checkbox "Seleccionar Todos"
        select_all = st.checkbox("Seleccionar todos los videos", value=False)
        
        selected_ids = []
        # Crear un contenedor con scroll si hay muchos videos
        with st.container(height=300):
            for vid in video_ids:
                # Si 'select_all' es True, los checkboxes se marcan automáticamente
                is_selected = st.checkbox(f"🎬 Video ID: {vid}", value=select_all, key=f"chk_{vid}")
                if is_selected:
                    selected_ids.append(vid)
                    
    with col2:
        st.markdown("### ⏱️ Tasa de Muestreo")
        st.markdown("Indica cada cuántos segundos se extraerá un fotograma para analizar.")
        
        # Input numérico para la tasa de muestreo
        sample_rate = st.number_input(
            "Segundos por fotograma", 
            min_value=1, 
            max_value=60, 
            value=5,
            step=1,
            help="Un valor más bajo genera más fotogramas (mayor precisión, pero más lento)."
        )
        
        # --- NUEVO: Configuración Avanzada BLIP ---
        generation_config = {"num_beams": 1, "do_sample": False}
        with st.expander("🧠 Configuración Avanzada de IA"):
            st.markdown("<small>Opciones para el generador de texto BLIP</small>", unsafe_allow_html=True)
            strategy = st.selectbox(
                "Estrategia de Inferencia", 
                [
                    "Greedy Search (Rápida, Única)", 
                    "Beam Search (Por Ramas, Precisa)", 
                    "Sampling (Creativa, Aleatoria)"
                ]
            )
            
            if "Beam Search" in strategy:
                num_beams = st.slider("Número de Ramas (num_beams)", min_value=2, max_value=10, value=3, step=1, help="Más ramas mejoran la calidad pero reducen la velocidad.")
                generation_config = {"num_beams": num_beams, "do_sample": False}
            elif "Sampling" in strategy:
                temperature = st.slider("Temperatura", min_value=0.1, max_value=2.0, value=1.0, step=0.1, help="Valores altos generan más creatividad, pero pueden ser incoherentes.")
                top_p = st.slider("Top-P", min_value=0.1, max_value=1.0, value=0.9, step=0.1)
                generation_config = {"do_sample": True, "temperature": temperature, "top_p": top_p, "num_beams": 1}
            else:
                # Greedy por defecto
                generation_config = {"num_beams": 1, "do_sample": False}
        # ------------------------------------------
        
        st.markdown("---")
        st.metric(label="Videos Seleccionados", value=len(selected_ids))
        
        procesar = st.button("🚀 Iniciar Procesamiento", use_container_width=True, type="primary")
        
    if procesar:
        if len(selected_ids) == 0:
            st.warning("⚠️ Debes seleccionar al menos un video para continuar.")
            return [], sample_rate, generation_config, False
            
    return selected_ids, sample_rate, generation_config, procesar
