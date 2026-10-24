"""
Paleta institucional ByteBox / ResourceSpace.
RESTRICCIÓN ESTRICTA: Prohibido el uso de colores neón (verdes eléctricos, cianes brillantes o fucsias).
"""

# Superficies y fondos neutros
BG_MAIN = "#F8F9FA"
BG_CARD = "#FFFFFF"
BG_SUBTLE = "#EDF2F7"
BG_SIDEBAR = "#33373B"
BG_SIDEBAR_DEEP = "#26292C"
BG_SIDEBAR_CARD = "#2B2F33"

# Bordes
BORDER_LIGHT = "#E2E8F0"
BORDER_MEDIUM = "#CBD5E0"
BORDER_STRONG = "#94A3B8"
BORDER_SIDEBAR = "#4A5056"

# Acentos corporativos sobrios
PRIMARY_BLUE = "#1B75BB"
PRIMARY_BLUE_HOVER = "#145D94"
PRIMARY_NAVY = "#0E446D"
BRAND_VIOLET = "#3B2A59"

# Tipografía
TEXT_PRIMARY = "#1A202C"
TEXT_MUTED = "#4A5568"
TEXT_ON_DARK = "#F7FAFC"
TEXT_SIDEBAR_MUTED = "#CBD5E0"

# Estados semánticos sobrios (WCAG AA, cero neón)
STATUS_OK_BG = "#14532D"
STATUS_OK_BORDER = "#86EFAC"
STATUS_OK_SOFT_BG = "#E8F5EE"
STATUS_OK_SOFT_TEXT = "#14532D"

STATUS_WARN_BG = "#78350F"
STATUS_WARN_BORDER = "#FCD34D"
STATUS_WARN_SOFT_BG = "#FEF3C7"
STATUS_WARN_SOFT_TEXT = "#78350F"

STATUS_ERR_BG = "#7F1D1D"
STATUS_ERR_BORDER = "#FCA5A5"

STATUS_INFO_BG = "#1E3A5F"
STATUS_INFO_BORDER = "#93C5FD"
STATUS_INFO_SOFT_BG = "#E8F3FB"
STATUS_INFO_SOFT_TEXT = "#0E446D"

CARD_STYLE = {
    "background": BG_CARD,
    "border": f"1px solid {BORDER_LIGHT}",
    "border_radius": "8px",
    "padding": "18px 20px",
    "box_shadow": "0 1px 3px rgba(0, 0, 0, 0.05)",
    "width": "100%",
}

PRIMARY_BUTTON_STYLE = {
    "background": PRIMARY_BLUE,
    "color": "#FFFFFF",
    "border": f"1px solid {PRIMARY_NAVY}",
    "border_radius": "6px",
    "font_weight": "600",
    "cursor": "pointer",
    "_hover": {"background": PRIMARY_BLUE_HOVER},
    "_disabled": {
        "background": BORDER_MEDIUM,
        "color": TEXT_MUTED,
        "cursor": "not-allowed",
        "opacity": "0.8",
    },
}

SECONDARY_BUTTON_STYLE = {
    "background": "#F8FAFC",
    "color": TEXT_PRIMARY,
    "border": f"1px solid {BORDER_STRONG}",
    "border_radius": "6px",
    "font_weight": "600",
    "cursor": "pointer",
    "_hover": {"background": BG_SUBTLE},
}

INPUT_LIGHT_STYLE = {
    "background_color": "#FFFFFF",
    "color": TEXT_PRIMARY,
    "border": f"1px solid {BORDER_STRONG}",
    "border_radius": "5px",
    "_placeholder": {"color": TEXT_MUTED},
}
