import threading
from concurrent.futures import ThreadPoolExecutor

_lock = threading.Lock()
_blip_analyzer = None
_clip_searcher = None
_qwen_synthesizer = None
_blip_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="blip-cpu")
_clip_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="clip-cpu")
_qwen_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="qwen-cpu")


def get_blip_pool() -> ThreadPoolExecutor:
    """Un solo hilo para OpenCV + inferencia BLIP (evita cuelgues de torch en el executor por defecto)."""
    return _blip_pool


def get_clip_pool() -> ThreadPoolExecutor:
    """Un solo hilo para OpenCV + inferencia CLIP."""
    return _clip_pool


def is_blip_loaded() -> bool:
    return _blip_analyzer is not None


def get_qwen_pool() -> ThreadPoolExecutor:
    """Un solo hilo para llama.cpp / Qwen GGUF."""
    return _qwen_pool


def is_clip_loaded() -> bool:
    return _clip_searcher is not None


def is_qwen_loaded() -> bool:
    return _qwen_synthesizer is not None


def get_blip_analyzer():
    """Carga lazy y singleton en CPU de VideoAnalyzer (BLIP)."""
    global _blip_analyzer
    with _lock:
        if _blip_analyzer is None:
            from ia_video_app.models.blip_processor import VideoAnalyzer

            _blip_analyzer = VideoAnalyzer()
        return _blip_analyzer


def get_clip_searcher():
    """Carga lazy y singleton en CPU de CLIPVideoSearcher (CLIP ViT-B/32)."""
    global _clip_searcher
    with _lock:
        if _clip_searcher is None:
            from ia_video_app.models.clip_processor import CLIPVideoSearcher

            _clip_searcher = CLIPVideoSearcher()
        return _clip_searcher


def get_qwen_synthesizer():
    """Carga lazy y singleton en CPU de FrameSynthesizer (Qwen GGUF Q4)."""
    global _qwen_synthesizer
    with _lock:
        if _qwen_synthesizer is None:
            from ia_video_app.models.frame_synthesizer import FrameSynthesizer

            _qwen_synthesizer = FrameSynthesizer()
        return _qwen_synthesizer
