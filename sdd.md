# Especificación de Requerimientos v6 (SDD): Plataforma de Catalogación de Video AI en Reflex (MVC) y Módulo Automatizado BLIP + Qwen

**Metodología:** Spec-Driven Development (SDD)  
**Arquitectura Objetivo:** Reflex Full-Stack bajo patrón **Model-View-Controller (MVC)** estricto (`ia_video_app/`), manteniendo compatibilidad con el módulo legado en `mi_proyecto_streamlit/`.  
**Reglas de Gobernanza:** Ver [`GAUNTLET_RULES.md`](./GAUNTLET_RULES.md).

---

## 1. Contexto de Arquitectura, Migración a Reflex y Reutilización

- **Arquitectura MVC Estricta en Reflex (`ia_video_app/`):**
  - **`models/`**: Esquemas tipados (`schemas.py`), cliente API con firma SHA256 (`resourcespace_client.py`), y motores de inferencia CPU (`blip_processor.py`, `clip_processor.py`, `frame_synthesizer.py`, `catalogation_result.py`, `model_paths.py`). Cero dependencias de la capa visual.
  - **`controllers/`**: Estado reactivo centralizado en `CatalogState(rx.State)` (`catalog_state.py`), manejadores de eventos y tareas asíncronas en segundo plano (`@rx.event(background=True)`). **Prohibido incluir código de UI layout en los controladores**.
  - **`views/`**: Componentes visuales modulares (`theme.py`, `header.py`, `sidebar.py`, `catalog_stats.py`, `search_filter_bar.py`, `video_grid.py`, `blip_workspace.py`, `clip_workspace.py`, `auto_workspace.py`, `upload_modal.py`).
  - **`runtime/`**: Lector de credenciales `.env` con fallback a `.streamlit/secrets.toml` (`config.py`), factory del repositorio (`repository.py`) y singletons lazy en CPU (`ai_registry.py`).

- **Aislamiento y Despliegue en Servidor Ubuntu (`/home/ubuntu/IA_video_app`):**
  - Ejecución 100% contenida en el entorno virtual aislado (`venv` / `.venv`).
  - Servicio administrado por **Systemd** (`deploy/reflex_catalog.service`) en los puertos `8503` (frontend) y `8504` (backend).
  - Publicación tras proxy reverso **Nginx** (`deploy/nginx_ia_videos.conf`) bajo el subpath `/IA_videos/` con soporte completo para WebSockets (`/_event`).

- **Identidad Visual y UX (Sin Colores Neón):**
  - Mantener la paleta sobria de ByteBox / ResourceSpace (`#F8F9FA`, `#FFFFFF`, `#33373B`, `#1B75BB`, `#0E446D`, `#3B2A59`, badges semánticos con contraste WCAG AA).
  - **Prohibición estricta de tonos neón** (verdes eléctricos, fucsias o cianes brillantes).
  - Incluir *skeleton loaders* durante cargas de datos, *empty states* guiados con CTA para nuevos usuarios y notificaciones *toast* en cada acción.

---

## 2. Requerimientos Funcionales (FR)

### **FR-1: Dashboard Unificado, Selección de Alcance e Intervalo de Muestreo**
- Presentar una barra superior de estadísticas (`Total Videos`, `Categorizados en Sesión`, `Pendientes de Procesar`, `Entorno CPU / Pesos`) y navegación directa entre los 3 módulos:
  1. **Catalogación BLIP**
  2. **Búsqueda Semántica CLIP**
  3. **Catalogación Automatizada (BLIP + Qwen)**
- Permitir definir el alcance de procesamiento:
  - **Modo A:** Selección de videos desde el catálogo filtrable o ingreso directo de `collection_id` de ResourceSpace.
  - **Modo B:** Procesamiento individual rápido desde cada tarjeta de recurso.
- **Frecuencia de Muestreo Configurable:** Selector de intervalo en segundos entre fotogramas ($1 - 30\text{ s}$, por defecto $5\text{ s}$).

### **FR-2: Manejo Seguro de Archivos Temporales y Miniaturas en Memoria**
1. Descargar el archivo de video desde ResourceSpace a la carpeta temporal `./temp_videos/`.
2. Extraer y analizar los fotogramas mediante generadores en Python para no saturar la RAM.
3. Convertir cada miniatura `PIL.Image` en memoria a formato Data URI Base64 (`data:image/jpeg;base64,...`) para su renderizado reactivo en Reflex sin escribir imágenes sueltas en disco.
4. **Eliminación limpia obligatoria:** Garantizar la eliminación inmediata del archivo de video descargado mediante `cleanup_video` dentro de un bloque `try/finally`.

### **FR-3: Muestreo de Fotogramas con Marcas de Tiempo (Timestamps)**
- Cada fotograma extraído debe registrar su posición en la línea de tiempo del video en formato estándar `[MM:SS]` o `[HH:MM:SS]`.

