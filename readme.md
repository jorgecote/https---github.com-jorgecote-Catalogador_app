# ByteBox | Catalogador de Video AI

Aplicación web en **Python + Streamlit** que se conecta a una instancia de **ResourceSpace (ByteBox / MAM)** para catalogar videos con **BLIP** y realizar **búsqueda semántica por lenguaje natural** con **CLIP**, todo en **CPU** y con limpieza automática de archivos temporales.

Este documento resume la arquitectura, las funcionalidades disponibles y los modos de uso paso a paso.

---

## Funcionalidades de la aplicación

La app tiene **dos módulos** accesibles desde la misma sesión de Streamlit:

| Módulo | Pantalla | Modelo IA | Qué hace |
|--------|----------|-----------|----------|
| **Catalogación BLIP** | `app.py` | Salesforce BLIP base | Genera descripciones textuales por fotograma con marca de tiempo |
| **Búsqueda semántica CLIP** | `pages/1_Busqueda_CLIP.py` | OpenAI CLIP ViT-B/32 | Encuentra fotogramas que coinciden con una consulta en lenguaje natural |

Ambos módulos comparten:

- Conexión autenticada a ByteBox (API ResourceSpace con firmas SHA256).
- Selector de **colección activa** (todas las colecciones o una específica).
- Filtro opcional por **ID de video**.
- Descarga temporal de videos → procesamiento → **eliminación inmediata** del archivo local.

---

## Requisitos del entorno

- **Python 3.10+** recomendado.
- **RAM:** 4–12 GB (sin GPU; inferencia 100 % en CPU).
- Acceso de red a la instancia de ResourceSpace / ByteBox.
- Credenciales API válidas en `secrets.toml`.

> **Importante:** BLIP y CLIP pueden coexistir en la misma sesión de Streamlit. Si aparece falta de memoria, reinicia la app (`Ctrl+C` en terminal y vuelve a ejecutar `streamlit run app.py`).

---

## Instalación y puesta en marcha

### 1. Clonar o abrir el proyecto

El repositorio vive en OneDrive. Trabaja siempre desde la carpeta raíz `Catalogador_app`.

### 2. Crear y activar el entorno virtual

```bash
python -m venv .venv --copies
.venv\Scripts\activate
```

En macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Instalar dependencias

Desde la raíz del proyecto:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Las dependencias principales son: `streamlit`, `torch` (CPU), `transformers`, `opencv-python-headless`, `Pillow`, `requests`.

### 4. Configurar credenciales

Crea el archivo `mi_proyecto_streamlit/.streamlit/secrets.toml` (no se sube a git):

```toml
[resourcespace]
base_url = "https://tu-instancia/resourcespace/api/"
user = "tu_usuario"
private_key = "tu_clave_privada"
```

### 5. Ejecutar la aplicación

```bash
cd mi_proyecto_streamlit
streamlit run app.py
```

Se abrirá en el navegador (por defecto `http://localhost:8501`).

**Acceso a los módulos:**

- **Catalogación BLIP:** pantalla principal al iniciar.
- **Búsqueda CLIP:** menú lateral multipage de Streamlit (*Busqueda CLIP*) o botón **🔍 Búsqueda semántica (CLIP)** desde catalogación (requiere estar conectado).

---

## Modo de uso 1 — Catalogación BLIP

### Objetivo

Analizar videos seleccionados fotograma a fotograma y obtener **captions** (descripciones en texto) con **timestamp**, visibles en la bandeja inferior de la interfaz.

### Pasos

1. **Conectar a ByteBox**
   - En la pantalla de inicio, pulsa el botón para conectar.
   - La app autentica contra la API, obtiene la lista de videos y las colecciones disponibles.
   - El sidebar mostrará `● Conectado (N videos disponibles)`.

2. **Definir el ámbito de trabajo**
   - En el sidebar, sección **CONEXIÓN BYTEBOX**, elige:
     - **Todas las colecciones / General** — todos los videos del servidor, o
     - Una **colección específica** — solo los videos de ese rodaje o proyecto.
   - Opcional: en **FILTRAR RECURSOS**, escribe parte de un ID para acotar la lista.

3. **Configurar la inferencia BLIP** (sidebar → **CONFIGURACIÓN IA (BLIP)**)
   - **Tasa de muestreo (segundos/frame):** intervalo entre fotogramas analizados (1–30 s, default 5). Valores bajos = más detalle y más tiempo de CPU.
   - **Estrategia de inferencia:**
     - *Greedy Search* — rápida, recomendada en CPU.
     - *Beam Search* — mayor calidad; ajusta número de ramas (`num_beams`).
     - *Sampling* — más variada; ajusta temperatura y Top-P.

