import reflex as rx
from ia_video_app.controllers.catalog_state import CatalogState
from ia_video_app.views import theme


def _module_tab_button(label: str, module_key: str) -> rx.Component:
    is_active = CatalogState.active_module == module_key
    return rx.button(
        label,
        on_click=CatalogState.set_active_module(module_key),
        disabled=is_active,
        background=rx.cond(is_active, theme.PRIMARY_BLUE, "#F8FAFC"),
        color=rx.cond(is_active, "#FFFFFF", theme.TEXT_PRIMARY),
        border=rx.cond(
            is_active,
            f"1px solid {theme.PRIMARY_NAVY}",
            f"1px solid {theme.BORDER_STRONG}",
        ),
        border_radius="6px",
        font_weight="600",
        padding_x="14px",
        padding_y="8px",
        cursor="pointer",
        _hover={
            "background": rx.cond(
                is_active, theme.PRIMARY_BLUE_HOVER, theme.BG_SUBTLE
            )
        },
    )


def _step_chip(step_num: str, label: str, phase_key: str) -> rx.Component:
    is_current = CatalogState.workflow_phase == phase_key
    return rx.hstack(
        rx.box(
            rx.text(step_num, font_size="0.72rem", font_weight="700", color="#FFFFFF"),
            width="20px",
            height="20px",
            border_radius="999px",
            background=rx.cond(is_current, theme.PRIMARY_BLUE, theme.TEXT_MUTED),
            display="flex",
            align_items="center",
            justify_content="center",
        ),
        rx.text(
            label,
            font_size="0.8rem",
            font_weight="700",
            color=rx.cond(is_current, theme.PRIMARY_NAVY, theme.TEXT_PRIMARY),
        ),
        spacing="2",
        align="center",
        padding_x="12px",
        padding_y="5px",
        border_radius="999px",
        background=rx.cond(is_current, theme.STATUS_INFO_SOFT_BG, theme.BG_SUBTLE),
        border=rx.cond(
            is_current,
            f"1px solid {theme.PRIMARY_BLUE}",
            f"1px solid {theme.BORDER_MEDIUM}",
        ),
    )


def render_status_banner() -> rx.Component:
    return rx.cond(
        CatalogState.status_title != "",
        rx.box(
            rx.vstack(
                rx.text(
                    CatalogState.status_title,
                    font_weight="700",
                    font_size="0.92rem",
                    color="#FFFFFF",
                ),
                rx.text(
                    CatalogState.status_message,
                    font_size="0.84rem",
                    color="#F8FAFC",
                ),
                align="start",
                spacing="1",
            ),
            width="100%",
            padding="12px 16px",
            border_radius="6px",
            margin_bottom="12px",
            background=rx.match(
                CatalogState.status_kind,
                ("success", theme.STATUS_OK_BG),
                ("warning", theme.STATUS_WARN_BG),
                ("error", theme.STATUS_ERR_BG),
                theme.STATUS_INFO_BG,
            ),
            border=rx.match(
                CatalogState.status_kind,
                ("success", f"1px solid {theme.STATUS_OK_BORDER}"),
                ("warning", f"1px solid {theme.STATUS_WARN_BORDER}"),
                ("error", f"1px solid {theme.STATUS_ERR_BORDER}"),
                f"1px solid {theme.STATUS_INFO_BORDER}",
            ),
        ),
    )


def render_header() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.link(
                rx.hstack(
                    rx.box(
                        rx.icon("film", size=22, color="#FFFFFF"),
                        background=theme.BRAND_VIOLET,
                        padding="8px",
                        border_radius="8px",
                    ),
                    rx.vstack(
                        rx.text(
                            "ByteBox",
                            font_size="1.25rem",
                            font_weight="700",
                            color=theme.BRAND_VIOLET,
                            line_height="1.1",
                        ),
                        rx.text(
                            "Digital Storage",
                            font_size="0.78rem",
                            font_weight="600",
                            color=theme.TEXT_MUTED,
                        ),
                        spacing="0",
                        align="start",
                    ),
                    spacing="3",
                    align="center",
                ),
                href=rx.cond(
                    CatalogState.dam_base_url != "",
                    CatalogState.dam_base_url,
                    "#",
                ),
                is_external=True,
                underline="none",
                title="Abrir ByteBox DAM",
            ),
            rx.spacer(),
            rx.hstack(
                rx.hstack(
                    rx.box(
                        width="8px",
                        height="8px",
                        border_radius="999px",
                        background=rx.cond(
                            CatalogState.is_connected, "#15803D", "#B45309"
                        ),
                    ),
                    rx.text(
                        rx.cond(
                            CatalogState.is_connected,
                            "Conectado a ResourceSpace",
                            "Sin conexión activa",
                        ),
                        font_size="0.78rem",
                        font_weight="600",
                        color=theme.TEXT_PRIMARY,
                    ),
                    spacing="2",
                    align="center",
                    background=theme.BG_SUBTLE,
                    border=f"1px solid {theme.BORDER_MEDIUM}",
                    padding="5px 10px",
                    border_radius="6px",
                ),
                rx.button(
                    rx.icon("upload", size=15),
                    "Subir / Verificar Video",
                    on_click=CatalogState.open_upload_modal,
                    style=theme.SECONDARY_BUTTON_STYLE,
                    size="2",
                ),
                spacing="3",
                align="center",
            ),
            width="100%",
            align="center",
            padding="12px 20px",
            background=theme.BG_CARD,
            border_bottom=f"1px solid {theme.BORDER_LIGHT}",
        ),
        rx.vstack(
            rx.hstack(
                rx.text(
                    "Catalogador de Video AI",
                    font_size="0.84rem",
                    font_weight="600",
                    color=theme.PRIMARY_BLUE,
                ),
                rx.text(">", font_size="0.84rem", color=theme.TEXT_MUTED),
                rx.text(
                    CatalogState.module_title,
                    font_size="0.84rem",
                    font_weight="700",
                    color=theme.TEXT_PRIMARY,
                ),
                rx.spacer(),
                rx.cond(
                    CatalogState.active_module != "chat",
                    rx.hstack(
                        _step_chip("1", "Conectar", "connect"),
                        _step_chip("2", "Seleccionar", "select"),
                        _step_chip("3", "Procesar", "processing"),
                        _step_chip("4", "Resultados", "results"),
                        spacing="2",
                        wrap="wrap",
                    ),
                ),
                width="100%",
                align="center",
                wrap="wrap",
            ),
            rx.hstack(
                _module_tab_button("Catalogación BLIP", "blip"),
                _module_tab_button("Búsqueda CLIP", "clip"),
                _module_tab_button("Catalogación automatizada", "automated"),
                _module_tab_button("Chat Qwen", "chat"),
                spacing="2",
                wrap="wrap",
                width="100%",
            ),
            render_status_banner(),
            width="100%",
            padding_x="20px",
            padding_top="8px",
            spacing="3",
        ),
        width="100%",
        spacing="0",
    )
