import streamlit as st


def render_header(
    app_url: str = "",
    current_section: str = "Inicio",
    module: str = "blip",
    is_connected: bool = False,
):
    """
    Barra superior ByteBox, breadcrumbs internos y subnavegación BLIP/CLIP.
    Devuelve eventos: go_blip, go_clip.
    """
    link_url = app_url or "#"
    module_label = "Catalogación BLIP" if module == "blip" else "Búsqueda CLIP"
    status_label = "Conectado" if is_connected else "Sin conexión"
    status_dot = "rs-dot-on" if is_connected else "rs-dot-off"

    st.markdown(f"""
    <div class="rs-header-container">
        <a href="{link_url}" target="_blank" class="rs-logo-link" title="Abrir ByteBox DAM">
            <svg width="36" height="36" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M24 4L6 14.5V33.5L24 44L42 33.5V14.5L24 4Z" fill="#3b2a59" stroke="#5a3d8a" stroke-width="2"/>
                <path d="M24 4L42 14.5L24 25L6 14.5L24 4Z" fill="#6d48a6"/>
                <path d="M6 14.5L24 25V44L6 33.5V14.5Z" fill="#4d3277"/>
                <path d="M42 14.5L24 25V44L42 33.5V14.5Z" fill="#2d1c47"/>
            </svg>
            <div>
                <div class="rs-logo-title">ByteBox</div>
                <div class="rs-logo-sub">Digital Storage</div>
            </div>
        </a>
        <div class="rs-header-meta">
            <div class="rs-badge-system">
                <span class="rs-dot {status_dot}"></span>
                <span>{status_label} · {module_label}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="rs-breadcrumbs">
        <span class="rs-crumb-link">Catalogador de Video AI</span>
        <span>&gt;</span>
        <span class="active">{current_section}</span>
    </div>
    """, unsafe_allow_html=True)

    nav1, nav2, _ = st.columns([1.2, 1.2, 3])
    with nav1:
        go_blip = st.button(
            "Catalogación BLIP",
            use_container_width=True,
            type="primary" if module == "blip" else "secondary",
            key="nav_to_blip",
            disabled=(module == "blip"),
        )
    with nav2:
        go_clip = st.button(
            "Búsqueda CLIP",
            use_container_width=True,
            type="primary" if module == "clip" else "secondary",
            key="nav_to_clip",
            disabled=(module == "clip" and is_connected),
        )

    return {"go_blip": go_blip, "go_clip": go_clip}
