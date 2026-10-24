import reflex as rx
from ia_video_app.controllers.catalog_state import CatalogState
from ia_video_app.models.schemas import AutoCatalogResult
from ia_video_app.views import theme
from ia_video_app.views.blip_workspace import (
    render_blip_install_progress,
    render_job_progress_panel,
    render_qwen_install_progress,
)


def _audit_frame_row(frame: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.cond(
                frame["image_data_uri"] != "",
                rx.image(
                    src=frame["image_data_uri"],
                    width="180px",
                    height="102px",
                    object_fit="cover",
                    border_radius="6px",
                ),
                rx.box(
                    rx.text("Sin miniatura", font_size="0.75rem", color=theme.TEXT_MUTED),
                    width="180px",
                    height="102px",
                    background=theme.BG_SUBTLE,
                    border_radius="6px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
            ),
            rx.vstack(
                rx.hstack(
                    rx.badge(
                        frame["timestamp"],
                        background=theme.PRIMARY_BLUE,
                        color="#FFFFFF",
                    ),
                    rx.text(
                        "Traza auditable del fotograma",
                        font_size="0.78rem",
                        font_weight="700",
                        color=theme.TEXT_MUTED,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "Muestras BLIP: ",
                    frame["blip_samples_text"],
                    font_size="0.8rem",
                    color=theme.TEXT_MUTED,
                ),
                rx.text(
                    "Síntesis Qwen: ",
                    frame["synthesis"],
                    font_size="0.86rem",
                    font_weight="700",
                    color=theme.TEXT_PRIMARY,
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            spacing="3",
            align="start",
            width="100%",
            wrap="wrap",
        ),
        padding="10px",
        border_bottom=f"1px solid {theme.BORDER_LIGHT}",
        width="100%",
    )


def _auto_result_card(result: AutoCatalogResult) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    f"Recurso ID #{result.video_id} · {result.frames_count} fotogramas sintetizados",
                    font_size="1rem",
                    font_weight="700",
                    color=theme.TEXT_PRIMARY,
                ),
                rx.spacer(),
                rx.cond(
                    result.saved_to_mam,
                    rx.badge(
                        "Guardado en DESCRIPCION",
                        background=theme.STATUS_OK_SOFT_BG,
                        color=theme.STATUS_OK_SOFT_TEXT,
                    ),
                    rx.badge(
                        "Pendiente de revisión humana",
                        background=theme.STATUS_INFO_SOFT_BG,
                        color=theme.STATUS_INFO_SOFT_TEXT,
                    ),
                ),
                width="100%",
                align="center",
            ),
            rx.text(
                "Descripción cronológica consolidada (editable antes de sincronizar con ResourceSpace):",
                font_size="0.82rem",
                font_weight="600",
                color=theme.TEXT_MUTED,
            ),
            rx.text_area(
                value=result.chronological_description,
                on_change=lambda val: CatalogState.update_auto_description(
                    result.video_id, val
                ),
                style=theme.INPUT_LIGHT_STYLE,
                width="100%",
                min_height="150px",
            ),
            rx.hstack(
                rx.button(
                    rx.icon("download", size=15),
                    "Exportar JSON",
                    on_click=CatalogState.export_auto_json(result.video_id),
                    style=theme.SECONDARY_BUTTON_STYLE,
                    size="2",
                ),
                rx.button(
                    "Restaurar original",
                    on_click=CatalogState.reset_auto_description(result.video_id),
                    style=theme.SECONDARY_BUTTON_STYLE,
                    size="2",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("save", size=15),
                    "Guardar en DESCRIPCION (ResourceSpace)",
                    on_click=CatalogState.save_resource_description(result.video_id),
                    style=theme.PRIMARY_BUTTON_STYLE,
                    size="2",
                ),
                width="100%",
                align="center",
                wrap="wrap",
                spacing="2",
            ),
            rx.divider(),
            rx.text(
                "Desglose Auditable por Fotograma (Miniatura + Muestras BLIP + Síntesis Qwen):",
                font_size="0.82rem",
                font_weight="700",
                color=theme.PRIMARY_NAVY,
            ),
            rx.vstack(
                rx.foreach(result.frames, _audit_frame_row),
                spacing="1",
                width="100%",
                max_height="340px",
                overflow_y="auto",
            ),
            spacing="3",
            width="100%",
        ),
        style=theme.CARD_STYLE,
    )


def _auto_disconnected_gate() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                "Conéctese primero a ByteBox",
                font_size="1.02rem",
                font_weight="700",
                color=theme.TEXT_PRIMARY,
            ),
            rx.text(
                "La catalogación automatizada reutiliza la misma sesión autenticada de ResourceSpace.",
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


def render_auto_workspace() -> rx.Component:
    return rx.cond(
        ~CatalogState.is_connected,
        _auto_disconnected_gate(),
        rx.vstack(
        rx.cond(
            ~CatalogState.is_processing,
        rx.box(
            rx.vstack(
                rx.text(
                    "Alcance de Catalogación Automatizada (BLIP Multi-Sampling + Qwen2.5-1.5B GGUF)",
                    font_size="1.02rem",
                    font_weight="700",
                    color=theme.TEXT_PRIMARY,
                ),
                rx.text(
                    "BLIP genera múltiples observaciones con temperatura y top-p progresivos; Qwen las fusiona en una idea cohesiva en español y permite guardar el resultado en el campo DESCRIPCION de ResourceSpace.",
                    font_size="0.84rem",
                    color=theme.TEXT_MUTED,
                ),
                rx.hstack(
                    rx.select(
                        ["Videos seleccionados", "ID de colección"],
                        value=CatalogState.auto_scope_mode,
                        on_change=CatalogState.set_auto_scope_mode,
                        width="220px",
                    ),
                    rx.cond(
                        CatalogState.auto_scope_mode == "ID de colección",
                        rx.input(
                            placeholder="ID numérico de colección (ej. 125)",
                            value=CatalogState.auto_collection_input,
                            on_change=CatalogState.set_auto_collection_input,
                            style=theme.INPUT_LIGHT_STYLE,
                            width="240px",
                        ),
                        rx.badge(
                            f"Videos marcados en el catálogo: {CatalogState.selected_count}",
                            color_scheme="blue",
                        ),
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("sparkles", size=16),
                        "Ejecutar Síntesis BLIP + Qwen",
                        on_click=CatalogState.run_automated_catalogation,
                        disabled=~CatalogState.can_start_automated,
                        style=theme.PRIMARY_BUTTON_STYLE,
                        size="2",
                    ),
                    width="100%",
                    align="center",
                    wrap="wrap",
                    spacing="3",
                ),
                spacing="3",
                width="100%",
            ),
            style=theme.CARD_STYLE,
        ),
        ),
        render_blip_install_progress(),
        render_qwen_install_progress(),
        render_job_progress_panel(),
        rx.cond(
            (CatalogState.workflow_phase == "results")
            & (CatalogState.auto_results.length() > 0)
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
            CatalogState.auto_results.length() > 0,
            rx.vstack(
                rx.foreach(CatalogState.auto_results, _auto_result_card),
                spacing="3",
                width="100%",
            ),
        ),
        rx.cond(
            CatalogState.workflow_phase == "results",
            rx.button(
                "Nueva catalogación automatizada",
                on_click=CatalogState.start_new_auto_catalog,
                style=theme.SECONDARY_BUTTON_STYLE,
                size="2",
            ),
        ),
        spacing="4",
        width="100%",
        ),
    )
