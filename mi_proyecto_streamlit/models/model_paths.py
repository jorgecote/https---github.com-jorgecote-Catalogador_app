from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
MODEL_WEIGHTS_DIR = APP_DIR / "model_weights"

CLIP_HUB_ID = "openai/clip-vit-base-patch32"
BLIP_HUB_ID = "Salesforce/blip-image-captioning-base"

CLIP_LOCAL_DIR = MODEL_WEIGHTS_DIR / "clip-vit-base-patch32"
BLIP_LOCAL_DIR = MODEL_WEIGHTS_DIR / "blip-image-captioning-base"


def _has_clip_weights(local_dir: Path) -> bool:
    if not local_dir.is_dir():
        return False
    has_config = (local_dir / "config.json").is_file()
    has_preprocessor = (local_dir / "preprocessor_config.json").is_file()
    has_weights = (local_dir / "model.safetensors").is_file() or (local_dir / "pytorch_model.bin").is_file()
    return has_config and has_preprocessor and has_weights


def _has_blip_weights(local_dir: Path) -> bool:
    if not local_dir.is_dir():
        return False
    has_config = (local_dir / "config.json").is_file()
    has_preprocessor = (local_dir / "preprocessor_config.json").is_file()
    has_weights = (local_dir / "model.safetensors").is_file() or (local_dir / "pytorch_model.bin").is_file()
    return has_config and has_preprocessor and has_weights


def resolve_clip_model_path() -> str:
    """Devuelve ruta local si existen pesos; si no, el ID del Hub."""
    if _has_clip_weights(CLIP_LOCAL_DIR):
        return str(CLIP_LOCAL_DIR)
    return CLIP_HUB_ID


def resolve_blip_model_path() -> str:
    """Devuelve ruta local si existen pesos; si no, el ID del Hub."""
    if _has_blip_weights(BLIP_LOCAL_DIR):
        return str(BLIP_LOCAL_DIR)
    return BLIP_HUB_ID


def has_blip_weights() -> bool:
    return _has_blip_weights(BLIP_LOCAL_DIR)


def has_clip_weights() -> bool:
    return _has_clip_weights(CLIP_LOCAL_DIR)


def clip_model_status() -> dict:
    local_ready = _has_clip_weights(CLIP_LOCAL_DIR)
    return {
        "hub_id": CLIP_HUB_ID,
        "local_dir": str(CLIP_LOCAL_DIR),
        "local_ready": local_ready,
        "resolved_path": resolve_clip_model_path(),
    }
