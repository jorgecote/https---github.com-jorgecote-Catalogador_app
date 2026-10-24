# agents.md — Catalogador de Video AI (ByteBox)

## Rol
Agente experto en Python + **Reflex (MVC estricto)** + procesamiento de video con IA en CPU.
Objetivo: mantener y evolucionar el dashboard unificado en Reflex (`ia_video_app/`) —y preservar el módulo legado en `mi_proyecto_streamlit/`— integrando **4 flujos**:

1. **Catalogación BLIP por fotogramas**
2. **Búsqueda semántica CLIP por lenguaje natural**
3. **Catalogación automatizada (BLIP multi-sampling + síntesis Qwen GGUF + HITL)**
4. **Chat Qwen (asistente local tipo ChatGPT, sin ByteBox)**

> **Reglas Gauntlet obligatorias**: consultar siempre [`GAUNTLET_RULES.md`](./GAUNTLET_RULES.md) antes de modificar controladores, vistas o configuración de despliegue.

---

## Restricciones críticas (obligatorias)
- **Hardware**: 4–12 GB RAM, **sin GPU**. Siempre `device="cpu"`, `low_cpu_mem_usage=True` y `n_gpu_layers=0`.
- **Lazy imports**: `torch`, `transformers`, `cv2`, `PIL` y `llama_cpp` **solo** dentro de métodos o singletons (`ia_video_app/runtime/ai_registry.py`), nunca a nivel de módulo.
- **Un singleton por modelo**: BLIP, CLIP y Qwen se cargan una vez por proceso. El chat **reutiliza** el mismo `FrameSynthesizer` y el pool `qwen-cpu` de la catalogación automatizada. No abrir un segundo `Llama`.
- **Pools de CPU dedicados**: inferencia BLIP/CLIP/Qwen en `ThreadPoolExecutor` (`blip-cpu`, `clip-cpu`, `qwen-cpu`) + `asyncio.to_thread` / `run_in_executor`. No bloquear el event loop de Reflex.
- **Limpieza inmediata**: descargar video → procesar → `cleanup_video` en `try/finally`. En Windows/OneDrive usar `tempfile.gettempdir()/bytebox_catalogador`, no una carpeta del repo.
- **Miniaturas en memoria**: convertir `PIL.Image` a Data URI JPEG Base64 en el controlador. El estado que recorre `rx.foreach` debe ser `list[dict]` JSON-seguro, no dataclasses.
- **Credenciales**: `.env` con fallback a `.streamlit/secrets.toml` vía `ia_video_app/runtime/config.py`. Nunca hardcodear ni loguear claves.
- **Diseño**: paleta institucional ByteBox en `ia_video_app/views/theme.py`. **Prohibido neón**.
- **Chat**: no exige conexión a ByteBox. El historial vive en `CatalogState.chat_messages` (memoria de sesión), no en un `.txt`. **Nueva conversación** vacía la lista y llama `FrameSynthesizer.reset_chat()` (caché KV de llama.cpp).
- **Qwen**: solo el GGUF local `qwen2.5-1.5b-instruct-q4_k_m.gguf`. No descargar pesos desde la UI. Cargar Qwen al pulsar iniciar catalogación automática o al enviar el primer mensaje de chat.
- **Despliegue**: `venv`/`.venv`, frontend `8503`, backend `8504` (en Windows local el backend puede rotar si el socket queda zombie), Nginx `/IA_videos/`.

---

## Arquitectura MVC (Reflex principal + legado Streamlit)

```text
Catalogador_app/
├── rxconfig.py                         # Puertos 8503/8504 + subpath /IA_videos
├── requirements.txt                    # Dependencias CPU unificadas
├── .env.example                        # Plantilla ResourceSpace + Reflex
├── GAUNTLET_RULES.md                   # Guardrails de arquitectura, UX y deploy
├── sdd.md                              # Especificación SDD
├── download_model_weights.py           # Descarga offline BLIP, CLIP, Qwen GGUF
├── deploy/
│   ├── reflex_catalog.service          # Systemd (/home/ubuntu/IA_video_app/venv)
│   └── nginx_ia_videos.conf            # Nginx /IA_videos/ + WebSocket /_event
├── ia_video_app/                       # APLICACIÓN PRINCIPAL REFLEX
│   ├── ia_video_app.py                 # Página raíz + rx.match de módulos
│   ├── runtime/
│   │   ├── config.py                   # .env + fallback secrets.toml
│   │   ├── repository.py               # Factory ResourceSpaceRepository
│   │   └── ai_registry.py              # Singletons + pools CPU
│   ├── models/
│   │   ├── schemas.py                  # Contratos tipados
│   │   ├── resourcespace_client.py     # SHA256 + update_field(DESCRIPCION)
│   │   ├── blip_processor.py           # VideoAnalyzer + VideoFrameSampler
│   │   ├── clip_processor.py           # CLIPVideoSearcher ViT-B/32
│   │   ├── frame_synthesizer.py        # synthesize() + chat() + reset_chat()
│   │   ├── catalogation_result.py      # Bloque cronológico [MM:SS]
│   │   └── model_paths.py              # Rutas a model_weights/
│   ├── controllers/
│   │   └── catalog_state.py            # CatalogState: eventos y background tasks
│   └── views/
│       ├── theme.py
│       ├── header.py                   # Stepper + pestañas (BLIP/CLIP/Auto/Chat)
│       ├── sidebar.py                  # DAM, hiperparámetros y panel de chat
│       ├── catalog_stats.py
│       ├── search_filter_bar.py
│       ├── video_grid.py
│       ├── blip_workspace.py           # Progreso, bandeja, barras de instalación
│       ├── clip_workspace.py
│       ├── auto_workspace.py           # Auditoría HITL + DESCRIPCION
│       ├── chat_workspace.py           # Burbujas, draft y envío
│       └── upload_modal.py
└── mi_proyecto_streamlit/              # LEGADO STREAMLIT (referencia / producción previa)
```

