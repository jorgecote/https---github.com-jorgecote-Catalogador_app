import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from pathlib import Path
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

st.set_page_config(
    page_title="ByteBox | Catalogador de Video AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

from views.styles import apply_bytebox_styles
from views.header import render_header
from views.sidebar import render_sidebar
from views.main_page import render_main_page
from views.selection_panel import render_selection_panel
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
def load_analyzer():
    from models.blip_processor import VideoAnalyzer
    return VideoAnalyzer()


def _dam_url():
    try:
        return st.secrets["resourcespace"]["base_url"]
    except Exception:
        return ""


def _collection_name():
    active_id = st.session_state.get("selected_collection_id")
    if active_id is None:
        return None
    for col in st.session_state.get("collections", []):
        if col["ref"] == active_id:
            return col["name"]
    return None


def main():
    apply_bytebox_styles()

    if "conectado" not in st.session_state:
        st.session_state["conectado"] = False
    if "video_ids" not in st.session_state:
        st.session_state["video_ids"] = []
    if "analyzed_frames" not in st.session_state:
        st.session_state["analyzed_frames"] = []
    if "active_video_id" not in st.session_state:
        st.session_state["active_video_id"] = None
    if "collections" not in st.session_state:
        st.session_state["collections"] = []
    if "selected_collection_id" not in st.session_state:
        st.session_state["selected_collection_id"] = None
    if "blip_phase" not in st.session_state:
        st.session_state["blip_phase"] = "connect"
    if "pending_blip_ids" not in st.session_state:
        st.session_state["pending_blip_ids"] = []

    dam_url = _dam_url()
    has_secrets = bool(dam_url)

    sidebar_params = render_sidebar(
        is_connected=st.session_state["conectado"],
        total_videos=len(st.session_state["video_ids"]),
        collections=st.session_state["collections"],
        selected_collection_id=st.session_state["selected_collection_id"]
    )

    if not st.session_state["conectado"]:
        st.session_state["blip_phase"] = "connect"
    elif st.session_state["blip_phase"] == "connect":
        st.session_state["blip_phase"] = "select"

    phase = resolve_workflow_phase(
        st.session_state["conectado"],
        st.session_state.get("blip_phase"),
    )
    section = {
        "connect": "Inicio",
        "select": "Selección de recursos",
        "processing": "Procesamiento BLIP",
        "results": "Resultados BLIP",
    }.get(phase, "Catalogación")

    nav = render_header(
        app_url=dam_url,
        current_section=section,
        module="blip",
        is_connected=st.session_state["conectado"],
    )
    if nav.get("go_clip"):
        if st.session_state["conectado"]:
            st.switch_page("pages/1_Busqueda_CLIP.py")
        else:
            render_status_alert(
                "warning",
                "Conéctese primero a ByteBox",
                "La búsqueda CLIP reutiliza la misma sesión de catalogación.",
            )
    if nav.get("go_automated"):
        if st.session_state["conectado"]:
            st.switch_page("pages/03_Catalogacion_Automatizada.py")
        else:
            render_status_alert(
                "warning",
                "Conéctese primero a ByteBox",
                "La catalogación automatizada reutiliza la sesión de catalogación.",
            )

    render_workflow_stepper(phase, module="blip")

    if not st.session_state["conectado"]:
        conectar_presionado = render_main_page(base_url=dam_url, has_secrets=has_secrets)
        if conectar_presionado:
            try:
                with st.spinner("Autenticando con la API de ByteBox..."):
                    repository = get_repository()
                    lista_ids = repository.get_all_video_ids()
                    collections = repository.get_user_collections()
            except KeyError:
                render_status_alert(
                    "error",
                    "No se encontraron credenciales",
                    "Revise el archivo .streamlit/secrets.toml.",
                )
                return
            except Exception as e:
                st.session_state["conectado"] = False
                render_status_alert("error", "Error de conexión", str(e))
                return

            if lista_ids is not None:
                st.session_state["conectado"] = True
                st.session_state["video_ids"] = lista_ids
                st.session_state["collections"] = collections
                st.session_state["selected_collection_id"] = None
                st.session_state["blip_phase"] = "select"
                st.rerun()
            else:
                st.session_state["conectado"] = False
                render_status_alert(
                    "error",
                    "No se pudo listar videos",
                    "Verifique credenciales y permisos en ByteBox.",
                )
        render_collection_tray(
            analyzed_frames=st.session_state["analyzed_frames"],
            active_video_id=st.session_state.get("active_video_id"),
        )
        return

    new_col_id = sidebar_params.get("selected_collection_id", None)
    if new_col_id != st.session_state.get("selected_collection_id", None):
        try:
            repository = get_repository()
            with st.spinner("Cargando material de la colección seleccionada..."):
                if new_col_id is None:
                    lista_ids = repository.get_all_video_ids()
                else:
                    lista_ids = repository.get_collection_video_ids(new_col_id)
            for vid in st.session_state.get("video_ids", []):
                key = f"chk_vid_{vid}"
                if key in st.session_state:
                    del st.session_state[key]
            if "select_all_vids" in st.session_state:
                st.session_state["select_all_vids"] = False
            st.session_state["selected_collection_id"] = new_col_id
            st.session_state["video_ids"] = lista_ids
            st.session_state["blip_phase"] = "select"
            st.rerun()
        except Exception as e:
            render_status_alert("error", "Error al cargar colección", str(e))

    collection_name = _collection_name()

    if st.session_state.get("blip_phase") != "processing":
        selected_ids, procesar, ir_a_clip = render_selection_panel(
            video_ids=st.session_state["video_ids"],
            search_filter=sidebar_params["search_filter"],
            collection_name=collection_name
        )
        if ir_a_clip:
            st.switch_page("pages/1_Busqueda_CLIP.py")
        if procesar and selected_ids:
            st.session_state["pending_blip_ids"] = list(selected_ids)
            st.session_state["analyzed_frames"] = []
            st.session_state["blip_phase"] = "processing"
            st.rerun()

    if st.session_state.get("blip_phase") == "processing":
        selected_ids = st.session_state.get("pending_blip_ids") or []
        render_processing_header(
            "Catalogación BLIP en curso",
            f"{len(selected_ids)} video(s) en cola. Solo se muestra el recurso actual.",
        )
        repository = get_repository()
        with st.spinner("Cargando modelo BLIP en CPU..."):
            analyzer = load_analyzer()

        failed = 0
        current_slot = st.empty()
        for index, vid in enumerate(selected_ids, start=1):
            st.session_state["active_video_id"] = str(vid)
            render_job_progress(index, len(selected_ids), f"Video {index} de {len(selected_ids)} · ID {vid}")
            with current_slot.container():
                with st.spinner(f"Descargando video ID {vid}..."):
                    local_path = repository.download_video(vid, dest_folder="temp_videos")
                if not local_path:
                    render_status_alert("error", f"No se pudo descargar el video {vid}")
                    failed += 1
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
                results_list = []
                frame_num = 0
                try:
                    for timestamp, caption, thumb_img in analyzer.process_video_stream(
                        local_path,
                        sample_rate_sec=sidebar_params["sample_rate"],
                        generation_kwargs=sidebar_params["generation_config"]
                    ):
                        frame_num += 1
                        status_placeholder.info(
                            f"Analizando fotograma #{frame_num} en [{timestamp}]"
                        )
                        st.session_state["analyzed_frames"].append({
                            "video_id": vid,
                            "timestamp": timestamp,
                            "caption": caption,
                            "image": thumb_img
                        })
                        results_list.append((timestamp, caption))
                        rows_html = "".join([
                            f"<tr><td><span class='rs-time-badge'>{t}</span></td><td>{c}</td></tr>"
                            for t, c in results_list[-8:]
                        ])
                        render_meta_table(
                            meta_table_placeholder,
                            ["Marca de tiempo", "Descriptor BLIP"],
                            rows_html,
                        )
                    status_placeholder.success(
                        f"Video {vid} catalogado ({frame_num} fotogramas)."
                    )
                except Exception as e:
                    failed += 1
                    status_placeholder.error(f"Error en video {vid}: {e}")
                repository.cleanup_video(local_path)

        ok = len(selected_ids) - failed
        st.session_state["pending_blip_ids"] = []
        st.session_state["blip_phase"] = "results"
        st.toast("Catalogación finalizada", icon="✅")
        render_summary_banner(
            "Catalogación completada",
            f"{ok} de {len(selected_ids)} video(s) analizados. Revise la bandeja inferior.",
        )

    if st.session_state.get("blip_phase") == "results" and st.session_state.get("analyzed_frames"):
        if st.button("Nueva selección"):
            st.session_state["blip_phase"] = "select"
            st.rerun()

    render_collection_tray(
        analyzed_frames=st.session_state["analyzed_frames"],
        active_video_id=st.session_state.get("active_video_id")
    )


if __name__ == "__main__":
    main()
