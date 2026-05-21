import streamlit as st

def render_main_page():
    """
    VISTA: Dibuja los elementos en la pantalla.
    No maneja lógica, solo devuelve lo que el usuario interactúa.
    """
    # Título principal de la aplicación
    st.title("Catalogador de Video AI")
    st.caption("Conexión entre ResourceSpace y BLIP-base")
    
    # Texto informativo
    st.write("Bienvenido al sistema de catalogación automatizada.")
    
    # Creamos un botón y devolvemos su estado (True si se presionó, False si no)
    boton_conectar = st.button("Iniciar Conexión", type="primary")
    
    return boton_conectar