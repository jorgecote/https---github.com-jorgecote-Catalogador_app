import streamlit as st


def render_search_sidebar(
    is_connected: bool,
    total_videos: int = 0,
    collections: list = None,
    selected_collection_id: int = None,
):
    """Sidebar CLIP: conexión, ámbito, parámetros, filtro y ayuda."""
    with st.sidebar:
        st.markdown('<div class="rs-sidebar-section-title">CONEXIÓN BYTEBOX</div>', unsafe_allow_html=True)
        chosen_collection_id = None
        if is_connected:
            st.markdown(
                f'<div class="rs-sidebar-note">Conectado · {total_videos} videos en ámbito</div>',
                unsafe_allow_html=True,
            )
            if collections:
                options = [{"ref": None, "label": "Todas las colecciones / General"}]
                for col in collections:
                    count_suffix = f" ({col['count']} ítems)" if col.get("count") is not None else ""
                    options.append({
                        "ref": col["ref"],
                        "label": f"[{col['ref']}] {col['name']}{count_suffix}",
                    })
                default_idx = 0
                if selected_collection_id is not None:
                    for idx, opt in enumerate(options):
                        if opt["ref"] == selected_collection_id:
                            default_idx = idx
                            break
                selected_opt = st.selectbox(
                    "Colección activa",
                    options=options,
                    index=default_idx,
                    format_func=lambda x: x["label"],
                    key="clip_active_collection",
                )
                chosen_collection_id = selected_opt["ref"]
        else:
            st.markdown(
                '<div class="rs-sidebar-note">Sin conexión. Vuelva a catalogación BLIP para autenticar.</div>',
                unsafe_allow_html=True,
            )
            go_back = st.button("Volver a catalogación BLIP", use_container_width=True, key="clip_go_back")
            return {
                "sample_rate": 5,
                "threshold": 0.25,
                "search_filter": "",
                "selected_collection_id": None,
                "go_back": go_back,
            }

        st.markdown('<div class="rs-sidebar-section-title">ÁMBITO Y FILTRO</div>', unsafe_allow_html=True)
        collection_key = selected_collection_id if selected_collection_id is not None else "general"
        search_filter = st.text_input(
            "Filtrar por ID de video",
            placeholder="Limitar por ID (opcional)...",
            key=f"clip_video_filter_{collection_key}",
        )

        st.markdown('<div class="rs-sidebar-section-title">CONFIGURACIÓN CLIP</div>', unsafe_allow_html=True)
        sample_rate = st.slider(
            "Tasa de muestreo (segundos/frame)",
            min_value=1,
            max_value=30,
            value=5,
            step=1,
            key="clip_sample_rate",
            help="Valores bajos extraen más fotogramas y tardan más en CPU.",
        )
        threshold = st.slider(
            "Umbral de similitud",
            min_value=0.15,
            max_value=0.40,
            value=0.25,
            step=0.01,
            key="clip_threshold",
            help="Fotogramas con similitud CLIP mayor o igual al umbral son coincidencia.",
        )
        st.markdown(
            '<div class="rs-sidebar-note">Valores típicos útiles: 0.22 – 0.32. Umbral alto = menos resultados, más precisos.</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="rs-sidebar-section-title">NAVEGACIÓN</div>', unsafe_allow_html=True)
        go_back = st.button(
            "Volver a catalogación BLIP",
            use_container_width=True,
            key="clip_go_back",
        )

        st.markdown('<div class="rs-sidebar-section-title">SISTEMA</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="rs-sidebar-note">CLIP ViT-B/32 en CPU. Si BLIP ya está en esta sesión, ambos modelos pueden quedar en RAM.</div>',
            unsafe_allow_html=True,
        )

        return {
            "sample_rate": sample_rate,
            "threshold": threshold,
            "search_filter": search_filter,
            "selected_collection_id": chosen_collection_id,
            "go_back": go_back,
        }
