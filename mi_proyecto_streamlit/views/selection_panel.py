import streamlit as st

def _toggle_select_all():
    """Callback que se ejecuta al cambiar el checkbox 'Seleccionar todos'.
    Lee los IDs de video directamente del session_state para evitar datos obsoletos."""
    val = st.session_state.get("select_all_vids", False)
    for vid in st.session_state.get("_current_filtered_ids", []):
        st.session_state[f"chk_vid_{vid}"] = val

def render_selection_panel(video_ids: list, search_filter: str = "", collection_name: str = None):
    """
    Renderiza el panel de selección de recursos al estilo ByteBox,
    permitiendo filtrar y elegir los videos a procesar.
    """
    if not video_ids:
        coll_msg = f" en la colección '{collection_name}'" if collection_name else " en el servidor de ByteBox"
        st.info(f"No se encontraron recursos de video disponibles{coll_msg}.")
        return [], False

    # Filtrar IDs si hay texto de búsqueda
    filtered_ids = video_ids
    if search_filter:
        filtered_ids = [vid for vid in video_ids if search_filter.lower() in str(vid).lower()]

    # Guardar los IDs filtrados en session_state para que el callback los pueda leer
    st.session_state["_current_filtered_ids"] = filtered_ids

    header_suffix = f" (Colección: {collection_name})" if collection_name else ""
    st.markdown(f"""
    <div class="rs-card">
        <div class="rs-card-header">
            <span>🎞️</span> Recursos de Video para Catalogación{header_suffix}
        </div>
        <div class="rs-card-subtitle">
            Seleccione los videos de ByteBox que desea analizar fotograma a fotograma con el modelo de IA.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Barra superior de controles de selección
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 1, 1])
    
    with ctrl_col1:
        st.checkbox(
            "☑ Seleccionar todos los videos visibles", 
            key="select_all_vids",
            on_change=_toggle_select_all
        )
        
    with ctrl_col2:
        st.caption(f"Mostrando **{len(filtered_ids)}** de **{len(video_ids)}** videos")
        
    selected_ids = []
    
    # Contenedor con scroll para selección de videos con aspecto de tarjetas DAM
    with st.container(height=260):
        # Disponer en 2 columnas para una vista limpia
        cols = st.columns(2)
        for idx, vid in enumerate(filtered_ids):
            col = cols[idx % 2]
            with col:
                is_selected = st.checkbox(
                    f"🎥 Recurso ID: **{vid}**", 
                    key=f"chk_vid_{vid}"
                )
                if is_selected:
                    selected_ids.append(vid)

    # Panel de Acción Inferior
    action_col1, action_col2 = st.columns([2, 1], gap="medium")
    
    with action_col1:
        st.markdown(f"""
        <div style="background-color: #f1f5f9; padding: 10px 15px; border-radius: 4px; border: 1px solid #cbd5e1; font-size: 0.88rem;">
            <strong>Selección actual:</strong> <span style="color: #1b75bb; font-weight: 700;">{len(selected_ids)}</span> video(s) seleccionado(s) para procesamiento.
        </div>
        """, unsafe_allow_html=True)

    with action_col2:
        # El botón de catalogación se deshabilita si no hay videos seleccionados
        boton_deshabilitado = (len(selected_ids) == 0)
        procesar = st.button(
            "🚀 Iniciar Catalogación AI", 
            type="primary", 
            use_container_width=True, 
            disabled=boton_deshabilitado
        )

    return selected_ids, procesar
