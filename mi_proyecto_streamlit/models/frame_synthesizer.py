class FrameSynthesizer:
    """Sintetiza captions BLIP usando Qwen GGUF cuantizado en CPU."""

    def __init__(self, model_path=None, n_ctx: int = 2048):
        from models.model_paths import QWEN_GGUF_FILE, has_qwen_gguf

        resolved_path = model_path or QWEN_GGUF_FILE
        if not model_path and not has_qwen_gguf():
            raise RuntimeError(
                "No se encontró Qwen GGUF. Descargue el archivo "
                "`qwen2.5-1.5b-instruct-q4_k_m.gguf` desde el repositorio "
                "Qwen2.5-1.5B-Instruct-GGUF y colóquelo en:\n"
                f"`{QWEN_GGUF_FILE}`"
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

    def synthesize(self, captions: list[str]) -> str:
        """Devuelve una frase objetiva en español a partir de captions BLIP."""
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
