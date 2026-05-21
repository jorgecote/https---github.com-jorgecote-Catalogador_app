import streamlit as st

# Importamos la Vista
from views.main_page import render_main_page

# Importamos la nueva Vista para la selección
from views.selection_panel import render_selection_panel

# Importamos las clases de nuestro Modelo
from models.resourcespace_client import ResourceSpaceAPI, ResourceSpaceRepository

@st.cache_resource
def load_analyzer():
    from models.blip_processor import VideoAnalyzer
    return VideoAnalyzer()

# -----------------------------------------------------------------------------
# CONTROLADOR PRINCIPAL
# -----------------------------------------------------------------------------

def main():
    # Inicializamos el estado de la sesión si no existe
    if "conectado" not in st.session_state:
        st.session_state["conectado"] = False
    if "video_ids" not in st.session_state:
        st.session_state["video_ids"] = []

    # 1. RENDERIZAR LA VISTA PRINCIPAL
    # Llamamos a la vista principal (el botón de conectar)
    conectar_presionado = render_main_page()
    
    # 2. LÓGICA DE CONTROL DE CONEXIÓN
    if conectar_presionado:
        
        # Intentamos leer los secretos de forma segura
        try:
            url_instancia = st.secrets["resourcespace"]["base_url"]
            usuario = st.secrets["resourcespace"]["user"]
            api_key = st.secrets["resourcespace"]["private_key"]
        except KeyError:
            st.error("❌ No se encontraron las credenciales en el archivo `.streamlit/secrets.toml`")
            return

        # Mostramos la animación de carga mientras se hace la petición
        with st.spinner("🔄 Conectando automáticamente con ResourceSpace..."):
            
            # Instanciamos el modelo con los datos seguros ocultos
            api_connector = ResourceSpaceAPI(
                base_url=url_instancia, 
                user=usuario, 
                private_key=api_key
            )
            repository = ResourceSpaceRepository(api_connector)
            
            # Solicitamos los IDs
            lista_ids = repository.get_all_video_ids()
        
        # Actualizamos el estado según el resultado
        if lista_ids is not None:
            st.session_state["conectado"] = True
            st.session_state["video_ids"] = lista_ids
            st.success(f"¡Conexión exitosa! Se encontraron {len(lista_ids)} recursos de video.")
        else:
            st.session_state["conectado"] = False
            st.error("❌ Error de conexión. Revisa que las credenciales en `secrets.toml` sean correctas.")
            
    # 3. RENDERIZAR EL PANEL DE SELECCIÓN (Si hay conexión activa)
    if st.session_state["conectado"]:
        selected_ids, sample_rate, gen_config, procesar = render_selection_panel(st.session_state["video_ids"])
        
        # 4. LÓGICA DE PROCESAMIENTO
        if procesar and len(selected_ids) > 0:
            st.divider()
            st.info(f"⏳ Iniciando el procesamiento de {len(selected_ids)} videos...")
            
            # Re-instanciamos el repositorio ya que la página se recargó
            url_instancia = st.secrets["resourcespace"]["base_url"]
            usuario = st.secrets["resourcespace"]["user"]
            api_key = st.secrets["resourcespace"]["private_key"]
            api_connector = ResourceSpaceAPI(base_url=url_instancia, user=usuario, private_key=api_key)
            repository = ResourceSpaceRepository(api_connector)
            
            # Cargamos el modelo de IA en caché para que no se recargue en cada interacción
            with st.spinner("Cargando modelo de Inteligencia Artificial (BLIP) en CPU..."):
                analyzer = load_analyzer()
            
            # Procesamos cada video
            for vid in selected_ids:
                st.write(f"### 🎬 Procesando Video ID: {vid}")
                
                with st.spinner("Descargando video temporalmente..."):
                    local_path = repository.download_video(vid, dest_folder="temp_videos")
                
                if not local_path:
                    st.error(f"❌ Error: No se pudo descargar el video ID {vid}")
                    continue
                
                # El placeholder debe estar FUERA del spinner para que Streamlit re-renderice
                st.markdown(f"**🔍 Analizando Video ID: {vid}**")
                status_text = st.empty()
                
                with st.container(border=True):
                    resultados_markdown = ""
                    placeholder = st.empty()
                    
                    try:
                        # --- BLOQUE DE DIAGNÓSTICO EN VIVO ---
                        import cv2
                        import os
                        
                        # 1. Validar tamaño del archivo
                        tamanio_mb = os.path.getsize(local_path) / (1024 * 1024)
                        st.write(f"📊 **Diagnóstico del archivo:** {tamanio_mb:.2f} MB")
                        
                        # 2. Validar qué ve OpenCV
                        test_cap = cv2.VideoCapture(local_path)
                        total_frames = test_cap.get(cv2.CAP_PROP_FRAME_COUNT)
                        detected_fps = test_cap.get(cv2.CAP_PROP_FPS)
                        test_cap.release()
                        
                        st.write(f"🎞️ **Fotogramas detectados por OpenCV:** {total_frames}")
                        st.write(f"⚡ **FPS detectados:** {detected_fps}")
                        
                        if detected_fps > 0:
                            duracion_seg = total_frames / detected_fps
                            st.write(f"⏱️ **Duración estimada:** {duracion_seg:.2f} segundos")
                        # -------------------------------------
                        
                        frame_num = 0
                        for timestamp, cap in analyzer.process_video_stream(local_path, sample_rate, generation_kwargs=gen_config):
                            frame_num += 1
                            # Actualizamos el status fuera del contenedor
                            status_text.caption(f"⏳ Analizando fotograma {frame_num} en [{timestamp}]...")
                            # Acumulamos y redibujamos toda la lista
                            resultados_markdown += f"- **[{timestamp}]** {cap}\n"
                            placeholder.markdown(resultados_markdown)
                        
                        # Mensaje de finalización modificado para auditoría
                        st.write(f"🏁 **Bucle finalizado.** Total fotogramas entregados por la IA: {frame_num}")
                        status_text.success(f"✅ Análisis completado — {frame_num} fotogramas procesados")
                        
                    except Exception as e:
                        status_text.error(f"❌ Error al procesar el video ID {vid}: {e}")
                # Cumpliendo con la regla de persistencia temporal
                repository.cleanup_video(local_path)
                st.caption(f"🗑️ Archivo temporal eliminado para el video {vid}")
                
            st.balloons()
            st.success("🎉 ¡El procesamiento de todos los videos seleccionados ha finalizado con éxito!")

if __name__ == "__main__":
    main()
    