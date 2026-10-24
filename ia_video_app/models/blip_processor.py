class VideoFrameSampler:
    """Extrae fotogramas de muestreo sin ejecutar BLIP. OpenCV debe usarse en un solo hilo."""

    def __init__(self, video_path: str, sample_rate_sec: int):
        import cv2
        from PIL import Image

        self._cv2 = cv2
        self._Image = Image
        self.cap = cv2.VideoCapture(str(video_path))
        self.opened = bool(self.cap.isOpened())
        fps = self.cap.get(cv2.CAP_PROP_FPS) if self.opened else 0.0
        self.fps = fps if fps and fps > 0 else 25.0
        self.total_frames = (
            int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) if self.opened else 0
        )
        self.frame_interval = max(1, int(self.fps * max(1, int(sample_rate_sec))))
        self.duration_sec = (
            int(self.total_frames / self.fps) if self.total_frames else 0
        )
        if self.total_frames > 0:
            self.sample_count = (
                self.total_frames + self.frame_interval - 1
            ) // self.frame_interval
        else:
            self.sample_count = 0
        self._frame_count = 0
        self._success = False
        self._frame = None
        if self.opened:
            self._success, self._frame = self.cap.read()

    def next_sample(self):
        if not self.opened:
            return None
        while self._success:
            if self._frame_count % self.frame_interval == 0:
                frame_rgb = self._cv2.cvtColor(self._frame, self._cv2.COLOR_BGR2RGB)
                pil_img = self._Image.fromarray(frame_rgb)
                seconds = int(self._frame_count / self.fps)
                minutes, secs = divmod(seconds, 60)
                hours, minutes = divmod(minutes, 60)
                timestamp = (
                    f"{hours:02d}:{minutes:02d}:{secs:02d}"
                    if hours > 0
                    else f"{minutes:02d}:{secs:02d}"
                )
                thumb = pil_img.resize((180, 105))
                self._success, self._frame = self.cap.read()
                self._frame_count += 1
                return timestamp, pil_img, thumb
            self._success, self._frame = self.cap.read()
            self._frame_count += 1
        return None

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None


class VideoAnalyzer:
    """
    Procesamiento de video e inferencia de descripciones con BLIP en CPU.
    Todos los imports pesados (torch, transformers, cv2, PIL) son lazy.
    """

    def __init__(self, model_name: str = "Salesforce/blip-image-captioning-base"):
        import torch
        from transformers import BlipProcessor, BlipForConditionalGeneration
        from ia_video_app.models.model_paths import (
            has_blip_weights,
            resolve_blip_local_dir,
        )

        import os

        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        self.device = "cpu"
        self._torch = torch
        try:
            torch.set_num_threads(1)
        except Exception:
            pass

        local_ready = has_blip_weights()
        local_dir = resolve_blip_local_dir()
        load_path = str(local_dir) if local_ready else model_name

        try:
            self.processor = BlipProcessor.from_pretrained(
                load_path,
                local_files_only=local_ready,
            )
            self.model = BlipForConditionalGeneration.from_pretrained(
                load_path,
                low_cpu_mem_usage=True,
                local_files_only=local_ready,
            ).to(self.device)
            self.model.eval()
        except OSError as exc:
            if local_ready:
                raise RuntimeError(
                    f"Los pesos locales de BLIP están incompletos en `{local_dir}`."
                ) from exc
            raise RuntimeError(
                "No se pudo descargar BLIP. Ejecute:\n"
                "python download_model_weights.py --model blip --insecure"
            ) from exc

    def generate_caption(self, image, generation_kwargs: dict = None) -> str:
        if generation_kwargs is None:
            generation_kwargs = {"num_beams": 1, "do_sample": False}

        inputs = self.processor(image, return_tensors="pt").to(self.device)
        with self._torch.no_grad():
            out = self.model.generate(**inputs, max_new_tokens=50, **generation_kwargs)

        return self.processor.decode(out[0], skip_special_tokens=True)

    def generate_sampling_captions(
        self,
        image,
        count: int = 3,
        temperature: float = 0.8,
        top_p: float = 0.9,
    ) -> list[str]:
        count = max(1, int(count))
        captions = []
        for sample_index in range(count):
            sample_temperature = min(0.9, max(0.6, temperature + sample_index * 0.02))
            sample_top_p = min(0.95, max(0.85, top_p + sample_index * 0.02))
            caption = self.generate_caption(
                image,
                {
                    "do_sample": True,
                    "num_beams": 1,
                    "temperature": sample_temperature,
                    "top_p": sample_top_p,
                },
            )
            captions.append(caption)
        return captions

    def process_video_stream(
        self, video_path: str, sample_rate_sec: int, generation_kwargs: dict = None
    ):
        sampler = VideoFrameSampler(video_path, sample_rate_sec)
        if not sampler.opened:
            yield "00:00", "Error: No se pudo abrir el video.", None
            return
        try:
            while True:
                sample = sampler.next_sample()
                if sample is None:
                    break
                timestamp, pil_img, thumb = sample
                caption = self.generate_caption(pil_img, generation_kwargs)
                yield timestamp, caption, thumb
        finally:
            sampler.close()

    def process_video_sampling_stream(
        self,
        video_path: str,
        sample_rate_sec: int,
        caption_count: int = 3,
        temperature: float = 0.8,
        top_p: float = 0.9,
    ):
        import cv2
        from PIL import Image

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            yield "00:00", [], None
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_interval = max(1, int(fps * sample_rate_sec))
        frame_count = 0
        success, frame = cap.read()

        while success:
            if frame_count % frame_interval == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                samples = self.generate_sampling_captions(
                    pil_img,
                    count=caption_count,
                    temperature=temperature,
                    top_p=top_p,
                )
                timestamp_sec = int(frame_count / fps)
                minutes, seconds = divmod(timestamp_sec, 60)
                hours, minutes = divmod(minutes, 60)
                timestamp = (
                    f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    if hours > 0
                    else f"{minutes:02d}:{seconds:02d}"
                )
                yield timestamp, samples, pil_img.resize((320, 180))

            success, frame = cap.read()
            frame_count += 1

        cap.release()