### **FR-4: Inferencia Múltiple por Sampling Progresivo (BLIP)**
- En el módulo de Catalogación Automatizada, ejecutar `VideoAnalyzer.generate_sampling_captions()` generando $N$ descripciones por fotograma (por defecto $N=3$, configurable de $1$ a $5$).
- Variar progresivamente en cada muestra tanto la **temperatura** (`temperature + sample_index * 0.02`, acotada a $[0.60, 0.90]$) como el **núcleo de probabilidad** (`top_p + sample_index * 0.02`, acotado a $[0.85, 0.95]$) para obtener observaciones complementarias sin ruido.

### **FR-5: Síntesis Cohesiva de Fotograma mediante LLM Ligero en CPU (Qwen GGUF)**
- Integrar `llama-cpp-python` en CPU (`n_gpu_layers=0`) cargando el modelo local cuantizado a 4 bits `Qwen2.5-1.5B-Instruct Q4_K_M GGUF` (`qwen2.5-1.5b-instruct-q4_k_m.gguf`).
- **Regla de Prompting del Sintetizador (`FrameSynthesizer.synthesize`):**
  - No limitarse a traducir literalmente ni a enumerar las salidas de BLIP.
  - Usar los elementos que coinciden entre las muestras como estructura principal y conservar también detalles aislados (adjetivos, atmósfera, sentimientos, iluminación, lugar u objetos secundarios) siempre que sean compatibles con la escena y aporten valor descriptivo.
  - Redactar **una única frase original, fluida y coherente en español**, sin inventar elementos no respaldados ni mencionar modelos de IA.

### **FR-6: Visualización Detallada por Fotograma (Traza Auditable)**
- Mostrar por cada recurso procesado el desglose auditable de fotogramas con:
  1. **Miniatura y marca de tiempo** `[MM:SS]`.
  2. **Muestras crudas de BLIP** ($N$ observaciones generadas).
  3. **Síntesis de Qwen** en español.

### **FR-7: Consolidación de la Descripción Cronológica**
- Concatenar las síntesis de todos los fotogramas del recurso en un único bloque cronológico editable:
```text
[00:05] Plano general de una calle transitada con vehículos y peatones bajo luz de tarde.
[00:15] Un sujeto con chaqueta azul camina frente a un establecimiento comercial.
[00:30] Primer plano de una persona hablando en un entorno tranquilo de oficina.
```

### **FR-8: Revisión Humana Final (*Human-in-the-Loop*) y Sincronización con ResourceSpace**
- Desplegar un área de texto editable (`rx.text_area`) precargada con la descripción cronológica consolidada.
- **Acciones disponibles por recurso:**
  - **"Guardar en DESCRIPCION (ResourceSpace)"**: Invoca la función `update_field` de la API de ResourceSpace pasando `resource=<video_id>`, `field="DESCRIPCION"` y `value=<texto_revisado>` (sin pedir IDs de campo técnicos al usuario).
  - **"Restaurar original / Omitir"**: Restaura la síntesis original o mantiene intacta la metadata del MAM.
  - **"Exportar JSON"**: Descarga localmente (`rx.download`) un archivo `catalogacion_<id>.json` con la descripción consolidada y la traza completa por fotograma.

---

## 3. Requerimientos No Funcionales (NFR)

- **NFR-1 (Arquitectura MVC y Modularidad):** Separación estricta entre `models/`, `controllers/`, `views/` y `runtime/`. Ningún controlador puede contener código de interfaz.
- **NFR-2 (Gestión de Memoria en CPU):** Carga lazy mediante singletons en `ai_registry.py` y liberación inmediata de archivos temporales en `try/finally`.
- **NFR-3 (Feedback Reactivo en Tiempo Real):** Actualización progresiva del estado mediante tareas `@rx.event(background=True)` con barra de progreso, contador de recursos, log en vivo y notificaciones `rx.toast`.
- **NFR-4 (Despliegue tras Proxy Reverso):** Configuración lista para Systemd y Nginx bajo `/IA_videos/` en puerto `8503`.

---

## 4. Estado de Implementación (Checklist SDD)

- [x] Reestructurar el proyecto bajo arquitectura MVC en Reflex (`ia_video_app/models`, `controllers`, `views`, `runtime`).
- [x] Implementar soporte de credenciales `.env` con fallback a `.streamlit/secrets.toml`.
- [x] Extender `VideoAnalyzer` (BLIP) para muestreo múltiple con variación progresiva de `temperature` y `top_p`.
- [x] Integrar `FrameSynthesizer` con `Qwen2.5-1.5B-Instruct Q4_K_M GGUF` en CPU y prompt de síntesis cohesiva.
- [x] Construir `CatalogState(rx.State)` con los 3 pipelines en background (BLIP, CLIP y Automatizada Qwen).
- [x] Construir las vistas modulares con paleta neutra ByteBox (sin colores neón), skeleton loaders, empty states y modal de subida.
- [x] Conectar la acción de guardado con la API de ResourceSpace mediante `update_field` en el campo fijo `DESCRIPCION`.
- [x] Generar configuración de producción (`rxconfig.py`, `deploy/reflex_catalog.service` y `deploy/nginx_ia_videos.conf`) para puerto `8503` y subpath `/IA_videos/`.
