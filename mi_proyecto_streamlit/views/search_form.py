import streamlit as st
from views.status_alert import render_status_alert


def render_search_form(
    collection_name: str = None,
    total_videos: int = 0,
    collection_id: int = None,
    threshold: float = 0.25,
    sample_rate: int = 5,
):
    """Formulario CLIP: ámbito, consulta y acción. Devuelve (query, buscar)."""
    scope = collection_name or "Todas las colecciones"
    st.markdown(
        f'<div class="rs-scope-chip">Ámbito: {scope} · {total_videos} video(s) · umbral {threshold:.2f} · cada {sample_rate}s</div>',
        unsafe_allow_html=True,
    )

    st.markdown("""
    <div class="rs-card">
        <div class="rs-card-header">Consulta en lenguaje natural</div>
        <div class="rs-card-subtitle">
            Describa lo que busca. CLIP puntuará fotogramas del ámbito actual.
            Los tiempos quedan listos para un EDL futuro.
        </div>
    </div>
    """, unsafe_allow_html=True)

    collection_key = collection_id if collection_id is not None else "general"
    query = st.text_area(
        "Consulta en lenguaje natural",
        placeholder="Ejemplo: una persona caminando de noche cerca de un edificio...",
        height=90,
        key=f"clip_query_text_{collection_key}",
    )

    if total_videos <= 0:
        render_status_alert(
            "warning",
            "No hay videos en el ámbito actual",
            "Cambie de colección o elimine el filtro por ID para habilitar la búsqueda.",
        )
    elif not str(query).strip():
        st.caption("Escriba una consulta para habilitar Buscar videos.")

    col1, col2 = st.columns([3, 1])
    with col2:
        buscar = st.button(
            "Buscar videos",
            type="primary",
            use_container_width=True,
            disabled=(total_videos <= 0 or not str(query).strip()),
        )

    return str(query).strip(), buscar