4. **Seleccionar videos**
   - Marca los checkboxes de los recursos a procesar.
   - Usa **☑ Seleccionar todos los videos visibles** para la lista filtrada actual.
   - El contador inferior indica cuántos videos están seleccionados.

5. **Iniciar catalogación**
   - Pulsa **🚀 Iniciar Catalogación AI**.
   - Por cada video: descarga → análisis en vivo (tabla con timestamp + caption) → eliminación del archivo temporal.
   - Al finalizar aparece una notificación y los resultados quedan en la **bandeja de colección** inferior (miniaturas + descripciones).

### Qué obtienes

- Tabla en vivo por video: marca de tiempo + descriptor BLIP.
- Bandeja persistente en sesión con todos los fotogramas analizados (`analyzed_frames`).
- Cada entrada incluye: `video_id`, `timestamp`, `caption`, miniatura.

### Cuándo usar este modo

- Catalogar material nuevo de un rodaje.
- Generar descripciones legibles por humanos para revisión editorial.
- Preparar metadata descriptiva antes de escribir en el MAM (escritura automática aún pendiente).

---

## Modo de uso 2 — Búsqueda semántica CLIP

### Objetivo

Encontrar **fotogramas concretos** dentro de uno o varios videos describiendo en lenguaje natural lo que buscas (ej.: *"una persona caminando de noche cerca de un edificio"*, *"primer plano de un micrófono"*).

CLIP compara el embedding del texto con cada fotograma muestreado y devuelve los que superan un **umbral de similitud**, con timestamp listo para una futura generación de EDL.

### Requisito previo

Debes **conectar primero en catalogación BLIP** en la misma sesión de Streamlit. CLIP reutiliza `conectado`, `video_ids`, `collections` y `selected_collection_id`.

Si entras a CLIP sin conexión, verás un aviso con enlace para volver a catalogación.

### Pasos

1. **Ir al módulo CLIP**
   - Desde catalogación (conectado): **🔍 Búsqueda semántica (CLIP)**, o
   - Menú multipage: **Busqueda CLIP**.

2. **Definir el ámbito** (sidebar CLIP)
   - **Colección activa:** igual que en BLIP (todas o una colección).
   - **Filtrar por ID de video:** opcional, limita la búsqueda a IDs que contengan el texto escrito.

3. **Configurar parámetros CLIP** (sidebar → **CONFIGURACIÓN CLIP**)
   - **Tasa de muestreo:** segundos entre fotogramas evaluados (1–30, default 5).
   - **Umbral de similitud:** 0.15–0.40 (default 0.25). Valores típicos útiles: **0.22 – 0.32**.
     - Umbral bajo → más coincidencias (posibles falsos positivos).
     - Umbral alto → menos coincidencias, más precisas.

4. **Escribir la consulta**
   - En el área de texto, describe lo que buscas en lenguaje natural.
   - Pulsa **🔎 Buscar videos**.
   - CLIP se carga en CPU **solo en este momento** (no al abrir la pantalla).

5. **Revisar resultados**
   - Durante la búsqueda verás el progreso por video (descarga, fotogramas, similitud).
   - Al terminar, la sección **Videos que coinciden** lista los hits ordenados por score máximo.
   - Cada video expandible muestra tabla: tiempo, segundos, índice de frame, similitud CLIP.

### Qué obtienes

Estructura interna `clip_hits` (persiste en sesión):

```python
{
    "video_id": 12345,
    "max_score": 0.3124,
    "match_count": 3,
    "frames": [
        {
            "timestamp": "01:23",
            "timestamp_sec": 83,
            "frame_index": 16,
            "score": 0.3124
        }
    ]
}
```

### Cuándo usar este modo

- Localizar planos concretos sin revisar el video completo a mano.
- Explorar material de un rodaje con preguntas en lenguaje natural.
- Obtener timestamps como base para un EDL o pre-edición (generación de `.edl` aún pendiente).

### Consejos prácticos

- Empieza con umbral **0.25** y muestreo **5 s**; ajusta según resultados.
- Consultas concretas suelen funcionar mejor que frases muy genéricas.
- Buscar en **toda la biblioteca** puede tardar mucho: acota por colección o ID cuando sea posible.
- Si ya catalogaste con BLIP en la misma sesión y hay poca RAM, reinicia Streamlit antes de una búsqueda CLIP larga.

---

## Navegación entre módulos

```text
[Pantalla inicio BLIP]  ──conectar──►  [Catalogación BLIP]
                                              │
                    ◄── Volver a catalogación BLIP ──┤
                                              │
                                              ▼
                                    [Búsqueda semántica CLIP]
```

