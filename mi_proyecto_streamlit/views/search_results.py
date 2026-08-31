import streamlit as st


def render_search_results(clip_hits: list, query: str = ""):
    """
    Lista videos que cumplen el umbral, con tabla de timestamps y score.
    clip_hits: lista de dicts {video_id, max_score, match_count, frames}.
    """
    if not clip_hits:
        if query:
            st.info("No hay coincidencias por encima del umbral para esta consulta.")
        return

    q_label = f" para «{query}»" if query else ""
    st.markdown(f"""
    <div class="rs-card" style="margin-top: 16px;">
        <div class="rs-card-header">
            <span>🎯</span> Videos que coinciden{q_label}
        </div>
        <div class="rs-card-subtitle">
            {len(clip_hits)} video(s) con al menos un fotograma sobre el umbral, ordenados por similitud máxima.
        </div>
    </div>
    """, unsafe_allow_html=True)

    for hit in clip_hits:
        vid = hit.get("video_id")
        max_score = hit.get("max_score", 0.0)
        match_count = hit.get("match_count", 0)
        frames = hit.get("frames") or []

        label = (
            f"🎥 Recurso ID {vid}  ·  "
            f"{match_count} fotograma(s)  ·  "
            f"score máx. {max_score:.3f}"
        )
        with st.expander(label, expanded=(len(clip_hits) == 1)):
            rows_html = "".join([
                (
                    "<tr>"
                    f"<td><span class='rs-time-badge'>{fr.get('timestamp', '')}</span></td>"
                    f"<td>{int(fr.get('timestamp_sec', 0))}</td>"
                    f"<td>{int(fr.get('frame_index', 0))}</td>"
                    f"<td><span class='rs-score-badge'>{float(fr.get('score', 0)):.3f}</span></td>"
                    "</tr>"
                )
                for fr in frames
            ])
            st.markdown(f"""
            <table class="rs-meta-table">
                <thead>
                    <tr>
                        <th style="width: 120px;">Tiempo</th>
                        <th style="width: 110px;">Segundos</th>
                        <th style="width: 110px;">Frame #</th>
                        <th>Similitud CLIP</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            """, unsafe_allow_html=True)
