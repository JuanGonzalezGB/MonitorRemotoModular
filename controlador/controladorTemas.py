# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Juan S.G. Castellanos

"""
controlador/controladorTemas.py

ControladorTemas recibe la app (MonitorApp) y puede:
  - aplicarTema(codigo)  → preview en vivo sin guardar
  - aceptarTema(codigo)  → preview + persiste en config.json

Los widgets se retematiztan recorriendo el árbol de tk y leyendo
los atributos _bg_rol y _fg_rol que etiquetar() estampa en cada widget.
El color se resuelve con getattr(estilo, rol) — los nombres de los roles
coinciden exactamente con los atributos del objeto estilo (bg, cyan, etc.).
"""
import tkinter as tk
from tkinter import ttk

from estilo.estiloFactory import EstiloFactory
from modelo import config

# ─── Roles semánticos ────────────────────────────────────────────────────────
# Los valores son strings que coinciden con los atributos de Estilo
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

_ROL_DEFAULT_BG = ROL_BG
_ROL_DEFAULT_FG = ROL_WHITE


def _color(estilo, rol: str) -> str:
    """Resuelve un rol a su color usando getattr sobre el objeto estilo."""
    return getattr(estilo, rol, estilo.white)


def etiquetar(widget: tk.Widget, bg_rol: str, fg_rol: str | None = None) -> None:
    """
    Estampa roles semánticos en un widget para que el controlador
    sepa qué colores aplicar al retematizar.

      etiquetar(lbl, ROL_BG, ROL_CYAN)
        → bg usará estilo.bg, fg usará estilo.cyan

      etiquetar(frame, ROL_BG2)
        → solo bg; fg se omite (frames no tienen fg)

    Los botones con activebackground/activeforeground heredan
    automáticamente los mismos roles que bg y fg.
    """
    widget._bg_rol = bg_rol
    if fg_rol is not None:
        widget._fg_rol = fg_rol


class ControladorTemas:
    def __init__(self, app):
        """
        app debe exponer:
          app.root         → tk.Tk
          app.estilo       → Estilo actual
          app._ttk_style   → ttk.Style
          app.apply_estilo(nuevo_estilo) → callback para referencias internas
        """
        self._app = app

    # ─── API pública ─────────────────────────────────────────────────────────

    def aplicarTema(self, codigo: str) -> None:
        """Cambia el tema en vivo (preview); no guarda en disco."""
        nuevo = EstiloFactory.definirEstilo(codigo)
        self._app.apply_estilo(nuevo)
        self._retemar_arbol(self._app.root, nuevo)
        self._retemar_ttk(nuevo)

    def aceptarTema(self, codigo: str) -> None:
        """Cambia el tema y lo persiste en config.json."""
        self.aplicarTema(codigo)
        config.set_tema(codigo)

    # ─── Internos ────────────────────────────────────────────────────────────

    def _retemar_arbol(self, widget: tk.Widget, estilo) -> None:
        """Recorre recursivamente el árbol de widgets y aplica colores por rol."""

        bg_rol = getattr(widget, "_bg_rol", None)
        fg_rol = getattr(widget, "_fg_rol", None)

        if bg_rol:
            try:
                color_bg = _color(estilo, bg_rol)
                widget.config(bg=color_bg)
                # Botones: sincronizar activebackground con bg
                widget.config(activebackground=color_bg)
            except tk.TclError:
                pass

        if fg_rol:
            try:
                color_fg = _color(estilo, fg_rol)
                widget.config(fg=color_fg)
                # Botones: sincronizar activeforeground con fg
                widget.config(activeforeground=color_fg)
            except tk.TclError:
                pass

        # Separadores sin _bg_rol explícito pero con _bg_rol legacy (no debería ocurrir,
        # pero se mantiene para compatibilidad con widgets creados manualmente)
        for child in widget.winfo_children():
            self._retemar_arbol(child, estilo)

    def _retemar_ttk(self, estilo) -> None:
        """Actualiza los estilos de las barras de progreso ttk."""
        s = self._app._ttk_style
        bg2 = estilo.bg2
        s.configure("Green.Horizontal.TProgressbar",
                    troughcolor=bg2, background=estilo.green)
        s.configure("Orange.Horizontal.TProgressbar",
                    troughcolor=bg2, background=estilo.orange)
        s.configure("Red.Horizontal.TProgressbar",
                    troughcolor=bg2, background=estilo.red)
