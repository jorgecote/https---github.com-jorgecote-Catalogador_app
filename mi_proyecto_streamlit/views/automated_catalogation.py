import json
import streamlit as st

from views.status_alert import render_status_alert


def render_automated_config(collections: list, available_video_ids: list):
    """Configura alcance, muestreo y sampling. No realiza llamadas API."""
    st.markdown("""
    <div class="rs-card">
      <div class="rs-card-header">Configuración de catalogación automatizada</div>
      <div class="rs-card-subtitle">
        BLIP genera varias muestras por fotograma; Qwen las sintetiza en una
        descripción cronológica editable.
      </div>
    </div>
    """, unsafe_allow_html=True)

    scope_mode = st.radio(
        "Alcance",
        options=("Colección completa", "Videos individuales"),
        horizontal=True,
        key="auto_scope_mode",
    )

    collection_id = None
    selected_ids = []
    if scope_mode == "Colección completa":
        options = ["Ingresar ID de colección"] + [
            f"[{item['ref']}] {item['name']}" for item in collections or []
        ]
        selection = st.selectbox("Colección", options, key="auto_collection_option")
        if selection == options[0]:
            collection_id = st.number_input(
                "ID de colección",
                min_value=1,
                step=1,
                value=None,
                placeholder="Ej.: 125",
                key="auto_collection_id",
            )
        else:
            collection_id = int(selection.split("]", 1)[0][1:])
    else:
        selected_ids = st.multiselect(
            "Videos a catalogar",
            options=available_video_ids or [],
            format_func=lambda resource_id: f"Recurso ID {resource_id}",
            key="auto_selected_ids",
        )

    config_col1, config_col2, config_col3 = st.columns(3)
    with config_col1:
        sample_rate = st.slider(
            "Intervalo (segundos/frame)",
            min_value=1,
            max_value=30,
            value=5,
            key="auto_sample_rate",
        )
    with config_col2:
        caption_count = st.slider(
            "Muestras BLIP por frame",
            min_value=1,
            max_value=5,
            value=3,
            key="auto_caption_count",
        )
    with config_col3:
        temperature = st.slider(
            "Variación BLIP",
            min_value=0.6,
            max_value=0.9,
            value=0.8,
            step=0.05,
            key="auto_temperature",
        )

    can_start = bool(collection_id) if scope_mode == "Colección completa" else bool(selected_ids)
    if not can_start:
        render_status_alert(
            "info",
            "Defina el alcance",
            "Seleccione una colección o uno o más videos para habilitar el análisis.",
        )

    start = st.button(
        "Iniciar catalogación automatizada",
        type="primary",
        disabled=not can_start,
        key="auto_start",
    )
    return {
        "scope_mode": scope_mode,
        "collection_id": int(collection_id) if collection_id else None,
        "video_ids": list(selected_ids),
        "sample_rate": sample_rate,
        "caption_count": caption_count,
        "temperature": temperature,
        "top_p": 0.9,
        "start": start,
    }


def render_audit_trace(video_result: dict):
    """Traza auditable paginada: miniatura, captions BLIP y síntesis."""
    video_id = video_result["video_id"]
    frames = video_result.get("frames") or []
    with st.expander(f"Traza auditable · Recurso ID {video_id} · {len(frames)} fotogramas"):
        for frame in frames:
            image_col, detail_col = st.columns([1, 2])
            with image_col:
                st.image(frame.get("image"), caption=f"[{frame.get('timestamp', '00:00')}]", width="stretch")
            with detail_col:
                st.markdown(f"**Timestamp:** `{frame.get('timestamp', '00:00')}`")
                st.markdown("**Muestras BLIP**")
                for caption in frame.get("blip_samples") or []:
                    st.markdown(f"- {caption}")
                st.markdown(f"**Síntesis Qwen:** {frame.get('synthesis', '')}")
            st.divider()


def render_review_actions(results: list[dict]):
    """Revisión, edición, exportación y evento de escritura MAM por recurso."""
    if not results:
        return []

    st.markdown("""
    <div class="rs-card">
      <div class="rs-card-header">Revisión humana y sincronización</div>
      <div class="rs-card-subtitle">
        Revise el texto antes de guardar. La sincronización actualiza el campo
        <code>DESCRIPCION</code> del recurso correspondiente.
      </div>
    </div>
    """, unsafe_allow_html=True)

    save_events = []
    for result in results:
        video_id = result["video_id"]
        text_key = f"auto_description_{video_id}"
        if text_key not in st.session_state:
            st.session_state[text_key] = result.get("chronological_description", "")

        with st.expander(f"Revisar descripción · Recurso ID {video_id}", expanded=True):
            st.text_area(
                "Descripción cronológica",
                key=text_key,
                height=190,
            )
            export_col, save_col, discard_col = st.columns([1.2, 1.3, 1])
            with export_col:
                export_payload = {
                    "video_id": video_id,
                    "frames": [
                        {key: value for key, value in frame.items() if key != "image"}
                        for frame in result.get("frames") or []
                    ],
                    "chronological_description": st.session_state[text_key],
                }
                st.download_button(
                    "Exportar JSON",
                    data=json.dumps(export_payload, ensure_ascii=False, indent=2),
                    file_name=f"catalogacion_{video_id}.json",
                    mime="application/json",
                    key=f"auto_export_json_{video_id}",
                )
            with save_col:
                save_clicked = st.button(
                    "Guardar en DESCRIPCION",
                    type="primary",
                    disabled=not st.session_state[text_key].strip(),
                    key=f"auto_save_{video_id}",
                )
            with discard_col:
                if st.button("Omitir", key=f"auto_discard_{video_id}"):
                    st.info("Se omitió la sincronización. La metadata de ByteBox no fue modificada.")

            if save_clicked:
                save_events.append(
                    {
                        "video_id": video_id,
                        "value": st.session_state[text_key],
                    }
                )

    return save_events
