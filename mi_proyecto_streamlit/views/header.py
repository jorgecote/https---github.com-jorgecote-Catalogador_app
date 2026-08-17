import streamlit as st

def render_header(app_url: str = "http://157.137.212.40/bytebox/10.7/", current_section: str = "Inicio"):
    """
    Renderiza la barra superior limpia con el logo de ByteBox
    enlazado a la aplicación principal de ByteBox, seguido de las migas de pan.
    """
    link_url = app_url if app_url else "http://157.137.212.40/bytebox/10.7/"
    
    # Renderizamos la barra de navegación superior (sin líneas en blanco internas para evitar errores de parseo de Streamlit)
    navbar_html = f"""<div class="rs-header-container"><a href="{link_url}" target="_blank" class="rs-logo-link" title="Abrir ByteBox DAM"><svg width="36" height="36" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M24 4L6 14.5V33.5L24 44L42 33.5V14.5L24 4Z" fill="#3b2a59" stroke="#5a3d8a" stroke-width="2"/><path d="M24 4L42 14.5L24 25L6 14.5L24 4Z" fill="#6d48a6"/><path d="M6 14.5L24 25V44L6 33.5V14.5Z" fill="#4d3277"/><path d="M42 14.5L24 25V44L42 33.5V14.5Z" fill="#2d1c47"/><path d="M15 9.5L33 20" stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/><path d="M33 9.5L15 20" stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/><path d="M15 29.5V39" stroke="rgba(255,255,255,0.2)" stroke-width="1.5"/><path d="M33 29.5V39" stroke="rgba(255,255,255,0.2)" stroke-width="1.5"/></svg><div><div class="rs-logo-title">ByteBox</div><div class="rs-logo-sub">Digital Storage</div></div></a><div class="rs-badge-system"><span style="color: #1b75bb; font-size: 1rem; margin-right: 4px;">●</span><span>Módulo de Catalogación AI</span></div></div>"""
    
    # Renderizamos los breadcrumbs
    breadcrumbs_html = f"""<div class="rs-breadcrumbs"><a href="{link_url}" target="_blank">Panel de control</a><span>&gt;</span><span class="active">Catalogador de Video AI</span><span>&gt;</span><span style="color: #1b75bb; font-weight: 600;">{current_section}</span></div>"""
    
    st.markdown(navbar_html, unsafe_allow_html=True)
    st.markdown(breadcrumbs_html, unsafe_allow_html=True)
