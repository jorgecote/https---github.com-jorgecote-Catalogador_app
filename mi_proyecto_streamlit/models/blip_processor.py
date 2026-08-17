import cv2
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

class VideoAnalyzer:
    """
    Se encarga del procesamiento de video y la inferencia de Inteligencia Artificial
    para generar descripciones de fotogramas usando el modelo BLIP.
    """
    def __init__(self, model_name: str = "Salesforce/blip-image-captioning-base"):
        """
        Inicializa el modelo BLIP optimizado para CPU y baja memoria,
        cumpliendo estrictamente con las restricciones de hardware.
        """
        # Restricción: Forzar a CPU explícitamente
        self.device = "cpu"
        
        # Cargar el procesador (tokenizador + feature extractor)
        self.processor = BlipProcessor.from_pretrained(model_name)
        
        # Restricción: low_cpu_mem_usage=True para evitar picos de memoria en la carga
        self.model = BlipForConditionalGeneration.from_pretrained(
            model_name, 
            low_cpu_mem_usage=True
        ).to(self.device)

    def generate_caption(self, image: Image.Image, generation_kwargs: dict = None) -> str:
        """
        Infiere la descripción de una única imagen usando BLIP.
        """
        if generation_kwargs is None:
            generation_kwargs = {"num_beams": 1, "do_sample": False}
            
        inputs = self.processor(image, return_tensors="pt").to(self.device)
        
        # Usar torch.no_grad() es obligatorio para evitar que el grafo de gradientes
        # consuma la memoria RAM disponible durante la inferencia
        with torch.no_grad():
            out = self.model.generate(**inputs, max_new_tokens=50, **generation_kwargs)
            
        caption = self.processor.decode(out[0], skip_special_tokens=True)
        return caption

    def process_video_stream(self, video_path: str, sample_rate_sec: int, generation_kwargs: dict = None):
        """
        Generador que lee el video fotograma a fotograma, calcula la marca de tiempo,
        y arroja (yield) progresivamente los resultados (timestamp, caption).
        Esto ahorra memoria RAM al no cargar todos los fotogramas en una lista.
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            yield "00:00", "Error: No se pudo abrir el video."
            return
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or not fps:
            fps = 25.0 
            
        frame_interval = int(fps * sample_rate_sec)
        if frame_interval <= 0:
            frame_interval = 1
            
        frame_count = 0
        success, frame = cap.read()
        
        while success:
            if frame_count % frame_interval == 0:
                # Convertir imagen para BLIP
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                
                # Generar texto
                caption = self.generate_caption(pil_img, generation_kwargs)
                
                # Calcular marca de tiempo
                seconds = int(frame_count / fps)
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                if h > 0:
                    timestamp = f"{h:02d}:{m:02d}:{s:02d}"
                else:
                    timestamp = f"{m:02d}:{s:02d}"
                    
                # Miniatura ligera para la interfaz (ResourceSpace Collection Tray)
                thumb = pil_img.resize((180, 105))
                yield timestamp, caption, thumb
                
            # Avanzar al siguiente frame
            success, frame = cap.read()
            frame_count += 1
            
        cap.release()

    def process_video(self, video_path: str, sample_rate_sec: int = 5, generation_kwargs: dict = None) -> list:
        """
        Versión no-generador para scripts y tests que devuelve una lista de tuplas (timestamp, caption).
        """
        results = []
        for timestamp, caption, _ in self.process_video_stream(video_path, sample_rate_sec, generation_kwargs):
            results.append(f"[{timestamp}] {caption}")
        return results
