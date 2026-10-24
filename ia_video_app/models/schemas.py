from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CollectionItem:
    """Colección de ResourceSpace disponible en el selector."""

    ref: int
    name: str
    count: Optional[int] = None
    label: str = ""


@dataclass
class VideoItem:
    """Representación tipada de un recurso de video en el catálogo."""

    video_id: int
    title: str = ""
    category: str = "Repositorio DAM"
    status: str = "Pendiente"
    date_label: str = "Sincronizado"
    tags: list[str] = field(default_factory=list)
    selected: bool = False
    frames_count: int = 0
    summary_preview: str = ""


@dataclass
class FrameAnalysis:
    """Fotograma procesado por BLIP o CLIP con miniatura codificada en Base64."""

    video_id: int
    timestamp: str
    caption: str
    image_data_uri: str = ""
    is_match: bool = False
    score: float = 0.0


@dataclass
class ClipFrameMatch:
    """Fotograma que supera el umbral de similitud en búsqueda CLIP."""

    timestamp: str
    timestamp_sec: int
    frame_index: int
    score: float
    score_label: str = ""


@dataclass
class ClipHit:
    """Resultado agrupado por video en búsqueda semántica CLIP."""

    video_id: int
    max_score: float = 0.0
    max_score_label: str = ""
    match_count: int = 0
    frames: list[ClipFrameMatch] = field(default_factory=list)


@dataclass
class AuditFrameItem:
    """Traza auditable de un fotograma para catalogación automatizada BLIP + Qwen."""

    timestamp: str
    image_data_uri: str = ""
    blip_samples_text: str = ""
    synthesis: str = ""


@dataclass
class AutoCatalogResult:
    """Resultado consolidado por video en catalogación automatizada."""

    video_id: int
    status: str = "completed"
    frames_count: int = 0
    frames: list[dict] = field(default_factory=list)
    chronological_description: str = ""
    saved_to_mam: bool = False
