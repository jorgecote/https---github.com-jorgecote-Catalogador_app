import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from views.styles import apply_bytebox_styles
from views.header import render_header
from views.search_sidebar import render_search_sidebar
from views.search_form import render_search_form
from views.search_results import render_search_results
from views.collection_tray import render_collection_tray
from views.status_alert import render_status_alert
from views.workflow_stepper import render_workflow_stepper, resolve_workflow_phase
from views.processing_panel import (
    render_processing_header,
    render_job_progress,
    render_meta_table,
    render_summary_banner,
)
from runtime.repository import get_repository


@st.cache_resource
def load_clip_searcher():
    from models.clip_processor import CLIPVideoSearcher
    return CLIPVideoSearcher()


def _ensure_session_defaults():
    defaults = {
        "conectado": False,
        "video_ids": [],
        "collections": [],
        "selected_collection_id": None,
        "clip_hits": [],
        "clip_last_query": "",
        "clip_analyzed_frames": [],
        "clip_phase": "connect",
        "pending_clip_query": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _collection_name(collections, collection_id):
    if collection_id is None:
        return None
    for col in collections or []:
        if col["ref"] == collection_id:
            return col["name"]
    return None


def _reload_video_ids(collection_id):
    repository = get_repository()
    if collection_id is None:
        lista_ids = repository.get_all_video_ids()
    else:
        lista_ids = repository.get_collection_video_ids(collection_id)
    st.session_state["selected_collection_id"] = collection_id
    st.session_state["video_ids"] = lista_ids if lista_ids is not None else []


def _dam_url():
    try:
        return st.secrets["resourcespace"]["base_url"]
    except Exception:
        return ""


def main():
    apply_bytebox_styles()
    _ensure_session_defaults()

    sidebar_params = render_search_sidebar(
        is_connected=st.session_state["conectado"],
        total_videos=len(st.session_state["video_ids"]),
        collections=st.session_state["collections"],
        selected_collection_id=st.session_state["selected_collection_id"]
    )

    if sidebar_params.get("go_back"):
        st.session_state["clip_phase"] = "select"
        st.switch_page("app.py")

    if not st.session_state["conectado"]:
        st.session_state["clip_phase"] = "connect"
    elif st.session_state.get("clip_phase") == "connect":
        st.session_state["clip_phase"] = "select"

    phase = resolve_workflow_phase(
        st.session_state["conectado"],
        st.session_state.get("clip_phase"),
    )
    section = {
        "connect": "Inicio",
        "select": "Consulta CLIP",
        "processing": "Búsqueda en curso",
        "results": "Resultados CLIP",
    }.get(phase, "Búsqueda CLIP")

    nav = render_header(
        app_url=_dam_url(),
        current_section=section,
        module="clip",
        is_connected=st.session_state["conectado"],
    )
    if nav.get("go_blip"):
        st.session_state["clip_phase"] = "select"
        st.switch_page("app.py")
    if nav.get("go_automated"):
        st.switch_page("pages/03_Catalogacion_Automatizada.py")

    render_workflow_stepper(phase, module="clip")

    if not st.session_state["conectado"]:
        render_status_alert(
            "warning",
            "Conéctese primero desde catalogación BLIP",
            "CLIP reutiliza la sesión autenticada de ByteBox.",
        )
        if st.button("Ir a catalogación BLIP", type="primary"):
            st.switch_page("app.py")
        return

    new_col_id = sidebar_params.get("selected_collection_id", None)
    if new_col_id != st.session_state.get("selected_collection_id", None):
        try:
            with st.spinner("Cargando material de la colección seleccionada..."):
                _reload_video_ids(new_col_id)
            st.session_state["clip_hits"] = []
            st.session_state["clip_last_query"] = ""
            st.session_state["clip_analyzed_frames"] = []
            st.session_state["clip_phase"] = "select"
            st.rerun()
        except Exception as e:
            render_status_alert("error", "Error al cargar colección", str(e))

    collection_name = _collection_name(
        st.session_state.get("collections", []),
        st.session_state.get("selected_collection_id")
    )
    video_ids = list(st.session_state.get("video_ids") or [])
    search_filter = sidebar_params.get("search_filter") or ""
    if search_filter:
        video_ids = [vid for vid in video_ids if search_filter.lower() in str(vid).lower()]

    if st.session_state.get("clip_phase") != "processing":
        query, buscar = render_search_form(
            collection_name=collection_name,
            total_videos=len(video_ids),
            collection_id=st.session_state.get("selected_collection_id"),
            threshold=sidebar_params["threshold"],
            sample_rate=sidebar_params["sample_rate"],
        )
        if buscar and query:
            st.session_state["pending_clip_query"] = query
            st.session_state["clip_last_query"] = query
            st.session_state["clip_hits"] = []
            st.session_state["clip_analyzed_frames"] = []
            st.session_state["clip_scope_ids"] = video_ids
            st.session_state["clip_phase"] = "processing"
            st.rerun()

    if st.session_state.get("clip_phase") == "processing":
        query = st.session_state.get("pending_clip_query") or ""
        video_ids = st.session_state.get("clip_scope_ids") or video_ids
        render_processing_header(
            "Búsqueda CLIP en curso",
            f"Consulta: «{query}». Se muestra solo el recurso actual.",
        )
        try:
            repository = get_repository()
        except KeyError:
            render_status_alert(
                "error",
                "No se encontraron credenciales",
                "Revise .streamlit/secrets.toml.",
            )
            return

        with st.spinner("Cargando CLIP ViT-B/32 en CPU..."):
            try:
                searcher = load_clip_searcher()
            except Exception as e:
                render_status_alert("error", "No se pudo cargar CLIP", str(e))
                st.session_state["clip_phase"] = "select"
                return

        try:
            text_features = searcher.encode_text(query)
        except Exception as e:
            render_status_alert("error", "No se pudo codificar la consulta", str(e))
            st.session_state["clip_phase"] = "select"
            return

        sample_rate = sidebar_params["sample_rate"]
        threshold = sidebar_params["threshold"]
        hits = []
        current_slot = st.empty()
        for index, vid in enumerate(video_ids, start=1):
            render_job_progress(index, len(video_ids), f"Video {index} de {len(video_ids)} · ID {vid}")
            local_path = None
            with current_slot.container():
                try:
                    with st.spinner(f"Descargando video ID {vid}..."):
                        local_path = repository.download_video(vid, dest_folder="temp_videos")
                    if not local_path:
                        render_status_alert("error", f"No se pudo descargar el video {vid}")
                        continue
                    try:
                        import cv2
                        test_cap = cv2.VideoCapture(local_path)
                        total_frames = test_cap.get(cv2.CAP_PROP_FRAME_COUNT)
                        detected_fps = test_cap.get(cv2.CAP_PROP_FPS) or 25.0
                        test_cap.release()
                        tamanio_mb = os.path.getsize(local_path) / (1024 * 1024)
                        st.caption(
                            f"Archivo: {tamanio_mb:.2f} MB · {int(total_frames)} fotogramas · {detected_fps:.1f} FPS"
                        )
                    except Exception:
                        pass

                    status_placeholder = st.empty()
                    meta_table_placeholder = st.empty()
                    matching_frames = []
                    video_analyzed_frames = []
                    frame_num = 0
                    max_score = 0.0
                    try:
                        for (
                            timestamp,
                            timestamp_sec,
                            frame_index,
                            score,
                            is_match,
                            thumbnail,
                        ) in searcher.search_video_stream(
                            local_path,
                            sample_rate_sec=sample_rate,
                            text_features=text_features,
                            threshold=threshold
                        ):
                            frame_num += 1
                            max_score = max(max_score, score)
                            status_placeholder.info(
                                f"Fotograma #{frame_num} en [{timestamp}] · similitud {score:.3f}"
                            )
                            video_analyzed_frames.append({
                                "video_id": vid,
                                "timestamp": timestamp,
                                "caption": f"Similitud CLIP: {score:.3f}",
                                "image": thumbnail,
                                "is_match": is_match,
                            })
                            if is_match:
                                matching_frames.append({
                                    "timestamp": timestamp,
                                    "timestamp_sec": timestamp_sec,
                                    "frame_index": frame_index,
                                    "score": round(score, 4)
                                })
                                rows_html = "".join([
                                    (
                                        f"<tr><td><span class='rs-time-badge'>{fr['timestamp']}</span></td>"
                                        f"<td>{fr['score']:.3f}</td></tr>"
                                    )
                                    for fr in matching_frames
                                ])
                                render_meta_table(
                                    meta_table_placeholder,
                                    ["Marca de tiempo", "Similitud CLIP"],
                                    rows_html,
                                )
                        if matching_frames:
                            status_placeholder.success(
                                f"{len(matching_frames)} coincidencia(s) en video {vid} "
                                f"(score máx. {max_score:.3f})."
                            )
                            hits.append({
                                "video_id": vid,
                                "max_score": round(max_score, 4),
                                "match_count": len(matching_frames),
                                "frames": matching_frames
                            })
                            st.session_state["clip_analyzed_frames"].extend(video_analyzed_frames)
                        else:
                            status_placeholder.info(
                                f"Sin coincidencias sobre el umbral {threshold:.2f} en video {vid} "
                                f"(score máx. {max_score:.3f})."
                            )
                    except Exception as e:
                        status_placeholder.error(f"Error en video {vid}: {e}")
                finally:
                    if local_path:
                        repository.cleanup_video(local_path)

        hits.sort(key=lambda h: h["max_score"], reverse=True)
        st.session_state["clip_hits"] = hits
        st.session_state["pending_clip_query"] = ""
        st.session_state["clip_phase"] = "results"
        st.toast("Búsqueda CLIP finalizada", icon="✅")
        render_summary_banner(
            "Búsqueda finalizada",
            f"{len(hits)} video(s) con coincidencias para «{query}».",
        )

    render_search_results(
        clip_hits=st.session_state.get("clip_hits") or [],
        query=st.session_state.get("clip_last_query") or "",
        threshold=sidebar_params.get("threshold"),
    )
    if st.session_state.get("clip_phase") == "results":
        if st.button("Nueva consulta"):
            st.session_state["clip_phase"] = "select"
            st.rerun()

    render_collection_tray(
        analyzed_frames=st.session_state.get("clip_analyzed_frames") or [],
        active_video_id=None,
        title="Fotogramas de videos con coincidencias CLIP",
        empty_message="Aquí aparecerán los fotogramas de los videos que superen el umbral.",
    )


main()
