#!/usr/bin/env python3
"""
Descarga pesos de modelos IA a mi_proyecto_streamlit/model_weights/ para uso offline.

Uso:
  python download_model_weights.py --model clip
  python download_model_weights.py --model blip
  python download_model_weights.py --model qwen
  python download_model_weights.py --model all

Si la red institucional bloquea SSL (CERTIFICATE_VERIFY_FAILED), use --insecure
solo en un entorno de confianza o descargue los archivos manualmente desde:
  https://huggingface.co/openai/clip-vit-base-patch32
  https://huggingface.co/Salesforce/blip-image-captioning-base
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
APP_DIR = PROJECT_ROOT / "mi_proyecto_streamlit"
sys.path.insert(0, str(APP_DIR))

from models.model_paths import (  # noqa: E402
    BLIP_HUB_ID,
    BLIP_LOCAL_DIR,
    CLIP_HUB_ID,
    CLIP_LOCAL_DIR,
    MODEL_WEIGHTS_DIR,
    QWEN_GGUF_FILENAME,
    QWEN_GGUF_HUB_ID,
    QWEN_GGUF_DIR,
)

MODELS = {
    "clip": (CLIP_HUB_ID, CLIP_LOCAL_DIR),
    "blip": (BLIP_HUB_ID, BLIP_LOCAL_DIR),
    "qwen": (QWEN_GGUF_HUB_ID, QWEN_GGUF_DIR),
}


def _apply_ssl_fix(insecure: bool) -> None:
    if insecure:
        import ssl
        import urllib3
        ssl._create_default_https_context = ssl._create_unverified_context
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return

    try:
        import certifi
        bundle = certifi.where()
        os.environ["SSL_CERT_FILE"] = bundle
        os.environ["REQUESTS_CA_BUNDLE"] = bundle
        os.environ["CURL_CA_BUNDLE"] = bundle
    except ImportError:
        pass


def _download_repo_insecure(repo_id: str, local_dir: Path, allow_files=None) -> None:
    """Descarga directa vía HTTPS sin verificar certificado (redes corporativas)."""
    import requests
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session = requests.Session()
    session.verify = False

    api_url = f"https://huggingface.co/api/models/{repo_id}"
    response = session.get(api_url, timeout=60)
    response.raise_for_status()
    siblings = response.json().get("siblings") or []

    local_dir.mkdir(parents=True, exist_ok=True)
    for item in siblings:
        filename = item.get("rfilename")
        if not filename or filename.startswith("."):
            continue
        if allow_files is not None and filename not in allow_files:
            continue

        dest = local_dir / filename
        if dest.is_file() and dest.stat().st_size > 0:
            print(f"  Ya existe: {filename}")
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
        print(f"  Descargando {filename}...")

        with session.get(url, stream=True, timeout=300) as file_resp:
            file_resp.raise_for_status()
            with open(dest, "wb") as out_file:
                for chunk in file_resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        out_file.write(chunk)

    print(f"  OK: {repo_id}")


def download_one(hub_id: str, local_dir: Path, insecure: bool, allow_files=None) -> None:
    print(f"\nDescargando {hub_id}")
    print(f"  -> {local_dir}")

    if insecure:
        _download_repo_insecure(hub_id, local_dir, allow_files=allow_files)
        return

    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=hub_id,
        local_dir=str(local_dir),
        allow_patterns=allow_files,
    )
    print(f"  OK: {hub_id}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Descarga pesos locales para BLIP, CLIP y Qwen GGUF."
    )
    parser.add_argument(
        "--model",
        choices=["clip", "blip", "qwen", "all"],
        default="clip",
        help="Modelo a descargar (default: clip)",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Desactiva verificacion SSL (redes con proxy/certificado corporativo)",
    )
    args = parser.parse_args()

    _apply_ssl_fix(args.insecure)
    MODEL_WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    targets = list(MODELS.keys()) if args.model == "all" else [args.model]

    try:
        for key in targets:
            hub_id, local_dir = MODELS[key]
            allowed = [QWEN_GGUF_FILENAME] if key == "qwen" else None
            download_one(hub_id, local_dir, args.insecure, allow_files=allowed)
    except Exception as exc:
        print("\nERROR al descargar modelos.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        print(
            "\nSi aparece CERTIFICATE_VERIFY_FAILED, pruebe el modelo solicitado con:\n"
            f"  python download_model_weights.py --model {args.model} --insecure\n"
            "O copie manualmente los archivos del repo Hugging Face a:\n"
            f"  {CLIP_LOCAL_DIR}\n"
            f"  {BLIP_LOCAL_DIR}",
            file=sys.stderr,
        )
        return 1

    print("\nListo. Reinicie Streamlit antes de usar el modelo descargado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
