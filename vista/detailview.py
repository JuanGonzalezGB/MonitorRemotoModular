#!/usr/bin/env python3
"""
vista/detailview.py — diálogo de detalle gráfico para CPU o GPU.

Muestra dos gráficas apiladas:
  - Temperatura en el tiempo (°C)
  - Uso en el tiempo (%)

Se abre al hacer clic en la barra de CPU o GPU en la ventana principal.
Se alimenta con push(temp, usage) desde el loop de update de MonitorApp.
"""
import tkinter as tk
from collections import deque
from estilo.estilizador import Estilo
from controlador.controladorTemas import etiquetar, ROL_BG, ROL_BG2, ROL_BORDER, ROL_CYAN, ROL_MUTED

F_TITLE  = ("monospace", 10, "bold")
F_SMALL  = ("monospace", 8)

HISTORY  = 60   # puntos máximos en la gráfica
W, H     = 420, 110  # dimensiones de cada canvas de gráfica
PAD      = 8


class DetailView(tk.Toplevel):
    def __init__(self, parent: tk.Tk, app, title: str,
                 color_temp: str, color_usage: str):
        super().__init__(parent)
        self._app = app
        self._color_temp  = color_temp
        self._color_usage = color_usage

        self.title(title)
        self.geometry("480x260")
        self.resizable(False, False)

        estilo = app.estilo
        self.configure(bg=estilo.bg)
        self.after(100, self.grab_set)

        self._temp_hist:  deque[float] = deque(maxlen=HISTORY)
        self._usage_hist: deque[float] = deque(maxlen=HISTORY)

        self._build_ui(estilo, title)

    # ─── Build ───────────────────────────────────────────────────────────────

    def _build_ui(self, e: Estilo, title: str):
        # Header
        hdr = tk.Frame(self, bg=e.bg)
        etiquetar(hdr, ROL_BG)
        hdr.pack(fill="x", padx=8, pady=(6, 0))

        tk.Label(hdr, text=title.upper(), bg=e.bg, fg=e.cyan,
                 font=F_TITLE).pack(side="left")
        tk.Button(hdr, text="✕", bg=e.bg, fg=e.muted,
                  relief="flat", bd=0, cursor="hand2",
                  activebackground=e.bg, activeforeground=e.cyan,
                  command=self.destroy).pack(side="right")

        sep = tk.Frame(self, bg=e.border, height=1)
        sep._bg_rol = ROL_BORDER
        sep.pack(fill="x", padx=8, pady=4)

        # ── SCROLL ─────────────────────────────────────

        container = tk.Frame(self, bg=e.bg)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=e.bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)

        scroll_frame = tk.Frame(canvas, bg=e.bg)

        scroll_frame.bind(
            "<Configure>",
            lambda ev: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Scroll con mouse (sin bind_all)
        canvas.bind("<Enter>", lambda ev: canvas.focus_set())
        canvas.bind("<MouseWheel>", lambda ev: canvas.yview_scroll(int(-1*(ev.delta/120)), "units"))
        canvas.bind("<Button-4>", lambda ev: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda ev: canvas.yview_scroll(1, "units"))

        # ── CONTENIDO ─────────────────────────────────

        # Gráfica temperatura
        self._canvas_temp = self._make_graph_block(
            "Temperatura (°C)", e, max_val=110, parent=scroll_frame)

        sep2 = tk.Frame(scroll_frame, bg=e.border, height=1)
        sep2._bg_rol = ROL_BORDER
        sep2.pack(fill="x", padx=8, pady=4)

        # Gráfica uso
        self._canvas_usage = self._make_graph_block(
            "Uso (%)", e, max_val=100, parent=scroll_frame)

    def _make_graph_block(self, label: str, e: Estilo,
                          max_val: int, parent=None) -> tk.Canvas:
        if parent is None:
            parent = self

        block = tk.Frame(parent, bg=e.bg)
        etiquetar(block, ROL_BG)
        block.pack(fill="x", padx=8)

        tk.Label(block, text=label, bg=e.bg, fg=e.muted,
                 font=F_SMALL).pack(anchor="w")

        canvas = tk.Canvas(block, width=W, height=H,
                           bg=e.bg2, highlightthickness=0)
        etiquetar(canvas, ROL_BG2)
        canvas.pack(pady=(2, 0))
        canvas._max_val = max_val
        return canvas

    # ─── API pública ─────────────────────────────────────────────────────────

    def push(self, temp: float | None, usage: float | None):
        """Llamado desde MonitorApp._update cada vez que llegan datos nuevos."""
        if temp is not None:
            self._temp_hist.append(temp)
        if usage is not None:
            self._usage_hist.append(usage)
        self._draw(self._canvas_temp,  self._temp_hist,  self._color_temp)
        self._draw(self._canvas_usage, self._usage_hist, self._color_usage)

    # ─── Dibujo ──────────────────────────────────────────────────────────────

    def _draw(self, canvas: tk.Canvas, hist: deque, color: str):
        canvas.delete("all")
        e = self._app.estilo
        max_val = canvas._max_val

        cw, ch = W, H
        inner_w = cw - PAD * 2
        inner_h = ch - PAD * 2

        # Grid horizontal (25 %, 50 %, 75 %)
        for pct in (0.25, 0.5, 0.75):
            y = PAD + inner_h * (1 - pct)
            canvas.create_line(PAD, y, cw - PAD, y,
                               fill=e.border, dash=(2, 4))

        if len(hist) < 2:
            canvas.create_text(cw // 2, ch // 2,
                               text="Recopilando datos…",
                               fill=e.muted, font=F_SMALL)
            return

        points = list(hist)
        n = len(points)
        step = inner_w / (HISTORY - 1)

        coords = []
        for i, val in enumerate(points):
            x = PAD + (HISTORY - n + i) * step
            y = PAD + inner_h * (1 - min(val, max_val) / max_val)
            coords.extend([x, y])

        fill_coords = [PAD, PAD + inner_h] + coords + [PAD + (HISTORY - n + n - 1) * step, PAD + inner_h]
        canvas.create_polygon(fill_coords,
                              fill=color, stipple="gray25", outline="")

        canvas.create_line(coords, fill=color, width=2, smooth=True)

        last = points[-1]
        canvas.create_text(cw - PAD, PAD,
                           text=f"{last:.1f}",
                           fill=color, font=F_SMALL, anchor="ne")