from ia_video_app.models.resourcespace_client import (
    ResourceSpaceAPI,
    ResourceSpaceRepository,
)
from ia_video_app.runtime.config import get_resourcespace_credentials


def get_repository() -> ResourceSpaceRepository:
    """
    Factory de ResourceSpaceRepository desacoplada de Streamlit.
    Usa variables de entorno (.env) o fallback a secrets.toml.
    """
    creds = get_resourcespace_credentials()
    if not (creds.get("base_url") and creds.get("user") and creds.get("private_key")):
        raise KeyError(
            "Credenciales de ResourceSpace incompletas. Configure .env o .streamlit/secrets.toml."
        )

    api = ResourceSpaceAPI(
        base_url=creds["base_url"],
        user=creds["user"],
        private_key=creds["private_key"],
    )
    return ResourceSpaceRepository(api)
