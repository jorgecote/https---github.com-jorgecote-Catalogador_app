import streamlit as st


def resolve_workflow_phase(is_connected: bool, current_phase: str = None) -> str:
    if not is_connected:
        return "connect"
    if current_phase in ("processing", "results", "select"):
        return current_phase
    return "select"


def render_workflow_stepper(phase: str, module: str = "blip"):
    """Pasos visibles: Conectar, Seleccionar, Procesar/Buscar, Resultados."""
    process_label = "Buscar" if module == "clip" else "Procesar"
    steps = [
        ("connect", "1", "Conectar"),
        ("select", "2", "Seleccionar"),
        ("processing", "3", process_label),
        ("results", "4", "Resultados"),
    ]
    order = [key for key, _, _ in steps]
    current_idx = order.index(phase) if phase in order else 0

    chips = []
    for idx, (key, number, label) in enumerate(steps):
        css = "rs-step"
        if idx < current_idx:
            css += " rs-step-done"
        elif idx == current_idx:
            css += " rs-step-active"
        chips.append(
            f'<div class="{css}"><span class="rs-step-num">{number}</span>{label}</div>'
        )

    st.markdown(f'<div class="rs-stepper">{"".join(chips)}</div>', unsafe_allow_html=True)
