import os
import sys

# Configurar codificación UTF-8 para evitar errores de codificación en consolas de Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from pathlib import Path
import streamlit as st

# Asegurar que el directorio de la aplicación esté siempre en sys.path
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Configuración de página de Streamlit
st.set_page_config(
    page_title="ByteBox | Catalogador de Video AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importamos estilos y vistas (ligeros, solo Streamlit)
from views.styles import apply_bytebox_styles
from views.header import render_header
from views.sidebar import render_sidebar
from views.main_page import render_main_page
from views.selection_panel import render_selection_panel
from views.collection_tray import render_collection_tray
from runtime.repository import get_repository

# ─── MODELO ──────────────────────────────────────────────────────────────────
# Los imports de modelos pesados (resourcespace_client, blip_processor) son
# lazy: se realizan solo en el momento en que el usuario conecta o procesa,
# no en el arranque de la aplicación.
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource
def load_analyzer():
    """Carga y cachea el modelo BLIP. Se ejecuta una sola vez por proceso."""
    from models.blip_processor import VideoAnalyzer
    return VideoAnalyzer()

# -----------------------------------------------------------------------------
# CONTROLADOR PRINCIPAL
# -----------------------------------------------------------------------------

def main():
    # Inyectamos estilos visuales oficiales de ByteBox
    apply_bytebox_styles()

    # Inicializamos estados de sesión
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

    # Obtenemos la URL de la instancia de ResourceSpace de forma segura
    base_url = ""
    try:
        base_url = st.secrets["resourcespace"]["base_url"]
    except Exception:
        pass

    # 1. RENDERIZAR BARRA LATERAL (Panel de Configuración ResourceSpace)
    sidebar_params = render_sidebar(
        is_connected=st.session_state["conectado"],
        total_videos=len(st.session_state["video_ids"]),
        collections=st.session_state["collections"],
        selected_collection_id=st.session_state["selected_collection_id"]
    )

    # 2. RENDERIZAR ENCABEZADO SUPERIOR (Logo y Migas de Pan)
    current_step = "Procesamiento y Catalogación" if st.session_state["conectado"] else "Inicio"
    BYTEBOX_APP_URL = "http://157.137.212.40/bytebox/10.7/"
    render_header(app_url=BYTEBOX_APP_URL, current_section=current_step)

    # 3. VISTA PRINCIPAL CUANDO NO ESTÁ CONECTADO
    if not st.session_state["conectado"]:
        conectar_presionado = render_main_page(base_url=BYTEBOX_APP_URL)
        
        if conectar_presionado:
            try:
                with st.spinner("🔄 Autenticando con la API de ByteBox..."):
                    repository = get_repository()
                    lista_ids = repository.get_all_video_ids()
                    collections = repository.get_user_collections()
            except KeyError:
                st.error("❌ No se encontraron las credenciales en el archivo `.streamlit/secrets.toml`")
                return
            except Exception as e:
                st.session_state["conectado"] = False
                st.error(f"❌ Error de conexión: {e}")
                return

            if lista_ids is not None:
                st.session_state["conectado"] = True
                st.session_state["video_ids"] = lista_ids
                st.session_state["collections"] = collections
                st.session_state["selected_collection_id"] = None
                st.rerun()
            else:
                st.session_state["conectado"] = False
                st.error("❌ Error de conexión. Verifique las credenciales en `.streamlit/secrets.toml`.")

    # 4. VISTA CUANDO ESTÁ CONECTADO
    else:
        # Detectar si cambió la colección seleccionada en la barra lateral
        new_col_id = sidebar_params.get("selected_collection_id", None)
        if new_col_id != st.session_state.get("selected_collection_id", None):
            try:
                repository = get_repository()
                with st.spinner("🔄 Cargando material de la colección seleccionada..."):
                    if new_col_id is None:
                        lista_ids = repository.get_all_video_ids()
                    else:
                        lista_ids = repository.get_collection_video_ids(new_col_id)
                # Limpiar checkboxes anteriores del estado de sesión para evitar conflictos
                for vid in st.session_state.get("video_ids", []):
                    key = f"chk_vid_{vid}"
                    if key in st.session_state:
                        del st.session_state[key]
                if "select_all_vids" in st.session_state:
                    st.session_state["select_all_vids"] = False

                st.session_state["selected_collection_id"] = new_col_id
                st.session_state["video_ids"] = lista_ids
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al cargar colección: {e}")

        # Obtener el nombre de la colección activa para mostrarlo en el panel
        collection_name = None
        if st.session_state.get("selected_collection_id") is not None:
            active_id = st.session_state["selected_collection_id"]
            for col in st.session_state.get("collections", []):
                if col["ref"] == active_id:
                    collection_name = col["name"]
                    break

        selected_ids, procesar, ir_a_clip = render_selection_panel(
            video_ids=st.session_state["video_ids"],
            search_filter=sidebar_params["search_filter"],
            collection_name=collection_name
        )

        if ir_a_clip:
            if st.session_state["conectado"]:
                st.switch_page("pages/1_Busqueda_CLIP.py")
            else:
                st.error("❌ Conéctese a ByteBox antes de abrir la búsqueda semántica.")

        # 5. LÓGICA DE PROCESAMIENTO Y CATALOGACIÓN
        if procesar and len(selected_ids) > 0:
            st.session_state["analyzed_frames"] = []  # Limpiar bandeja de fotogramas anteriores
            st.markdown("""
            <div class="rs-card" style="margin-top: 20px; border-left: 4px solid #1b75bb;">
                <div class="rs-card-header">
                    <span>⚡</span> Ejecución del Pipeline de Catalogación AI
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Instanciar repositorio con lazy import
            repository = get_repository()

            # Cargar analizador BLIP
            with st.spinner("Cargando modelo de IA (BLIP-base) en CPU con optimización de memoria..."):
                analyzer = load_analyzer()

            # Procesar cada video seleccionado
            for vid in selected_ids:
                st.session_state["active_video_id"] = str(vid)
                st.markdown(f"#### 🎬 Procesando Recurso Video ID: `{vid}`")

                with st.spinner(f"Descargando video ID {vid} desde ByteBox..."):
                    local_path = repository.download_video(vid, dest_folder="temp_videos")

                if not local_path:
                    st.error(f"❌ No se pudo descargar el video ID {vid}")
                    continue

                # Diagnóstico inicial
                try:
                    import cv2
                    test_cap = cv2.VideoCapture(local_path)
                    total_frames = test_cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    detected_fps = test_cap.get(cv2.CAP_PROP_FPS) or 25.0
                    test_cap.release()
                    tamanio_mb = os.path.getsize(local_path) / (1024 * 1024)
                    
                    st.caption(f"📊 Archivo: `{tamanio_mb:.2f} MB` | Fotogramas totales: `{int(total_frames)}` | FPS: `{detected_fps:.1f}`")
                except Exception:
                    pass

                # Contenedor de análisis en vivo
                status_placeholder = st.empty()
                progress_container = st.container(border=True)
                
                with progress_container:
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
                            status_placeholder.info(f"⏳ Analizando fotograma #{frame_num} en marca de tiempo `[{timestamp}]`...")
                            
                            # Guardar frame para la bandeja de colección inferior
                            frame_data = {
                                "video_id": vid,
                                "timestamp": timestamp,
                                "caption": caption,
                                "image": thumb_img
                            }
                            st.session_state["analyzed_frames"].append(frame_data)
                            results_list.append((timestamp, caption))
                            
                            # Actualizar tabla de metadatos en vivo
                            rows_html = "".join([
                                f"<tr><td><span style='background:#1b75bb;color:white;padding:2px 6px;border-radius:3px;font-weight:600;'>{t}</span></td><td>{c}</td></tr>"
                                for t, c in results_list
                            ])
                            meta_table_placeholder.markdown(f"""
                            <table class="rs-meta-table">
                                <thead>
                                    <tr>
                                        <th style="width: 110px;">Marca de Tiempo</th>
                                        <th>Descriptor Generado por IA (BLIP)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rows_html}
                                </tbody>
                            </table>
                            """, unsafe_allow_html=True)

                        status_placeholder.success(f"✅ Análisis completado con éxito para el video ID {vid} ({frame_num} fotogramas catalogados).")

                    except Exception as e:
                        status_placeholder.error(f"❌ Error durante el análisis del video ID {vid}: {e}")

                # Limpieza obligatoria del archivo temporal de disco
                repository.cleanup_video(local_path)
                st.caption(f"🗑️ Archivo temporal de video `{vid}` eliminado correctamente del disco local.")

            # Notificación de finalización (sin globos — popup tipo toast nativo de Streamlit)
            st.toast("🎉 ¡Catalogación finalizada con éxito!", icon="✅")
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #1b75bb 0%, #0e446d 100%);
                border-radius: 8px;
                padding: 20px 28px;
                color: #ffffff;
                margin-top: 24px;
                box-shadow: 0 6px 16px rgba(27, 117, 187, 0.35);
                display: flex;
                align-items: center;
                gap: 16px;
            ">
                <span style="font-size: 2rem;">✅</span>
                <div>
                    <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 4px;">
                        ¡Catalogación completada con éxito!
                    </div>
                    <div style="font-size: 0.88rem; opacity: 0.9;">
                        Todos los videos seleccionados han sido analizados fotograma a fotograma. Revisa la bandeja de colección inferior para explorar los resultados.
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 6. BANDEJA DE COLECCIÓN INFERIOR (Bottom Tray con miniaturas y descripciones)
    render_collection_tray(
        analyzed_frames=st.session_state["analyzed_frames"],
        active_video_id=st.session_state.get("active_video_id")
    )

if __name__ == "__main__":
    main()