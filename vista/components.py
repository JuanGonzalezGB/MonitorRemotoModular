#!/usr/bin/env python3
"""
Funciones constructoras de widgets reutilizables.
Cada función recibe el tema (Estilo) y el frame padre,
y devuelve las referencias necesarias para actualizarlos.

Los widgets se etiquetan con etiquetar(widget, bg_rol, fg_rol) para que
ControladorTemas pueda retematizarlos en caliente.
Los separadores usan directamente sep._bg_rol = "border".
"""
import tkinter as tk
from tkinter import ttk
from typing import Callable
from estilo.estilizador import Estilo
from controlador.controladorTemas import (
    etiquetar,
    ROL_BG, ROL_BG2, ROL_BORDER, ROL_CYAN, ROL_MUTED, ROL_WHITE,
)


F_TITLE  = ("monospace", 10, "bold")
F_NORMAL = ("monospace", 10)
F_SMALL  = ("monospace", 8)


# ─── Helpers de color ────────────────────────────────────────────────────────

def temp_color(temp: float | None, estilo: Estilo) -> str:
    if temp is None:
        return estilo.muted
    if temp < 50:
        return estilo.green
    elif temp < 70:
        return estilo.orange
    return estilo.red


def _temp_rol(temp: float | None) -> str:
    """Devuelve el ROL semántico correspondiente a la temperatura."""
    if temp is None or temp < 50:
        return ROL_BG   # será reemplazado en el label dinámicamente
    elif temp < 70:
        return "orange"
    return "red"


def temp_fg_rol(temp: float | None) -> str:
    """
    Rol de fg para un label de temperatura.
    Usar junto con lbl._fg_rol = temp_fg_rol(temp) cada vez que se actualiza,
    para que el próximo cambio de tema respete el estado actual.
    """
    if temp is None:
        return "muted"
    if temp < 50:
        return "green"
    elif temp < 70:
        return "orange"
    return "red"


def bar_style(temp: float | None) -> str:
    if temp is None or temp < 50:
        return "Green.Horizontal.TProgressbar"
    elif temp < 70:
        return "Orange.Horizontal.TProgressbar"
    return "Red.Horizontal.TProgressbar"


def apply_progressbar_styles(style: ttk.Style, estilo: Estilo) -> None:
    """Registra los tres estilos de barra usando los colores del tema."""
    style.configure("Green.Horizontal.TProgressbar",
                    troughcolor=estilo.bg2, background=estilo.green)
    style.configure("Orange.Horizontal.TProgressbar",
                    troughcolor=estilo.bg2, background=estilo.orange)
    style.configure("Red.Horizontal.TProgressbar",
                    troughcolor=estilo.bg2, background=estilo.red)


# ─── Widgets ─────────────────────────────────────────────────────────────────

def make_header(parent: tk.Widget, estilo: Estilo,
                on_theme: Callable | None = None) -> tk.Label:
    """
    Crea el header con título, reloj y botón 🎨.
    Devuelve el label del reloj.
    """
    header = tk.Frame(parent, bg=estilo.bg)
    etiquetar(header, ROL_BG)
    header.pack(fill="x", padx=6, pady=(4, 0))

    lbl_title = tk.Label(header, text="TEMP MONITOR",
                         bg=estilo.bg, fg=estilo.cyan, font=F_TITLE)
    etiquetar(lbl_title, ROL_BG, ROL_CYAN)
    lbl_title.pack(side="left")

    if on_theme:
        btn_theme = tk.Button(
            header, text="🎨",
            bg=estilo.bg, fg=estilo.muted,
            relief="flat", bd=0, cursor="hand2",
            activebackground=estilo.bg,
            activeforeground=estilo.cyan,
            font=F_SMALL,
            command=on_theme,
        )
        etiquetar(btn_theme, ROL_BG, ROL_MUTED)
        btn_theme.pack(side="right", padx=(0, 4))

    clock_lbl = tk.Label(header, text="",
                         bg=estilo.bg, fg=estilo.muted, font=F_SMALL)
    etiquetar(clock_lbl, ROL_BG, ROL_MUTED)
    clock_lbl.pack(side="right")

    sep = tk.Frame(parent, bg=estilo.border, height=1)
    sep._bg_rol = ROL_BORDER
    sep.pack(fill="x", padx=6, pady=3)

    return clock_lbl


def make_scroll_area(parent: tk.Widget, estilo: Estilo):
    """Crea el área scrollable. Devuelve el frame interior."""
    container = tk.Frame(parent, bg=estilo.bg)
    etiquetar(container, ROL_BG)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, bg=estilo.bg, highlightthickness=0)
    etiquetar(canvas, ROL_BG)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)

    scroll_frame = tk.Frame(canvas, bg=estilo.bg)
    etiquetar(scroll_frame, ROL_BG)
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    scroll_frame.bind("<Configure>",
                      lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    canvas.bind("<Button-1>", lambda e: canvas.scan_mark(e.x, e.y))
    canvas.bind("<B1-Motion>", lambda e: canvas.scan_dragto(e.x, e.y, gain=1))
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    return scroll_frame


def make_panel(parent: tk.Widget, title: str, estilo: Estilo) -> tk.Frame:
    """Panel con título pequeño arriba."""
    frame = tk.Frame(parent, bg=estilo.bg2)
    etiquetar(frame, ROL_BG2)
    frame.pack(fill="x", pady=3, padx=6)

    lbl = tk.Label(frame, text=title, bg=estilo.bg2, fg=estilo.muted, font=F_SMALL)
    etiquetar(lbl, ROL_BG2, ROL_MUTED)
    lbl.pack(anchor="w", padx=6, pady=(4, 0))
    return frame


def make_temp_widget(parent: tk.Frame, estilo: Estilo):
    """Label de temperatura + barra. Devuelve (label, progressbar)."""
    lbl = tk.Label(parent, text="--", bg=estilo.bg2, fg=estilo.white, font=F_NORMAL)
    etiquetar(lbl, ROL_BG2, ROL_WHITE)
    lbl.pack(anchor="w", padx=6)

    bar = ttk.Progressbar(parent, length=440, maximum=100)
    bar.pack(padx=6, pady=(2, 6))

    return lbl, bar


def make_core_row(parent: tk.Frame, name: str, estilo: Estilo):
    """Fila de un core individual. Devuelve (lbl_nombre, lbl_temp)."""
    row = tk.Frame(parent, bg=estilo.bg2)
    etiquetar(row, ROL_BG2)
    row.pack(fill="x")

    lbl_name = tk.Label(row, text=name, bg=estilo.bg2, fg=estilo.muted, font=F_SMALL)
    etiquetar(lbl_name, ROL_BG2, ROL_MUTED)
    lbl_name.pack(side="left")

    lbl_temp = tk.Label(row, text="--", bg=estilo.bg2, fg=estilo.white, font=F_SMALL)
    etiquetar(lbl_temp, ROL_BG2, ROL_WHITE)   # rol inicial; se actualiza en cada refresh
    lbl_temp.pack(side="right")

    return lbl_name, lbl_temp
