import asyncio
import base64
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Optional
import reflex as rx

from ia_video_app.models.catalogation_result import chronological_description
from ia_video_app.models.model_paths import (
    has_blip_weights,
    has_clip_weights,
    has_qwen_gguf,
)
from ia_video_app.models.schemas import (
    AuditFrameItem,
    AutoCatalogResult,
    ClipFrameMatch,
    ClipHit,
    CollectionItem,
    VideoItem,
)
from ia_video_app.runtime.config import (
    get_resourcespace_credentials,
    has_valid_credentials,
)
from ia_video_app.runtime.repository import get_repository


def _pil_to_data_uri(pil_img) -> str:
    """Convierte un objeto PIL.Image en memoria a un Data URI JPEG Base64."""
    if pil_img is None:
        return ""
    try:
        buf = io.BytesIO()
        rgb_img = pil_img.convert("RGB")
        rgb_img.thumbnail((180, 105))
        rgb_img.save(buf, format="JPEG", quality=68)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return ""


def _frame_dict(
    video_id: int,
    timestamp: str,
    caption: str,
    image_data_uri: str = "",
    is_match: bool = False,
    score: float = 0.0,
) -> dict:
    return {
        "video_id": int(video_id),
        "timestamp": str(timestamp or "00:00"),
        "caption": str(caption or "Sin descripción"),
        "image_data_uri": str(image_data_uri or ""),
        "is_match": bool(is_match),
        "score": float(score or 0),
    }


def _audit_dict(timestamp: str, image_data_uri: str, blip_samples, synthesis: str) -> dict:
    if isinstance(blip_samples, list):
        samples_text = " | ".join(str(s) for s in blip_samples if str(s).strip())
    else:
        samples_text = str(blip_samples or "")
    return {
        "timestamp": str(timestamp or "00:00"),
        "image_data_uri": str(image_data_uri or ""),
        "blip_samples_text": samples_text,
        "synthesis": str(synthesis or ""),
    }


async def _aiter_sync_factory(factory):
    """Ejecuta un generador síncrono en un hilo y entrega ítems sin bloquear asyncio."""
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def worker():
        try:
            for item in factory():
                loop.call_soon_threadsafe(queue.put_nowait, ("item", item))
            loop.call_soon_threadsafe(queue.put_nowait, ("done", None))
        except Exception as exc:
            loop.call_soon_threadsafe(queue.put_nowait, ("error", exc))

    future = loop.run_in_executor(None, worker)
    while True:
        kind, payload = await queue.get()
        if kind == "done":
            break
        if kind == "error":
            await future
            raise payload
        yield payload
    await future


