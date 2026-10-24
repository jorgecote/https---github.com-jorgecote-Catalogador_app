# ByteBox | Catalogador de Video AI

Dashboard en **Python + Reflex** que se conecta a **ResourceSpace (ByteBox / MAM)** para catalogar videos con IA **100 % en CPU** (sin GPU, 4–12 GB RAM).

La app principal vive en `ia_video_app/`. El árbol `mi_proyecto_streamlit/` se conserva como referencia del sistema Streamlit previo.

| Módulo | Modelo | Para qué sirve | ¿Requiere ByteBox? |
|--------|--------|----------------|--------------------|
| **Catalogación BLIP** | Salesforce BLIP base | Descripciones por fotograma con timestamp y miniatura | Sí |
| **Búsqueda CLIP** | CLIP ViT-B/32 | Encontrar planos con una frase en lenguaje natural | Sí |
| **Catalogación automatizada** | BLIP + Qwen2.5-1.5B GGUF | Texto cronológico auditable y revisión humana | Sí |
| **Chat Qwen** | El mismo GGUF Q4 | Asistente local tipo ChatGPT | No |

Los videos se descargan a una carpeta temporal, se analizan y **se borran al terminar**. Las claves API no van en el código.

---

## Requisitos

- Python 3.10+
- 4–12 GB de RAM, sin GPU
- Node.js (lo usa Reflex para el frontend)
- Acceso de red a ResourceSpace / ByteBox (solo para BLIP, CLIP y catalogación automática)
- Pesos locales de BLIP, CLIP y Qwen (script de descarga)

---

## Inicio rápido

```bash
git clone <url-del-repositorio>
cd Catalogador_app

python -m venv .venv --copies
# Windows:  .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Copie `.env.example` a `.env` y complete las credenciales:

```env
RESOURCESPACE_BASE_URL=https://tu-instancia/resourcespace/api/
RESOURCESPACE_USER=tu_usuario
RESOURCESPACE_PRIVATE_KEY=tu_clave_privada
```

También se acepta el fallback `mi_proyecto_streamlit/.streamlit/secrets.toml` (sección `[resourcespace]`). **No suba `.env` ni `secrets.toml` a Git.**

Descargue los pesos una vez:

```bash
python download_model_weights.py --model all --insecure
```

Arranque local:

```powershell
$env:NPM_CONFIG_STRICT_SSL="false"
$env:NODE_TLS_REJECT_UNAUTHORIZED="0"
$env:REFLEX_API_URL="http://localhost:8504"
.\.venv\Scripts\python.exe -u -m reflex run --frontend-port 8503 --backend-port 8504
```

Abra [http://localhost:8503/](http://localhost:8503/).

---

## Cómo usar cada módulo

### 1. Catalogación BLIP
Conecte a ByteBox, elija colección y videos, ajuste el muestreo (1–30 s) y la estrategia (Greedy / Beam / Sampling). **Iniciar catalogación** genera captions con marca de tiempo. Los resultados quedan en la bandeja inferior (miniatura + texto).

### 2. Búsqueda semántica CLIP
Con la misma sesión, abra **Búsqueda CLIP**, escriba lo que busca (*“persona caminando de noche cerca de un edificio”*), fije umbral (útil: 0.22–0.32) y pulse buscar. Los hits se ordenan por similitud y traen timestamp para un EDL futuro.

### 3. Catalogación automatizada (BLIP + Qwen)
Elija videos o un ID de colección. Cada fotograma produce varias muestras BLIP; Qwen las fusiona en una frase en español. Revise el bloque `[MM:SS]`, exporte JSON u oprima **Guardar en DESCRIPCION** para escribir el campo fijo del MAM.

### 4. Chat Qwen
Pestaña **Chat Qwen**. No hace falta conectar el DAM. El historial está en memoria de sesión (no en un `.txt`). **Nueva conversación** borra los mensajes y la caché interna del modelo.

La primera vez que un modelo corre en la sesión verá una barra de instalación (pesos a RAM). Si combina varios modelos con poca memoria, reinicie la app.

---

## Arquitectura

MVC estricto. Las vistas no llaman a la API ni cargan modelos; el controlador orquesta; los modelos son agnósticos a Reflex.

```text
ia_video_app/
├── ia_video_app.py          # Ruta / y rx.match de módulos
├── controllers/             # CatalogState (eventos y jobs en background)
├── models/                  # ResourceSpace, BLIP, CLIP, Qwen, esquemas
├── runtime/                 # .env, repositorio, singletons CPU
└── views/                   # UI ByteBox (cero neón)
```

Documentación para agentes y reglas de capa: [`agents.md`](agents.md) · [`GAUNTLET_RULES.md`](GAUNTLET_RULES.md) · [`sdd.md`](sdd.md).

---

## Despliegue

Producción prevista: Oracle Cloud Ubuntu, venv aislado, Systemd + Nginx en `/IA_videos/`.

| Pieza | Archivo |
|-------|---------|
| Unidad Systemd | [`deploy/reflex_catalog.service`](deploy/reflex_catalog.service) |
| Nginx (HTTP + WebSocket `/_event`) | [`deploy/nginx_ia_videos.conf`](deploy/nginx_ia_videos.conf) |
| Puertos | frontend `8503`, backend `8504` |
| Variables | `REFLEX_FRONTEND_PATH=/IA_videos` (ver `.env.example`) |

---

## Hoja de ruta

- Índice persistente de embeddings CLIP (evitar re-escaneo en cada búsqueda).
- Exportación de EDL CMX 3600 desde `clip_hits` y descripciones cronológicas.

---

## Problemas frecuentes

| Síntoma | Qué revisar |
|---------|-------------|
| No conecta a ByteBox | `.env` o `secrets.toml` con `base_url`, `user` y `private_key` |
| CLIP o Auto piden conexión | Conectar primero desde BLIP (el chat no lo necesita) |
| Falta Qwen | `python download_model_weights.py --model qwen --insecure` |
| App lenta o se cierra | Poca RAM; no deje BLIP+CLIP+Qwen cargados a la vez |
| CLIP sin resultados / demasiado ruido | Bajar o subir el umbral (0.22–0.32) |
| Backend local no responde `/ping` | En Windows, relanzar Reflex; el socket del backend puede quedar colgado |

---

## Licencia y secretos

Este repositorio no incluye pesos de modelos ni credenciales. Use `.env.example` y `download_model_weights.py`. No commitee `.env`, `secrets.toml`, `.web/`, `.states/` ni `model_weights/`.
