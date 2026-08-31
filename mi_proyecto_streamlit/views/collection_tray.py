import streamlit as st
# PIL se importa de forma lazy dentro de la función únicamente cuando hay frames que mostrar


FRAMES_PER_PAGE = 36


def render_collection_tray(
    analyzed_frames: list,
    active_video_id: str = None,
    title: str = "Colección de Fotogramas Analizados",
    empty_message: str = None,
):
    """
    Renderiza la bandeja inferior de colección (Bottom Tray) al estilo ByteBox,
    mostrando las miniaturas de los fotogramas analizados junto a sus marcas de tiempo y descripciones.
    
    analyzed_frames es una lista de diccionarios:
    [{'video_id': 123, 'timestamp': '00:05', 'caption': '...', 'image': PIL.Image}, ...]
    """
    total_items = len(analyzed_frames)
    if empty_message is None:
        empty_message = (
            "🎞️ Aquí aparecerán las miniaturas de los fotogramas y sus "
            "descriptores a medida que la IA analice los videos seleccionados."
        )
    
    st.markdown("""
    <div style="margin-top: 30px;"></div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown(f"""
        <div class="rs-collection-tray">
            <div class="rs-tray-header">
                <div>
                    <span class="rs-tray-title">{title}:</span>
                    <strong style="color: #ffffff; margin-left: 8px;">
                        {f'Video ID: {active_video_id}' if active_video_id else 'General'}
                    </strong>
                    <span style="color: #94a3b8; margin-left: 12px; font-size: 0.8rem;">
                        ({total_items} Ítem{'s' if total_items != 1 else ''})
                    </span>
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8;">
                    Vista en miniatura de metadatos AI
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not analyzed_frames:
            st.markdown(f"""
            <div style="background-color: #2b2f33; border: 1px dashed #4a5056; border-radius: 4px; padding: 25px; text-align: center; color: #94a3b8; font-size: 0.85rem; margin-top: -10px;">
                {empty_message}
            </div>
            """, unsafe_allow_html=True)
            return

        # Renderizar una sola página evita bloquear el navegador cuando hay muchos
        # fotogramas (por ejemplo, una búsqueda CLIP en una colección grande).
        page_count = (total_items + FRAMES_PER_PAGE - 1) // FRAMES_PER_PAGE
        page = 1
        if page_count > 1:
            page = st.selectbox(
                "Página de fotogramas",
                options=list(range(1, page_count + 1)),
                format_func=lambda current: f"Página {current} de {page_count}",
                key=f"tray_page_{title}",
            )

        first_item = (page - 1) * FRAMES_PER_PAGE
        visible_frames = analyzed_frames[first_item : first_item + FRAMES_PER_PAGE]
        if page_count > 1:
            st.caption(
                f"Mostrando {first_item + 1}–{first_item + len(visible_frames)} "
                f"de {total_items} fotogramas."
            )

        # Las columnas nativas de Streamlit soportan PIL.Image directamente.
        cols_per_row = 6
        
        # Estilos específicos para la sección de cuadrícula nativa de Streamlit
        st.markdown("""
        <style>
        .bb-tray-card {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            padding: 8px;
            margin-bottom: 12px;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .bb-tray-card:hover {
            border-color: #1b75bb;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .bb-tray-card-match {
            border: 2px solid #16a34a;
            box-shadow: 0 2px 8px rgba(22, 163, 74, 0.22);
        }
        .bb-tray-score-match {
            background-color: #15803d;
            color: #ffffff;
            font-size: 0.68rem;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 3px;
        }
        .bb-tray-badge {
            background-color: #1b75bb;
            color: #ffffff;
            font-size: 0.68rem;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 3px;
        }
        .bb-tray-desc {
            color: #0f172a;
            font-size: 0.74rem;
            line-height: 1.25;
            height: 3.2rem;
            overflow-y: auto;
            margin-top: 6px;
            word-wrap: break-word;
            font-weight: 600;
        }
        </style>
        """, unsafe_allow_html=True)

        # Agrupar las tarjetas en filas
        for i in range(0, len(visible_frames), cols_per_row):
            row_frames = visible_frames[i : i + cols_per_row]
            cols = st.columns(cols_per_row)
            
            for idx, item in enumerate(row_frames):
                with cols[idx]:
                    ts = item.get("timestamp", "00:00")
                    caption = item.get("caption", "Sin descripción")
                    img = item.get("image")
                    vid = item.get("video_id", "")
                    is_match = item.get("is_match", False)
                    match_class = " bb-tray-card-match" if is_match else ""
                    score_badge = (
                        "<span class='bb-tray-score-match'>✓ Coincidencia</span>"
                        if is_match else ""
                    )
                    
                    st.markdown(
                        f'<div class="bb-tray-card{match_class}">',
                        unsafe_allow_html=True,
                    )
                    if img:
                        st.image(img, width="stretch")
                    else:
                        st.markdown('<div style="height: 105px; background: #1e2225; display: flex; align-items: center; justify-content: center; color: #718096; font-size: 0.7rem; border-bottom: 1px solid #4a5056;">Sin imagen</div>', unsafe_allow_html=True)
                    
                    meta_and_desc = f"""
                    <div style="padding-top: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span class="bb-tray-badge">⏱ {ts}</span>
                            <span style="color: #475569; font-size: 0.65rem; font-weight: 600;">ID {vid}</span>
                        </div>
                        <div style="margin-top: 5px;">{score_badge}</div>
                        <div class="bb-tray-desc" title="{caption}">
                            {caption}
                        </div>
                    </div>
                    </div>
                    """
                    st.markdown(meta_and_desc, unsafe_allow_html=True)