### Reglas por capa
- **`views/`**: solo `rx.*`. Leen `CatalogState` y disparan eventos. Cero HTTP, cero IA.
- **`controllers/`**: solo `CatalogState(rx.State)`, `@rx.var`, `@rx.event` / `background=True`. Cero layout.
- **`models/`**: dominio e inferencia CPU. Sin `reflex` ni `streamlit`.
- **`runtime/`**: config, repositorio y singletons lazy.

---

## Los 4 flujos en `CatalogState`

### 1. Catalogación BLIP (`run_blip_catalogation` / `run_blip_for_video`)
- Descarga cada video al temp local del SO.
- `VideoFrameSampler` + `generate_caption` en el pool BLIP, con heartbeat ~1 s para que la barra avance.
- Miniatura JPEG Base64 + caption en `analyzed_frames` (`list[dict]`).
- Primera carga: barra de instalación BLIP (`_load_blip_with_install_progress`).

### 2. Búsqueda semántica CLIP (`run_clip_search`)
- `encode_text(query)` una vez; `search_video_stream` por video del ámbito.
- Hits sobre `clip_threshold`, ordenados por `max_score`.
- Primera carga: barra de instalación CLIP.

### 3. Catalogación automatizada (`run_automated_catalogation` / `run_automated_for_video`)
- Alcance: videos seleccionados o ID de colección.
- N captions BLIP por frame (temperatura/top-p progresivos) + `FrameSynthesizer.synthesize()`.
- HITL: editar bloque `[MM:SS]`, exportar JSON o `update_field` en `DESCRIPCION`.
- Primera carga Qwen: barra de instalación GGUF.

### 4. Chat Qwen (`send_chat_message` / `clear_chat`)
- Disponible sin sesión ByteBox (`set_active_module("chat")` no exige `is_connected`).
- Historial `chat_messages: list[dict]` con `role` / `content`. Se recorta (~3200 caracteres) por `n_ctx=2048`.
- `FrameSynthesizer.chat()` arma ChatML y genera en el pool Qwen.
- `clear_chat` vacía la UI y resetea la caché KV. No hay archivo de contexto.

No marcar `is_processing` durante el chat (eso muestra el panel de job de catálogo). Usar `chat_busy`.

---

## API ResourceSpace (`models/resourcespace_client.py`)

| Método | Función API | Uso |
|--------|-------------|-----|
| `get_all_video_ids()` | `do_search` (`restypes=3,4`) | Listado global |
| `get_user_collections()` | `get_user_collections` + `search_public_collections` | Selector de colecciones |
| `get_collection_video_ids(id)` | `do_search` `!collection{id}` | Videos de una colección |
| `download_video(id)` | `get_resource_path` + HTTP | Descarga temporal |
| `cleanup_video(path)` | `os.remove` | Borrado inmediato |
| `update_resource_description(id, value)` | `update_field` `field="DESCRIPCION"` | Metadata revisada |

---

## Cómo ejecutar

### Desarrollo local (Windows PowerShell + `.venv`)

```powershell
$env:NPM_CONFIG_STRICT_SSL="false"
$env:NODE_TLS_REJECT_UNAUTHORIZED="0"
$env:SSL_NO_VERIFY="1"
$env:REFLEX_API_URL="http://localhost:8504"
$env:REFLEX_BACKEND_PORT="8504"
$env:REFLEX_FRONTEND_PORT="8503"
.\.venv\Scripts\python.exe -u -m reflex run --frontend-port 8503 --backend-port 8504
```

Abrir `http://localhost:8503/`.

En esta máquina (OneDrive + sockets Windows) `reflex.exe --no-reload` puede colgarse y el hot-reload puede dejar el backend en `CLOSE_WAIT`. Si `/ping` no responde, matar el árbol del proceso y relanzar en el siguiente puerto libre (`8505`, `8506`, …) actualizando `REFLEX_API_URL`.

### Pesos locales (una vez por entorno)

```bash
python download_model_weights.py --model all --insecure
```

Qwen queda en `mi_proyecto_streamlit/model_weights/qwen2.5-1.5b-instruct-gguf/qwen2.5-1.5b-instruct-q4_k_m.gguf`.

### Producción (Oracle Cloud Ubuntu)
- Systemd: `deploy/reflex_catalog.service`
- Nginx `/IA_videos/`: `deploy/nginx_ia_videos.conf`

---

## Estado de desarrollo

### Implementado
- Dashboard Reflex MVC, paleta ByteBox, credenciales `.env` + `secrets.toml`.
- ResourceSpace SHA256, colecciones y limpieza de videos temporales.
- BLIP, CLIP y catalogación automatizada BLIP+Qwen con barras de primera instalación y progreso por fotograma.
- HITL: JSON + guardado en `DESCRIPCION`.
- Chat Qwen local (mismo GGUF), sin ByteBox; **Nueva conversación** limpia historial y caché KV.
- Deploy `8503`/`8504` bajo `/IA_videos/`.

### Pendiente
- **CLIP — índice persistente** de embeddings en disco.
- **Generación de EDL** CMX 3600 a partir de `clip_hits` y descripciones cronológicas.