- BLIP → CLIP: botón en panel de selección (solo si `conectado`).
- CLIP → BLIP: botón en sidebar CLIP o menú multipage.

---

## Arquitectura del software (MVC)

```text
Catalogador_app/
├── .venv/                              # Entorno virtual (local, no en git)
├── requirements.txt                    # Dependencias Python
├── agents.md                           # Guía para agentes IA / mantenimiento
│
└── mi_proyecto_streamlit/
    ├── .streamlit/secrets.toml         # Credenciales (local, no en git)
    ├── app.py                          # Controlador catalogación BLIP
    ├── runtime/
    │   └── repository.py               # Factory get_repository() → API + secrets
    ├── pages/
    │   └── 1_Busqueda_CLIP.py          # Controlador búsqueda CLIP
    ├── models/
    │   ├── resourcespace_client.py     # ResourceSpaceAPI + ResourceSpaceRepository
    │   ├── blip_processor.py           # VideoAnalyzer (BLIP)
    │   └── clip_processor.py           # CLIPVideoSearcher (CLIP ViT-B/32)
    └── views/
        ├── styles.py                   # Tema visual ByteBox
        ├── header.py
        ├── sidebar.py                  # Sidebar BLIP
        ├── main_page.py
        ├── selection_panel.py          # Selección videos + acceso CLIP
        ├── collection_tray.py          # Bandeja resultados BLIP
        ├── search_sidebar.py           # Sidebar CLIP
        ├── search_form.py              # Formulario consulta CLIP
        └── search_results.py           # Resultados CLIP
```

### Reglas de capas

- **views/** — Solo UI Streamlit; reciben datos y devuelven eventos. Sin API ni modelos IA.
- **models/** — Lógica de negocio e IA; sin dependencia de Streamlit.
- **app.py** y **pages/** — Orquestación, `session_state`, carga lazy de modelos.
- **runtime/** — Helpers del controlador (secrets, factory del repositorio).

---

## Seguridad y credenciales

- Las claves API viven únicamente en `mi_proyecto_streamlit/.streamlit/secrets.toml`.
- El código lee credenciales con `st.secrets["resourcespace"]` vía `runtime/repository.py`.
- No hardcodear ni registrar claves en logs o consola.
- Autenticación ResourceSpace: firmado SHA256 en cada petición (`ResourceSpaceAPI`).

---

## Estado del proyecto

### Implementado

- Conexión segura a ResourceSpace / ByteBox.
- Listado y filtrado por **colecciones**.
- Catalogación BLIP con estrategias de inferencia configurables.
- Bandeja de fotogramas analizados con timestamps.
- Búsqueda semántica CLIP por lenguaje natural.
- Navegación multipage BLIP ↔ CLIP con sesión compartida.
- Limpieza automática de videos temporales tras cada procesamiento.

### Pendiente

- **Descripción unificada del video** — consolidar captions BLIP en un resumen global.
- **Escritura de metadata en ResourceSpace** — subir descripciones al MAM automáticamente.
- **Índice persistente de embeddings CLIP** — evitar re-escaneo completo en cada búsqueda.
- **Generación de EDL** — exportar `.edl` a partir de `clip_hits` y/o captions BLIP.
- **Evaluación BLIP-2** — mejor calidad de captioning en CPU (requiere ≥12 GB RAM; no recomendado como reemplazo directo por velocidad).

Para detalle técnico orientado a desarrollo y agentes IA, ver [`agents.md`](agents.md).

---

## Solución de problemas frecuentes

| Problema | Causa probable | Qué hacer |
|----------|----------------|-----------|
| `No se encontraron las credenciales en secrets.toml` | Falta o ruta incorrecta del archivo | Crear `mi_proyecto_streamlit/.streamlit/secrets.toml` con las tres claves |
| CLIP pide conectar primero | Sesión sin conexión BLIP | Volver a `app.py` y conectar a ByteBox |
| App muy lenta o se cierra | Poca RAM con BLIP + CLIP cargados | Reiniciar Streamlit; no ejecutar ambos modelos a la vez si no es necesario |
| Muchos falsos positivos en CLIP | Umbral bajo | Subir umbral (ej. 0.28–0.32) |
| No encuentra nada en CLIP | Umbral alto o consulta vaga | Bajar umbral o usar descripción más específica |
| Error al descargar un video | URL o permisos en ResourceSpace | Verificar ID, permisos de usuario API y tipo de recurso |

---

## Referencia rápida de comandos

```bash
# Activar entorno
.venv\Scripts\activate

# Instalar / actualizar dependencias
python -m pip install -r requirements.txt

# Ejecutar app
cd mi_proyecto_streamlit
streamlit run app.py
```
