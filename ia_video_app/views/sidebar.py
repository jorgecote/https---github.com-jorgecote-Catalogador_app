import reflex as rx
from ia_video_app.controllers.catalog_state import CatalogState
from ia_video_app.views import theme


def _section_label(text: str) -> rx.Component:
    return rx.text(
        text,
        font_size="0.73rem",
        font_weight="700",
        color="#E2E8F0",
        text_transform="uppercase",
        letter_spacing="0.5px",
        padding_bottom="4px",
        border_bottom=f"1px solid {theme.BORDER_SIDEBAR}",
        width="100%",
        white_space="normal",
    )


def _help_note(text: str) -> rx.Component:
    return rx.text(
        text,
        font_size="0.74rem",
        color=theme.TEXT_SIDEBAR_MUTED,
        line_height="1.4",
        white_space="normal",
    )


def _int_slider(value_var, min_value: int, max_value: int, step: int, on_change) -> rx.Component:
    return rx.slider(
        value=[value_var],
        min=min_value,
        max=max_value,
        step=step,
        on_change=on_change,
        width="100%",
        disabled=CatalogState.is_processing,
    )


def _float_slider(value_var, min_value: float, max_value: float, step: float, on_change) -> rx.Component:
    return rx.slider(
        value=[value_var],
        min=min_value,
        max=max_value,
        step=step,
        on_change=on_change,
        width="100%",
        disabled=CatalogState.is_processing,
    )


def _chat_sidebar() -> rx.Component:
    return rx.vstack(
        _section_label("Chat Qwen"),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("message_circle", size=16, color="#93C5FD"),
                    rx.text(
                        "Asistente local CPU",
                        font_size="0.82rem",
                        font_weight="700",
                        color=theme.TEXT_ON_DARK,
                    ),
                    spacing="2",
                    align="center",
                ),
                _help_note("Qwen2.5-1.5B-Instruct GGUF Q4. Mismo modelo de la catalogación automatizada."),
                spacing="2",
                width="100%",
                align="start",
            ),
            background=theme.BG_SIDEBAR_CARD,
            border=f"1px solid {theme.BORDER_SIDEBAR}",
            border_radius="6px",
            padding="12px",
            width="100%",
        ),
        _section_label("Parámetros"),
        rx.vstack(
            rx.text(
                f"Temperatura: {CatalogState.chat_temperature}",
                font_size="0.78rem",
                font_weight="600",
                color=theme.TEXT_ON_DARK,
            ),
            rx.slider(
                value=[CatalogState.chat_temperature],
                min=0.20,
                max=0.95,
                step=0.05,
                on_change=CatalogState.set_chat_temperature_str,
                width="100%",
                disabled=CatalogState.chat_busy,
            ),
            _help_note("Valores altos dan respuestas más variadas. 0.70 es un punto medio."),
            rx.button(
                "Nueva conversación",
                on_click=CatalogState.clear_chat,
                disabled=CatalogState.chat_busy,
                width="100%",
                style=theme.SECONDARY_BUTTON_STYLE,
                size="2",
            ),
            rx.button(
                "Volver a catalogación BLIP",
                on_click=CatalogState.set_active_module("blip"),
                disabled=CatalogState.chat_busy,
                width="100%",
                style=theme.SECONDARY_BUTTON_STYLE,
                size="2",
            ),
            spacing="2",
            width="100%",
            align="start",
        ),
        rx.cond(
            ~CatalogState.is_connected,
            rx.box(
                rx.vstack(
                    _help_note("El chat no requiere ByteBox. Puede conectar el DAM si quiere catalogar después."),
                    rx.button(
                        "Iniciar conexión con ByteBox",
                        on_click=CatalogState.connect_resourcespace,
                        loading=CatalogState.is_loading,
                        disabled=CatalogState.is_loading | CatalogState.chat_busy,
                        width="100%",
                        style=theme.PRIMARY_BUTTON_STYLE,
                        size="2",
                    ),
                    spacing="2",
                    width="100%",
                    align="start",
                ),
                background=theme.BG_SIDEBAR_CARD,
                border=f"1px solid {theme.BORDER_SIDEBAR}",
                border_radius="6px",
                padding="12px",
                width="100%",
            ),
        ),
        spacing="4",
        width="100%",
        align="start",
    )


