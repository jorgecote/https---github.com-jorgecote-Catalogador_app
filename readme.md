```
Este archivo `README.md` sirve como bitácora técnica del proyecto y resume los avances, decisiones arquitectónicas y la configuración actual del entorno para garantizar que cualquier sesión futura pueda retomarse con total claridad.

## 🚀 Contexto y Estado del Proyecto

El objetivo principal es construir una aplicación web ligera que se conecte a una instancia de **ResourceSpace (MAM)** para extraer IDs de videos, descargarlos temporalmente, procesar sus fotogramas secuencialmente con el modelo de Inteligencia Artificial **BLIP (Salesforce/blip-image-captioning-base)** y, tras guardar las descripciones textuales generadas con sus respectivas etiquetas de tiempo, eliminar los archivos temporales de forma segura.

### 📋 Decisiones de Infraestructura y Cambio Tecnológico
**Lenguaje: Python**.
**Framework: Streamlit**.

**Ventajas de Streamlit en este proyecto:**
- **100% Python nativo:** Sin necesidad de Node.js, NPM o compilaciones complejas de JavaScript.
- **Eficiencia en recursos:** Consumo de RAM optimizado y compatibilidad directa con entornos limitados.
- **Velocidad de prototipado:** Renderizado interactivo inmediato mediante un flujo de ejecución lineal guiado por Python.

---

## 🏗️ Arquitectura del Software (MVC)

Para garantizar la mantenibilidad, escalabilidad y orden en el código, el proyecto se estructuró siguiendo estrictamente el patrón de diseño **Modelo-Vista-Controlador (MVC)**:

```text
Catalogador_app/                        # Carpeta raíz general (en OneDrive)
│
├── .venv/                              # Entorno virtual de Python aislado (local por máquina)
│
└── mi_proyecto_streamlit/              # Carpeta raíz del código fuente
    │
    ├── .streamlit/                     # Configuración oculta de Streamlit
    │   └── secrets.toml                # Caja fuerte de credenciales (Variables de entorno)
    │
    ├── app.py                          # CONTROLADOR: Punto de entrada y lógica de negocio
    ├── requirements.txt                # Dependencias del proyecto (Streamlit, Torch, etc.)
    │
    ├── models/                         # MODELO: Lógica de datos, APIs y procesamiento de IA
    │   ├── __init__.py
    │   └── resourcespace_client.py     # API y Repositorio de conexión a ResourceSpace
    │
    └── views/                          # VISTA: Componentes de interfaz de usuario (Frontend)
        ├── __init__.py
        └── main_page.py                # Pantalla principal e interactiva preliminar

```

### Componentes Técnicos Implementados:

1. **La Vista (`views/main_page.py`):** Contiene funciones encargadas exclusivamente del diseño visual (botones, textos, títulos). Captura las interacciones del usuario y las transmite al controlador sin procesar datos internos.
2. **El Controlador (`app.py`):** Es el cerebro de la aplicación. Gestiona el estado de la pantalla, captura los clics de la vista, lee de forma segura las variables del entorno y consume los servicios del modelo para orquestar la aplicación.
3. **El Modelo (`models/resourcespace_client.py`):** Implementado con una separación formal de responsabilidades dividida en dos capas:
* **`ResourceSpaceAPI` (Bajo Nivel):** Administra la seguridad de la red y automatiza el firmado criptográfico de URLs mediante el algoritmo `SHA256` exigido por ResourceSpace, utilizando la librería nativa `hashlib`. Su método genérico `call_function` permite invocar cualquier endpoint de la API.
* **`ResourceSpaceRepository` (Alto Nivel):** Traduce las necesidades del negocio en consultas técnicas. Implementa la lógica para invocar la función `do_search` y limpia la respuesta JSON para extraer únicamente las referencias (`ref`) de los videos disponibles.



---

## 🔒 Gestión de Seguridad (Secrets)

Para automatizar la conexión sin comprometer la seguridad de las credenciales de la plataforma MAM (y evitar el *hardcoding* de llaves privadas en el código), se implementó el sistema nativo de **Streamlit Secrets**.

Las credenciales reales se alojan localmente en cada máquina dentro de la ruta `mi_proyecto_streamlit/.streamlit/secrets.toml` con la siguiente estructura (este archivo está excluido del control de versiones):

```toml
[resourcespace]
base_url = "[https://tu-sistema.resourcespace.com/api/](https://tu-sistema.resourcespace.com/api/)"
user = "tu_usuario"
private_key = "tu_clave_privada_sha256"

```

El controlador lee estos parámetros en tiempo de ejecución de manera transparente mediante `st.secrets["resourcespace"]["..."]`.

---

## 🛠️ Comandos de Inicialización del Entorno

Pasos ejecutados para configurar y levantar el proyecto de forma segura evitando conflictos de sincronización en la nube:

1. **Creación del entorno aislado (evitando enlaces rotos):**
```bash
python -m venv .venv --copies

```


2. **Activación del entorno:**
```bash
.venv\\Scripts\\activate

```


3. **Instalación de dependencias básicas:**
```bash
python -m pip install --upgrade pip
python -m pip install streamlit pillow torch transformers requests

```


4. **Ejecución del servidor de desarrollo:**
```bash
cd mi_proyecto_streamlit
streamlit run app.py

```



---

## 🧭 Próximos Pasos Definidos

Con la infraestructura base, el controlador automatizado y la conexión segura a la API de ResourceSpace ya consolidados, los siguientes pasos del desarrollo son:

1. **Diseño del Panel de Selección (`views/selection_panel.py`):** Transformar el visualizador JSON crudo actual en una interfaz interactiva donde el usuario seleccione mediante casillas los IDs de los videos a procesar y defina mediante un slider la frecuencia temporal de muestreo de fotogramas (ej. un fotograma cada 1, 2 o 5 segundos).
2. **Lógica de Descarga y Borrado Temporal:** Extender el modelo de ResourceSpace para obtener las URLs físicas de los recursos, descargarlos temporalmente al disco local y estructurar la rutina de eliminación inmediata tras el análisis.
3. **Integración del Modelo BLIP:** Desarrollar el componente `models/blip_processor.py` heredando las optimizaciones de baja memoria analizadas con anterioridad (`low_cpu_mem_usage=True`) para procesar los fotogramas y emitir las etiquetas de descripción cronometradas.
"""


```