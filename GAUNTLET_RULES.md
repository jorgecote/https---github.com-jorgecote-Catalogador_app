# GAUNTLET_RULES.md — Reglas Estrictas de Arquitectura, UX y Despliegue (Reflex MVC)

Este documento establece los **Guardrails y Restricciones No Negociables (Gauntlet Constraints)** para la evolución y mantenimiento del sistema de catalogación de video (`IA_video_app` / `Catalogador_app`).

---

## 1. Contexto y Objetivo Principal
- **Stack Objetivo**: Frontend y Backend reactivo en **Reflex** bajo arquitectura **Model-View-Controller (MVC)** estricta.
- **Servidor de Producción**: Oracle Cloud Ubuntu (`/home/ubuntu/IA_video_app`).
- **Aislamiento y Coexistencia**: Ejecución dentro de un entorno virtual aislado (`venv` / `.venv`), administrado por **Systemd** en el puerto `8503` (frontend) / `8504` (backend) y publicado tras **Nginx** bajo el subpath `/IA_videos/`.
- **Objetivo UX**: Interfaz intuitiva, fluida y altamente responsiva para usuarios de primera vez, conservando la paleta institucional de ByteBox / ResourceSpace y **prohibiendo estrictamente tonos neón**.

---

## 2. Restricciones No Negociables (Gauntlet Guardrails)

### A. Restricciones de Entorno, Hardware y Aislamiento
1. **Ejecución Aislada**:
   - Todo el código, paquetes y scripts de ejecución DEBEN residir dentro del entorno virtual del proyecto (`/home/ubuntu/IA_video_app/venv/` en producción o `.venv/` en desarrollo local).
   - Queda prohibido instalar dependencias globales en el sistema operativo anfitrión.
2. **Inferencia 100% en CPU y Baja Memoria**:
   - Hardware objetivo: 4–12 GB de RAM, **sin GPU**.
   - Siempre forzar `device="cpu"`, `low_cpu_mem_usage=True` y `n_gpu_layers=0` (en `llama-cpp-python`).
   - Todos los imports pesados (`torch`, `transformers`, `cv2`, `PIL`, `llama_cpp`) DEBEN ser **lazy** (dentro de métodos o inicializadores invocados bajo demanda).
3. **Limpieza Inmediata de Archivos Temporales**:
   - Todo video descargado en `temp_videos/` debe eliminarse inmediatamente en un bloque `try / finally` mediante `cleanup_video`. Prohibido dejar residuos en disco.
4. **Compatibilidad con Proxy Reverso Nginx (`/IA_videos/`)**:
   - `rxconfig.py` y el servicio Systemd deben soportar despliegue bajo el subpath `/IA_videos/` en el puerto `8503`, garantizando que el canal WebSocket `/_event` y `/_upload` funcionen sin romper llamadas del cliente.

### B. Restricciones Arquitectónicas y Calidad de Código (MVC Estricto)
5. **Separación de Capas MVC**:
   - `ia_video_app/models/`: Esquemas de datos (`@dataclass`), conectores API (`ResourceSpaceAPI`, `ResourceSpaceRepository`) y procesadores de IA (`BLIP`, `CLIP`, `Qwen GGUF`). **Cero dependencias del framework UI**.
   - `ia_video_app/controllers/`: Clases de estado (`CatalogState(rx.State)`), manejadores de eventos (`@rx.event`), tareas en segundo plano (`@rx.event(background=True)`) y lógica de negocio. **PROHIBIDO incluir componentes visuales o código de layout UI en los controladores**.
   - `ia_video_app/views/`: Componentes visuales puros (`header.py`, `sidebar.py`, `catalog_stats.py`, `search_filter_bar.py`, `video_grid.py`, `blip_workspace.py`, `clip_workspace.py`, `auto_workspace.py`, `upload_modal.py`). Las vistas **SOLO leen variables reactivas del estado y disparan eventos del controlador**.
   - `ia_video_app/runtime/`: Configuración de credenciales (`.env` con fallback a `.streamlit/secrets.toml`), factory del repositorio y registro singleton lazy de modelos IA.
6. **Cero Código Espagueti Inline**:
   - Toda vista nueva o modificación debe dividirse en componentes modulares y reutilizables dentro de `ia_video_app/views/`.

### C. Guardrails de Diseño UI/UX y Paleta de Colores
7. **Prohibición Estricta de Colores Neón**:
   - Quedan **estrictamente prohibidos** los verdes eléctricos/neón, fucsias/hot pinks, cianes brillantes o azules fluorescentes.
   - **Paleta Institucional Obligatoria (`ia_video_app/views/theme.py`)**:
     - Superficies claras: `#F8F9FA` (fondo base), `#FFFFFF` (tarjetas), `#EDF2F7` (superficie sutil).
     - Sidebar oscuro: `#33373B` (base), `#26292C` (profundo), `#2B2F33` (tarjetas laterales).
     - Acentos corporativos: `#1B75BB` (azul primario), `#145D94` (hover), `#0E446D` (marino), `#3B2A59` (violeta ByteBox).
     - Estados semánticos sobrios (WCAG AA): Éxito `#14532D`, Advertencia `#78350F`, Error `#7F1D1D`, Info `#1E3A5F`.
8. **Experiencia para Usuarios de Primera Vez (First-Time UX)**:
   - **Jerarquía visual clara**: Barra superior de métricas (`catalog_stats.py`), navegación clara entre los 3 módulos y stepper de 4 pasos (`Conectar` → `Seleccionar` → `Procesar` → `Resultados`).
   - **Empty States guiados**: Tarjetas informativas con botones de llamada a la acción (CTA) claros cuando no hay sesión activa o cuando un filtro no arroja resultados.
   - **Micro-interacciones fluidas**: Skeleton loaders (`rx.skeleton`) durante cargas de red, barras de progreso en tiempo real y notificaciones `rx.toast` para cada acción completada o error.

---

## 3. Lista de Verificación Obligatoria (Gauntlet Verification Checklist)

Antes de aprobar cualquier cambio o despliegue, verificar:
- [ ] ¿Existe algún componente visual o código de layout UI dentro de `controllers/` o `models/`? (**Debe ser NO**).
- [ ] ¿Existe algún color neón en `views/theme.py` o en estilos inline? (**Debe ser NO**).
- [ ] ¿Es compatible la configuración con el proxy reverso Nginx en `/IA_videos/` (puerto `8503` / backend `8504`)? (**Debe ser SÍ**).
- [ ] ¿Están incluidos los empty states guiados, skeleton loaders y notificaciones toast? (**Debe ser SÍ**).
- [ ] ¿Se eliminan los videos temporales en bloques `finally` y las miniaturas se transmiten en memoria (Data URI Base64)? (**Debe ser SÍ**).
- [ ] ¿La escritura de metadata en ResourceSpace utiliza la función `update_field` sobre el campo fijo `DESCRIPCION`? (**Debe ser SÍ**).
