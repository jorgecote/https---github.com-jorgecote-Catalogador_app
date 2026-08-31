# agents.md — Catalogador de Video AI (ByteBox)

## Rol
Agente experto en Python + Streamlit + MVC limpio.
Objetivo: mantener y evolucionar el pipeline ResourceSpace → descarga temporal → BLIP (CPU) → descripciones con timestamp → limpieza inmediata; y el módulo CLIP de búsqueda semántica por fotogramas.

## Restricciones críticas (obligatorias)
- Hardware: 4-12 GB RAM, **sin GPU**. Siempre `device="cpu"` y `low_cpu_mem_usage=True`.
- Imports pesados (`torch`, `transformers`, `cv2`, `PIL`) → **lazy** (dentro de métodos o funciones cacheadas).
- Videos: descargar a carpeta temporal → procesar → **eliminar inmediatamente** con `cleanup_video`. Nunca dejar archivos residuales.
- Rutas: solo relativas (`Path(__file__).resolve().parent`). Proyecto vive en OneDrive.
- Secrets: solo vía `st.secrets["resourcespace"]`. Nunca hardcodear ni loguear claves.
- No importar BLIP en la página CLIP (y no cargar CLIP al abrir catalogación). Si ambos modelos quedan en `cache_resource` de la misma sesión, reiniciar Streamlit ante falta de RAM.

## Arquitectura MVC (estricta)

```text
mi_proyecto_streamlit/
├── app.py                          # CONTROLADOR catalogación BLIP
├── runtime/
│   └── repository.py               # Factory Streamlit → ResourceSpaceRepository (secrets)
├── pages/
│   └── 1_Busqueda_CLIP.py          # CONTROLADOR búsqueda semántica CLIP
├── models/
│   ├── resourcespace_client.py     # ResourceSpaceAPI + ResourceSpaceRepository
│   ├── blip_processor.py           # VideoAnalyzer (BLIP)
│   └── clip_processor.py           # CLIPVideoSearcher (CLIP ViT-B/32)
└── views/
    ├── styles.py                   # Tema ByteBox (incl. .rs-score-badge para CLIP)
    ├── header.py
    ├── sidebar.py                  # Sidebar catalogación BLIP
    ├── main_page.py
    ├── selection_panel.py          # Checkboxes BLIP + botón navegación a CLIP
    ├── collection_tray.py
    ├── search_sidebar.py           # Sidebar módulo CLIP
    ├── search_form.py              # Formulario consulta lenguaje natural
    └── search_results.py           # Tabla de hits con timestamps y scores
```

