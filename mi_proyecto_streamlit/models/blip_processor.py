# ─────────────────────────────────────────────────────────────────────────────
# NOTA: Este módulo NO importa torch, transformers, cv2 ni PIL al nivel de
# módulo para ahorrar RAM. Todos los imports pesados se realizan de forma
# lazy (perezosa) dentro de los métodos que los necesitan.  El intérprete de
# Python cachea automáticamente los módulos ya cargados en sys.modules, por
# lo que el coste de la importación se paga una única vez por proceso.
# ─────────────────────────────────────────────────────────────────────────────

class VideoAnalyzer:
    """
    Se encarga del procesamiento de video y la inferencia de Inteligencia Artificial
    para generar descripciones de fotogramas usando el modelo BLIP.
    Todos los imports pesados (torch, transformers, cv2, PIL) son lazy:
    se cargan únicamente cuando el usuario activa el pipeline de catalogación.
    """

    def __init__(self, model_name: str = "Salesforce/blip-image-captioning-base"):
        """
        Inicializa el modelo BLIP optimizado para CPU y baja memoria.
        Los imports de torch y transformers se realizan aquí, en el momento
        en que @st.cache_resource llama a esta función por primera vez.
        """
        # Lazy import: torch y transformers se cargan SOLO al instanciar el analizador
        import torch
        from transformers import BlipProcessor, BlipForConditionalGeneration

        # Forzar CPU explícitamente
        self.device = "cpu"
        self._torch = torch  # Guardar referencia para reutilizarla en generate_caption

        # Cargar el procesador (tokenizador + feature extractor)
        self.processor = BlipProcessor.from_pretrained(model_name)

        # low_cpu_mem_usage=True evita picos de memoria durante la carga de pesos
        self.model = BlipForConditionalGeneration.from_pretrained(
            model_name,
            low_cpu_mem_usage=True
        ).to(self.device)

    def generate_caption(self, image, generation_kwargs: dict = None) -> str:
        """
        Infiere la descripción de una única imagen usando BLIP.
        Recibe un objeto PIL.Image ya construido por process_video_stream.
        """
        if generation_kwargs is None:
            generation_kwargs = {"num_beams": 1, "do_sample": False}

        inputs = self.processor(image, return_tensors="pt").to(self.device)

        # torch.no_grad() evita que el grafo de gradientes consuma RAM extra
        with self._torch.no_grad():
            out = self.model.generate(**inputs, max_new_tokens=50, **generation_kwargs)

        caption = self.processor.decode(out[0], skip_special_tokens=True)
        return caption

    def process_video_stream(self, video_path: str, sample_rate_sec: int, generation_kwargs: dict = None):
        """
        Generador que lee el video fotograma a fotograma y emite (yield)
        progresivamente los resultados para no acumular todos los frames en RAM.
        cv2 y PIL se importan aquí de forma lazy.
        """
        # Lazy import: cv2 y PIL se cargan solo cuando se procesa un video
        import cv2
        from PIL import Image

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            yield "00:00", "Error: No se pudo abrir el video.", None
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 25.0

        frame_interval = max(1, int(fps * sample_rate_sec))
        frame_count = 0
        success, frame = cap.read()

        while success:
            if frame_count % frame_interval == 0:
                # Convertir frame BGR → RGB → PIL
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)

                # Generar descriptor con el modelo BLIP
                caption = self.generate_caption(pil_img, generation_kwargs)

                # Calcular marca de tiempo legible
                seconds = int(frame_count / fps)
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                timestamp = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

                # Miniatura compacta para la bandeja de colección
                thumb = pil_img.resize((180, 105))
                yield timestamp, caption, thumb

            success, frame = cap.read()
            frame_count += 1

        cap.release()

    def process_video(self, video_path: str, sample_rate_sec: int = 5, generation_kwargs: dict = None) -> list:
        """
        Versión no-generador para scripts y tests.
        Devuelve una lista de strings '[timestamp] caption'.
        """
        results = []
        for timestamp, caption, _ in self.process_video_stream(video_path, sample_rate_sec, generation_kwargs):
            results.append(f"[{timestamp}] {caption}")
        return results
