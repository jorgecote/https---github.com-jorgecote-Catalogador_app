class FrameSynthesizer:
    """Sintetiza captions BLIP usando Qwen GGUF cuantizado en CPU."""

    def __init__(self, model_path=None, n_ctx: int = 2048):
        from ia_video_app.models.model_paths import (
            has_qwen_gguf,
            resolve_qwen_gguf_file,
        )

        resolved_path = model_path or resolve_qwen_gguf_file()
        if not model_path and not has_qwen_gguf():
            raise RuntimeError(
                "No se encontró Qwen GGUF. Ejecute `python download_model_weights.py --model qwen` "
                f"y verifique `{resolved_path}`."
            )

        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "Falta llama-cpp-python. Instale las dependencias con "
                "`python -m pip install -r requirements.txt`."
            ) from exc

        self._llm = Llama(
            model_path=str(resolved_path),
            n_ctx=n_ctx,
            n_gpu_layers=0,
            verbose=False,
        )

    def reset_chat(self) -> None:
        """Limpia la caché KV de llama.cpp para no arrastrar turnos anteriores."""
        reset = getattr(self._llm, "reset", None)
        if callable(reset):
            reset()
            return
        ctx = getattr(self._llm, "_ctx", None)
        clear = getattr(ctx, "kv_cache_clear", None) if ctx is not None else None
        if callable(clear):
            clear()

    def synthesize(self, captions: list[str]) -> str:
        cleaned = [str(caption).strip() for caption in captions if str(caption).strip()]
        if not cleaned:
            return "No se obtuvo una descripción para este fotograma."

        samples = "\n".join(f"- {caption}" for caption in cleaned)
        prompt = f"""<|im_start|>system
Eres un redactor experto en catalogación audiovisual. Las descripciones que
recibirás son observaciones alternativas del mismo fotograma, no texto para
traducir ni una lista que debas repetir. Compáralas, usa los elementos que
coinciden como estructura principal y combínalos en UNA sola descripción
original, fluida y coherente en español.

Expresa una idea visual completa con sujeto, acción o situación y contexto
cuando esté respaldado por las observaciones. Los detalles que aparezcan en una
sola observación —como adjetivos, atmósfera, sentimiento, iluminación, lugar o
un objeto secundario— también deben conservarse si son compatibles con la
escena principal y hacen la descripción más significativa. No los descartes
solo por no repetirse; omítelos únicamente si contradicen las demás
observaciones o parecen claramente inciertos.

Reformula con lenguaje natural: no traduzcas literalmente, no enumeres
posibilidades, no copies frases textuales y no menciones captions, modelos ni
inteligencia artificial. No inventes personas, objetos, lugares, acciones o
detalles que no estén apoyados. Devuelve solo la frase final.
<|im_end|>
<|im_start|>user
Observaciones del fotograma:
{samples}
<|im_end|>
<|im_start|>assistant
"""
        result = self._llm(
            prompt,
            max_tokens=80,
            temperature=0.35,
            top_p=0.9,
            stop=["<|im_end|>", "\n\n"],
        )
        text = result["choices"][0]["text"].strip()
        return text or cleaned[0]

    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 256,
        temperature: float = 0.70,
        top_p: float = 0.90,
    ) -> str:
        """Conversación ChatML con historial recortado al contexto CPU."""
        system = (
            "Eres el asistente de ByteBox, un catálogo de video con IA en CPU. "
            "Responde en español, con claridad y sin inventar hechos. "
            "Puedes ayudar a redactar descripciones, explicar BLIP, CLIP o Qwen, "
            "y resolver dudas generales. No menciones pesos, prompts internos ni "
            "que eres un modelo GGUF salvo que te lo pregunten."
        )
        trimmed: list[dict] = []
        budget = 3200
        used = 0
        for item in reversed(list(messages or [])):
            role = str(item.get("role") or "")
            content = str(item.get("content") or "").strip()
            if role not in ("user", "assistant") or not content:
                continue
            if used + len(content) > budget and trimmed:
                break
            trimmed.append({"role": role, "content": content})
            used += len(content)
        trimmed.reverse()

        parts = [f"<|im_start|>system\n{system}<|im_end|>\n"]
        for item in trimmed:
            parts.append(
                f"<|im_start|>{item['role']}\n{item['content']}<|im_end|>\n"
            )
        parts.append("<|im_start|>assistant\n")
        self.reset_chat()
        result = self._llm(
            "".join(parts),
            max_tokens=max(32, int(max_tokens)),
            temperature=max(0.1, min(1.0, float(temperature))),
            top_p=max(0.5, min(1.0, float(top_p))),
            stop=["<|im_end|>"],
        )
        return (result["choices"][0]["text"] or "").strip() or (
            "No pude generar una respuesta. Intente de nuevo."
        )