### Reglas de capas
- **views/**: solo componentes Streamlit + HTML/CSS. Reciben datos, devuelven eventos. Cero requests, cero modelos de IA.
- **models/**: agnósticos a Streamlit. Sin `import streamlit`.
- **app.py** y **pages/**: orquestación, session_state y lazy loading de modelos.
- **runtime/**: helpers de controlador (pueden usar Streamlit/secrets). No es capa de modelos.

## Stack actual
- Python + Streamlit (multipage)
- `torch` (CPU) + `transformers` (BLIP base + CLIP ViT-B/32)
- `opencv-python-headless` + Pillow
- `requests` + hashlib (firmas SHA256 ResourceSpace)

## Session state compartido (BLIP ↔ CLIP)

| Clave | Tipo | Origen | Uso |
|-------|------|--------|-----|
| `conectado` | bool | `app.py` al conectar | Requisito para catalogar y para CLIP |
| `video_ids` | list[int] | Conexión / cambio de colección | Ámbito de videos en BLIP y CLIP |
| `collections` | list[dict] | `get_user_collections()` | Selector de colección en ambos sidebars |
| `selected_collection_id` | int \| None | Sidebar BLIP o CLIP | Filtra `video_ids` por colección |
| `analyzed_frames` | list[dict] | Solo BLIP | Bandeja inferior de captions |
| `active_video_id` | str \| None | Solo BLIP | Video activo en bandeja |
| `clip_hits` | list[dict] | Solo CLIP | Resultados de búsqueda semántica |
| `clip_last_query` | str | Solo CLIP | Última consulta enviada |

Formato de cada elemento en `collections`: `{ "ref": int, "name": str, "count": int | None }`.

## Flujo principal (app.py — catalogación BLIP)
1. Sidebar (`render_sidebar`) + Header.
2. Si no conectado → `render_main_page` → conectar vía `get_repository()` → `get_all_video_ids()` + `get_user_collections()`.
3. Si conectado → cambio de colección recarga IDs con `get_all_video_ids()` o `get_collection_video_ids()`.
4. `render_selection_panel`: checkboxes, filtro por ID, botones **Iniciar Catalogación AI** y **Búsqueda semántica (CLIP)**.
5. Navegación a CLIP: `st.switch_page("pages/1_Busqueda_CLIP.py")` si `conectado`.
6. Al procesar: `load_analyzer()` → `download_video` → `process_video_stream` (generador) → UI en vivo → `cleanup_video`.
7. Siempre renderizar `collection_tray` con `analyzed_frames`.

## Módulo CLIP — búsqueda semántica por lenguaje natural

### Propósito
Permite buscar fotogramas dentro de videos de ByteBox describiendo en lenguaje natural lo que se busca (ej. *"persona caminando de noche cerca de un edificio"*). CLIP puntúa cada fotograma muestreado contra el embedding del texto; los que superan el umbral se registran con timestamp para una futura generación de EDL.

### Navegación
- Entrada: botón **🔍 Búsqueda semántica (CLIP)** en `views/selection_panel.py` (requiere sesión conectada).
- Salida: botón **← Volver a catalogación BLIP** en `views/search_sidebar.py` → `st.switch_page("app.py")`.

### Responsabilidad por archivo

| Archivo | Rol |
|---------|-----|
| `pages/1_Busqueda_CLIP.py` | Controlador: valida conexión, recarga colección, orquesta descarga/búsqueda/limpieza, persiste `clip_hits` |
| `models/clip_processor.py` | Modelo: `CLIPVideoSearcher` — carga CLIP, `encode_text`, `search_video_stream` |
| `runtime/repository.py` | Factory compartida: `get_repository()` lee secrets y devuelve `ResourceSpaceRepository` |
| `views/search_sidebar.py` | Vista: colección activa, sample_rate, threshold, filtro ID, navegación |
| `views/search_form.py` | Vista: textarea de consulta + botón Buscar (deshabilitado si no hay videos o query vacía) |
| `views/search_results.py` | Vista: expanders por video con tabla timestamp / segundos / frame / score |

### API del modelo (`CLIPVideoSearcher`)
- **Modelo**: `openai/clip-vit-base-patch32` (HuggingFace), CPU, `low_cpu_mem_usage=True`.
- **`encode_text(query: str)`** → tensor L2-normalizado de features de texto.
- **`search_video_stream(video_path, sample_rate_sec, text_features, threshold=0.25)`** → generador.
  - Yield: `(timestamp, timestamp_sec, frame_index, score, is_match)`.
  - `timestamp`: `"MM:SS"` o `"HH:MM:SS"`.
  - `is_match`: `score >= threshold`.
- Imports pesados (`torch`, `transformers`, `cv2`, `PIL`) solo dentro de métodos.

### Flujo CLIP (`pages/1_Busqueda_CLIP.py`)
1. Requiere `session_state["conectado"]` (misma sesión que catalogación).
2. Ámbito: todos los videos o una colección (`selected_collection_id`); filtro opcional por ID en sidebar.
3. Al pulsar **Buscar videos**:
   - `load_clip_searcher()` (`@st.cache_resource`, solo entonces se carga CLIP).
   - `encode_text(query)` una vez por búsqueda.
   - Por cada `video_id` en ámbito: `download_video` → `search_video_stream` → UI en vivo → `cleanup_video` en `finally`.
4. Acumula hits, ordena por `max_score` descendente, guarda en `clip_hits`.

### Contrato de resultados (`clip_hits`)

```python
{
    "video_id": int,
    "max_score": float,      # redondeado a 4 decimales
    "match_count": int,
    "frames": [
        {
            "timestamp": str,       # "MM:SS" o "HH:MM:SS"
            "timestamp_sec": int,
            "frame_index": int,     # índice del fotograma muestreado (0-based)
            "score": float          # cosine similarity CLIP, redondeado a 4 decimales
        },
        ...
    ]
}
```

Pensado para consumo futuro por un generador de EDL.

### Parámetros UI (sidebar CLIP)
- **Tasa de muestreo**: 1–30 s entre fotogramas (default 5). Menor = más detalle, más CPU.
- **Umbral de similitud**: 0.15–0.40 (default 0.25). Valores típicos útiles: 0.22–0.32.
- **Filtro por ID**: substring opcional sobre `video_id`.

## API ResourceSpace relevante (`models/resourcespace_client.py`)

| Método | Función API | Uso |
|--------|-------------|-----|
| `get_all_video_ids()` | `do_search` (restypes 3,4) | Listado global de videos |
| `get_user_collections()` | `get_user_collections` + `search_public_collections` | Selector de colecciones |
| `get_collection_video_ids(id)` | `do_search` con `!collection{id}` | Videos de una colección |
| `download_video(id)` | `get_resource_path` + HTTP | Descarga temporal |
| `cleanup_video(path)` | — | Elimina archivo local |

## Convenciones de código
- Lazy imports obligatorios para todo lo pesado.
- `@st.cache_resource` para BLIP (`load_analyzer` en `app.py`) y CLIP (`load_clip_searcher` en la página CLIP, solo al pulsar Buscar).
- Generadores preferidos sobre listas grandes (ahorro de RAM).
- Nombres claros y en español/inglés técnico mixto (consistente con el código existente).
- Manejo de errores amigable en UI (`st.error`, `st.toast`).
- Estilos centralizados en `views/styles.py` (tema ByteBox; badges `.rs-time-badge` y `.rs-score-badge`).

## Secrets esperados

```toml
[resourcespace]
base_url = "..."
user = "..."
private_key = "..."
```

## Cómo ejecutar

```bash
cd mi_proyecto_streamlit
streamlit run app.py
```

La página CLIP aparece en el menú multipage como **Busqueda CLIP** y también se accede desde catalogación.

## Estado de desarrollo

### ✅ Implementado
- Conexión ResourceSpace con firmas SHA256.
- Catalogación BLIP por fotogramas con bandeja de resultados.
- Colecciones: listado (`get_user_collections`) y filtrado por colección en BLIP y CLIP.
- Módulo CLIP multipage: consulta en lenguaje natural, muestreo configurable, umbral, resultados con timestamps.
- Factory compartida `runtime/repository.py`.
- Navegación bidireccional BLIP ↔ CLIP reutilizando session state.

### 🔜 Pendiente
- **Descripción unificada del video + escritura de metadata**: consolidar captions BLIP en descripción global; escribir en ResourceSpace.
- **CLIP — índice persistente**: cachear embeddings en disco para evitar re-escaneo completo en cada búsqueda.
- **Generación de EDL**: consumir `clip_hits` y/o descripciones BLIP para proponer pre-edición en `.edl`.
- **Mejora del modelo de captioning**: evaluar BLIP-2 u otro modelo ligero en CPU (BLIP-2 OPT-2.7B marginal en ≥12 GB RAM; no recomendado como reemplazo directo por velocidad/memoria).

## Anti-patrones (prohibidos)
- Importar `torch` / `transformers` / `cv2` a nivel de módulo.
- Dejar archivos de video sin limpiar.
- Poner lógica de negocio o API calls en `views/`.
- Usar GPU o asumir CUDA.
- Rutas absolutas o hardcodeadas.
- Exponer secrets en logs o código.
- Importar `blip_processor` desde la página CLIP.
