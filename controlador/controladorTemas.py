"""
controlador/controladorTemas.py

ControladorTemas recibe la ventana raíz (MonitorApp) y puede:
  - aplicarTema(codigo)  → preview en vivo sin guardar
  - aceptarTema(codigo)  → preview + persiste en config.json

Los widgets se retematiztan recorriendo el árbol de widgets de tk y
leyendo el atributo _roles que components.py estampa en cada widget.
Ese atributo es una lista de roles semánticos (ROL_BG, ROL_CYAN, …)
que el controlador traduce a colores del nuevo estilo.
"""
import tkinter as tk
from tkinter import ttk

from estilo.estiloFactory import EstiloFactory
from modelo import config

# ─── Roles semánticos ────────────────────────────────────────────────────────
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


def _color_for_rol(rol: str, estilo) -> str:
    return {
        ROL_BG:     estilo.colorBg(),
        ROL_BG2:    estilo.colorBg2(),
        ROL_BORDER: estilo.colorBorder(),
        ROL_GREEN:  estilo.colorGreen(),
        ROL_ORANGE: estilo.colorOrange(),
        ROL_RED:    estilo.colorRed(),
        ROL_CYAN:   estilo.colorCyan(),
        ROL_BLUE:   estilo.colorBlue(),
        ROL_WHITE:  estilo.colorWhite(),
        ROL_MUTED:  estilo.colorMuted(),
        ROL_BOTON:  estilo.colorBoton(),
    }.get(rol, "")


def etiquetar(widget: tk.Widget, *roles: str) -> None:
    """
    Estampa roles semánticos en un widget para que el controlador
    sepa qué colores cambiar al retematizar.
    Uso: etiquetar(lbl, ROL_BG, ROL_CYAN)
         → bg del widget usará colorBg(), fg usará colorCyan()
    """
    widget._roles = list(roles)


class ControladorTemas:
    def __init__(self, app):
        """
        app debe exponer:
          app.root      → tk.Tk
          app.estilo    → Estilo actual
          app._ttk_style → ttk.Style
          app._on_tema_changed(nuevo_estilo) → callback para actualizar
                                               referencias internas
        """
        self._app = app

    # ─── API pública ─────────────────────────────────────────────────────────

    def aplicarTema(self, codigo: str) -> None:
        """Cambia el tema en vivo (preview); no guarda en disco."""
        nuevo = EstiloFactory.definirEstilo(codigo)
        self._app.estilo = nuevo
        self._retemar_arbol(self._app.root, nuevo)
        self._retemar_ttk(nuevo)
        self._app._on_tema_changed(nuevo)

    def aceptarTema(self, codigo: str) -> None:
        """Cambia el tema y lo persiste en config.json."""
        self.aplicarTema(codigo)
        config.set_tema(codigo)

    # ─── Internos ────────────────────────────────────────────────────────────

    def _retemar_arbol(self, widget: tk.Widget, estilo) -> None:
        """Recorre todo el árbol de widgets y aplica colores por rol."""
        roles: list = getattr(widget, "_roles", [])

        if roles:
            colores = [_color_for_rol(r, estilo) for r in roles]
            opciones = list(zip(["bg", "fg", "activebackground",
                                 "activeforeground", "highlightbackground"], colores))
            for opcion, color in opciones:
                try:
                    widget.config(**{opcion: color})
                except tk.TclError:
                    pass

        # Caso especial: separadores con _bg_rol
        bg_rol = getattr(widget, "_bg_rol", None)
        if bg_rol:
            try:
                widget.config(bg=_color_for_rol(bg_rol, estilo))
            except tk.TclError:
                pass

        for child in widget.winfo_children():
            self._retemar_arbol(child, estilo)

    def _retemar_ttk(self, estilo) -> None:
        """Actualiza los estilos de las barras de progreso ttk."""
        s = self._app._ttk_style
        bg2 = estilo.colorBg2()
        s.configure("Green.Horizontal.TProgressbar",
                    troughcolor=bg2, background=estilo.colorGreen())
        s.configure("Orange.Horizontal.TProgressbar",
                    troughcolor=bg2, background=estilo.colorOrange())
        s.configure("Red.Horizontal.TProgressbar",
                    troughcolor=bg2, background=estilo.colorRed())