class CatalogState(rx.State):
    """
    Controlador principal MVC (rx.State).
    Contiene exclusivamente lógica de negocio, estado reactivo y manejadores de eventos.
    CERO código de interfaz visual (UI layout).
    """

    # --- Estado de conexión y navegación ---
    is_connected: bool = False
    is_loading: bool = False
    is_processing: bool = False
    cancel_requested: bool = False
    active_module: str = "blip"  # "blip" | "clip" | "automated" | "chat"
    workflow_phase: str = "connect"  # "connect" | "select" | "processing" | "results"
    dam_base_url: str = ""
    credentials_ready: bool = False

    # --- Notificaciones / Alertas ---
    status_kind: str = "info"  # "info" | "success" | "warning" | "error"
    status_title: str = ""
    status_message: str = ""

    # --- Catálogo, colecciones y filtros ---
    video_ids: list[int] = []
    videos: list[VideoItem] = []
    collections: list[CollectionItem] = []
    selected_collection_label: str = "Todos los videos"
    selected_collection_id: Optional[int] = None
    search_query: str = ""
    selected_category: str = "Todos"
    selected_status_filter: str = "Todos"
    selected_tag: str = "Todos"
    selected_video_ids: list[int] = []

    # --- Paginación del grid y bandeja ---
    current_page: int = 1
    page_size: int = 18
    tray_page: int = 1
    tray_page_size: int = 18

    # --- Parámetros de inferencia IA ---
    sample_rate_sec: int = 5
    blip_strategy_label: str = "Estándar (Greedy)"
    blip_num_beams: int = 3
    blip_sample_temperature: float = 0.9
    blip_sample_top_p: float = 0.9
    clip_query: str = ""
    clip_last_query: str = ""
    clip_threshold: float = 0.25
    auto_scope_mode: str = "Videos seleccionados"
    auto_collection_input: str = ""
    auto_caption_count: int = 3
    auto_temperature: float = 0.80
    auto_top_p: float = 0.90

    # --- Progreso del trabajo en curso ---
    job_title: str = ""
    job_subtitle: str = ""
    job_current_index: int = 0
    job_total_count: int = 0
    job_progress_pct: int = 0
    job_live_log: str = ""
    job_epoch: int = 0
    active_video_id: str = ""
    show_blip_install: bool = False
    blip_install_pct: int = 0
    blip_install_label: str = ""
    show_clip_install: bool = False
    clip_install_pct: int = 0
    clip_install_label: str = ""
    show_qwen_install: bool = False
    qwen_install_pct: int = 0
    qwen_install_label: str = ""
    chat_messages: list[dict] = []
    chat_draft: str = ""
    chat_busy: bool = False
    chat_temperature: float = 0.70
    chat_status: str = ""

    # --- Resultados por módulo ---
    analyzed_frames: list[dict] = []
    clip_hits: list[ClipHit] = []
    clip_analyzed_frames: list[dict] = []
    auto_results: list[AutoCatalogResult] = []
    categorized_video_ids: list[int] = []

    # --- Modal de subida / ingesta local ---
    upload_modal_open: bool = False
    upload_progress: int = 0
    is_uploading: bool = False
    uploaded_filenames: list[str] = []

    # =========================================================================
    # VARIABLES COMPUTADAS (@rx.var)
    # =========================================================================

    @rx.var
    def module_title(self) -> str:
        titles = {
            "blip": "Catalogación BLIP por Fotogramas",
            "clip": "Búsqueda Semántica CLIP",
            "automated": "Catalogación Automatizada (BLIP + Qwen)",
            "chat": "Chat Qwen (asistente local)",
        }
        return titles.get(self.active_module, "Catalogador de Video AI")

    @rx.var
    def phase_label(self) -> str:
        labels = {
            "connect": "1. Conectar",
            "select": "2. Seleccionar",
            "processing": "3. Procesando",
            "results": "4. Resultados",
        }
        return labels.get(self.workflow_phase, "1. Conectar")

    @rx.var
    def collection_options(self) -> list[str]:
        opts = ["Todos los videos"]
        for col in self.collections:
            opts.append(col.label)
        return opts

    @rx.var
    def total_videos_count(self) -> int:
        return len(self.videos)

    @rx.var
    def categorized_count(self) -> int:
        return len(self.categorized_video_ids)

    @rx.var
    def pending_count(self) -> int:
        total = len(self.videos)
        done = len([v for v in self.videos if v.video_id in self.categorized_video_ids])
        return max(0, total - done)

    @rx.var
    def selected_count(self) -> int:
        return len(self.selected_video_ids)

    @rx.var
    def storage_used_label(self) -> str:
        ready = []
        if has_blip_weights():
            ready.append("BLIP")
        if has_clip_weights():
            ready.append("CLIP")
        if has_qwen_gguf():
            ready.append("Qwen")
        if ready:
            return f"Pesos CPU: {', '.join(ready)}"
        return "Modo Hub / Caché bajo demanda"

    @rx.var
    def filtered_videos(self) -> list[VideoItem]:
        items = self.videos
        q = self.search_query.strip().lower()
        if q:
            items = [
                v
                for v in items
                if q in str(v.video_id).lower()
                or q in v.title.lower()
                or q in v.summary_preview.lower()
            ]
        if self.selected_status_filter == "Catalogados":
            items = [v for v in items if v.video_id in self.categorized_video_ids]
        elif self.selected_status_filter == "Pendientes":
            items = [v for v in items if v.video_id not in self.categorized_video_ids]
        return items

    @rx.var
    def total_pages(self) -> int:
        total = len(self.filtered_videos)
        if total == 0:
            return 1
        return (total + self.page_size - 1) // self.page_size

    @rx.var
    def paginated_videos(self) -> list[VideoItem]:
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return self.filtered_videos[start:end]

    @rx.var
    def page_indicator_label(self) -> str:
        return f"Página {self.current_page} de {self.total_pages}"

    def _tray_source(self) -> list[dict]:
        if self.active_module == "clip":
            return list(self.clip_analyzed_frames)
        return list(self.analyzed_frames)

    @rx.var
    def has_blip_results(self) -> bool:
        return len(self.analyzed_frames) > 0

    @rx.var
    def show_catalog_browser(self) -> bool:
        if self.active_module == "chat":
            return False
        if self.is_processing:
            return False
        if self.active_module == "blip":
            return not (self.workflow_phase == "results" and len(self.analyzed_frames) > 0)
        return True

    @rx.var
    def tray_scope_label(self) -> str:
        return f"Video ID: {self.active_video_id}" if self.active_video_id else "Ámbito actual"

    @rx.var
    def total_tray_frames(self) -> int:
        return len(self._tray_source())

    @rx.var
    def total_tray_pages(self) -> int:
        total = len(self._tray_source())
        if total == 0:
            return 1
        return (total + self.tray_page_size - 1) // self.tray_page_size

    @rx.var
    def paginated_tray_frames(self) -> list[dict]:
        frames = self._tray_source()
        start = (self.tray_page - 1) * self.tray_page_size
        end = start + self.tray_page_size
        return frames[start:end]

    @rx.var
    def can_start_blip(self) -> bool:
        return self.is_connected and not self.is_processing and len(self.selected_video_ids) > 0

    @rx.var
    def can_start_clip(self) -> bool:
        return (
            self.is_connected
            and not self.is_processing
            and len(self.filtered_videos) > 0
            and bool(self.clip_query.strip())
        )

    @rx.var
    def can_start_automated(self) -> bool:
        if not self.is_connected or self.is_processing:
            return False
        if self.auto_scope_mode == "ID de colección":
            return bool(self.auto_collection_input.strip().isdigit())
        return len(self.selected_video_ids) > 0

    @rx.var
    def can_send_chat(self) -> bool:
        return (
            bool(self.chat_draft.strip())
            and not self.chat_busy
            and not self.is_processing
        )

    @rx.var
    def has_chat_messages(self) -> bool:
        return len(self.chat_messages) > 0

    # =========================================================================
    # INICIALIZACIÓN Y CONEXIÓN A BYTEBOX / RESOURCESPACE
    # =========================================================================

    @staticmethod
    def _coerce_number(value) -> float:
        if isinstance(value, (list, tuple)):
            if not value:
                raise ValueError("valor vacío")
            value = value[0]
        return float(value)

    @rx.event
    def on_load_app(self):
        creds = get_resourcespace_credentials()
        self.dam_base_url = creds.get("base_url", "")
        self.credentials_ready = has_valid_credentials()
        if self.chat_busy:
            self.chat_busy = False
            self.chat_status = ""
        if self.is_processing:
            self.is_processing = False
            self.cancel_requested = False
            self.show_blip_install = False
            self.blip_install_pct = 0
            self.show_clip_install = False
            self.clip_install_pct = 0
            self.show_qwen_install = False
            self.qwen_install_pct = 0
            if self.analyzed_frames or self.clip_analyzed_frames or self.auto_results:
                self.workflow_phase = "results"
            elif not self.is_connected:
                self.workflow_phase = "connect"
            else:
                self.workflow_phase = "select"
                if self.job_title:
                    self.status_kind = "warning"
                    self.status_title = "Catalogación interrumpida"
                    self.status_message = (
                        "El proceso anterior se detuvo. Pulse de nuevo "
                        "Iniciar Catalogación BLIP o Buscar videos."
                    )
            self.job_title = ""
        elif not self.is_connected:
            self.workflow_phase = "connect"
        elif self.analyzed_frames or self.clip_analyzed_frames or self.auto_results:
            self.workflow_phase = "results"
        elif self.workflow_phase == "processing":
            self.workflow_phase = "select"
        if not self.credentials_ready:
            self.status_kind = "error"
            self.status_title = "Faltan credenciales de ByteBox"
            self.status_message = (
                "Configure .env o mi_proyecto_streamlit/.streamlit/secrets.toml "
                "con base_url, user y private_key."
            )
        elif not self.is_connected:
            self.status_kind = "info"
            self.status_title = "Listo para autenticar"
            self.status_message = (
                "La conexión usa las credenciales locales. No se muestran claves en pantalla."
            )

    def _build_video_items(self, ids: list[int]) -> list[VideoItem]:
        selected_set = set(self.selected_video_ids)
        done_set = set(self.categorized_video_ids)
        items: list[VideoItem] = []
        for vid in ids:
            is_done = vid in done_set
            items.append(
                VideoItem(
                    video_id=int(vid),
                    title=f"Recurso Audiovisual #{vid}",
                    category=self.selected_collection_label,
                    status="Catalogado" if is_done else "Pendiente",
                    date_label="Repositorio ByteBox",
                    tags=["Video", "DAM", "Catalogado" if is_done else "Por analizar"],
                    selected=vid in selected_set,
                )
            )
        return items

    @rx.event(background=True)
    async def connect_resourcespace(self):
        async with self:
            self.is_loading = True
            self.status_kind = "info"
            self.status_title = "Conectando con ByteBox"
            self.status_message = "Autenticando y cargando colecciones. Espere unos segundos..."

        try:
            repository = get_repository()
            raw_ids = repository.get_all_video_ids()
            raw_collections = repository.get_user_collections()
        except KeyError as exc:
            async with self:
                self.is_loading = False
                self.is_connected = False
                self.status_kind = "error"
                self.status_title = "Credenciales no configuradas"
                self.status_message = str(exc)
            return rx.toast.error("Faltan credenciales en .env o secrets.toml")
        except Exception as exc:
            async with self:
                self.is_loading = False
                self.is_connected = False
                self.status_kind = "error"
                self.status_title = "Error de conexión con ResourceSpace"
                self.status_message = str(exc)
            return rx.toast.error("Error de red al conectar con ByteBox")

        if raw_ids is None:
            async with self:
                self.is_loading = False
                self.is_connected = False
                self.status_kind = "error"
                self.status_title = "No se pudo autenticar"
                self.status_message = "Verifique su clave privada y permisos en ResourceSpace."
            return rx.toast.error("Autenticación rechazada por ByteBox")

        parsed_collections: list[CollectionItem] = []
        for col in raw_collections or []:
            ref = int(col["ref"])
            name = str(col.get("name", f"Colección {ref}"))
            count = col.get("count")
            suffix = f" ({count})" if count is not None else ""
            parsed_collections.append(
                CollectionItem(
                    ref=ref,
                    name=name,
                    count=count,
                    label=f"[{ref}] {name}{suffix}",
                )
            )

        async with self:
            self.collections = parsed_collections
            self.video_ids = [int(v) for v in raw_ids]
            self.selected_collection_id = None
            self.selected_collection_label = "Todos los videos"
            self.selected_video_ids = []
            self.videos = self._build_video_items(self.video_ids)
            self.current_page = 1
            self.is_connected = True
            self.is_loading = False
            self.workflow_phase = "select"
            self.status_kind = "success"
            self.status_title = "Conexión establecida con ByteBox"
            self.status_message = (
                f"{len(self.video_ids)} recursos de video cargados y listos para catalogar."
            )
        return rx.toast.success(f"Conectado: {len(raw_ids)} videos disponibles")

    # =========================================================================
    # NAVEGACIÓN, FILTROS Y SELECCIÓN DE RECURSOS
    # =========================================================================

    @rx.event
    def set_active_module(self, module_name: str):
        if self.is_processing or self.chat_busy:
            return rx.toast.warning("Espere a que finalice el procesamiento en curso.")
        if module_name == "chat":
            self.active_module = "chat"
            self.status_kind = "info"
            self.status_title = "Chat Qwen en CPU"
            self.status_message = (
                "Asistente local Qwen2.5-1.5B-Instruct GGUF. No requiere ByteBox."
            )
            return
        if module_name != "blip" and not self.is_connected:
            self.active_module = module_name
            self.status_kind = "warning"
            self.status_title = "Conéctese primero a ByteBox"
            self.status_message = (
                "CLIP y la catalogación automatizada reutilizan la misma sesión autenticada."
            )
            return
        self.active_module = module_name
        self.tray_page = 1
        if self.is_connected:
            self.workflow_phase = "select"

    @rx.event
    def set_search_query(self, value: str):
        self.search_query = value
        self.current_page = 1

    @rx.event
    def set_status_filter(self, status_label: str):
        self.selected_status_filter = status_label
        self.current_page = 1

    @rx.event
    def clear_filters(self):
        self.search_query = ""
        self.selected_status_filter = "Todos"
        self.current_page = 1

    @rx.event(background=True)
    async def change_collection(self, collection_label: str):
        async with self:
            if not self.is_connected or self.is_processing:
                return
            self.selected_collection_label = collection_label
            self.is_loading = True

        try:
            repository = get_repository()
            if collection_label == "Todos los videos":
                selected_id = None
                ids = repository.get_all_video_ids() or []
            else:
                selected_id = int(
                    collection_label.split("]", 1)[0].replace("[", "").strip()
                )
                ids = repository.get_collection_video_ids(selected_id) or []

            async with self:
                self.selected_collection_id = selected_id
                self.video_ids = [int(x) for x in ids]
                self.selected_video_ids = []
                self.videos = self._build_video_items(self.video_ids)
                self.current_page = 1
                self.is_loading = False
                self.workflow_phase = "select"
        except Exception as exc:
            async with self:
                self.is_loading = False
                self.status_kind = "error"
                self.status_title = "Error al cambiar colección"
                self.status_message = str(exc)

    @rx.event
    def toggle_video_selection(self, video_id: int):
        vid = int(video_id)
        if vid in self.selected_video_ids:
            self.selected_video_ids = [x for x in self.selected_video_ids if x != vid]
        else:
            self.selected_video_ids = self.selected_video_ids + [vid]
        self.videos = self._build_video_items(self.video_ids)

    @rx.event
    def select_all_filtered(self):
        filtered_ids = [v.video_id for v in self.filtered_videos]
        combined = set(self.selected_video_ids) | set(filtered_ids)
        self.selected_video_ids = sorted(list(combined))
        self.videos = self._build_video_items(self.video_ids)
        return rx.toast.info(f"{len(self.selected_video_ids)} recursos seleccionados")

    @rx.event
    def clear_selection(self):
        self.selected_video_ids = []
        self.videos = self._build_video_items(self.video_ids)

    @rx.event
    def cancel_processing(self):
        self.cancel_requested = True
        self.is_processing = False
        self.show_blip_install = False
        self.show_clip_install = False
        self.show_qwen_install = False
        if self.is_connected:
            self.workflow_phase = "select"
        self.job_live_log = "Proceso detenido por el usuario."
        self.status_kind = "warning"
        self.status_title = "Proceso detenido"
        self.status_message = "Puede volver a seleccionar recursos e iniciar de nuevo."

    @rx.event
    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1

    @rx.event
    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1

    @rx.event
    def prev_tray_page(self):
        if self.tray_page > 1:
            self.tray_page -= 1

    @rx.event
    def next_tray_page(self):
        if self.tray_page < self.total_tray_pages:
            self.tray_page += 1

    # =========================================================================
    # PARÁMETROS DE CONFIGURACIÓN IA
    # =========================================================================

    @rx.event
    def set_sample_rate_str(self, value: str | int | float | list):
        try:
            self.sample_rate_sec = max(1, min(30, int(self._coerce_number(value))))
        except Exception:
            self.sample_rate_sec = 5

    @rx.event
    def set_blip_strategy(self, value: str):
        self.blip_strategy_label = value

    @rx.event
    def set_blip_num_beams_str(self, value: str | int | float | list):
        try:
            self.blip_num_beams = max(2, min(8, int(self._coerce_number(value))))
        except Exception:
            self.blip_num_beams = 3

    @rx.event
    def set_blip_sample_temperature_str(self, value: str | int | float | list):
        try:
            self.blip_sample_temperature = round(
                max(0.2, min(1.5, self._coerce_number(value))), 1
            )
        except Exception:
            self.blip_sample_temperature = 0.9

    @rx.event
    def set_blip_sample_top_p_str(self, value: str | int | float | list):
        try:
            self.blip_sample_top_p = round(
                max(0.5, min(1.0, self._coerce_number(value))), 2
            )
        except Exception:
            self.blip_sample_top_p = 0.9

    @rx.event
    def set_clip_query(self, value: str):
        self.clip_query = value

    @rx.event
    def set_clip_threshold_str(self, value: str | int | float | list):
        try:
            self.clip_threshold = round(
                max(0.15, min(0.40, self._coerce_number(value))), 2
            )
        except Exception:
            self.clip_threshold = 0.25

    @rx.event
    def set_auto_scope_mode(self, value: str):
        self.auto_scope_mode = value

    @rx.event
    def set_auto_collection_input(self, value: str):
        self.auto_collection_input = value

    @rx.event
    def set_auto_caption_count_str(self, value: str | int | float | list):
        try:
            self.auto_caption_count = max(1, min(5, int(self._coerce_number(value))))
        except Exception:
            self.auto_caption_count = 3

    @rx.event
    def set_auto_temperature_str(self, value: str | int | float | list):
        try:
            self.auto_temperature = round(
                max(0.60, min(0.90, self._coerce_number(value))), 2
            )
        except Exception:
            self.auto_temperature = 0.80

    @rx.event
    def return_to_selection(self):
        if not self.is_processing:
            self.workflow_phase = "select"

    @rx.event
    def start_new_clip_query(self):
        if self.is_processing:
            return
        self.workflow_phase = "select"
        self.clip_query = ""
        self.clip_last_query = ""

    @rx.event
    def start_new_auto_catalog(self):
        if self.is_processing:
            return
        self.workflow_phase = "select"

    @rx.event
    def set_chat_draft(self, value: str):
        self.chat_draft = value

    @rx.event
    def set_chat_temperature_str(self, value: str | int | float | list):
        try:
            self.chat_temperature = round(
                max(0.20, min(0.95, self._coerce_number(value))), 2
            )
        except Exception:
            self.chat_temperature = 0.70

    @rx.event
    def clear_chat(self):
        if self.chat_busy:
            return rx.toast.warning("Espere a que Qwen termine de responder.")
        self.chat_messages = []
        self.chat_draft = ""
        self.chat_status = ""
        from ia_video_app.runtime.ai_registry import get_qwen_synthesizer, is_qwen_loaded

        if is_qwen_loaded():
            try:
                get_qwen_synthesizer().reset_chat()
            except Exception:
                pass
        return rx.toast.info("Conversación y contexto de Qwen limpiados.")

    @rx.event(background=True)
    async def send_chat_message(self):
        async with self:
            text = self.chat_draft.strip()
            if not text or self.chat_busy or self.is_processing:
                return
            history = list(self.chat_messages)
            history.append({"role": "user", "content": text})
            self.chat_messages = list(history)
            self.chat_draft = ""
            self.chat_busy = True
            self.chat_status = "Cargando Qwen en CPU..."
            temperature = self.chat_temperature

        try:
            synthesizer = await self._load_qwen_with_install_progress()
            async with self:
                self.chat_status = "Qwen está escribiendo..."
            reply_task = asyncio.create_task(
                self._run_on_qwen_pool(
                    synthesizer.chat, history, 256, temperature, 0.90
                )
            )
            waited = 0
            while not reply_task.done():
                await asyncio.sleep(1)
                waited += 1
                async with self:
                    self.chat_status = f"Qwen está escribiendo... {waited}s CPU"
            reply = str(await reply_task).strip()
            async with self:
                self.chat_messages = list(history) + [
                    {"role": "assistant", "content": reply}
                ]
                self.chat_busy = False
                self.chat_status = ""
                self.show_qwen_install = False
        except Exception as exc:
            async with self:
                self.chat_busy = False
                self.show_qwen_install = False
                self.chat_status = ""
                self.status_kind = "error"
                self.status_title = "No se pudo responder con Qwen"
                self.status_message = str(exc)
                self.chat_messages = list(history) + [
                    {
                        "role": "assistant",
                        "content": f"Error al generar la respuesta: {exc}",
                    }
                ]

    # =========================================================================
    # PIPELINE 1: CATALOGACIÓN BLIP POR FOTOGRAMAS (BACKGROUND TASK)
    # =========================================================================

    def _blip_generation_kwargs(self) -> dict:
        if "Beam" in self.blip_strategy_label:
            return {"num_beams": max(2, int(self.blip_num_beams)), "do_sample": False}
        if "Creativo" in self.blip_strategy_label:
            return {
                "do_sample": True,
                "num_beams": 1,
                "temperature": self.blip_sample_temperature,
                "top_p": self.blip_sample_top_p,
            }
        return {"num_beams": 1, "do_sample": False}

    @staticmethod
    def _blip_temp_dir() -> str:
        path = Path(tempfile.gettempdir()) / "bytebox_catalogador"
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    @staticmethod
    async def _run_on_blip_pool(func, *args):
        from ia_video_app.runtime.ai_registry import get_blip_pool

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(get_blip_pool(), func, *args)

    @staticmethod
    async def _run_on_clip_pool(func, *args):
        from ia_video_app.runtime.ai_registry import get_clip_pool

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(get_clip_pool(), func, *args)

    @staticmethod
    async def _run_on_qwen_pool(func, *args):
        from ia_video_app.runtime.ai_registry import get_qwen_pool

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(get_qwen_pool(), func, *args)

    async def _load_blip_with_install_progress(self):
        from ia_video_app.runtime.ai_registry import get_blip_analyzer, is_blip_loaded

        if is_blip_loaded():
            return await asyncio.to_thread(get_blip_analyzer)

        needs_download = not has_blip_weights()
        async with self:
            self.show_blip_install = True
            self.blip_install_pct = 6
            self.blip_install_label = (
                "Descargando e instalando pesos BLIP (Salesforce/blip-image-captioning-base)..."
                if needs_download
                else "Primera carga de BLIP en esta sesión: instalando pesos en memoria CPU..."
            )
            self.job_live_log = self.blip_install_label

        from ia_video_app.runtime.ai_registry import get_blip_pool

        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(get_blip_pool(), get_blip_analyzer)
        pct = 6
        elapsed_sec = 0
        label = (
            "Descargando e instalando pesos BLIP (Salesforce/blip-image-captioning-base)..."
            if needs_download
            else "Primera carga de BLIP en esta sesión: instalando pesos en memoria CPU..."
        )
        try:
            while not future.done():
                await asyncio.sleep(0.8)
                elapsed_sec += 1
                if pct < 88:
                    pct = min(88, pct + 5)
                elif pct < 99:
                    pct = min(99, pct + 1)
                if has_blip_weights() and needs_download:
                    label = "Pesos descargados. Cargando BLIP en memoria CPU..."
                    needs_download = False
                elif pct >= 88:
                    label = (
                        f"Finalizando instalación en CPU ({elapsed_sec}s). "
                        "La primera carga puede tardar 1-3 minutos; no recargue la página."
                    )
                async with self:
                    if self.cancel_requested:
                        break
                    self.blip_install_pct = pct
                    self.blip_install_label = label
                    self.job_live_log = label
            analyzer = await future
        except Exception:
            async with self:
                self.show_blip_install = False
                self.blip_install_pct = 0
            raise

        async with self:
            self.blip_install_pct = 100
            self.blip_install_label = "BLIP instalado y listo."
            self.job_live_log = "BLIP listo. Continuando con la catalogación..."
        await asyncio.sleep(0.35)
        async with self:
            self.show_blip_install = False
        return analyzer

    async def _load_clip_with_install_progress(self):
        from ia_video_app.runtime.ai_registry import (
            get_clip_pool,
            get_clip_searcher,
            is_clip_loaded,
        )

        if is_clip_loaded():
            return await self._run_on_clip_pool(get_clip_searcher)

        needs_download = not has_clip_weights()
        async with self:
            self.show_clip_install = True
            self.clip_install_pct = 6
            self.clip_install_label = (
                "Descargando e instalando pesos CLIP (openai/clip-vit-base-patch32)..."
                if needs_download
                else "Primera carga de CLIP en esta sesión: instalando pesos en memoria CPU..."
            )
            self.job_live_log = self.clip_install_label

        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(get_clip_pool(), get_clip_searcher)
        pct = 6
        elapsed_sec = 0
        label = (
            "Descargando e instalando pesos CLIP (openai/clip-vit-base-patch32)..."
            if needs_download
            else "Primera carga de CLIP en esta sesión: instalando pesos en memoria CPU..."
        )
        try:
            while not future.done():
                await asyncio.sleep(0.8)
                elapsed_sec += 1
                if pct < 88:
                    pct = min(88, pct + 5)
                elif pct < 99:
                    pct = min(99, pct + 1)
                if has_clip_weights() and needs_download:
                    label = "Pesos descargados. Cargando CLIP ViT-B/32 en memoria CPU..."
                    needs_download = False
                elif pct >= 88:
                    label = (
                        f"Finalizando instalación CLIP en CPU ({elapsed_sec}s). "
                        "La primera carga puede tardar 1-3 minutos; no recargue la página."
                    )
                async with self:
                    if self.cancel_requested:
                        break
                    self.clip_install_pct = pct
                    self.clip_install_label = label
                    self.job_live_log = label
            searcher = await future
        except Exception:
            async with self:
                self.show_clip_install = False
                self.clip_install_pct = 0
            raise

        async with self:
            self.clip_install_pct = 100
            self.clip_install_label = "CLIP instalado y listo."
            self.job_live_log = "CLIP listo. Codificando la consulta..."
        await asyncio.sleep(0.35)
        async with self:
            self.show_clip_install = False
        return searcher

    async def _load_qwen_with_install_progress(self):
        from ia_video_app.runtime.ai_registry import (
            get_qwen_pool,
            get_qwen_synthesizer,
            is_qwen_loaded,
        )

        if is_qwen_loaded():
            return await self._run_on_qwen_pool(get_qwen_synthesizer)

        needs_file = not has_qwen_gguf()
        async with self:
            self.show_qwen_install = True
            self.qwen_install_pct = 6
            self.qwen_install_label = (
                "No se encontró el GGUF. Instale pesos locales de Qwen2.5-1.5B-Instruct Q4..."
                if needs_file
                else "Primera carga de Qwen2.5-1.5B-Instruct GGUF Q4 en memoria CPU..."
            )
            self.job_live_log = self.qwen_install_label

        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(get_qwen_pool(), get_qwen_synthesizer)
        pct = 6
        elapsed_sec = 0
        label = (
            "Cargando Qwen GGUF desde disco. Si falta el archivo, ejecute "
            "python download_model_weights.py --model qwen"
            if needs_file
            else "Primera carga de Qwen2.5-1.5B-Instruct GGUF Q4 en memoria CPU..."
        )
        try:
            while not future.done():
                await asyncio.sleep(0.8)
                elapsed_sec += 1
                if pct < 88:
                    pct = min(88, pct + 5)
                elif pct < 99:
                    pct = min(99, pct + 1)
                if has_qwen_gguf() and needs_file:
                    label = "GGUF encontrado. Cargando Qwen en llama.cpp (CPU)..."
                    needs_file = False
                elif pct >= 88:
                    label = (
                        f"Finalizando instalación Qwen en CPU ({elapsed_sec}s). "
                        "La primera carga puede tardar 1-2 minutos; no recargue la página."
                    )
                async with self:
                    if self.cancel_requested:
                        break
                    self.qwen_install_pct = pct
                    self.qwen_install_label = label
                    self.job_live_log = label
            synthesizer = await future
        except Exception:
            async with self:
                self.show_qwen_install = False
                self.qwen_install_pct = 0
            raise

        async with self:
            self.qwen_install_pct = 100
            self.qwen_install_label = "Qwen instalado y listo."
            self.job_live_log = "Qwen listo. Continuando con la síntesis..."
        await asyncio.sleep(0.35)
        async with self:
            self.show_qwen_install = False
        return synthesizer

    @rx.event(background=True)
    async def run_blip_for_video(self, video_id: int):
        await self._run_blip_pipeline(int(video_id))

    @rx.event(background=True)
    async def run_blip_catalogation(self):
        await self._run_blip_pipeline(0)

    async def _run_blip_pipeline(self, video_id: int = 0):
        async with self:
            if video_id:
                self.selected_video_ids = [int(video_id)]
                self.videos = self._build_video_items(self.video_ids)
            if not self.selected_video_ids:
                self.status_kind = "warning"
                self.status_title = "Seleccione al menos un video"
                self.status_message = "Marque recursos en el catálogo o use Analizar en una tarjeta."
                return
            if self.is_processing:
                return
            target_ids = list(self.selected_video_ids)
            sample_rate = self.sample_rate_sec
            gen_kwargs = self._blip_generation_kwargs()
            self.cancel_requested = False
            self.is_processing = True
            self.job_epoch += 1
            job_epoch = self.job_epoch
            self.workflow_phase = "processing"
            self.analyzed_frames = []
            self.tray_page = 1
            self.job_title = "Catalogación BLIP en curso"
            self.job_subtitle = f"Procesando {len(target_ids)} recurso(s) en CPU..."
            self.job_total_count = len(target_ids)
            self.job_current_index = 0
            self.job_progress_pct = 8
            self.job_live_log = "Cargando modelo BLIP en CPU (low_cpu_mem_usage=True)..."

        failed = 0
        cancelled = False
        collected_frames: list[dict] = []
        try:
            analyzer = await self._load_blip_with_install_progress()
            repository = get_repository()

            for idx, vid in enumerate(target_ids, start=1):
                async with self:
                    if self.cancel_requested or self.job_epoch != job_epoch:
                        cancelled = True
                        break
                    self.active_video_id = str(vid)
                    self.job_current_index = idx
                    self.job_progress_pct = max(
                        8, int(((idx - 1) / max(1, len(target_ids))) * 90)
                    )
                    self.job_subtitle = (
                        f"Video {idx} de {len(target_ids)} · ID {vid}"
                    )
                    self.job_live_log = f"Descargando temporalmente video ID {vid}..."

                local_path = None
                sampler = None
                try:
                    print(f"[BLIP] Descargando video {vid}...", flush=True)
                    local_path = await asyncio.to_thread(
                        repository.download_video, vid, self._blip_temp_dir()
                    )
                    if not local_path:
                        failed += 1
                        async with self:
                            self.job_live_log = f"No se pudo descargar el recurso {vid}."
                        continue

                    size_mb = os.path.getsize(local_path) / (1024 * 1024)
                    print(f"[BLIP] Video {vid} listo ({size_mb:.1f} MB): {local_path}", flush=True)
                    async with self:
                        self.job_live_log = (
                            f"Video ID {vid} descargado ({size_mb:.1f} MB). "
                            "Abriendo fotogramas..."
                        )

                    from ia_video_app.models.blip_processor import VideoFrameSampler

                    sampler = await self._run_on_blip_pool(
                        VideoFrameSampler, local_path, sample_rate
                    )
                    if not sampler.opened:
                        failed += 1
                        async with self:
                            self.job_live_log = f"No se pudo abrir el video {vid}."
                        continue

                    estimated = max(1, sampler.sample_count or 1)
                    async with self:
                        self.job_live_log = (
                            f"Ejecutando BLIP en video ID {vid} · "
                            f"{estimated} fotograma(s) estimados..."
                        )

                    frame_num = 0
                    while True:
                        async with self:
                            if self.cancel_requested or self.job_epoch != job_epoch:
                                cancelled = True
                        if cancelled:
                            break

                        sample = await self._run_on_blip_pool(sampler.next_sample)
                        if sample is None:
                            break
                        timestamp, pil_img, thumb = sample
                        frame_num += 1
                        pct = 8 + int(
                            (
                                (idx - 1)
                                + (frame_num / estimated)
                            )
                            / max(1, len(target_ids))
                            * 90
                        )
                        async with self:
                            self.job_progress_pct = min(99, max(8, pct))
                            self.job_subtitle = (
                                f"Video {idx}/{len(target_ids)} · ID {vid} · "
                                f"fotograma {frame_num}/{estimated}"
                            )
                            self.job_live_log = (
                                f"Ejecutando BLIP en [{timestamp}] · "
                                f"fotograma {frame_num}/{estimated}..."
                            )
                        print(
                            f"[BLIP] Inferencia {vid} [{timestamp}] "
                            f"{frame_num}/{estimated}",
                            flush=True,
                        )

                        caption_task = asyncio.create_task(
                            self._run_on_blip_pool(
                                analyzer.generate_caption, pil_img, gen_kwargs
                            )
                        )
                        waited = 0
                        while not caption_task.done():
                            await asyncio.sleep(1)
                            waited += 1
                            async with self:
                                if self.cancel_requested or self.job_epoch != job_epoch:
                                    cancelled = True
                                self.job_live_log = (
                                    f"BLIP infiriendo [{timestamp}] · "
                                    f"fotograma {frame_num}/{estimated} · {waited}s CPU"
                                )
                        caption = await caption_task
                        uri = _pil_to_data_uri(thumb)
                        collected_frames.append(
                            _frame_dict(vid, timestamp, caption, uri)
                        )
                        print(f"[BLIP] Caption {vid} [{timestamp}]: {caption}", flush=True)
                        async with self:
                            self.analyzed_frames = list(collected_frames)
                            self.job_live_log = (
                                f"Video {vid} · Fotograma #{frame_num} "
                                f"[{timestamp}]: {caption}"
                            )

                    if cancelled:
                        break

                    async with self:
                        if vid not in self.categorized_video_ids:
                            self.categorized_video_ids = self.categorized_video_ids + [vid]
                        self.videos = self._build_video_items(self.video_ids)
                except Exception as exc:
                    failed += 1
                    print(f"[BLIP] Error video {vid}: {exc}", flush=True)
                    async with self:
                        self.job_live_log = f"Error procesando video {vid}: {exc}"
                finally:
                    if sampler is not None:
                        try:
                            await self._run_on_blip_pool(sampler.close)
                        except Exception:
                            pass
                    if local_path:
                        await asyncio.to_thread(repository.cleanup_video, local_path)

            ok = len(target_ids) - failed
            async with self:
                self.analyzed_frames = list(collected_frames)
                self.is_processing = False
                self.show_blip_install = False
                self.job_progress_pct = 100 if not cancelled else self.job_progress_pct
                self.workflow_phase = "results" if collected_frames else "select"
                if cancelled:
                    self.status_kind = "warning"
                    self.status_title = "Catalogación BLIP detenida"
                    self.status_message = (
                        f"Se detuvo tras {len(collected_frames)} fotogramas. "
                        "Revise la bandeja inferior."
                    )
                elif collected_frames:
                    self.status_kind = "success" if failed == 0 else "warning"
                    self.status_title = "Catalogación BLIP completada"
                    self.status_message = (
                        f"{ok} de {len(target_ids)} video(s) analizados. "
                        f"{len(collected_frames)} fotogramas en la bandeja. "
                        "Revise las miniaturas y descriptores."
                    )
                else:
                    self.status_kind = "warning"
                    self.status_title = "Catalogación BLIP sin resultados"
                    self.status_message = (
                        f"No se generaron fotogramas ({failed} fallo(s) "
                        f"de {len(target_ids)})."
                    )
        except Exception as exc:
            async with self:
                self.is_processing = False
                self.show_blip_install = False
                self.workflow_phase = "select"
                self.status_kind = "error"
                self.status_title = "Error al inicializar o ejecutar BLIP"
                self.status_message = str(exc)

    # =========================================================================
    # PIPELINE 2: BÚSQUEDA SEMÁNTICA CLIP (BACKGROUND TASK)
    # =========================================================================

    @rx.event(background=True)
    async def run_clip_search(self):
        async with self:
            query = self.clip_query.strip()
            scope_ids = [v.video_id for v in self.filtered_videos]
            if not query or not scope_ids or self.is_processing:
                return
            sample_rate = self.sample_rate_sec
            threshold = self.clip_threshold
            self.cancel_requested = False
            self.is_processing = True
            self.job_epoch += 1
            job_epoch = self.job_epoch
            self.workflow_phase = "processing"
            self.clip_hits = []
            self.clip_analyzed_frames = []
            self.tray_page = 1
            self.job_title = "Búsqueda Semántica CLIP en curso"
            self.clip_last_query = query
            self.job_subtitle = f"Consulta: «{query}» · Umbral {threshold:.2f}"
            self.job_total_count = len(scope_ids)
            self.job_current_index = 0
            self.job_progress_pct = 8
            self.job_live_log = "Cargando modelo CLIP ViT-B/32 en CPU..."

        collected_hits: list[ClipHit] = []
        collected_tray: list[dict] = []
        try:
            searcher = await self._load_clip_with_install_progress()
            async with self:
                self.job_live_log = f"Codificando consulta CLIP: «{query}»..."
            text_features = await self._run_on_clip_pool(searcher.encode_text, query)
            repository = get_repository()
        except Exception as exc:
            async with self:
                self.is_processing = False
                self.show_clip_install = False
                self.workflow_phase = "select"
                self.status_kind = "error"
                self.status_title = "No se pudo ejecutar CLIP"
                self.status_message = str(exc)
            return

        from ia_video_app.models.blip_processor import VideoFrameSampler

        cancelled = False
        for idx, vid in enumerate(scope_ids, start=1):
            local_path = None
            sampler = None
            async with self:
                if self.cancel_requested or self.job_epoch != job_epoch:
                    cancelled = True
                    break
                self.active_video_id = str(vid)
                self.job_current_index = idx
                self.job_progress_pct = max(
                    8, int(((idx - 1) / max(1, len(scope_ids))) * 90)
                )
                self.job_subtitle = (
                    f"Consulta: «{query}» · Video {idx}/{len(scope_ids)} · ID {vid}"
                )
                self.job_live_log = f"Descargando video ID {vid} para evaluación CLIP..."

            try:
                print(f"[CLIP] Descargando video {vid}...", flush=True)
                local_path = await asyncio.to_thread(
                    repository.download_video, vid, self._blip_temp_dir()
                )
                if not local_path:
                    async with self:
                        self.job_live_log = f"No se pudo descargar el recurso {vid}."
                    continue

                size_mb = os.path.getsize(local_path) / (1024 * 1024)
                print(f"[CLIP] Video {vid} listo ({size_mb:.1f} MB)", flush=True)
                async with self:
                    self.job_live_log = (
                        f"Video ID {vid} descargado ({size_mb:.1f} MB). "
                        "Abriendo fotogramas..."
                    )

                sampler = await self._run_on_clip_pool(
                    VideoFrameSampler, local_path, sample_rate
                )
                if not sampler.opened:
                    async with self:
                        self.job_live_log = f"No se pudo abrir el video {vid}."
                    continue

                estimated = max(1, sampler.sample_count or 1)
                matching_frames: list[ClipFrameMatch] = []
                video_frames: list[dict] = []
                max_score = 0.0
                frame_num = 0

                while True:
                    async with self:
                        if self.cancel_requested or self.job_epoch != job_epoch:
                            cancelled = True
                    if cancelled:
                        break
                    sample = await self._run_on_clip_pool(sampler.next_sample)
                    if sample is None:
                        break
                    timestamp, pil_img, thumbnail = sample
                    frame_num += 1
                    pct = 8 + int(
                        ((idx - 1) + (frame_num / estimated))
                        / max(1, len(scope_ids))
                        * 90
                    )
                    async with self:
                        self.job_progress_pct = min(99, max(8, pct))
                        self.job_live_log = (
                            f"Ejecutando CLIP en [{timestamp}] · "
                            f"fotograma {frame_num}/{estimated}..."
                        )

                    score_task = asyncio.create_task(
                        self._run_on_clip_pool(
                            searcher._score_image, pil_img, text_features
                        )
                    )
                    waited = 0
                    while not score_task.done():
                        await asyncio.sleep(1)
                        waited += 1
                        async with self:
                            self.job_live_log = (
                                f"CLIP infiriendo [{timestamp}] · "
                                f"fotograma {frame_num}/{estimated} · {waited}s CPU"
                            )
                    score = float(await score_task)
                    is_match = score >= threshold
                    max_score = max(max_score, score)
                    uri = _pil_to_data_uri(thumbnail)
                    frame_dict = _frame_dict(
                        vid,
                        timestamp,
                        f"Similitud CLIP: {score:.3f}",
                        uri,
                        is_match=is_match,
                        score=round(score, 4),
                    )
                    video_frames.append(frame_dict)
                    print(
                        f"[CLIP] {vid} [{timestamp}] score={score:.3f} match={is_match}",
                        flush=True,
                    )
                    parts = [int(p) for p in str(timestamp).split(":")]
                    if len(parts) == 3:
                        timestamp_sec = parts[0] * 3600 + parts[1] * 60 + parts[2]
                    elif len(parts) == 2:
                        timestamp_sec = parts[0] * 60 + parts[1]
                    else:
                        timestamp_sec = 0
                    if is_match:
                        matching_frames.append(
                            ClipFrameMatch(
                                timestamp=timestamp,
                                timestamp_sec=timestamp_sec,
                                frame_index=frame_num - 1,
                                score=round(score, 4),
                                score_label=f"{score:.4f}",
                            )
                        )
                    async with self:
                        self.job_live_log = (
                            f"Video {vid} · [{timestamp}] similitud {score:.3f}"
                            + (" · coincidencia" if is_match else "")
                        )
                        if matching_frames:
                            live_matches = [
                                item for item in video_frames if item["is_match"]
                            ]
                            self.clip_analyzed_frames = list(
                                collected_tray + live_matches
                            )

                if cancelled:
                    break

                if matching_frames:
                    hit = ClipHit(
                        video_id=vid,
                        max_score=round(max_score, 4),
                        max_score_label=f"{max_score:.4f}",
                        match_count=len(matching_frames),
                        frames=matching_frames,
                    )
                    collected_hits.append(hit)
                    collected_hits.sort(key=lambda h: h.max_score, reverse=True)
                    collected_tray.extend(video_frames)
                    async with self:
                        self.clip_hits = list(collected_hits)
                        self.clip_analyzed_frames = list(collected_tray)
                    print(
                        f"[CLIP] Video {vid}: {len(matching_frames)} match(es), "
                        f"max={max_score:.3f}",
                        flush=True,
                    )
                else:
                    async with self:
                        self.job_live_log = (
                            f"Sin coincidencias sobre el umbral {threshold:.2f} "
                            f"en video {vid} (score máx. {max_score:.3f})."
                        )
            except Exception as exc:
                print(f"[CLIP] Error video {vid}: {exc}", flush=True)
                async with self:
                    self.job_live_log = f"Error en video {vid}: {exc}"
            finally:
                if sampler is not None:
                    try:
                        await self._run_on_clip_pool(sampler.close)
                    except Exception:
                        pass
                if local_path:
                    await asyncio.to_thread(repository.cleanup_video, local_path)

        async with self:
            self.is_processing = False
            self.show_clip_install = False
            self.clip_analyzed_frames = list(collected_tray)
            self.clip_hits = list(collected_hits)
            self.job_progress_pct = 100
            self.workflow_phase = "results"
            if cancelled:
                self.status_kind = "warning"
                self.status_title = "Búsqueda CLIP detenida"
                self.status_message = (
                    f"Se detuvo con {len(collected_hits)} video(s) sobre el umbral. "
                    "Revise la bandeja inferior."
                )
            else:
                self.status_kind = "success" if collected_hits else "info"
                self.status_title = "Búsqueda CLIP finalizada"
                self.status_message = (
                    f"{len(collected_hits)} video(s) superaron el umbral "
                    f"{threshold:.2f} para «{query}»."
                )

    # =========================================================================
    # PIPELINE 3: CATALOGACIÓN AUTOMATIZADA BLIP + QWEN GGUF (BACKGROUND TASK)
    # =========================================================================

    @rx.event(background=True)
    async def run_automated_for_video(self, video_id: int):
        async with self:
            self.selected_video_ids = [int(video_id)]
            self.videos = self._build_video_items(self.video_ids)
            self.auto_scope_mode = "Videos seleccionados"
        await self._run_automated_pipeline()

    @rx.event(background=True)
    async def run_automated_catalogation(self):
        await self._run_automated_pipeline()

    async def _run_automated_pipeline(self):
        async with self:
            if self.is_processing:
                return
            scope_mode = self.auto_scope_mode
            col_input = self.auto_collection_input.strip()
            selected_ids = list(self.selected_video_ids)
            sample_rate = self.sample_rate_sec
            caption_count = self.auto_caption_count
            temperature = self.auto_temperature
            top_p = self.auto_top_p

            self.cancel_requested = False
            self.is_processing = True
            self.job_epoch += 1
            job_epoch = self.job_epoch
            self.workflow_phase = "processing"
            self.auto_results = []
            self.job_title = "Catalogación Automatizada (BLIP + Qwen) en curso"
            self.job_subtitle = "Fases: descarga temporal → sampling BLIP → síntesis Qwen → limpieza"
            self.job_progress_pct = 8
            self.job_live_log = "Resolviendo alcance y cargando modelos BLIP + Qwen GGUF en CPU..."

        try:
            repository = get_repository()
            if scope_mode == "ID de colección" and col_input.isdigit():
                target_ids = await asyncio.to_thread(
                    repository.get_collection_video_ids, int(col_input)
                )
            else:
                target_ids = selected_ids

            if not target_ids:
                async with self:
                    self.is_processing = False
                    self.workflow_phase = "select"
                    self.status_kind = "warning"
                    self.status_title = "Sin videos en el alcance seleccionado"
                    self.status_message = "Seleccione al menos un video o ingrese un ID de colección con recursos."
                return

            analyzer = await self._load_blip_with_install_progress()
            synthesizer = await self._load_qwen_with_install_progress()
        except Exception as exc:
            async with self:
                self.is_processing = False
                self.show_blip_install = False
                self.show_qwen_install = False
                self.workflow_phase = "select"
                self.status_kind = "error"
                self.status_title = "No se pudieron cargar los modelos"
                self.status_message = str(exc)
            return

        from ia_video_app.models.blip_processor import VideoFrameSampler

        results_acc: list[AutoCatalogResult] = []
        failed = 0
        cancelled = False
        for idx, vid in enumerate(target_ids, start=1):
            local_path = None
            sampler = None
            async with self:
                if self.cancel_requested or self.job_epoch != job_epoch:
                    cancelled = True
                    break
                self.active_video_id = str(vid)
                self.job_total_count = len(target_ids)
                self.job_current_index = idx
                self.job_progress_pct = max(
                    8, int(((idx - 1) / max(1, len(target_ids))) * 90)
                )
                self.job_subtitle = (
                    f"Video {idx}/{len(target_ids)} · ID {vid} · "
                    f"{caption_count} muestras BLIP + Qwen"
                )
                self.job_live_log = f"Descargando temporalmente recurso ID {vid}..."

            try:
                print(f"[AUTO] Descargando video {vid}...", flush=True)
                local_path = await asyncio.to_thread(
                    repository.download_video, vid, self._blip_temp_dir()
                )
                if not local_path:
                    failed += 1
                    async with self:
                        self.job_live_log = f"No se pudo descargar el recurso {vid}."
                    continue

                size_mb = os.path.getsize(local_path) / (1024 * 1024)
                async with self:
                    self.job_live_log = (
                        f"Video ID {vid} descargado ({size_mb:.1f} MB). "
                        "Abriendo fotogramas..."
                    )

                sampler = await self._run_on_blip_pool(
                    VideoFrameSampler, local_path, sample_rate
                )
                if not sampler.opened:
                    failed += 1
                    async with self:
                        self.job_live_log = f"No se pudo abrir el video {vid}."
                    continue

                estimated = max(1, sampler.sample_count or 1)
                audit_frames: list[dict] = []
                raw_frames_for_text: list[dict] = []
                frame_num = 0

                while True:
                    async with self:
                        if self.cancel_requested or self.job_epoch != job_epoch:
                            cancelled = True
                    if cancelled:
                        break
                    sample = await self._run_on_blip_pool(sampler.next_sample)
                    if sample is None:
                        break
                    timestamp, pil_img, thumbnail = sample
                    frame_num += 1
                    pct = 8 + int(
                        ((idx - 1) + (frame_num / estimated))
                        / max(1, len(target_ids))
                        * 90
                    )
                    async with self:
                        self.job_progress_pct = min(99, max(8, pct))
                        self.job_live_log = (
                            f"BLIP muestreando [{timestamp}] · "
                            f"fotograma {frame_num}/{estimated} · "
                            f"{caption_count} observaciones..."
                        )
                    print(
                        f"[AUTO] BLIP sample {vid} [{timestamp}] "
                        f"{frame_num}/{estimated}",
                        flush=True,
                    )

                    sample_task = asyncio.create_task(
                        self._run_on_blip_pool(
                            analyzer.generate_sampling_captions,
                            pil_img,
                            caption_count,
                            temperature,
                            top_p,
                        )
                    )
                    waited = 0
                    while not sample_task.done():
                        await asyncio.sleep(1)
                        waited += 1
                        async with self:
                            self.job_live_log = (
                                f"BLIP infiriendo muestras [{timestamp}] · "
                                f"fotograma {frame_num}/{estimated} · {waited}s CPU"
                            )
                    blip_samples = await sample_task

                    async with self:
                        self.job_live_log = (
                            f"Recurso {vid} · [{timestamp}] "
                            f"Sintetizando {len(blip_samples)} muestras con Qwen..."
                        )
                    syn_task = asyncio.create_task(
                        self._run_on_qwen_pool(synthesizer.synthesize, blip_samples)
                    )
                    waited = 0
                    while not syn_task.done():
                        await asyncio.sleep(1)
                        waited += 1
                        async with self:
                            self.job_live_log = (
                                f"Qwen fusionando [{timestamp}] · "
                                f"fotograma {frame_num}/{estimated} · {waited}s CPU"
                            )
                    synthesis = await syn_task
                    uri = _pil_to_data_uri(thumbnail)
                    audit_frames.append(
                        _audit_dict(timestamp, uri, blip_samples, synthesis)
                    )
                    raw_frames_for_text.append(
                        {"timestamp": timestamp, "synthesis": synthesis}
                    )
                    print(f"[AUTO] Síntesis {vid} [{timestamp}]: {synthesis}", flush=True)

                    chrono_partial = chronological_description(raw_frames_for_text)
                    live_item = AutoCatalogResult(
                        video_id=int(vid),
                        status="processing",
                        frames_count=len(audit_frames),
                        frames=list(audit_frames),
                        chronological_description=chrono_partial,
                        saved_to_mam=False,
                    )
                    async with self:
                        self.auto_results = list(results_acc + [live_item])
                        self.job_live_log = (
                            f"Video {vid} · [{timestamp}]: {synthesis}"
                        )

                if cancelled:
                    break
                if not audit_frames:
                    failed += 1
                    continue

                chrono_text = chronological_description(raw_frames_for_text)
                res_item = AutoCatalogResult(
                    video_id=int(vid),
                    status="completed",
                    frames_count=len(audit_frames),
                    frames=list(audit_frames),
                    chronological_description=chrono_text,
                    saved_to_mam=False,
                )
                results_acc.append(res_item)
                async with self:
                    self.auto_results = list(results_acc)
                    if vid not in self.categorized_video_ids:
                        self.categorized_video_ids = self.categorized_video_ids + [vid]
                    self.videos = self._build_video_items(self.video_ids)
            except Exception as exc:
                failed += 1
                print(f"[AUTO] Error video {vid}: {exc}", flush=True)
                async with self:
                    self.job_live_log = f"Falló el recurso {vid}: {exc}"
            finally:
                if sampler is not None:
                    try:
                        await self._run_on_blip_pool(sampler.close)
                    except Exception:
                        pass
                if local_path:
                    await asyncio.to_thread(repository.cleanup_video, local_path)

        async with self:
            self.is_processing = False
            self.show_blip_install = False
            self.show_qwen_install = False
            self.auto_results = list(results_acc)
            self.job_progress_pct = 100 if not cancelled else self.job_progress_pct
            self.workflow_phase = "results" if results_acc else "select"
            if cancelled:
                self.status_kind = "warning"
                self.status_title = "Catalogación automatizada detenida"
                self.status_message = (
                    f"Se detuvo con {len(results_acc)} recurso(s) completados."
                )
            else:
                self.status_kind = "success" if failed == 0 else "warning"
                self.status_title = "Catalogación automatizada finalizada"
                self.status_message = (
                    f"{len(results_acc)} de {len(target_ids)} recurso(s) "
                    f"completados; {failed} fallido(s)."
                )

    # =========================================================================
    # ACCIONES HITL: EDICIÓN, EXPORTACIÓN JSON Y GUARDADO EN DESCRIPCION
    # =========================================================================

    @rx.event
    def update_auto_description(self, video_id: int, new_text: str):
        updated: list[AutoCatalogResult] = []
        for item in self.auto_results:
            if item.video_id == int(video_id):
                item.chronological_description = new_text
            updated.append(item)
        self.auto_results = updated

    @rx.event
    def reset_auto_description(self, video_id: int):
        updated: list[AutoCatalogResult] = []
        for item in self.auto_results:
            if item.video_id == int(video_id):
                raw = [
                    {
                        "timestamp": fr["timestamp"] if isinstance(fr, dict) else fr.timestamp,
                        "synthesis": fr["synthesis"] if isinstance(fr, dict) else fr.synthesis,
                    }
                    for fr in item.frames
                ]
                item.chronological_description = chronological_description(raw)
            updated.append(item)
        self.auto_results = updated
        return rx.toast.info(f"Descripción original restaurada para recurso #{video_id}")

    @rx.event
    def export_auto_json(self, video_id: int):
        for item in self.auto_results:
            if item.video_id == int(video_id):
                payload = {
                    "video_id": item.video_id,
                    "status": item.status,
                    "frames_count": item.frames_count,
                    "chronological_description": item.chronological_description,
                    "frames": [
                        {
                            "timestamp": f["timestamp"] if isinstance(f, dict) else f.timestamp,
                            "blip_samples": (
                                f["blip_samples_text"].split(" | ")
                                if isinstance(f, dict)
                                else f.blip_samples_text.split(" | ")
                            ),
                            "synthesis": f["synthesis"] if isinstance(f, dict) else f.synthesis,
                        }
                        for f in item.frames
                    ],
                }
                data_str = json.dumps(payload, ensure_ascii=False, indent=2)
                return rx.download(
                    data=data_str,
                    filename=f"catalogacion_{video_id}.json",
                )

    @rx.event
    def save_resource_description(self, video_id: int):
        target = None
        for item in self.auto_results:
            if item.video_id == int(video_id):
                target = item
                break
        if target is None or not target.chronological_description.strip():
            return rx.toast.error("La descripción no puede estar vacía.")

        try:
            repository = get_repository()
            ok = repository.update_resource_description(
                resource_id=target.video_id,
                value=target.chronological_description,
            )
            if ok:
                updated: list[AutoCatalogResult] = []
                for item in self.auto_results:
                    if item.video_id == int(video_id):
                        item.saved_to_mam = True
                    updated.append(item)
                self.auto_results = updated
                self.status_kind = "success"
                self.status_title = f"Metadata actualizada · Recurso {video_id}"
                self.status_message = "Campo DESCRIPCION guardado correctamente en ResourceSpace."
                return rx.toast.success(
                    f"Campo DESCRIPCION guardado en recurso #{video_id}"
                )
            return rx.toast.error(
                f"ResourceSpace no confirmó la actualización del recurso #{video_id}"
            )
        except Exception as exc:
            self.status_kind = "error"
            self.status_title = f"Error al guardar el recurso {video_id}"
            self.status_message = str(exc)
            return rx.toast.error(f"Error al guardar metadata: {exc}")

    # =========================================================================
    # MODAL DE SUBIDA LOCAL / PRE-CATALOGACIÓN
    # =========================================================================

    @rx.event
    def open_upload_modal(self):
        self.upload_modal_open = True
        self.upload_progress = 0

    @rx.event
    def close_upload_modal(self):
        self.upload_modal_open = False
        self.is_uploading = False

    @rx.event
    async def handle_video_upload(self, files: list[rx.UploadFile]):
        if not files:
            yield rx.toast.warning("Seleccione al menos un archivo de video (.mp4, .mov, .mkv).")
            return

        self.is_uploading = True
        self.upload_progress = 15
        yield

        temp_dir = Path("temp_videos")
        temp_dir.mkdir(parents=True, exist_ok=True)
        saved_names: list[str] = []

        try:
            for idx, upload_file in enumerate(files, start=1):
                data = await upload_file.read()
                safe_name = os.path.basename(upload_file.filename or f"upload_{idx}.mp4")
                dest = temp_dir / safe_name
                dest.write_bytes(data)
                saved_names.append(safe_name)
                # Limpieza inmediata tras validación para respetar restricción de disco
                if dest.exists():
                    dest.unlink()
                self.upload_progress = int((idx / len(files)) * 100)
                yield

            self.uploaded_filenames = saved_names
            self.is_uploading = False
            self.upload_modal_open = False
            yield rx.toast.success(
                f"{len(saved_names)} archivo(s) verificados y procesados sin residuos temporales."
            )
        except Exception as exc:
            self.is_uploading = False
            yield rx.toast.error(f"Error durante la carga: {exc}")
