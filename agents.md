Aquí tienes el agents.md actualizado con el nuevo orden de prioridades:
# agents.md — Catalogador de Video AI (ByteBox)

## Rol
Agente experto en Python + Streamlit + MVC limpio.
Objetivo: mantener y evolucionar el pipeline ResourceSpace → descarga temporal → BLIP (CPU) → descripciones con timestamp → limpieza inmediata.

## Restricciones críticas (obligatorias)
- Hardware: 4-12 GB RAM, **sin GPU**. Siempre `device="cpu"` y `low_cpu_mem_usage=True`.
- Imports pesados (`torch`, `transformers`, `cv2`, `PIL`) → **lazy** (dentro de métodos o funciones cacheadas).
- Videos: descargar a carpeta temporal → procesar → **eliminar inmediatamente** con `cleanup_video`. Nunca dejar archivos residuales.
- Rutas: solo relativas (`Path(__file__).resolve().parent`). Proyecto vive en OneDrive.
- Secrets: solo vía `st.secrets["resourcespace"]`. Nunca hardcodear ni loguear claves.

## Arquitectura MVC (estricta)
mi_proyecto_streamlit/
├── app.py                  # CONTROLADOR (orquestación + session_state)
├── models/
│   ├── resourcespace_client.py   # ResourceSpaceAPI (bajo nivel) + ResourceSpaceRepository (alto nivel)
│   └── blip_processor.py         # VideoAnalyzer (BLIP + extracción de frames)
└── views/                  # Solo UI Streamlit (sin lógica de negocio ni imports pesados)
    ├── styles.py
    ├── header.py
    ├── sidebar.py
    ├── main_page.py
    ├── selection_panel.py
    └── collection_tray.py
### Reglas de capas
- **views/**: solo componentes Streamlit + HTML/CSS. Reciben datos, devuelven eventos. Cero requests, cero modelos de IA.
- **models/**: agnósticos a Streamlit. Sin `import streamlit`.
- **app.py**: único lugar de orquestación, session_state y lazy loading de modelos.

## Stack actual
- Python + Streamlit
- `torch` (CPU) + `transformers` (BLIP base)
- `opencv-python-headless` + Pillow
- `requests` + hashlib (firmas SHA256 ResourceSpace)

## Flujo principal (app.py)
1. Sidebar + Header
2. Si no conectado → `render_main_page` → conectar vía `_get_repository()` → `get_all_video_ids()`
3. Si conectado → `render_selection_panel` (checkboxes + sample_rate + generation_config)
4. Al procesar: lazy load analyzer → `download_video` → `process_video_stream` (generador) → actualizar UI en vivo → `cleanup_video`
5. Siempre renderizar `collection_tray` con `analyzed_frames`

## Convenciones de código
- Lazy imports obligatorios para todo lo pesado.
- Usar `@st.cache_resource` solo para el modelo BLIP (`load_analyzer`).
- Generadores preferidos sobre listas grandes (ahorro de RAM).
- Nombres claros y en español/inglés técnico mixto (consistente con el código existente).
- Manejo de errores amigable en UI (`st.error`, `st.toast`).
- Estilos centralizados en `views/styles.py` (tema ByteBox).

## Secrets esperados
```toml
[resourcespace]
base_url = "..."
user = "..."
private_key = "..."
Cómo ejecutar
cd mi_proyecto_streamlit
streamlit run app.py
Prioridades actuales de desarrollo
Colecciones en ResourceSpace
Extender la API para listar y filtrar videos por colección (además del listado global). Permitir seleccionar una colección específica (ej. material nuevo de un rodaje) y catalogar solo sus videos.
Descripción unificada del video + escritura de metadata
Usar un algoritmo o un LLM muy ligero para consolidar los captions de fotogramas en una descripción global del video. Actualizar automáticamente la metadata correspondiente en el MAM (ResourceSpace).
Búsqueda semántica con CLIP
Integrar CLIP para búsqueda de videos mediante lenguaje natural, sin depender de la metadata de catalogación.
Mejora del modelo de captioning
Evaluar e integrar BLIP-2 (u otro modelo ligero compatible con CPU) para mejorar la calidad de las descripciones por fotograma.
(Nota: BLIP-2 OPT-2.7B es marginalmente viable solo en ≥12 GB RAM y no recomendado como reemplazo directo por velocidad/memoria.)

Generación de EDL (pre-edición sugerida)
A partir de una solicitud en lenguaje natural y usando las descripciones por fotograma, generar un archivo .edl como propuesta de pre-edición.
### Anti-patrones (prohibidos)
Importar torch/transformers/cv2 a nivel de módulo
Dejar archivos de video sin limpiar
Poner lógica de negocio o API calls en views/
Usar GPU o asumir CUDA
Rutas absolutas o hardcodeadas
Exponer secrets en logs o código