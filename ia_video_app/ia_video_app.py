import reflex as rx
from ia_video_app.controllers.catalog_state import CatalogState
from ia_video_app.views import theme
from ia_video_app.views.auto_workspace import render_auto_workspace
from ia_video_app.views.blip_workspace import render_blip_workspace
from ia_video_app.views.catalog_stats import render_catalog_stats
from ia_video_app.views.chat_workspace import render_chat_workspace
from ia_video_app.views.clip_workspace import render_clip_workspace
from ia_video_app.views.header import render_header
from ia_video_app.views.search_filter_bar import render_search_filter_bar
from ia_video_app.views.sidebar import render_sidebar
from ia_video_app.views.upload_modal import render_upload_modal
from ia_video_app.views.video_grid import render_video_grid


def index() -> rx.Component:
    """Vista raíz del Dashboard ByteBox (MVC: solo lectura de estado y disparo de eventos)."""
    return rx.box(
        render_header(),
        rx.flex(
            render_sidebar(),
            rx.box(
                rx.vstack(
                    rx.cond(
                        CatalogState.is_connected
                        & (CatalogState.active_module != "chat"),
                        render_catalog_stats(),
                    ),
                    rx.cond(
                        CatalogState.is_connected & CatalogState.show_catalog_browser,
                        render_search_filter_bar(),
                    ),
                    rx.cond(
                        CatalogState.show_catalog_browser,
                        render_video_grid(),
                    ),
                    rx.match(
                        CatalogState.active_module,
                        ("clip", render_clip_workspace()),
                        ("automated", render_auto_workspace()),
                        ("chat", render_chat_workspace()),
                        render_blip_workspace(),
                    ),
                    spacing="4",
                    width="100%",
                    padding="20px",
                    align="start",
                ),
                flex="1",
                min_width="0",
                width="100%",
            ),
            direction=rx.breakpoints(initial="column", lg="row"),
            width="100%",
            min_height="calc(100vh - 140px)",
            align="stretch",
        ),
        render_upload_modal(),
        background=theme.BG_MAIN,
        color=theme.TEXT_PRIMARY,
        min_height="100vh",
        width="100%",
        font_family="'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    )


app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        accent_color="blue",
        gray_color="slate",
    ),
)

app.add_page(
    index,
    route="/",
    title="ByteBox | Catalogador de Video AI",
    on_load=CatalogState.on_load_app,
)
