class CLIPVideoSearcher:
    """
    Búsqueda semántica imagen-texto con CLIP ViT-B/32 en CPU.
    Todos los imports pesados (torch, transformers, cv2, PIL) son lazy.
    """

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        import torch
        from transformers import CLIPProcessor, CLIPModel
        from ia_video_app.models.model_paths import (
            CLIP_HUB_ID,
            has_clip_weights,
            resolve_clip_local_dir,
        )

        import os

        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        self.device = "cpu"
        self._torch = torch
        try:
            torch.set_num_threads(1)
        except Exception:
            pass
        local_dir = resolve_clip_local_dir()

        if has_clip_weights():
            load_path = str(local_dir)
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
                "CLIP no está en caché. Ejecute: "
                "python download_model_weights.py --model clip --insecure"
            ) from exc

        self.model.eval()

    @staticmethod
    def _feature_tensor(features):
        if hasattr(features, "pooler_output") and features.pooler_output is not None:
            return features.pooler_output
        return features

    def encode_text(self, query: str):
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
        from ia_video_app.models.blip_processor import VideoFrameSampler

        sampler = VideoFrameSampler(video_path, sample_rate_sec)
        if not sampler.opened:
            yield "00:00", 0, 0, 0.0, False, None
            return
        sampled_index = 0
        try:
            while True:
                sample = sampler.next_sample()
                if sample is None:
                    break
                timestamp, pil_img, thumbnail = sample
                score = self._score_image(pil_img, text_features)
                parts = [int(p) for p in str(timestamp).split(":")]
                if len(parts) == 3:
                    timestamp_sec = parts[0] * 3600 + parts[1] * 60 + parts[2]
                elif len(parts) == 2:
                    timestamp_sec = parts[0] * 60 + parts[1]
                else:
                    timestamp_sec = 0
                yield (
                    timestamp,
                    timestamp_sec,
                    sampled_index,
                    score,
                    (score >= threshold),
                    thumbnail,
                )
                sampled_index += 1
        finally:
            sampler.close()
