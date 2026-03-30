#!/usr/bin/env python3
"""
Funciones constructoras de widgets reutilizables.
Cada función recibe el tema (Estilo) y el frame padre,
y devuelve las referencias necesarias para actualizarlos.
Los widgets se etiquetan con _roles para que ControladorTemas
pueda retematizarlos en caliente.
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
        return estilo.colorMuted()
    if temp < 50:
        return estilo.colorGreen()
    elif temp < 70:
        return estilo.colorOrange()
    return estilo.colorRed()


def bar_style(temp: float | None) -> str:
    if temp is None or temp < 50:
        return "Green.Horizontal.TProgressbar"
    elif temp < 70:
        return "Orange.Horizontal.TProgressbar"
    return "Red.Horizontal.TProgressbar"


def apply_progressbar_styles(style: ttk.Style, estilo: Estilo) -> None:
    """Registra los tres estilos de barra usando los colores del tema."""
    bg2 = estilo.colorBg2()
    style.configure("Green.Horizontal.TProgressbar",
                    troughcolor=bg2, background=estilo.colorGreen())
    style.configure("Orange.Horizontal.TProgressbar",
                    troughcolor=bg2, background=estilo.colorOrange())
    style.configure("Red.Horizontal.TProgressbar",
                    troughcolor=bg2, background=estilo.colorRed())


# ─── Widgets ─────────────────────────────────────────────────────────────────

def make_header(parent: tk.Widget, estilo: Estilo,
                on_theme: Callable | None = None) -> tk.Label:
    """
    Crea el header con título, reloj y botón 🎨.
    Devuelve el label del reloj.
    on_theme: callback para abrir el selector de temas.
    """
    header = tk.Frame(parent, bg=estilo.colorBg())
    etiquetar(header, ROL_BG)
    header.pack(fill="x", padx=6, pady=(4, 0))

    lbl_title = tk.Label(header, text="TEMP MONITOR",
                         bg=estilo.colorBg(), fg=estilo.colorCyan(),
                         font=F_TITLE)
    etiquetar(lbl_title, ROL_BG, ROL_CYAN)
    lbl_title.pack(side="left")

    # Botón paleta 🎨 — abre el selector de temas
    if on_theme:
        btn_theme = tk.Button(
            header, text="🎨",
            bg=estilo.colorBg(), fg=estilo.colorMuted(),
            relief="flat", bd=0, cursor="hand2",
            activebackground=estilo.colorBg(),
            activeforeground=estilo.colorCyan(),
            font=F_SMALL,
            command=on_theme,
        )
        etiquetar(btn_theme, ROL_BG, ROL_MUTED)
        btn_theme.pack(side="right", padx=(0, 4))

    clock_lbl = tk.Label(header, text="",
                         bg=estilo.colorBg(), fg=estilo.colorMuted(),
                         font=F_SMALL)
    etiquetar(clock_lbl, ROL_BG, ROL_MUTED)
    clock_lbl.pack(side="right")

    sep = tk.Frame(parent, bg=estilo.colorBorder(), height=1)
    sep._bg_rol = "border"
    sep.pack(fill="x", padx=6, pady=3)

    return clock_lbl


def make_scroll_area(parent: tk.Widget, estilo: Estilo):
    """
    Crea el área scrollable.
    Devuelve el frame interior donde se colocan los paneles.
    """
    container = tk.Frame(parent, bg=estilo.colorBg())
    etiquetar(container, ROL_BG)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, bg=estilo.colorBg(), highlightthickness=0)
    etiquetar(canvas, ROL_BG)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)

    scroll_frame = tk.Frame(canvas, bg=estilo.colorBg())
    etiquetar(scroll_frame, ROL_BG)
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    scroll_frame.bind("<Configure>",
                      lambda e: canvas.configure(
                          scrollregion=canvas.bbox("all")))

    # Scroll táctil
    canvas.bind("<Button-1>", lambda e: canvas.scan_mark(e.x, e.y))
    canvas.bind("<B1-Motion>", lambda e: canvas.scan_dragto(e.x, e.y, gain=1))

    # Scroll mouse
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    canvas.bind_all("<Button-4>",
                    lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>",
                    lambda e: canvas.yview_scroll(1, "units"))

    return scroll_frame


def make_panel(parent: tk.Widget, title: str, estilo: Estilo) -> tk.Frame:
    """Panel con título pequeño arriba. Devuelve el frame del panel."""
    frame = tk.Frame(parent, bg=estilo.colorBg2())
    etiquetar(frame, ROL_BG2)
    frame.pack(fill="x", pady=3, padx=6)

    lbl = tk.Label(frame, text=title,
                   bg=estilo.colorBg2(), fg=estilo.colorMuted(),
                   font=F_SMALL)
    etiquetar(lbl, ROL_BG2, ROL_MUTED)
    lbl.pack(anchor="w", padx=6, pady=(4, 0))
    return frame


def make_temp_widget(parent: tk.Frame, estilo: Estilo):
    """
    Label de temperatura + barra de progreso.
    Devuelve (label, progressbar).
    """
    lbl = tk.Label(parent, text="--",
                   bg=estilo.colorBg2(), fg=estilo.colorWhite(),
                   font=F_NORMAL)
    etiquetar(lbl, ROL_BG2, ROL_WHITE)
    lbl.pack(anchor="w", padx=6)

    bar = ttk.Progressbar(parent, length=440, maximum=100)
    bar.pack(padx=6, pady=(2, 6))

    return lbl, bar


def make_core_row(parent: tk.Frame, name: str, estilo: Estilo):
    """
    Fila de un core individual.
    Devuelve (label_nombre, label_temp).
    """
    row = tk.Frame(parent, bg=estilo.colorBg2())
    etiquetar(row, ROL_BG2)
    row.pack(fill="x")

    lbl_name = tk.Label(row, text=name,
                        bg=estilo.colorBg2(), fg=estilo.colorMuted(),
                        font=F_SMALL)
    etiquetar(lbl_name, ROL_BG2, ROL_MUTED)
    lbl_name.pack(side="left")

    lbl_temp = tk.Label(row, text="--",
                        bg=estilo.colorBg2(), fg=estilo.colorWhite(),
                        font=F_SMALL)
    etiquetar(lbl_temp, ROL_BG2, ROL_WHITE)
    lbl_temp.pack(side="right")

    return lbl_name, lbl_temp
