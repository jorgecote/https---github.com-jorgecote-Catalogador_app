import reflex as rx
from ia_video_app.controllers.catalog_state import CatalogState
from ia_video_app.views import theme


def render_blip_install_progress() -> rx.Component:
    return rx.cond(
        CatalogState.show_blip_install,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.spinner(size="3"),
                    rx.vstack(
                        rx.text(
                            "Instalación de BLIP (primera vez)",
                            font_size="1rem",
                            font_weight="700",
                            color=theme.PRIMARY_NAVY,
                        ),
                        rx.text(
                            CatalogState.blip_install_label,
                            font_size="0.82rem",
                            color=theme.TEXT_MUTED,
                        ),
                        spacing="0",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.badge(
                        f"{CatalogState.blip_install_pct} %",
                        color_scheme="blue",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.progress(value=CatalogState.blip_install_pct, width="100%"),
                rx.text(
                    "Esta barra solo aparece al instalar o cargar BLIP por primera vez. Luego se oculta.",
                    font_size="0.74rem",
                    color=theme.TEXT_MUTED,
                ),
                spacing="2",
                width="100%",
            ),
            background=theme.BG_CARD,
            border=f"1px solid {theme.BORDER_LIGHT}",
            border_left=f"4px solid {theme.BRAND_VIOLET}",
            border_radius="8px",
            padding="16px",
            width="100%",
        ),
    )


def render_clip_install_progress() -> rx.Component:
    return rx.cond(
        CatalogState.show_clip_install,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.spinner(size="3"),
                    rx.vstack(
                        rx.text(
                            "Instalación de CLIP (primera vez)",
                            font_size="1rem",
                            font_weight="700",
                            color=theme.PRIMARY_NAVY,
                        ),
                        rx.text(
                            CatalogState.clip_install_label,
                            font_size="0.82rem",
                            color=theme.TEXT_MUTED,
                        ),
                        spacing="0",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.badge(
                        f"{CatalogState.clip_install_pct} %",
                        color_scheme="blue",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.progress(value=CatalogState.clip_install_pct, width="100%"),
                rx.text(
                    "Esta barra solo aparece al instalar o cargar CLIP por primera vez. Luego se oculta.",
                    font_size="0.74rem",
                    color=theme.TEXT_MUTED,
                ),
                spacing="2",
                width="100%",
            ),
            background=theme.BG_CARD,
            border=f"1px solid {theme.BORDER_LIGHT}",
            border_left=f"4px solid {theme.BRAND_VIOLET}",
            border_radius="8px",
            padding="16px",
            width="100%",
        ),
    )


def render_qwen_install_progress() -> rx.Component:
    return rx.cond(
        CatalogState.show_qwen_install,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.spinner(size="3"),
                    rx.vstack(
                        rx.text(
                            "Instalación de Qwen (primera vez)",
                            font_size="1rem",
                            font_weight="700",
                            color=theme.PRIMARY_NAVY,
                        ),
                        rx.text(
                            CatalogState.qwen_install_label,
                            font_size="0.82rem",
                            color=theme.TEXT_MUTED,
                        ),
                        spacing="0",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.badge(
                        f"{CatalogState.qwen_install_pct} %",
                        color_scheme="blue",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.progress(value=CatalogState.qwen_install_pct, width="100%"),
                rx.text(
                    "Esta barra solo aparece al cargar Qwen2.5-1.5B-Instruct GGUF Q4 por primera vez. Luego se oculta.",
                    font_size="0.74rem",
                    color=theme.TEXT_MUTED,
                ),
                spacing="2",
                width="100%",
            ),
            background=theme.BG_CARD,
            border=f"1px solid {theme.BORDER_LIGHT}",
            border_left=f"4px solid {theme.BRAND_VIOLET}",
            border_radius="8px",
            padding="16px",
            width="100%",
        ),
    )


def render_job_progress_panel() -> rx.Component:
    return rx.cond(
        CatalogState.is_processing,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.spinner(size="3"),
                    rx.vstack(
                        rx.text(
                            CatalogState.job_title,
                            font_size="1rem",
                            font_weight="700",
                            color=theme.PRIMARY_NAVY,
                        ),
                        rx.text(
                            CatalogState.job_subtitle,
                            font_size="0.82rem",
                            color=theme.TEXT_MUTED,
                        ),
                        spacing="0",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.badge(
                            f"Recurso {CatalogState.job_current_index} de {CatalogState.job_total_count}",
                            color_scheme="blue",
                        ),
                        rx.button(
                            "Detener",
                            on_click=CatalogState.cancel_processing,
                            style=theme.SECONDARY_BUTTON_STYLE,
                            size="1",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.progress(value=CatalogState.job_progress_pct, width="100%"),
                rx.text(
                    CatalogState.job_live_log,
                    font_size="0.8rem",
                    font_weight="600",
                    color=theme.TEXT_PRIMARY,
                ),
                spacing="2",
                width="100%",
            ),
            background=theme.BG_CARD,
            border=f"1px solid {theme.BORDER_LIGHT}",
            border_left=f"4px solid {theme.PRIMARY_BLUE}",
            border_radius="8px",
            padding="16px",
            width="100%",
        ),
    )


