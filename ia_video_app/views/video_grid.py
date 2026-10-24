import reflex as rx
from ia_video_app.controllers.catalog_state import CatalogState
from ia_video_app.models.schemas import VideoItem
from ia_video_app.views import theme


def _skeleton_grid() -> rx.Component:
    return rx.grid(
        rx.foreach(
            [1, 2, 3, 4, 5, 6],
            lambda _: rx.box(
                rx.vstack(
                    rx.skeleton(height="22px", width="60%"),
                    rx.skeleton(height="16px", width="85%"),
                    rx.skeleton(height="32px", width="100%"),
                    spacing="3",
                    align="start",
                ),
                style=theme.CARD_STYLE,
            ),
        ),
        columns=rx.breakpoints(initial="1", sm="2", lg="3"),
        spacing="3",
        width="100%",
    )


def _disconnected_empty_state() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.text(
                    "Organice sus materiales de video con IA",
                    font_size="1.35rem",
                    font_weight="700",
                    color=theme.PRIMARY_NAVY,
                    text_align="center",
                ),
                rx.text(
                    "Conéctese a ByteBox para catalogar fotogramas con BLIP o buscar escenas en lenguaje natural con CLIP.",
                    font_size="0.92rem",
                    color=theme.TEXT_MUTED,
                    text_align="center",
                    max_width="620px",
                ),
                spacing="2",
                align="center",
            ),
            width="100%",
            padding="28px 24px",
            border_radius="8px",
            background=theme.STATUS_INFO_SOFT_BG,
            border=f"1px solid {theme.PRIMARY_BLUE}",
        ),
        rx.box(
            rx.vstack(
                rx.text(
                    "Conexión con el repositorio MAM",
                    font_size="1.02rem",
                    font_weight="700",
                    color=theme.TEXT_PRIMARY,
                ),
                rx.text(
                    "Tras conectar podrá: 1) seleccionar una colección, 2) catalogar videos con BLIP o 3) buscar fotogramas con CLIP. Ambos modos reutilizan la misma sesión.",
                    font_size="0.86rem",
                    color=theme.TEXT_MUTED,
                ),
                rx.button(
                    "Iniciar conexión con ByteBox",
                    on_click=CatalogState.connect_resourcespace,
                    loading=CatalogState.is_loading,
                    disabled=CatalogState.is_loading,
                    style=theme.PRIMARY_BUTTON_STYLE,
                    size="3",
                    width="100%",
                    max_width="420px",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            style=theme.CARD_STYLE,
        ),
        spacing="4",
        width="100%",
    )


def _no_results_empty_state() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.icon("search_x", size=28, color=theme.TEXT_MUTED),
            rx.text(
                "No se encontraron recursos con los filtros actuales",
                font_size="1rem",
                font_weight="700",
                color=theme.TEXT_PRIMARY,
            ),
            rx.text(
                "Pruebe limpiando el filtro de búsqueda o seleccionando otra colección en el panel lateral.",
                font_size="0.84rem",
                color=theme.TEXT_MUTED,
            ),
            rx.button(
                "Restablecer filtros",
                on_click=CatalogState.clear_filters,
                style=theme.SECONDARY_BUTTON_STYLE,
                size="2",
            ),
            spacing="2",
            align="center",
            padding_y="18px",
        ),
        style=theme.CARD_STYLE,
    )


def _video_card(item: VideoItem) -> rx.Component:
    is_done = item.status == "Catalogado"
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.checkbox(
                    checked=item.selected,
                    on_change=lambda _: CatalogState.toggle_video_selection(
                        item.video_id
                    ),
                ),
                rx.text(
                    f"ID #{item.video_id}",
                    font_size="0.95rem",
                    font_weight="700",
                    color=theme.TEXT_PRIMARY,
                ),
                rx.spacer(),
                rx.badge(
                    item.status,
                    background=rx.cond(
                        is_done,
                        theme.STATUS_OK_SOFT_BG,
                        theme.STATUS_WARN_SOFT_BG,
                    ),
                    color=rx.cond(
                        is_done,
                        theme.STATUS_OK_SOFT_TEXT,
                        theme.STATUS_WARN_SOFT_TEXT,
                    ),
                ),
                width="100%",
                align="center",
            ),
            rx.text(
                item.title,
                font_size="0.84rem",
                font_weight="600",
                color=theme.TEXT_MUTED,
            ),
            rx.hstack(
                rx.badge(item.category, variant="surface", color_scheme="gray"),
                rx.spacer(),
                rx.cond(
                    CatalogState.active_module == "clip",
                    rx.badge("En ámbito CLIP", variant="surface", color_scheme="blue"),
                    rx.cond(
                        CatalogState.active_module == "automated",
                        rx.button(
                            rx.icon("play", size=13),
                            "Analizar",
                            size="1",
                            on_click=CatalogState.run_automated_for_video(item.video_id),
                            disabled=CatalogState.is_processing,
                            style=theme.SECONDARY_BUTTON_STYLE,
                        ),
                        rx.button(
                            rx.icon("play", size=13),
                            "Analizar",
                            size="1",
                            on_click=CatalogState.run_blip_for_video(
                                item.video_id
                            ),
                            disabled=CatalogState.is_processing,
                            style=theme.SECONDARY_BUTTON_STYLE,
                        ),
                    ),
                ),
                width="100%",
                align="center",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        background=rx.cond(item.selected, theme.STATUS_INFO_SOFT_BG, theme.BG_CARD),
        border=rx.cond(
            item.selected,
            f"2px solid {theme.PRIMARY_BLUE}",
            f"1px solid {theme.BORDER_LIGHT}",
        ),
        border_radius="8px",
        padding="14px 16px",
        transition="all 0.15s ease-in-out",
        _hover={"border_color": theme.PRIMARY_BLUE},
    )


def render_video_grid() -> rx.Component:
    return rx.cond(
        CatalogState.is_loading,
        _skeleton_grid(),
        rx.cond(
            ~CatalogState.is_connected,
            _disconnected_empty_state(),
            rx.cond(
                CatalogState.filtered_videos.length() == 0,
                _no_results_empty_state(),
                rx.vstack(
                    rx.grid(
                        rx.foreach(CatalogState.paginated_videos, _video_card),
                        columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                        spacing="3",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.button(
                            "← Anterior",
                            on_click=CatalogState.prev_page,
                            disabled=CatalogState.current_page <= 1,
                            style=theme.SECONDARY_BUTTON_STYLE,
                            size="1",
                        ),
                        rx.text(
                            CatalogState.page_indicator_label,
                            font_size="0.82rem",
                            font_weight="600",
                            color=theme.TEXT_MUTED,
                        ),
                        rx.button(
                            "Siguiente →",
                            on_click=CatalogState.next_page,
                            disabled=CatalogState.current_page
                            >= CatalogState.total_pages,
                            style=theme.SECONDARY_BUTTON_STYLE,
                            size="1",
                        ),
                        spacing="3",
                        align="center",
                        justify="end",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
            ),
        ),
    )
