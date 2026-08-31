# ─────────────────────────────────────────────────────────────────────────────
# NOTA: Este módulo NO importa torch, transformers, cv2 ni PIL al nivel de
# módulo para ahorrar RAM. Todos los imports pesados se realizan de forma
# lazy (perezosa) dentro de los métodos que los necesitan.
# ─────────────────────────────────────────────────────────────────────────────

def _clip_download_instructions(local_dir: str) -> str:
    return (
        "CLIP no está en caché y no pudo descargarse desde Hugging Face "
        "(red institucional o certificado SSL).\n\n"
        "Ejecute **una sola vez** desde la raíz del proyecto, en PowerShell:\n\n"
        "```powershell\n"
        "python download_model_weights.py --model clip --insecure\n"
        "```\n\n"
        f"Los archivos deben quedar en:\n`{local_dir}`\n\n"
        "Reinicie Streamlit después. Las siguientes búsquedas usarán esos pesos locales."
    )


class CLIPVideoSearcher:
    """
    Búsqueda semántica imagen-texto con CLIP (HuggingFace).
    Todos los imports pesados (torch, transformers, cv2, PIL) son lazy.

    Orden de carga (igual espíritu que BLIP):
    1. Pesos locales en model_weights/ si ya se descargaron antes.
    2. Hub Hugging Face en el primer uso (si la red lo permite).
    """

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        import torch
        from transformers import CLIPProcessor, CLIPModel
        from models.model_paths import (
            CLIP_HUB_ID,
            CLIP_LOCAL_DIR,
            has_clip_weights,
        )

        self.device = "cpu"
        self._torch = torch

        if has_clip_weights():
            load_path = str(CLIP_LOCAL_DIR)
            local_only = True
        else:
            load_path = model_name or CLIP_HUB_ID
            local_only = False

        try:
            self.processor = CLIPProcessor.from_pretrained(
                load_path,
                local_files_only=local_only,
            )
            self.model = CLIPModel.from_pretrained(
                load_path,
                low_cpu_mem_usage=True,
                local_files_only=local_only,
            ).to(self.device)
        except OSError as exc:
            if has_clip_weights():
                raise
            raise RuntimeError(
                _clip_download_instructions(str(CLIP_LOCAL_DIR))
            ) from exc

        self.model.eval()

    @staticmethod
    def _feature_tensor(features):
        """Compat transformers 4.x (tensor) y 5.x (BaseModelOutputWithPooling)."""
        if hasattr(features, "pooler_output") and features.pooler_output is not None:
            return features.pooler_output
        return features

    def encode_text(self, query: str):
        """Devuelve un tensor de features de texto L2-normalizado (CPU)."""
        if not query or not str(query).strip():
            raise ValueError("La consulta de búsqueda no puede estar vacía.")

        inputs = self.processor(
            text=[str(query).strip()],
            return_tensors="pt",
            padding=True,
            truncation=True,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with self._torch.no_grad():
            feat = self._feature_tensor(self.model.get_text_features(**inputs))

        feat = feat / feat.norm(dim=-1, keepdim=True)
        return feat

    def _score_image(self, image, text_features) -> float:
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with self._torch.no_grad():
            img_feat = self._feature_tensor(self.model.get_image_features(**inputs))

        img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
        score = (img_feat @ text_features.T).squeeze()
        return float(score.item())

    def search_video_stream(
        self,
        video_path: str,
        sample_rate_sec: int,
        text_features,
        threshold: float = 0.25,
    ):
        """
        Generador que puntúa fotogramas contra la consulta CLIP.
        Yield: timestamp, timestamp_sec, frame_index, score, is_match, thumbnail.
        La miniatura permite mostrar los fotogramas analizados sin conservar
        el video temporal en disco.
        """
        import cv2
        from PIL import Image

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            yield "00:00", 0, 0, 0.0, False
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 25.0

        frame_interval = max(1, int(fps * sample_rate_sec))
        frame_count = 0
        sampled_index = 0
        success, frame = cap.read()

        while success:
            if frame_count % frame_interval == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)

                score = self._score_image(pil_img, text_features)

                timestamp_sec = int(frame_count / fps)
                m, s = divmod(timestamp_sec, 60)
                h, m = divmod(m, 60)
                timestamp = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

                thumbnail = pil_img.resize((180, 105))
                yield (
                    timestamp,
                    timestamp_sec,
                    sampled_index,
                    score,
                    (score >= threshold),
                    thumbnail,
                )
                sampled_index += 1

            success, frame = cap.read()
            frame_count += 1

        cap.release()
