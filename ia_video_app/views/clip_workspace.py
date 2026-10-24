import reflex as rx
from ia_video_app.controllers.catalog_state import CatalogState
from ia_video_app.models.schemas import ClipFrameMatch, ClipHit
from ia_video_app.views import theme
from ia_video_app.views.blip_workspace import (
    render_clip_install_progress,
    render_collection_tray,
    render_job_progress_panel,
)


def _clip_frame_row(fr: ClipFrameMatch) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.badge(fr.timestamp, background=theme.PRIMARY_BLUE, color="#FFFFFF")
        ),
        rx.table.cell(rx.text(f"{fr.timestamp_sec} s", font_size="0.82rem")),
        rx.table.cell(rx.text(f"#{fr.frame_index}", font_size="0.82rem")),
        rx.table.cell(
            rx.badge(
                fr.score_label,
                background=theme.PRIMARY_NAVY,
                color="#FFFFFF",
            )
        ),
    )


def _clip_hit_card(hit: ClipHit) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    f"Recurso Video ID #{hit.video_id}",
                    font_size="0.98rem",
                    font_weight="700",
                    color=theme.TEXT_PRIMARY,
                ),
                rx.badge(
                    f"{hit.match_count} coincidencia(s)",
                    background=theme.STATUS_OK_SOFT_BG,
                    color=theme.STATUS_OK_SOFT_TEXT,
                ),
                rx.spacer(),
                rx.badge(
                    f"Max Score: {hit.max_score_label}",
                    background=theme.PRIMARY_NAVY,
                    color="#FFFFFF",
                ),
                width="100%",
                align="center",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Timestamp"),
                        rx.table.column_header_cell("Segundos"),
                        rx.table.column_header_cell("Frame Muestreado"),
                        rx.table.column_header_cell("Similitud CLIP"),
                    )
                ),
                rx.table.body(rx.foreach(hit.frames, _clip_frame_row)),
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        style=theme.CARD_STYLE,
    )


def _clip_disconnected_gate() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                "Conéctese primero a ByteBox",
                font_size="1.02rem",
                font_weight="700",
                color=theme.TEXT_PRIMARY,
            ),
            rx.text(
                "CLIP reutiliza la misma sesión autenticada. Vuelva a catalogación BLIP o pulse el botón de la pantalla principal.",
                font_size="0.86rem",
                color=theme.TEXT_MUTED,
            ),
            rx.button(
                "Volver a catalogación BLIP",
                on_click=CatalogState.set_active_module("blip"),
                style=theme.SECONDARY_BUTTON_STYLE,
                size="2",
            ),
            spacing="2",
            align="start",
        ),
        style=theme.CARD_STYLE,
    )


def render_clip_workspace() -> rx.Component:
    return rx.cond(
        ~CatalogState.is_connected,
        _clip_disconnected_gate(),
        rx.vstack(
            rx.cond(
                ~CatalogState.is_processing,
                rx.box(
                    rx.vstack(
                        rx.text(
                            "Búsqueda Semántica por Lenguaje Natural (CLIP ViT-B/32)",
                            font_size="1.05rem",
                            font_weight="700",
                            color=theme.TEXT_PRIMARY,
                        ),
                        rx.text(
                            "Describa la escena, acción u objeto que desea localizar. CLIP puntuará los fotogramas de los videos filtrados contra su consulta.",
                            font_size="0.85rem",
                            color=theme.TEXT_MUTED,
                        ),
                        rx.text_area(
                            placeholder="Ejemplo: persona caminando de noche cerca de un edificio iluminado...",
                            value=CatalogState.clip_query,
                            on_change=CatalogState.set_clip_query,
                            style=theme.INPUT_LIGHT_STYLE,
                            width="100%",
                            min_height="90px",
                        ),
                        rx.hstack(
                            rx.badge(
                                f"Videos en ámbito: {CatalogState.filtered_videos.length()}",
                                color_scheme="blue",
                            ),
                            rx.badge(
                                f"Umbral actual: {CatalogState.clip_threshold}",
                                color_scheme="gray",
                            ),
                            rx.spacer(),
                            rx.button(
                                rx.icon("search", size=16),
                                "Buscar videos",
                                on_click=CatalogState.run_clip_search,
                                disabled=~CatalogState.can_start_clip,
                                style=theme.PRIMARY_BUTTON_STYLE,
                                size="2",
                            ),
                            width="100%",
                            align="center",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    style=theme.CARD_STYLE,
                ),
            ),
            render_clip_install_progress(),
            render_job_progress_panel(),
            rx.cond(
                (CatalogState.workflow_phase == "results")
                & (CatalogState.clip_last_query != "")
                & ~CatalogState.is_processing,
                rx.box(
                    rx.vstack(
                        rx.text(
                            CatalogState.status_title,
                            font_size="1rem",
                            font_weight="700",
                            color=theme.PRIMARY_NAVY,
                        ),
                        rx.text(
                            CatalogState.status_message,
                            font_size="0.86rem",
                            color=theme.TEXT_MUTED,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    style=theme.CARD_STYLE,
                ),
            ),
            rx.cond(
                CatalogState.clip_hits.length() > 0,
                rx.vstack(
                    rx.text(
                        "Videos con coincidencias sobre el umbral (ordenados por relevancia)",
                        font_size="0.95rem",
                        font_weight="700",
                        color=theme.TEXT_PRIMARY,
                    ),
                    rx.foreach(CatalogState.clip_hits, _clip_hit_card),
                    spacing="3",
                    width="100%",
                ),
            ),
            rx.cond(
                CatalogState.workflow_phase == "results",
                rx.button(
                    "Nueva consulta",
                    on_click=CatalogState.start_new_clip_query,
                    style=theme.SECONDARY_BUTTON_STYLE,
                    size="2",
                ),
            ),
            render_collection_tray(
                title="Fotogramas de Videos con Coincidencias CLIP",
                empty_message="Ejecute una consulta en lenguaje natural arriba; aquí se mostrarán los fotogramas de los videos que superen el umbral resaltando las coincidencias.",
            ),
            spacing="4",
            width="100%",
        ),
    )
