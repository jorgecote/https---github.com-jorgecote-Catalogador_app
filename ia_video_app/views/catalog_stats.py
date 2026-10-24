import reflex as rx
from ia_video_app.controllers.catalog_state import CatalogState
from ia_video_app.views import theme


def _stat_card(
    icon_name: str,
    label: str,
    value_expr,
    subtext: str,
    accent_color: str,
) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon(icon_name, size=20, color=accent_color),
                background=theme.BG_SUBTLE,
                padding="10px",
                border_radius="8px",
                border=f"1px solid {theme.BORDER_MEDIUM}",
            ),
            rx.vstack(
                rx.text(
                    label,
                    font_size="0.76rem",
                    font_weight="600",
                    color=theme.TEXT_MUTED,
                    text_transform="uppercase",
                    letter_spacing="0.4px",
                ),
                rx.text(
                    value_expr,
                    font_size="1.25rem",
                    font_weight="700",
                    color=theme.TEXT_PRIMARY,
                ),
                rx.text(
                    subtext,
                    font_size="0.74rem",
                    color=theme.TEXT_MUTED,
                ),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        background=theme.BG_CARD,
        border=f"1px solid {theme.BORDER_LIGHT}",
        border_left=f"4px solid {accent_color}",
        border_radius="8px",
        padding="14px 16px",
        box_shadow="0 1px 2px rgba(0, 0, 0, 0.04)",
    )


def render_catalog_stats() -> rx.Component:
    return rx.grid(
        _stat_card(
            "video",
            "Total Videos en Ámbito",
            CatalogState.total_videos_count.to_string(),
            CatalogState.selected_collection_label,
            theme.PRIMARY_BLUE,
        ),
        _stat_card(
            "check_check",
            "Categorizados en Sesión",
            CatalogState.categorized_count.to_string(),
            "Con captions o traza generada",
            "#15803D",
        ),
        _stat_card(
            "clock",
            "Pendientes de Procesar",
            CatalogState.pending_count.to_string(),
            f"Seleccionados ahora: {CatalogState.selected_count}",
            "#B45309",
        ),
        _stat_card(
            "hard_drive",
            "Entorno CPU / Pesos",
            CatalogState.storage_used_label,
            "Limpieza temporal inmediata",
            theme.BRAND_VIOLET,
        ),
        columns=rx.breakpoints(initial="1", sm="2", lg="4"),
        spacing="3",
        width="100%",
    )
