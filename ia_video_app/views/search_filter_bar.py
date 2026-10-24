import reflex as rx
from ia_video_app.controllers.catalog_state import CatalogState
from ia_video_app.views import theme


def _filter_pill(label: str) -> rx.Component:
    is_active = CatalogState.selected_status_filter == label
    return rx.button(
        label,
        on_click=CatalogState.set_status_filter(label),
        size="1",
        background=rx.cond(is_active, theme.PRIMARY_NAVY, theme.BG_SUBTLE),
        color=rx.cond(is_active, "#FFFFFF", theme.TEXT_PRIMARY),
        border=f"1px solid {theme.BORDER_MEDIUM}",
        border_radius="999px",
        padding_x="12px",
        cursor="pointer",
    )


def render_search_filter_bar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.input(
                    placeholder="Filtrar recursos por ID o título (ej. 45)...",
                    value=CatalogState.search_query,
                    on_change=CatalogState.set_search_query,
                    style=theme.INPUT_LIGHT_STYLE,
                    width=rx.breakpoints(initial="100%", md="320px"),
                ),
                rx.hstack(
                    _filter_pill("Todos"),
                    _filter_pill("Pendientes"),
                    _filter_pill("Catalogados"),
                    spacing="2",
                    wrap="wrap",
                ),
                rx.spacer(),
                rx.cond(
                    CatalogState.active_module != "clip",
                    rx.hstack(
                        rx.button(
                            "Seleccionar filtrados",
                            on_click=CatalogState.select_all_filtered,
                            style=theme.SECONDARY_BUTTON_STYLE,
                            size="2",
                            disabled=~CatalogState.is_connected,
                        ),
                        rx.button(
                            "Limpiar selección",
                            on_click=CatalogState.clear_selection,
                            style=theme.SECONDARY_BUTTON_STYLE,
                            size="2",
                            disabled=CatalogState.selected_count == 0,
                        ),
                        spacing="2",
                        wrap="wrap",
                    ),
                    rx.badge(
                        "CLIP usa todos los videos filtrados de la colección activa",
                        variant="surface",
                        color_scheme="blue",
                    ),
                ),
                width="100%",
                align="center",
                wrap="wrap",
                spacing="3",
            ),
            rx.hstack(
                rx.badge(
                    f"Ámbito: {CatalogState.selected_collection_label}",
                    color_scheme="gray",
                    variant="surface",
                ),
                rx.badge(
                    f"Seleccionados: {CatalogState.selected_count}",
                    color_scheme="blue",
                    variant="surface",
                ),
                rx.spacer(),
                rx.cond(
                    CatalogState.active_module == "blip",
                    rx.button(
                        rx.icon("play", size=16),
                        "Iniciar Catalogación BLIP",
                        on_click=CatalogState.run_blip_catalogation,
                        disabled=~CatalogState.can_start_blip,
                        style=theme.PRIMARY_BUTTON_STYLE,
                        size="2",
                    ),
                ),
                rx.cond(
                    CatalogState.active_module == "automated",
                    rx.button(
                        rx.icon("sparkles", size=16),
                        "Iniciar Catalogación Automatizada (BLIP + Qwen)",
                        on_click=CatalogState.run_automated_catalogation,
                        disabled=~CatalogState.can_start_automated,
                        style=theme.PRIMARY_BUTTON_STYLE,
                        size="2",
                    ),
                ),
                width="100%",
                align="center",
                wrap="wrap",
            ),
            spacing="3",
            width="100%",
        ),
        style=theme.CARD_STYLE,
    )
