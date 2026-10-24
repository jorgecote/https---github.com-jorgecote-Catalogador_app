import reflex as rx
from ia_video_app.controllers.catalog_state import CatalogState
from ia_video_app.views import theme


def render_upload_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "Subir / Verificar Video Local",
                        font_size="1.05rem",
                        font_weight="700",
                        color=theme.TEXT_PRIMARY,
                    ),
                    rx.spacer(),
                    rx.button(
                        "Cerrar",
                        on_click=CatalogState.close_upload_modal,
                        style=theme.SECONDARY_BUTTON_STYLE,
                        size="1",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.text(
                    "Arrastre archivos .mp4, .mov o .mkv para validar su integridad antes de catalogar. Los archivos temporales se limpian de inmediato.",
                    font_size="0.84rem",
                    color=theme.TEXT_MUTED,
                ),
                rx.upload(
                    rx.vstack(
                        rx.icon("cloud_upload", size=28, color=theme.PRIMARY_BLUE),
                        rx.text(
                            "Arrastre y suelte un video aquí o haga clic para seleccionar",
                            font_size="0.86rem",
                            font_weight="600",
                            color=theme.TEXT_PRIMARY,
                        ),
                        rx.text(
                            "Formatos admitidos: MP4, MOV, MKV",
                            font_size="0.76rem",
                            color=theme.TEXT_MUTED,
                        ),
                        spacing="2",
                        align="center",
                        padding="20px",
                    ),
                    id="video_upload_zone",
                    multiple=False,
                    accept={
                        "video/mp4": [".mp4"],
                        "video/quicktime": [".mov"],
                        "video/x-matroska": [".mkv"],
                    },
                    border=f"2px dashed {theme.BORDER_STRONG}",
                    border_radius="8px",
                    background=theme.BG_MAIN,
                    width="100%",
                ),
                rx.cond(
                    CatalogState.is_uploading,
                    rx.vstack(
                        rx.progress(value=CatalogState.upload_progress, width="100%"),
                        rx.text(
                            "Verificando y limpiando archivo temporal...",
                            font_size="0.78rem",
                            color=theme.TEXT_MUTED,
                        ),
                        width="100%",
                    ),
                ),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        on_click=CatalogState.close_upload_modal,
                        style=theme.SECONDARY_BUTTON_STYLE,
                    ),
                    rx.button(
                        "Procesar archivo seleccionado",
                        on_click=CatalogState.handle_video_upload(
                            rx.upload_files(upload_id="video_upload_zone")
                        ),
                        loading=CatalogState.is_uploading,
                        style=theme.PRIMARY_BUTTON_STYLE,
                    ),
                    justify="end",
                    spacing="2",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            style={"max_width": "500px", "background": theme.BG_CARD},
        ),
        open=CatalogState.upload_modal_open,
    )
