import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _parse_secrets_toml(toml_path: Path) -> dict[str, str]:
    """Lee la sección [resourcespace] de secrets.toml como fallback."""
    if not toml_path.is_file():
        return {}

    try:
        import tomllib
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
        section = data.get("resourcespace") or {}
        return {
            "base_url": str(section.get("base_url", "")).strip(),
            "user": str(section.get("user", "")).strip(),
            "private_key": str(section.get("private_key", "")).strip(),
        }
    except Exception:
        result: dict[str, str] = {}
        in_section = False
        try:
            for raw_line in toml_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    in_section = line.lower() == "[resourcespace]"
                    continue
                if in_section and "=" in line:
                    key, val = line.split("=", 1)
                    result[key.strip()] = val.strip().strip('"').strip("'")
        except Exception:
            return {}
        return result


def get_resourcespace_credentials() -> dict[str, str]:
    """
    Obtiene las credenciales de ResourceSpace desde variables de entorno (.env)
    con fallback automático a .streamlit/secrets.toml.
    """
    base_url = os.getenv("RESOURCESPACE_BASE_URL", "").strip()
    user = os.getenv("RESOURCESPACE_USER", "").strip()
    private_key = os.getenv("RESOURCESPACE_PRIVATE_KEY", "").strip()

    if base_url and user and private_key:
        return {
            "base_url": base_url,
            "user": user,
            "private_key": private_key,
        }

    candidates = [
        PROJECT_ROOT / ".streamlit" / "secrets.toml",
        PROJECT_ROOT / "mi_proyecto_streamlit" / ".streamlit" / "secrets.toml",
    ]
    for candidate in candidates:
        parsed = _parse_secrets_toml(candidate)
        if parsed.get("base_url") and parsed.get("user") and parsed.get("private_key"):
            return parsed

    return {
        "base_url": base_url,
        "user": user,
        "private_key": private_key,
    }


def has_valid_credentials() -> bool:
    creds = get_resourcespace_credentials()
    return bool(creds.get("base_url") and creds.get("user") and creds.get("private_key"))
