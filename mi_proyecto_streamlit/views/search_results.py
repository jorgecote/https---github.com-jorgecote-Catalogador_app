import streamlit as st
from views.status_alert import render_status_alert


def render_search_results(clip_hits: list, query: str = "", threshold: float = None):
    """Resultados CLIP: jerarquía videos → coincidencias → timestamps."""
    if not clip_hits:
        if query:
            hint = " Pruebe un umbral más bajo en el panel izquierdo." if threshold is not None else ""
            render_status_alert(
                "warning",
                f"Sin coincidencias para «{query}»",
                f"Ningún fotograma superó el umbral.{hint}",
            )
        return

    q_label = f" para «{query}»" if query else ""
    st.markdown(f"""
    <div class="rs-card">
        <div class="rs-card-header">Videos que coinciden{q_label}</div>
        <div class="rs-card-subtitle">
            {len(clip_hits)} video(s) con al menos un fotograma sobre el umbral,
            ordenados por similitud máxima. Las miniaturas coincidentes están resaltadas en la bandeja.
        </div>
    </div>
    """, unsafe_allow_html=True)

    for hit in clip_hits:
        vid = hit.get("video_id")
        max_score = hit.get("max_score", 0.0)
        match_count = hit.get("match_count", 0)
        frames = hit.get("frames") or []
        label = f"Recurso ID {vid}  ·  {match_count} coincidencia(s)  ·  score máx. {max_score:.3f}"
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
                <tbody>{rows_html}</tbody>
            </table>
            """, unsafe_allow_html=True)
