from estilo import dark, light, matrix, crimson

# ─── Registro de temas ───────────────────────────────────────────────────────
# Para agregar un tema:
#   1. Crea tu clase en estilo/mi_tema.py heredando de Estilo
#   2. Importala aquí y agrégala a CLASESTEMAS
#   3. Agrégala a TEMAS con { "Nombre visible": "codigo" }

CLASESTEMAS: dict = {
    "dark": dark.DarkColor,
    "light": light.LightColor,
    "matrix": matrix.MatrixColor,
    "crimson_dark":crimson.CrimsonColor
}

# Nombre visible en el dropdown → código interno usado por EstiloFactory
TEMAS: dict[str, str] = {
    "Oscuro": "dark",
    "Claro": "light",
    "Matrix": "matrix",
    "Blood": "crimson_dark"
}

# ─── Fuentes compartidas ─────────────────────────────────────────────────────
FORMATS: dict = {
    "F_TITLE":  ("monospace", 10, "bold"),
    "F_NORMAL": ("monospace", 10),
    "F_SMALL":  ("monospace", 8),
}

GRAPHFORMAT = {
    "GRAPH_W" : 440,
    "GRAPH_H" : 60
}

FORMATS = {
    "F_TITLE"  : ("monospace", 10, "bold"),
    "F_NORMAL" : ("monospace", 9),
    "F_SMALL"  : ("monospace", 8),
    "COL_NAME"   : 14,
    "COL_IP"     : 15,
    "COL_VENDOR" : 12,
    "COL_PING"   :  6
}

ROLES = {
    "BG"     : "bg",
    "BG2"    : "bg2",
    "CYAN"   : "cyan",
    "MUTED"  : "muted",
    "GREEN"  : "green",
    "ORANGE" : "orange",
    "RED"    : "red",
    "BLUE"   : "blue",
    "WHITE"  : "white",
    "BOTON"  : "boton",
}

ROL_BG     = "bg"
ROL_BG2    = "bg2"
ROL_BORDER = "border"
ROL_GREEN  = "green"
ROL_ORANGE = "orange"
ROL_RED    = "red"
ROL_CYAN   = "cyan"
ROL_BLUE   = "blue"
ROL_WHITE  = "white"
ROL_MUTED  = "muted"
ROL_BOTON  = "boton"