def _tray_frame_card(frame: dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.cond(
                frame["image_data_uri"] != "",
                rx.image(
                    src=frame["image_data_uri"],
                    width="100%",
                    height="105px",
                    object_fit="cover",
                    border_radius="4px",
                ),
                rx.box(
                    rx.text("Sin imagen", font_size="0.72rem", color=theme.TEXT_ON_DARK),
                    height="105px",
                    width="100%",
                    background=theme.BG_SIDEBAR_CARD,
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    border_radius="4px",
                ),
            ),
            rx.hstack(
                rx.badge(
                    frame["timestamp"],
                    background=theme.PRIMARY_BLUE,
                    color="#FFFFFF",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.text(
                        "ID",
                        font_size="0.7rem",
                        font_weight="700",
                        color=theme.TEXT_PRIMARY,
                    ),
                    rx.text(
                        frame["video_id"],
                        font_size="0.7rem",
                        font_weight="700",
                        color=theme.TEXT_PRIMARY,
                    ),
                    spacing="1",
                    align="center",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                frame["is_match"],
                rx.badge(
                    "Coincidencia",
                    background=theme.STATUS_OK_BG,
                    color="#FFFFFF",
                ),
            ),
            rx.text(
                frame["caption"],
                font_size="0.75rem",
                color=theme.TEXT_PRIMARY,
                font_weight="600",
                line_height="1.25",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        background=theme.BG_CARD,
        border=rx.cond(
            frame["is_match"],
            f"2px solid {theme.STATUS_OK_BG}",
            f"1px solid {theme.BORDER_STRONG}",
        ),
        border_radius="6px",
        padding="8px",
    )


def render_collection_tray(title: str, empty_message: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    title,
                    font_size="0.82rem",
                    font_weight="700",
                    text_transform="uppercase",
                    letter_spacing="0.6px",
                    color=theme.TEXT_ON_DARK,
                ),
                rx.text(
                    CatalogState.tray_scope_label,
                    font_size="0.78rem",
                    font_weight="700",
                    color="#FFFFFF",
                ),
                rx.badge(
                    f"{CatalogState.total_tray_frames} fotogramas",
                    color_scheme="gray",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        "←",
                        on_click=CatalogState.prev_tray_page,
                        disabled=CatalogState.tray_page <= 1,
                        size="1",
                        style=theme.SECONDARY_BUTTON_STYLE,
                    ),
                    rx.text(
                        f"Pág. {CatalogState.tray_page}/{CatalogState.total_tray_pages}",
                        font_size="0.76rem",
                        color=theme.TEXT_ON_DARK,
                    ),
                    rx.button(
                        "→",
                        on_click=CatalogState.next_tray_page,
                        disabled=CatalogState.tray_page
                        >= CatalogState.total_tray_pages,
                        size="1",
                        style=theme.SECONDARY_BUTTON_STYLE,
                    ),
                    spacing="2",
                    align="center",
                ),
                width="100%",
                align="center",
                padding_bottom="8px",
                border_bottom=f"1px solid {theme.BORDER_SIDEBAR}",
            ),
            rx.cond(
                CatalogState.total_tray_frames == 0,
                rx.box(
                    rx.text(
                        empty_message,
                        font_size="0.84rem",
                        color=theme.TEXT_SIDEBAR_MUTED,
                        text_align="center",
                    ),
                    width="100%",
                    padding="20px",
                    background=theme.BG_SIDEBAR_CARD,
                    border=f"1px dashed {theme.BORDER_STRONG}",
                    border_radius="6px",
                ),
                rx.grid(
                    rx.foreach(CatalogState.paginated_tray_frames, _tray_frame_card),
                    columns=rx.breakpoints(initial="1", sm="2", md="3", lg="6"),
                    spacing="3",
                    width="100%",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        background=theme.BG_SIDEBAR_DEEP,
        border=f"1px solid {theme.BORDER_SIDEBAR}",
        border_radius="8px",
        padding="14px 16px",
        width="100%",
    )


def render_blip_workspace() -> rx.Component:
    return rx.vstack(
        render_blip_install_progress(),
        render_job_progress_panel(),
        rx.cond(
            (CatalogState.workflow_phase == "results") & CatalogState.has_blip_results,
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
                    rx.button(
                        "Nueva selección",
                        on_click=CatalogState.return_to_selection,
                        style=theme.SECONDARY_BUTTON_STYLE,
                        size="2",
                    ),
                    spacing="2",
                    align="start",
                ),
                style=theme.CARD_STYLE,
            ),
        ),
        render_collection_tray(
            title="Colección de Fotogramas Analizados",
            empty_message="Aquí aparecerán las miniaturas de los fotogramas analizados.",
        ),
        spacing="4",
        width="100%",
    )
