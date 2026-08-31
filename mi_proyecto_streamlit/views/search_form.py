import streamlit as st


def render_search_form(
    collection_name: str = None,
    total_videos: int = 0,
    collection_id: int = None,
):
    """
    Formulario de consulta en lenguaje natural.
    Devuelve (query, buscar).
    """
    header_suffix = f" (Colección: {collection_name})" if collection_name else ""
    st.markdown(f"""
    <div class="rs-card">
        <div class="rs-card-header">
            <span>🔍</span> Búsqueda semántica de video (CLIP){header_suffix}
        </div>
        <div class="rs-card-subtitle">
            Describa en lenguaje natural lo que busca. Se analizarán fotogramas de
            <strong>{total_videos}</strong> video(s) del ámbito actual. Los tiempos de coincidencia
            quedan listos para una futura generación de EDL.
        </div>
    </div>
    """, unsafe_allow_html=True)

    collection_key = collection_id if collection_id is not None else "general"
    query = st.text_area(
        "Consulta en lenguaje natural",
        placeholder="Ejemplo: una persona caminando de noche cerca de un edificio...",
        height=90,
        key=f"clip_query_text_{collection_key}"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        if total_videos <= 0:
            st.warning(
                "No hay videos en el ámbito actual. Cambie de colección o "
                "elimine el filtro por ID."
            )
        else:
            st.caption(
                "El modelo CLIP se carga en CPU solo al pulsar Buscar "
                "(no al abrir esta pantalla)."
            )
    with col2:
        buscar = st.button(
            "🔎 Buscar videos",
            type="primary",
            use_container_width=True,
            disabled=(total_videos <= 0 or not str(query).strip())
        )

    return str(query).strip(), buscar
