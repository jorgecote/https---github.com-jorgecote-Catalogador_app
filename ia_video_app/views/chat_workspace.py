import reflex as rx
from ia_video_app.controllers.catalog_state import CatalogState
from ia_video_app.views import theme
from ia_video_app.views.blip_workspace import render_qwen_install_progress


def _chat_bubble(message: dict) -> rx.Component:
    return rx.cond(
        message["role"] == "user",
        rx.hstack(
            rx.spacer(),
            rx.box(
                rx.text(
                    message["content"],
                    font_size="0.92rem",
                    color="#FFFFFF",
                    white_space="pre-wrap",
                    line_height="1.45",
                ),
                background=theme.PRIMARY_NAVY,
                border_radius="12px 12px 4px 12px",
                padding="12px 14px",
                max_width="78%",
            ),
            width="100%",
            align="start",
        ),
        rx.hstack(
            rx.box(
                rx.vstack(
                    rx.text(
                        "Qwen",
                        font_size="0.7rem",
                        font_weight="700",
                        color=theme.TEXT_MUTED,
                    ),
                    rx.text(
                        message["content"],
                        font_size="0.92rem",
                        color=theme.TEXT_PRIMARY,
                        white_space="pre-wrap",
                        line_height="1.45",
                    ),
                    spacing="1",
                    align="start",
                ),
                background=theme.BG_CARD,
                border=f"1px solid {theme.BORDER_LIGHT}",
                border_radius="12px 12px 12px 4px",
                padding="12px 14px",
                max_width="78%",
            ),
            rx.spacer(),
            width="100%",
            align="start",
        ),
    )


def render_chat_workspace() -> rx.Component:
    return rx.vstack(
        render_qwen_install_progress(),
        rx.box(
            rx.vstack(
                rx.text(
                    "Chat con Qwen2.5-1.5B-Instruct (CPU local)",
                    font_size="1.05rem",
                    font_weight="700",
                    color=theme.TEXT_PRIMARY,
                ),
                rx.text(
                    "Asistente tipo ChatGPT sobre el mismo GGUF Q4 de catalogación. "
                    "No sale a internet y no necesita ByteBox. El contexto es corto: "
                    "las conversaciones muy largas se recortan.",
                    font_size="0.84rem",
                    color=theme.TEXT_MUTED,
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            style=theme.CARD_STYLE,
        ),
        rx.box(
            rx.cond(
                ~CatalogState.has_chat_messages,
                rx.center(
                    rx.vstack(
                        rx.text(
                            "Escriba un mensaje para empezar",
                            font_size="1rem",
                            font_weight="700",
                            color=theme.PRIMARY_NAVY,
                        ),
                        rx.text(
                            "Ejemplos: «Redacta una descripción de un plano nocturno en la calle» "
                            "o «¿Qué diferencia hay entre BLIP y CLIP?»",
                            font_size="0.84rem",
                            color=theme.TEXT_MUTED,
                            text_align="center",
                        ),
                        spacing="2",
                        align="center",
                        max_width="560px",
                    ),
                    min_height="280px",
                    width="100%",
                ),
                rx.vstack(
                    rx.foreach(CatalogState.chat_messages, _chat_bubble),
                    spacing="3",
                    width="100%",
                    align="stretch",
                ),
            ),
            width="100%",
            min_height="320px",
            max_height="520px",
            overflow_y="auto",
            background=theme.BG_SUBTLE,
            border=f"1px solid {theme.BORDER_LIGHT}",
            border_radius="8px",
            padding="16px",
        ),
        rx.cond(
            CatalogState.chat_busy,
            rx.hstack(
                rx.spinner(size="2"),
                rx.text(
                    CatalogState.chat_status,
                    font_size="0.82rem",
                    font_weight="600",
                    color=theme.TEXT_MUTED,
                ),
                spacing="2",
                align="center",
            ),
        ),
        rx.hstack(
            rx.text_area(
                placeholder="Escriba su mensaje…",
                value=CatalogState.chat_draft,
                on_change=CatalogState.set_chat_draft,
                style=theme.INPUT_LIGHT_STYLE,
                width="100%",
                min_height="72px",
                disabled=CatalogState.chat_busy,
            ),
            rx.vstack(
                rx.button(
                    "Enviar",
                    on_click=CatalogState.send_chat_message,
                    disabled=~CatalogState.can_send_chat,
                    style=theme.PRIMARY_BUTTON_STYLE,
                    size="3",
                    width="100%",
                ),
                rx.button(
                    "Nueva conversación",
                    on_click=CatalogState.clear_chat,
                    disabled=CatalogState.chat_busy,
                    style=theme.SECONDARY_BUTTON_STYLE,
                    size="2",
                    width="100%",
                ),
                spacing="2",
                min_width="160px",
            ),
            width="100%",
            align="end",
            spacing="3",
        ),
        spacing="3",
        width="100%",
    )
