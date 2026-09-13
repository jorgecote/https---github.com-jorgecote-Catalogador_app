
# Especificación de Requerimientos v5: Módulo de Catalogación Automatizada por Fotogramas con Marcas de Tiempo y Conexión a ResourceSpace

**Metodología:** Spec-Driven Development (SDD)

Implementar un nuevo flujo de trabajo dentro de Streamlit en `pages/03_Catalogacion_Automatizada.py` que **reutilice los módulos y funciones existentes** (descarga/borrado temporal de archivos de ResourceSpace y consumo de BLIP). El módulo debe permitir configurar el intervalo de muestreo de fotogramas, registrar sus marcas de tiempo (*timestamps*), **mostrar una traza visual auditable por cada fotograma** (fotograma + descripciones crudas de BLIP + síntesis del LLM) y generar una **descripción cronológica unificada**. Al finalizar, el usuario podrá revisar, editar y decidir si desea escribir este resultado en la metadata del MAM.

---

## 1. Contexto de Arquitectura, Reutilización e Interfaz

* **Principio de Reutilización de Código (DRY):**
* Reutilizar directamente las funciones ya creadas en el proyecto para:
* Autenticación y llamadas a la API de **ResourceSpace**.
* Descarga temporal de videos al almacenamiento local y su posterior eliminación obligatoria (`try/finally`).
* Inicialización y ejecución del modelo **BLIP** (extendiendo la función para soportar el modo *sampling*).




* **Navegación:**
* Crear la nueva página `pages/03_Catalogacion_Automatizada.py` en el proyecto Streamlit.
* Incluir un botón de acceso directo desde la página principal de consulta hacia esta nueva vista.


* **Estilo Visual:**
* Mantener la misma paleta de colores, estructura de barras laterales, tarjetas y contenedores CSS de la aplicación base.



---

## 2. Requerimientos Funcionales (FR)

### **FR-1: Selección de Alcance e Intervalo de Muestreo**

* Permitir al usuario seleccionar en la interfaz:
* **Modo A:** Colección completa de ResourceSpace (ingresando `collection_id`).
* **Modo B:** Recursos/videos individuales del MAM.


* **Frecuencia de Muestreo Configurable:**
* Incluir un control (`st.slider` o `st.number_input`) para elegir la tasa de extracción de fotogramas (ej. *extraer 1 fotograma cada X segundos* o *cada N frames*).



### **FR-2: Reutilización del Manejo de Archivos Temporales**

* Usar la infraestructura existente para:
1. Descargar el archivo de video desde ResourceSpace al disco local temporal (`./temp/`).
2. Extraer los fotogramas y sus metadatos.
3. **Eliminación limpia:** Garantizar la eliminación del archivo de video y fotogramas temporales del disco local una vez finalizado el procesamiento.



### **FR-3: Muestreo de Fotogramas con Marcas de Tiempo (Timestamps)**

* Cada fotograma extraído debe registrar su posición en la línea de tiempo del video en formato estándar `[HH:MM:SS]` o `[MM:SS]`.

### **FR-4: Inferencia Múltiple por Sampling (BLIP Reutilizado)**

* Reutilizar la función de carga de BLIP existente y ejecutarla en modo *sampling* generando $N$ descripciones (por defecto $N=3$) por fotograma variando hiperparámetros (`temperature` $0.6 - 0.9$, `top_p` $0.85 - 0.95$).

### **FR-5: Síntesis de Fotograma mediante LLM Ligero en CPU**

* Integrar un motor de inferencia liviano para CPU (ej. `llama-cpp-python` con modelos cuantiados GGUF a 4-bits como `Qwen2.5-1.5B-Instruct` o `SmolLM2-1.7B-Instruct`).
* El LLM procesará las $N$ descripciones de BLIP correspondientes a un mismo fotograma y las unificará en una sola frase coherente, objetiva y en español.

### **FR-6: Visualización Detallada por Fotograma (Traza Auditable)**

* Durante o al finalizar el procesamiento, la interfaz debe mostrar una **sección desplegable o tarjeta individual por cada fotograma analizado** conteniendo:
1. **Marca de tiempo y fotograma:** Imagen del frame extraído con su etiqueta `[HH:MM:SS]`.
2. **Muestras crudas de BLIP:** Lista de las $N$ descripciones generadas por BLIP.
3. **Síntesis del LLM:** La descripción unificada resultante para ese fotograma específico.



### **FR-7: Consolidación de la Descripción Cronológica**

* Concatenar las salidas del LLM de todos los fotogramas en un **único bloque de texto estructurado cronológicamente**:
```text
[00:00:05] Plano general de una calle transitada con vehículos y peatones.
[00:00:15] Un sujeto con chaqueta azul camina frente a un establecimiento comercial.
[00:00:30] Primer plano del entrevistado en un entorno de oficina.

```



### **FR-8: Revisión Humana Final y Sincronización Opcional con ResourceSpace (*Human-in-the-Loop*)**

* La actualización de la metadata en el MAM **es totalmente diferida y opcional**.
* Al terminar el análisis, la interfaz desplegará un campo de texto editable (`st.text_area`) precalentado con la descripción cronológica unificada completa para la revisión final del usuario.
* **Acciones del Usuario:**
* **"Guardar en Metadata de ResourceSpace":** Reutiliza el cliente API de ResourceSpace e invoca `update_resource_field` para actualizar el texto editado en el campo de descripción del recurso.
* **"Omitir / Descartar":** Mantiene intacta la metadata original del recurso en el MAM.
* **"Exportar Localmente":** Descarga un archivo en formato JSON o TXT con los resultados.



---

## 3. Requerimientos No Funcionales (NFR)

* **NFR-1 (Refactorización y Modularidad):**
* Extraer/importar funciones compartidas de la página principal hacia un módulo helper (ej. `utils/mam_utils.py` o `utils/blip_utils.py`) para evitar duplicidad de código.


* **NFR-2 (Gestión de Memoria y Limpieza):**
* Garantizar la eliminación de archivos temporales mediante bloques `try/finally`.
* Mantener el uso de `@st.cache_resource` y *lazy loading* para evitar excesos en el consumo de RAM en CPU.


* **NFR-3 (Feedback de Progreso):**
* Mostrar barras de progreso (`st.progress`, `st.status`) que informen la fase actual: *Descarga temporal ➔ Extracción ➔ Muestreo BLIP ➔ Síntesis LLM ➔ Limpieza*.



---

## 4. Tareas de Implementación para el Agente AI (Checklist)

```text
- [ ] Refactorizar/importar funciones existentes de descarga, borrado temporal y API de ResourceSpace desde el módulo común.
- [ ] Refactorizar/importar la función de inferencia de BLIP para permitir el parámetro de sampling (N descripciones).
- [ ] Crear la vista `pages/03_Catalogacion_Automatizada.py`.
- [ ] Agregar el selector de frecuencia de muestreo de fotogramas (ej. cada N segundos).
- [ ] Implementar la extracción de fotogramas con registro de marcas de tiempo [HH:MM:SS].
- [ ] Configurar `llama-cpp-python` para sintetizar las N descripciones de BLIP por fotograma en CPU.
- [ ] Construir el componente visual por fotograma: Fotograma + N muestras BLIP + Síntesis LLM.
- [ ] Concatenar la salida en el formato cronológico "[HH:MM:SS] Descripción...".
- [ ] Crear la interfaz de revisión final con `st.text_area` editable.
- [ ] Conectar la acción de guardado con la API de ResourceSpace (`update_resource_field`).
- [ ] Validar que la descarga y limpieza de archivos temporales funcione sin dejar residuos en disco.

```