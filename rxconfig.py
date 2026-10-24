import os
import reflex as rx
from reflex.plugins.sitemap import SitemapPlugin

# En producción tras Nginx (Systemd define REFLEX_FRONTEND_PATH=/IA_videos).
# En desarrollo local por defecto usa raíz ("") en el puerto 8503.
FRONTEND_PATH = os.getenv("REFLEX_FRONTEND_PATH", "")
FRONTEND_PORT = int(os.getenv("REFLEX_FRONTEND_PORT", "8503"))
BACKEND_PORT = int(os.getenv("REFLEX_BACKEND_PORT", "8504"))
API_URL = os.getenv("REFLEX_API_URL", f"http://localhost:{BACKEND_PORT}")

config = rx.Config(
    app_name="ia_video_app",
    frontend_path=FRONTEND_PATH,
    frontend_port=FRONTEND_PORT,
    backend_port=BACKEND_PORT,
    api_url=API_URL,
    disable_plugins=[SitemapPlugin],
)
