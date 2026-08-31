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
from runtime.repository import get_repository


@st.cache_resource
def load_clip_searcher():
    """Carga y cachea CLIP. No se llama hasta que el usuario pulsa Buscar."""
    from models.clip_processor import CLIPVideoSearcher
    return CLIPVideoSearcher()


def _ensure_session_defaults():
    if "conectado" not in st.session_state:
        st.session_state["conectado"] = False
    if "video_ids" not in st.session_state:
        st.session_state["video_ids"] = []
    if "collections" not in st.session_state:
        st.session_state["collections"] = []
    if "selected_collection_id" not in st.session_state:
        st.session_state["selected_collection_id"] = None
    if "clip_hits" not in st.session_state:
        st.session_state["clip_hits"] = []
    if "clip_last_query" not in st.session_state:
        st.session_state["clip_last_query"] = ""
    if "clip_analyzed_frames" not in st.session_state:
        st.session_state["clip_analyzed_frames"] = []


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


def main():
    apply_bytebox_styles()
    _ensure_session_defaults()

    BYTEBOX_APP_URL = "http://157.137.212.40/bytebox/10.7/"

    sidebar_params = render_search_sidebar(
        is_connected=st.session_state["conectado"],
        total_videos=len(st.session_state["video_ids"]),
        collections=st.session_state["collections"],
        selected_collection_id=st.session_state["selected_collection_id"]
    )

    if sidebar_params["go_back"]:
        st.switch_page("app.py")

    render_header(app_url=BYTEBOX_APP_URL, current_section="Búsqueda semántica CLIP")

    if not st.session_state["conectado"]:
        st.warning("Conéctese primero a ByteBox desde el módulo de catalogación BLIP. Esta pantalla reutiliza esa sesión.")
        if st.button("← Ir a catalogación AI", type="primary"):
            st.switch_page("app.py")
        return

    new_col_id = sidebar_params.get("selected_collection_id", None)
    if new_col_id != st.session_state.get("selected_collection_id", None):
        try:
            with st.spinner("🔄 Cargando material de la colección seleccionada..."):
                _reload_video_ids(new_col_id)
            st.session_state["clip_hits"] = []
            st.session_state["clip_last_query"] = ""
            st.session_state["clip_analyzed_frames"] = []
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al cargar colección: {e}")

    collection_name = _collection_name(
        st.session_state.get("collections", []),
        st.session_state.get("selected_collection_id")
    )

    video_ids = list(st.session_state.get("video_ids") or [])
    search_filter = sidebar_params.get("search_filter") or ""
    if search_filter:
        video_ids = [vid for vid in video_ids if search_filter.lower() in str(vid).lower()]

    query, buscar = render_search_form(
        collection_name=collection_name,
        total_videos=len(video_ids),
        collection_id=st.session_state.get("selected_collection_id"),
    )

    if buscar and query:
        st.session_state["clip_hits"] = []
        st.session_state["clip_last_query"] = query
        st.session_state["clip_analyzed_frames"] = []

        st.markdown("""
        <div class="rs-card" style="margin-top: 20px; border-left: 4px solid #1b75bb;">
            <div class="rs-card-header">
                <span>⚡</span> Búsqueda CLIP por fotogramas
            </div>
        </div>
        """, unsafe_allow_html=True)

        try:
            repository = get_repository()
        except KeyError:
            st.error("❌ No se encontraron las credenciales en `.streamlit/secrets.toml`")
            return

        with st.spinner("Cargando CLIP ViT-B/32 en CPU (descarga automática la primera vez)..."):
            try:
                searcher = load_clip_searcher()
            except Exception as e:
                st.error("❌ No se pudo cargar CLIP")
                st.markdown(str(e))
                return

        try:
            text_features = searcher.encode_text(query)
        except Exception as e:
            st.error(f"❌ No se pudo codificar la consulta: {e}")
            return

        sample_rate = sidebar_params["sample_rate"]
        threshold = sidebar_params["threshold"]
        hits = []

        for vid in video_ids:
            st.markdown(f"#### 🎬 Escaneando Recurso Video ID: `{vid}`")
            local_path = None
            try:
                with st.spinner(f"Descargando video ID {vid} desde ByteBox..."):
                    local_path = repository.download_video(vid, dest_folder="temp_videos")

                if not local_path:
                    st.error(f"❌ No se pudo descargar el video ID {vid}")
                    continue

                try:
                    import cv2
                    test_cap = cv2.VideoCapture(local_path)
                    total_frames = test_cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    detected_fps = test_cap.get(cv2.CAP_PROP_FPS) or 25.0
                    test_cap.release()
                    tamanio_mb = os.path.getsize(local_path) / (1024 * 1024)
                    st.caption(
                        f"📊 Archivo: `{tamanio_mb:.2f} MB` | "
                        f"Fotogramas totales: `{int(total_frames)}` | "
                        f"FPS: `{detected_fps:.1f}`"
                    )
                except Exception:
                    pass

                status_placeholder = st.empty()
                progress_container = st.container(border=True)
                matching_frames = []
                video_analyzed_frames = []
                frame_num = 0
                max_score = 0.0

                with progress_container:
                    meta_table_placeholder = st.empty()
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
                                f"⏳ Fotograma #{frame_num} en `[{timestamp}]` · similitud `{score:.3f}`"
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
                                meta_table_placeholder.markdown(f"""
                                <table class="rs-meta-table">
                                    <thead>
                                        <tr>
                                            <th style="width: 110px;">Marca de Tiempo</th>
                                            <th>Similitud CLIP</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {rows_html}
                                    </tbody>
                                </table>
                                """, unsafe_allow_html=True)

                        if matching_frames:
                            status_placeholder.success(
                                f"✅ {len(matching_frames)} coincidencia(s) en video ID {vid} "
                                f"(score máx. {max_score:.3f})."
                            )
                            hits.append({
                                "video_id": vid,
                                "max_score": round(max_score, 4),
                                "match_count": len(matching_frames),
                                "frames": matching_frames
                            })
                            st.session_state["clip_analyzed_frames"].extend(
                                video_analyzed_frames
                            )
                        else:
                            status_placeholder.info(
                                f"Sin coincidencias sobre el umbral {threshold:.2f} en video ID {vid} "
                                f"(score máx. {max_score:.3f})."
                            )
                    except Exception as e:
                        status_placeholder.error(f"❌ Error durante la búsqueda del video ID {vid}: {e}")
            finally:
                if local_path:
                    repository.cleanup_video(local_path)
                    st.caption(f"🗑️ Archivo temporal de video `{vid}` eliminado correctamente del disco local.")

        hits.sort(key=lambda h: h["max_score"], reverse=True)
        st.session_state["clip_hits"] = hits
        st.toast("Búsqueda CLIP finalizada", icon="✅")

    render_search_results(
        clip_hits=st.session_state.get("clip_hits") or [],
        query=st.session_state.get("clip_last_query") or ""
    )
    render_collection_tray(
        analyzed_frames=st.session_state.get("clip_analyzed_frames") or [],
        active_video_id=None,
        title="Fotogramas de videos con coincidencias CLIP",
        empty_message="🎞️ Aquí aparecerán los fotogramas de los videos que superen el umbral de similitud."
    )


main()
