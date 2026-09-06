import streamlit as st
from views.status_alert import render_status_alert


def _toggle_select_all():
    val = st.session_state.get("select_all_vids", False)
    for vid in st.session_state.get("_current_filtered_ids", []):
        st.session_state[f"chk_vid_{vid}"] = val


def render_selection_panel(video_ids: list, search_filter: str = "", collection_name: str = None):
    """
    Flujo BLIP: ámbito → selección de videos → acción.
    Devuelve selected_ids, procesar, ir_a_clip.
    """
    scope = collection_name or "Todas las colecciones"
    st.markdown(f'<div class="rs-scope-chip">Ámbito: {scope}</div>', unsafe_allow_html=True)

    if not video_ids:
        render_status_alert(
            "warning",
            "No hay videos en este ámbito",
            "Cambie de colección en el panel izquierdo o verifique la conexión con ByteBox.",
        )
        return [], False, False

    filtered_ids = video_ids
    if search_filter:
        filtered_ids = [vid for vid in video_ids if search_filter.lower() in str(vid).lower()]
    st.session_state["_current_filtered_ids"] = filtered_ids

    if not filtered_ids:
        render_status_alert(
            "warning",
            "El filtro no dejó videos visibles",
            "Elimine o cambie el filtro por ID en el panel izquierdo.",
        )
        return [], False, False

    st.markdown(f"""
    <div class="rs-card">
        <div class="rs-card-header">1. Seleccione los videos a catalogar</div>
        <div class="rs-card-subtitle">
            Marque los recursos y pulse Catalogar. La búsqueda CLIP permanece disponible como acción secundaria.
        </div>
    </div>
    """, unsafe_allow_html=True)

    ctrl_col1, ctrl_col2 = st.columns([3, 1])
    with ctrl_col1:
        st.checkbox(
            "Seleccionar todos los videos visibles",
            key="select_all_vids",
            on_change=_toggle_select_all,
        )
    with ctrl_col2:
        st.caption(f"{len(filtered_ids)} de {len(video_ids)} videos")

    selected_ids = []
    with st.container(height=280):
        cols = st.columns(2)
        for idx, vid in enumerate(filtered_ids):
            with cols[idx % 2]:
                if st.checkbox(f"Recurso ID {vid}", key=f"chk_vid_{vid}"):
                    selected_ids.append(vid)

    st.markdown("""
    <div class="rs-card">
        <div class="rs-card-header">2. Ejecutar acción</div>
        <div class="rs-card-subtitle">Catalogación BLIP analiza los videos seleccionados. CLIP busca en el ámbito actual.</div>
    </div>
    """, unsafe_allow_html=True)

    action_col1, action_col2, action_col3 = st.columns([2, 1.2, 1.2], gap="medium")
    with action_col1:
        st.markdown(
            f'<div class="rs-scope-chip">Selección: {len(selected_ids)} video(s)</div>',
            unsafe_allow_html=True,
        )
        if len(selected_ids) == 0:
            st.caption("Seleccione al menos un video para habilitar Catalogar.")
    with action_col2:
        procesar = st.button(
            "Catalogar con BLIP",
            type="primary",
            use_container_width=True,
            disabled=(len(selected_ids) == 0),
        )
    with action_col3:
        ir_a_clip = st.button(
            "Ir a búsqueda CLIP",
            use_container_width=True,
        )

    return selected_ids, procesar, ir_a_clip
