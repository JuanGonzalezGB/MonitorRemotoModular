from estilo import dark, light, matrix, crimson

# ─── Registro de temas ───────────────────────────────────────────────────────
# Para agregar un tema:
#   1. Crea tu clase en estilo/mi_tema.py heredando de Estilo
#   2. Importala aquí y agrégala a CLASESTEMAS
#   3. Agrégala a TEMAS con { "Nombre visible": "codigo" }

CLASESTEMAS: dict = {
    "dark": dark.DarkColor,
    "matrix": matrix.MatrixColor,
    "crimson_dark": crimson.CrimsonColor,
    "light": light.LightColor
}

# Nombre visible en el dropdown → código interno usado por EstiloFactory
TEMAS: dict[str, str] = {
    "Oscuro": "dark",
    "Claro": "light",
    "Matrix": "matrix",
    "Blood" : "crimson_dark"
}

# ─── Fuentes compartidas ─────────────────────────────────────────────────────
FORMATS: dict = {
    "F_TITLE":  ("monospace", 10, "bold"),
    "F_NORMAL": ("monospace", 10),
    "F_SMALL":  ("monospace", 8),
}
