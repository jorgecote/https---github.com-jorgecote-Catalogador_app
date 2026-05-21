# Antigravity Agent Context: Catalogador de Video AI

## 🤖 Perfil y Rol del Agente
Eres un agente desarrollador experto en Python, Streamlit y arquitecturas limpias (MVC). Tu objetivo es codificar, mantener y expandir el sistema de catalogación de video automatizado, conectando el MAM ResourceSpace con los modelos de IA de Hugging Face (BLIP).

---

## 🛑 Restricciones Críticas del Entorno (Léeme Primero)
Para cualquier propuesta de código o refactorización, debes respetar estrictamente estas limitaciones físicas del hardware del usuario:
1. **Hardware Limitado:** El sistema corre en equipos con recursos ajustados (desde 4 GB hasta 12 GB de RAM) y SIN GPU dedicada.
2. **Carga de Modelos de IA:** Al interactuar con `transformers` y `torch`, debes usar obligatoriamente optimizaciones de baja memoria como `low_cpu_mem_usage=True` y forzar el dispositivo a `cpu`.
3. **Persistencia Temporal:** Los videos procesados se descargan de ResourceSpace, se analizan fotograma a fotograma y **deben ser eliminados del disco local inmediatamente** tras generar las descripciones para evitar saturar el almacenamiento.
4. **Almacenamiento en la Nube:** El proyecto vive en una carpeta sincronizada por OneDrive. No uses rutas absolutas hardcodeadas; utiliza rutas relativas basadas en el directorio de ejecución actual para evitar el error `Fatal error in launcher`.

---

## 🏗️ Reglas de la Arquitectura (MVC con Streamlit)
El proyecto no es un script plano de Streamlit. Sigue un patrón estricto de separación de responsabilidades que debes mantener:

### 1. El Controlador (`app.py`)
- Es el punto de entrada principal.
- Orquesta el flujo: lee la configuración, invoca las funciones de la Vista para renderizar la pantalla y llama a los Métodos del Modelo para procesar datos.
- **Regla:** No maneja HTML/Streamlit avanzado directamente, ni calcula firmas criptográficas de APIs.

### 2. Las Vistas (`views/`)
- Módulos puros de interfaz gráfica (`main_page.py`, etc.).
- **Regla:** Solo contienen componentes de Streamlit (`st.button`, `st.dataframe`, etc.). Reciben datos procesados del controlador y devuelven eventos de interacción del usuario. No realizan peticiones HTTP ni cargan modelos de IA.

### 3. Los Modelos (`models/`)
- **`resourcespace_client.py`:** Dividido en `ResourceSpaceAPI` (bajo nivel, maneja firmas SHA256 con `hashlib` y peticiones `requests`) y `ResourceSpaceRepository` (alto nivel, expone métodos de negocio como `get_all_video_ids`).
- **`blip_processor.py` (Pendiente):** Manejará la lógica de extracción de fotogramas (con `Pillow`/`OpenCV`) y la inferencia con BLIP.
- **Regla:** Los modelos son agnósticos a la web. No importan `streamlit` ni modifican la pantalla.

---

## 🔒 Gestión de Credenciales y Secretos
Las claves de acceso a la API de ResourceSpace están automatizadas y protegidas fuera del código fuente. 
- Se leen exclusivamente a través de: `st.secrets["resourcespace"]["base_url" | "user" | "private_key"]`
- El archivo físico se ubica en: `mi_proyecto_streamlit/.streamlit/secrets.toml`
- **Regla:** Jamás escribas contraseñas reales ni las expongas en los logs de la consola.

---

## 📈 Plan de Trabajo y Siguiente Tarea
Cuando el usuario te pida avanzar, tu orden de prioridades actual es:
1. **[FASE ACTUAL]** Diseñar e implementar el módulo de vista `views/selection_panel.py` para listar los IDs recuperados mediante casillas interactivos (checkboxes) y capturar la tasa de muestreo en segundos.
2. Implementar la descarga de archivos multimedia temporales en el repositorio de ResourceSpace.
3. Crear el modelo `models/blip_processor.py` optimizado para CPU.
4. Integrar todo en el controlador (`app.py`).