def _disconnected_sidebar() -> rx.Component:
    return rx.vstack(
        _section_label("Conexión ByteBox"),
        rx.box(
            rx.vstack(
                _help_note("Sin conexión activa con ResourceSpace."),
                rx.button(
                    "Iniciar conexión con ByteBox",
                    on_click=CatalogState.connect_resourcespace,
                    loading=CatalogState.is_loading,
                    disabled=CatalogState.is_loading,
                    width="100%",
                    style=theme.PRIMARY_BUTTON_STYLE,
                    size="2",
                ),
                spacing="2",
                width="100%",
                align="start",
            ),
            background=theme.BG_SIDEBAR_CARD,
            border=f"1px solid {theme.BORDER_SIDEBAR}",
            border_radius="6px",
            padding="12px",
            width="100%",
        ),
        rx.cond(
            CatalogState.active_module != "blip",
            rx.button(
                "Volver a catalogación BLIP",
                on_click=CatalogState.set_active_module("blip"),
                width="100%",
                style=theme.SECONDARY_BUTTON_STYLE,
                size="2",
            ),
        ),
        spacing="3",
        width="100%",
        align="start",
    )


def _connected_sidebar() -> rx.Component:
    return rx.vstack(
        _section_label("Conexión ByteBox"),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("shield_check", size=16, color="#86EFAC"),
                    rx.text(
                        "Sesión DAM autenticada",
                        font_size="0.82rem",
                        font_weight="700",
                        color=theme.TEXT_ON_DARK,
                    ),
                    spacing="2",
                    align="center",
                ),
                _help_note(f"Conectado · {CatalogState.total_videos_count} videos en ámbito"),
                rx.button(
                    "Recargar biblioteca DAM",
                    on_click=CatalogState.connect_resourcespace,
                    loading=CatalogState.is_loading,
                    width="100%",
                    style=theme.PRIMARY_BUTTON_STYLE,
                    size="2",
                    disabled=CatalogState.is_processing,
                ),
                spacing="2",
                align="start",
                width="100%",
            ),
            background=theme.BG_SIDEBAR_CARD,
            border=f"1px solid {theme.BORDER_SIDEBAR}",
            border_radius="6px",
            padding="12px",
            width="100%",
        ),
        _section_label("Ámbito y filtro"),
        rx.vstack(
            rx.text(
                "Colección activa",
                font_size="0.78rem",
                font_weight="600",
                color=theme.TEXT_ON_DARK,
            ),
            rx.select(
                CatalogState.collection_options,
                value=CatalogState.selected_collection_label,
                on_change=CatalogState.change_collection,
                disabled=CatalogState.is_processing,
                width="100%",
            ),
            spacing="1",
            align="start",
            width="100%",
        ),
        _section_label("Configuración IA"),
        rx.vstack(
            rx.text(
                f"Tasa de muestreo: cada {CatalogState.sample_rate_sec} s",
                font_size="0.78rem",
                font_weight="600",
                color=theme.TEXT_ON_DARK,
            ),
            _int_slider(
                CatalogState.sample_rate_sec,
                1,
                30,
                1,
                CatalogState.set_sample_rate_str,
            ),
            _help_note("Valores bajos analizan más fotogramas y consumen más CPU."),
            rx.cond(
                CatalogState.active_module == "blip",
                rx.vstack(
                    rx.text(
                        "Estrategia de inferencia BLIP",
                        font_size="0.78rem",
                        font_weight="600",
                        color=theme.TEXT_ON_DARK,
                    ),
                    rx.select(
                        [
                            "Estándar (Greedy)",
                            "Alta precisión (Beam Search)",
                            "Creativo (Nucleus Sampling)",
                        ],
                        value=CatalogState.blip_strategy_label,
                        on_change=CatalogState.set_blip_strategy,
                        width="100%",
                    ),
                    rx.cond(
                        CatalogState.blip_strategy_label.contains("Beam"),
                        rx.vstack(
                            rx.text(
                                f"Ramas (num_beams): {CatalogState.blip_num_beams}",
                                font_size="0.78rem",
                                font_weight="600",
                                color=theme.TEXT_ON_DARK,
                            ),
                            _int_slider(
                                CatalogState.blip_num_beams,
                                2,
                                8,
                                1,
                                CatalogState.set_blip_num_beams_str,
                            ),
                            _help_note("Beam Search: más ramas, mejor texto y más CPU."),
                            spacing="1",
                            width="100%",
                        ),
                    ),
                    rx.cond(
                        CatalogState.blip_strategy_label.contains("Creativo"),
                        rx.vstack(
                            rx.text(
                                f"Temperatura: {CatalogState.blip_sample_temperature}",
                                font_size="0.78rem",
                                font_weight="600",
                                color=theme.TEXT_ON_DARK,
                            ),
                            _float_slider(
                                CatalogState.blip_sample_temperature,
                                0.2,
                                1.5,
                                0.1,
                                CatalogState.set_blip_sample_temperature_str,
                            ),
                            rx.text(
                                f"Top-P: {CatalogState.blip_sample_top_p}",
                                font_size="0.78rem",
                                font_weight="600",
                                color=theme.TEXT_ON_DARK,
                            ),
                            _float_slider(
                                CatalogState.blip_sample_top_p,
                                0.5,
                                1.0,
                                0.05,
                                CatalogState.set_blip_sample_top_p_str,
                            ),
                            _help_note("Sampling: más variedad. Temperatura alta = más creatividad."),
                            spacing="1",
                            width="100%",
                        ),
                    ),
                    rx.cond(
                        CatalogState.blip_strategy_label.contains("Greedy"),
                        _help_note("Greedy Search: descriptor más probable. Recomendada en CPU."),
                    ),
                    spacing="2",
                    width="100%",
                    align="start",
                ),
            ),
            rx.cond(
                CatalogState.active_module == "clip",
                rx.vstack(
                    rx.text(
                        f"Umbral de similitud: {CatalogState.clip_threshold}",
                        font_size="0.78rem",
                        font_weight="600",
                        color=theme.TEXT_ON_DARK,
                    ),
                    _float_slider(
                        CatalogState.clip_threshold,
                        0.15,
                        0.40,
                        0.01,
                        CatalogState.set_clip_threshold_str,
                    ),
                    _help_note("Valores típicos útiles: 0.22 – 0.32. Umbral alto = menos resultados, más precisos."),
                    rx.button(
                        "Volver a catalogación BLIP",
                        on_click=CatalogState.set_active_module("blip"),
                        width="100%",
                        style=theme.SECONDARY_BUTTON_STYLE,
                        size="2",
                    ),
                    spacing="2",
                    width="100%",
                    align="start",
                ),
            ),
            rx.cond(
                CatalogState.active_module == "automated",
                rx.vstack(
                    rx.text(
                        f"Muestras BLIP por frame: {CatalogState.auto_caption_count}",
                        font_size="0.78rem",
                        font_weight="600",
                        color=theme.TEXT_ON_DARK,
                    ),
                    _int_slider(
                        CatalogState.auto_caption_count,
                        1,
                        5,
                        1,
                        CatalogState.set_auto_caption_count_str,
                    ),
                    rx.text(
                        f"Temperatura base BLIP: {CatalogState.auto_temperature}",
                        font_size="0.78rem",
                        font_weight="600",
                        color=theme.TEXT_ON_DARK,
                    ),
                    _float_slider(
                        CatalogState.auto_temperature,
                        0.60,
                        0.90,
                        0.05,
                        CatalogState.set_auto_temperature_str,
                    ),
                    spacing="2",
                    width="100%",
                    align="start",
                ),
            ),
            spacing="3",
            width="100%",
            align="start",
        ),
        rx.box(
            _help_note(
                "Inferencia 100% en CPU. Los videos descargados en temp_videos/ se eliminan inmediatamente al terminar cada recurso."
            ),
            background=theme.BG_SIDEBAR_DEEP,
            border=f"1px solid {theme.BORDER_SIDEBAR}",
            border_radius="6px",
            padding="10px",
            width="100%",
        ),
        spacing="4",
        width="100%",
        align="start",
    )


def render_sidebar() -> rx.Component:
    return rx.box(
        rx.cond(
            CatalogState.active_module == "chat",
            _chat_sidebar(),
            rx.cond(
                CatalogState.is_connected,
                _connected_sidebar(),
                _disconnected_sidebar(),
            ),
        ),
        width=rx.breakpoints(initial="100%", lg="290px"),
        min_width=rx.breakpoints(initial="100%", lg="290px"),
        max_width=rx.breakpoints(initial="100%", lg="290px"),
        flex_shrink="0",
        background=theme.BG_SIDEBAR,
        color=theme.TEXT_ON_DARK,
        padding="18px 16px",
        border_right=f"1px solid {theme.BG_SIDEBAR_DEEP}",
    )
