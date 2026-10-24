from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LEGACY_WEIGHTS_DIR = PROJECT_ROOT / "mi_proyecto_streamlit" / "model_weights"
PRIMARY_WEIGHTS_DIR = PROJECT_ROOT / "model_weights"

MODEL_WEIGHTS_DIR = (
    LEGACY_WEIGHTS_DIR
    if LEGACY_WEIGHTS_DIR.is_dir() and not PRIMARY_WEIGHTS_DIR.is_dir()
    else PRIMARY_WEIGHTS_DIR
)
if not MODEL_WEIGHTS_DIR.is_dir() and LEGACY_WEIGHTS_DIR.is_dir():
    MODEL_WEIGHTS_DIR = LEGACY_WEIGHTS_DIR

CLIP_HUB_ID = "openai/clip-vit-base-patch32"
BLIP_HUB_ID = "Salesforce/blip-image-captioning-base"

CLIP_LOCAL_DIR = MODEL_WEIGHTS_DIR / "clip-vit-base-patch32"
BLIP_LOCAL_DIR = MODEL_WEIGHTS_DIR / "blip-image-captioning-base"
QWEN_GGUF_DIR = MODEL_WEIGHTS_DIR / "qwen2.5-1.5b-instruct-gguf"
QWEN_GGUF_FILE = QWEN_GGUF_DIR / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
QWEN_GGUF_HUB_ID = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
QWEN_GGUF_FILENAME = QWEN_GGUF_FILE.name


def _has_clip_weights(local_dir: Path) -> bool:
    if not local_dir.is_dir():
        return False
    has_config = (local_dir / "config.json").is_file()
    has_preprocessor = (local_dir / "preprocessor_config.json").is_file()
    has_weights = (local_dir / "model.safetensors").is_file() or (
        local_dir / "pytorch_model.bin"
    ).is_file()
    return has_config and has_preprocessor and has_weights


def _has_blip_weights(local_dir: Path) -> bool:
    if not local_dir.is_dir():
        return False
    has_config = (local_dir / "config.json").is_file()
    has_preprocessor = (local_dir / "preprocessor_config.json").is_file()
    has_weights = (local_dir / "model.safetensors").is_file() or (
        local_dir / "pytorch_model.bin"
    ).is_file()
    return has_config and has_preprocessor and has_weights


def has_blip_weights() -> bool:
    return _has_blip_weights(BLIP_LOCAL_DIR) or _has_blip_weights(
        LEGACY_WEIGHTS_DIR / "blip-image-captioning-base"
    )


def has_clip_weights() -> bool:
    return _has_clip_weights(CLIP_LOCAL_DIR) or _has_clip_weights(
        LEGACY_WEIGHTS_DIR / "clip-vit-base-patch32"
    )


def resolve_blip_local_dir() -> Path:
    legacy = LEGACY_WEIGHTS_DIR / "blip-image-captioning-base"
    if _has_blip_weights(BLIP_LOCAL_DIR):
        return BLIP_LOCAL_DIR
    if _has_blip_weights(legacy):
        return legacy
    return BLIP_LOCAL_DIR


def resolve_clip_local_dir() -> Path:
    legacy = LEGACY_WEIGHTS_DIR / "clip-vit-base-patch32"
    if _has_clip_weights(CLIP_LOCAL_DIR):
        return CLIP_LOCAL_DIR
    if _has_clip_weights(legacy):
        return legacy
    return CLIP_LOCAL_DIR


def resolve_qwen_gguf_file() -> Path:
    legacy = (
        LEGACY_WEIGHTS_DIR
        / "qwen2.5-1.5b-instruct-gguf"
        / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    )
    if QWEN_GGUF_FILE.is_file() and QWEN_GGUF_FILE.stat().st_size > 0:
        return QWEN_GGUF_FILE
    if legacy.is_file() and legacy.stat().st_size > 0:
        return legacy
    return QWEN_GGUF_FILE


def has_qwen_gguf() -> bool:
    target = resolve_qwen_gguf_file()
    return target.is_file() and target.stat().st_size > 0
