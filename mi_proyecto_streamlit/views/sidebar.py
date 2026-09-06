import streamlit as st


def render_sidebar(
    is_connected: bool,
    total_videos: int = 0,
    collections: list = None,
    selected_collection_id: int = None,
):
    """
    Sidebar BLIP: conexión, ámbito, parámetros, filtro y ayuda.
    Los controles de IA solo se muestran conectado.
    """
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
                    key="rs_active_collection",
                )
                chosen_collection_id = selected_opt["ref"]
        else:
            st.markdown(
                '<div class="rs-sidebar-note">Sin conexión. Use el botón de la pantalla principal.</div>',
                unsafe_allow_html=True,
            )
            return {
                "sample_rate": 5,
                "generation_config": {"num_beams": 1, "do_sample": False},
                "search_filter": "",
                "selected_collection_id": None,
            }

        st.markdown('<div class="rs-sidebar-section-title">ÁMBITO Y FILTRO</div>', unsafe_allow_html=True)
        search_filter = st.text_input(
            "Filtrar por ID de video",
            placeholder="Buscar ID...",
            key="rs_video_filter",
        )

        st.markdown('<div class="rs-sidebar-section-title">CONFIGURACIÓN IA (BLIP)</div>', unsafe_allow_html=True)
        sample_rate = st.slider(
            "Tasa de muestreo (segundos/frame)",
            min_value=1,
            max_value=30,
            value=5,
            step=1,
            help="Valores bajos analizan más fotogramas y consumen más CPU.",
        )

        strategy = st.selectbox(
            "Estrategia de inferencia",
            [
                "Greedy Search (Rápida, Óptima CPU)",
                "Beam Search (Mayor Calidad)",
                "Sampling (Creativa / Descriptiva)",
            ],
            key="rs_ai_strategy",
        )

        generation_config = {"num_beams": 1, "do_sample": False}
        if "Greedy Search" in strategy:
            st.markdown(
                '<div class="rs-sidebar-note">Greedy Search: descriptor más probable. Recomendada en CPU.</div>',
                unsafe_allow_html=True,
            )
        elif "Beam Search" in strategy:
            num_beams = st.slider("Ramas (num_beams)", min_value=2, max_value=8, value=3, step=1)
            generation_config = {"num_beams": num_beams, "do_sample": False}
            st.markdown(
                '<div class="rs-sidebar-note">Beam Search: más ramas, mejor texto y más CPU.</div>',
                unsafe_allow_html=True,
            )
        elif "Sampling" in strategy:
            temperature = st.slider("Temperatura", min_value=0.2, max_value=1.5, value=0.9, step=0.1)
            top_p = st.slider("Top-P", min_value=0.5, max_value=1.0, value=0.9, step=0.05)
            generation_config = {
                "do_sample": True,
                "temperature": temperature,
                "top_p": top_p,
                "num_beams": 1,
            }
            st.markdown(
                '<div class="rs-sidebar-note">Sampling: más variedad. Temperatura alta = más creatividad.</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="rs-sidebar-section-title">SISTEMA</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="rs-sidebar-note">Inferencia en CPU. Si CLIP ya está cargado en esta sesión, reinicie Streamlit ante falta de memoria.</div>',
            unsafe_allow_html=True,
        )

        return {
            "sample_rate": sample_rate,
            "generation_config": generation_config,
            "search_filter": search_filter,
            "selected_collection_id": chosen_collection_id,
        }
