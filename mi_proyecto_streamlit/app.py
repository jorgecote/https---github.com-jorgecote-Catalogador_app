import os
import sys
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

# Importamos estilos y vistas de la arquitectura limpia
from views.styles import apply_bytebox_styles
from views.header import render_header
from views.sidebar import render_sidebar
from views.main_page import render_main_page
from views.selection_panel import render_selection_panel
from views.collection_tray import render_collection_tray

# Importamos las clases del Modelo
from models.resourcespace_client import ResourceSpaceAPI, ResourceSpaceRepository

@st.cache_resource
def load_analyzer():
    """Carga y cachea el modelo BLIP optimizado para CPU."""
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

    # Obtenemos la URL de la instancia de ResourceSpace de forma segura
    base_url = ""
    try:
        base_url = st.secrets["resourcespace"]["base_url"]
    except Exception:
        pass

    # 1. RENDERIZAR BARRA LATERAL (Panel de Configuración ResourceSpace)
    sidebar_params = render_sidebar(
        is_connected=st.session_state["conectado"],
        total_videos=len(st.session_state["video_ids"])
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
                url_instancia = st.secrets["resourcespace"]["base_url"]
                usuario = st.secrets["resourcespace"]["user"]
                api_key = st.secrets["resourcespace"]["private_key"]
            except KeyError:
                st.error("❌ No se encontraron las credenciales en el archivo `.streamlit/secrets.toml`")
                return

            with st.spinner("🔄 Autenticando con la API de ByteBox..."):
                api_connector = ResourceSpaceAPI(
                    base_url=url_instancia, 
                    user=usuario, 
                    private_key=api_key
                )
                repository = ResourceSpaceRepository(api_connector)
                lista_ids = repository.get_all_video_ids()

            if lista_ids is not None:
                st.session_state["conectado"] = True
                st.session_state["video_ids"] = lista_ids
                st.rerun()
            else:
                st.session_state["conectado"] = False
                st.error("❌ Error de conexión. Verifique las credenciales en `.streamlit/secrets.toml`.")

    # 4. VISTA CUANDO ESTÁ CONECTADO
    else:
        selected_ids, procesar = render_selection_panel(
            video_ids=st.session_state["video_ids"],
            search_filter=sidebar_params["search_filter"]
        )

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
            
            # Reinstanciar repositorio
            url_instancia = st.secrets["resourcespace"]["base_url"]
            usuario = st.secrets["resourcespace"]["user"]
            api_key = st.secrets["resourcespace"]["private_key"]
            api_connector = ResourceSpaceAPI(base_url=url_instancia, user=usuario, private_key=api_key)
            repository = ResourceSpaceRepository(api_connector)

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