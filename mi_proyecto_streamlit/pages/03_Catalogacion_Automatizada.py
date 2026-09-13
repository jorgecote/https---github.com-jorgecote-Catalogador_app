import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from models.catalogation_result import build_video_result
from runtime.repository import get_repository
from views.automated_catalogation import (
    render_audit_trace,
    render_automated_config,
    render_review_actions,
)
from views.header import render_header
from views.processing_panel import render_job_progress, render_processing_header, render_summary_banner
from views.status_alert import render_status_alert
from views.styles import apply_bytebox_styles
from views.workflow_stepper import render_workflow_stepper


@st.cache_resource
def load_automated_models():
    """Carga BLIP y Qwen solo al iniciar el análisis automatizado."""
    from models.blip_processor import VideoAnalyzer
    from models.frame_synthesizer import FrameSynthesizer

    return VideoAnalyzer(), FrameSynthesizer()


def _defaults():
    defaults = {
        "conectado": False,
        "video_ids": [],
        "collections": [],
        "auto_phase": "select",
        "auto_pending_config": None,
        "auto_results": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _dam_url():
    try:
        return st.secrets["resourcespace"]["base_url"]
    except Exception:
        return ""


def _resolve_video_ids(config: dict) -> list[int]:
    if config["scope_mode"] == "Videos individuales":
        return config["video_ids"]
    repository = get_repository()
    return repository.get_collection_video_ids(config["collection_id"])


def _process_videos(config: dict):
    try:
        video_ids = _resolve_video_ids(config)
    except Exception as exc:
        render_status_alert("error", "No se pudo cargar el alcance", str(exc))
        st.session_state["auto_phase"] = "select"
        return

    if not video_ids:
        render_status_alert(
            "warning",
            "No se encontraron videos",
            "La colección seleccionada no contiene recursos de video.",
        )
        st.session_state["auto_phase"] = "select"
        return

    render_processing_header(
        "Catalogación automatizada en curso",
        "Fases: descarga temporal → BLIP sampling → síntesis Qwen → limpieza.",
    )
    try:
        with st.spinner("Cargando BLIP y Qwen en CPU..."):
            analyzer, synthesizer = load_automated_models()
        repository = get_repository()
    except Exception as exc:
        render_status_alert("error", "No se pudieron cargar los modelos", str(exc))
        st.session_state["auto_phase"] = "select"
        return

    results = []
    failed = 0
    current_slot = st.empty()
    for index, video_id in enumerate(video_ids, start=1):
        render_job_progress(index, len(video_ids), f"Recurso {index} de {len(video_ids)} · ID {video_id}")
        local_path = None
        with current_slot.container():
            status = st.empty()
            try:
                status.info(f"Descargando temporalmente el video {video_id}...")
                local_path = repository.download_video(video_id, dest_folder="temp_videos")
                if not local_path:
                    failed += 1
                    render_status_alert("error", f"No se pudo descargar el recurso {video_id}")
                    continue

                frames = []
                for timestamp, blip_samples, thumbnail in analyzer.process_video_sampling_stream(
                    local_path,
                    sample_rate_sec=config["sample_rate"],
                    caption_count=config["caption_count"],
                    temperature=config["temperature"],
                    top_p=config["top_p"],
                ):
                    status.info(f"[{timestamp}] Sintetizando descripciones con Qwen...")
                    synthesis = synthesizer.synthesize(blip_samples)
                    frames.append(
                        {
                            "timestamp": timestamp,
                            "image": thumbnail,
                            "blip_samples": blip_samples,
                            "synthesis": synthesis,
                        }
                    )
                results.append(build_video_result(video_id, frames))
                status.success(f"Recurso {video_id} analizado: {len(frames)} fotogramas.")
            except Exception as exc:
                failed += 1
                render_status_alert("error", f"Falló el recurso {video_id}", str(exc))
            finally:
                if local_path:
                    repository.cleanup_video(local_path)

    st.session_state["auto_results"] = results
    st.session_state["auto_pending_config"] = None
    st.session_state["auto_phase"] = "results"
    render_summary_banner(
        "Catalogación automatizada finalizada",
        f"{len(results)} de {len(video_ids)} recurso(s) completados; {failed} fallido(s).",
    )


def main():
    apply_bytebox_styles()
    _defaults()

    nav = render_header(
        app_url=_dam_url(),
        current_section="Catalogación automatizada",
        module="automated",
        is_connected=st.session_state["conectado"],
    )
    if nav.get("go_blip"):
        st.switch_page("app.py")
    if nav.get("go_clip"):
        st.switch_page("pages/1_Busqueda_CLIP.py")

    phase = st.session_state["auto_phase"]
    render_workflow_stepper(
        "processing" if phase == "processing" else ("results" if phase == "results" else "select"),
        module="blip",
    )

    if not st.session_state["conectado"]:
        render_status_alert(
            "warning",
            "Conéctese primero a ByteBox",
            "Esta herramienta reutiliza la sesión autenticada de catalogación BLIP.",
        )
        if st.button("Ir a catalogación BLIP", type="primary"):
            st.switch_page("app.py")
        return

    if phase == "select":
        config = render_automated_config(
            collections=st.session_state["collections"],
            available_video_ids=st.session_state["video_ids"],
        )
        if config["start"]:
            st.session_state["auto_pending_config"] = config
            st.session_state["auto_results"] = []
            st.session_state["auto_phase"] = "processing"
            st.rerun()

    if st.session_state["auto_phase"] == "processing":
        _process_videos(st.session_state["auto_pending_config"])

    results = st.session_state.get("auto_results") or []
    if st.session_state["auto_phase"] == "results":
        for result in results:
            render_audit_trace(result)

        save_events = render_review_actions(results)
        if save_events:
            repository = get_repository()
            for event in save_events:
                try:
                    if repository.update_resource_description(
                        resource_id=event["video_id"],
                        value=event["value"],
                    ):
                        render_status_alert(
                            "success",
                            f"Metadata actualizada · Recurso {event['video_id']}",
                            "Campo DESCRIPCION guardado correctamente.",
                        )
                    else:
                        render_status_alert(
                            "error",
                            f"No se pudo actualizar el recurso {event['video_id']}",
                            "ResourceSpace no confirmó la actualización.",
                        )
                except Exception as exc:
                    render_status_alert(
                        "error",
                        f"Error al guardar el recurso {event['video_id']}",
                        str(exc),
                    )

        if st.button("Nueva catalogación automatizada"):
            st.session_state["auto_phase"] = "select"
            st.rerun()


main()
