import streamlit as st


FRAMES_PER_PAGE = 36


def render_collection_tray(
    analyzed_frames: list,
    active_video_id: str = None,
    title: str = "Colección de Fotogramas Analizados",
    empty_message: str = None,
):
    """Bandeja de miniaturas paginada (BLIP y CLIP)."""
    total_items = len(analyzed_frames)
    if empty_message is None:
        empty_message = (
            "Aquí aparecerán las miniaturas de los fotogramas analizados."
        )

    scope_label = f"Video ID: {active_video_id}" if active_video_id else "Ámbito actual"
    st.markdown(f"""
    <div class="rs-collection-tray">
        <div class="rs-tray-header">
            <div>
                <span class="rs-tray-title">{title}</span>
                <strong style="color: #ffffff; margin-left: 8px;">{scope_label}</strong>
                <span style="color: #e2e8f0; margin-left: 12px; font-size: 0.8rem;">
                    ({total_items} ítem{'s' if total_items != 1 else ''})
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not analyzed_frames:
        st.markdown(f'<div class="rs-tray-empty">{empty_message}</div>', unsafe_allow_html=True)
        return

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
    visible_frames = analyzed_frames[first_item: first_item + FRAMES_PER_PAGE]
    if page_count > 1:
        st.caption(
            f"Mostrando {first_item + 1}–{first_item + len(visible_frames)} de {total_items} fotogramas."
        )

    cols_per_row = 6
    for i in range(0, len(visible_frames), cols_per_row):
        row_frames = visible_frames[i: i + cols_per_row]
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
                    "<span class='bb-tray-score-match'>Coincidencia</span>"
                    if is_match else ""
                )
                st.markdown(f'<div class="bb-tray-card{match_class}">', unsafe_allow_html=True)
                if img:
                    st.image(img, width="stretch")
                else:
                    st.markdown(
                        '<div class="rs-tray-empty" style="height:105px;padding:12px;">Sin imagen</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(f"""
                <div style="padding-top: 6px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="bb-tray-badge">{ts}</span>
                        <span style="color: #1a202c; font-size: 0.68rem; font-weight: 700;">ID {vid}</span>
                    </div>
                    <div style="margin-top: 5px;">{score_badge}</div>
                    <div class="bb-tray-desc" title="{caption}">{caption}</div>
                </div>
                </div>
                """, unsafe_allow_html=True)
