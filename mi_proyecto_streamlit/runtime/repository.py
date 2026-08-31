def get_repository():
    """Carga lazy de ResourceSpaceAPI y ResourceSpaceRepository + credenciales."""
    from models.resourcespace_client import ResourceSpaceAPI, ResourceSpaceRepository
    import streamlit as st

    url = st.secrets["resourcespace"]["base_url"]
    user = st.secrets["resourcespace"]["user"]
    key = st.secrets["resourcespace"]["private_key"]
    api = ResourceSpaceAPI(base_url=url, user=user, private_key=key)
    return ResourceSpaceRepository(api)
