#!/usr/bin/env python3
"""
vista/detailview.py — diálogo de detalle gráfico para CPU o GPU.

Los colores se guardan como roles semánticos y se resuelven contra
el estilo actual en cada redibujado, respetando cambios de tema en caliente.
"""
import tkinter as tk
from collections import deque
from estilo.estilizador import Estilo
from controlador.controladorTemas import etiquetar, _color, ROL_BG, ROL_BG2, ROL_BORDER, ROL_MUTED, ROL_CYAN

F_TITLE  = ("monospace", 10, "bold")
F_SMALL  = ("monospace", 8)

HISTORY  = 60
W, H     = 420, 110
PAD      = 8


class DetailView(tk.Toplevel):
    def __init__(self, parent: tk.Tk, app, title: str,
                 color_temp: str, color_usage: str):
        """
        color_temp / color_usage: roles semánticos del estilo
        (ej: "orange", "cyan", "red", "green", "blue")
        """
        super().__init__(parent)
        self._app        = app
        self._rol_temp   = color_temp    # se llama color_* por compatibilidad con app.py
        self._rol_usage  = color_usage

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
        hdr = tk.Frame(self, bg=e.bg)
        etiquetar(hdr, ROL_BG)
        hdr.pack(fill="x", padx=8, pady=(6, 0))

        lbl_title = tk.Label(hdr, text=title.upper(), bg=e.bg, fg=e.cyan, font=F_TITLE)
        etiquetar(lbl_title, ROL_BG, ROL_CYAN)
        lbl_title.pack(side="left")

        btn_x = tk.Button(hdr, text="✕", bg=e.bg, fg=e.muted,
                          relief="flat", bd=0, cursor="hand2",
                          activebackground=e.bg, activeforeground=e.cyan,
                          command=self.destroy)
        etiquetar(btn_x, ROL_BG, ROL_MUTED)
        btn_x.pack(side="right")

        sep = tk.Frame(self, bg=e.border, height=1)
        sep._bg_rol = ROL_BORDER
        sep.pack(fill="x", padx=8, pady=4)

        container = tk.Frame(self, bg=e.bg)
        etiquetar(container, ROL_BG)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=e.bg, highlightthickness=0)
        etiquetar(canvas, ROL_BG)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)

        scroll_frame = tk.Frame(canvas, bg=e.bg)
        etiquetar(scroll_frame, ROL_BG)
        scroll_frame.bind("<Configure>",
            lambda ev: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        canvas.bind("<Enter>", lambda ev: canvas.focus_set())
        canvas.bind("<MouseWheel>",
            lambda ev: canvas.yview_scroll(int(-1*(ev.delta/120)), "units"))
        canvas.bind("<Button-4>", lambda ev: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda ev: canvas.yview_scroll(1, "units"))

        self._canvas_temp = self._make_graph_block(
            "Temperatura (°C)", e, max_val=110, parent=scroll_frame)

        sep2 = tk.Frame(scroll_frame, bg=e.border, height=1)
        sep2._bg_rol = ROL_BORDER
        sep2.pack(fill="x", padx=8, pady=4)

        self._canvas_usage = self._make_graph_block(
            "Uso (%)", e, max_val=100, parent=scroll_frame)

    def _make_graph_block(self, label: str, e: Estilo,
                          max_val: int, parent: tk.Widget) -> tk.Canvas:
        block = tk.Frame(parent, bg=e.bg)
        etiquetar(block, ROL_BG)
        block.pack(fill="x", padx=8)

        lbl_block = tk.Label(block, text=label, bg=e.bg, fg=e.muted, font=F_SMALL)
        etiquetar(lbl_block, ROL_BG, ROL_MUTED)
        lbl_block.pack(anchor="w")

        c = tk.Canvas(block, width=W, height=H,
                      bg=e.bg2, highlightthickness=0)
        etiquetar(c, ROL_BG2)
        c.pack(pady=(2, 0))
        c._max_val = max_val
        return c

    # ─── API pública ─────────────────────────────────────────────────────────

    def push(self, temp: float | None, usage: float | None):
        if temp is not None:
            self._temp_hist.append(temp)
        if usage is not None:
            self._usage_hist.append(usage)
        self._draw(self._canvas_temp,  self._temp_hist,  self._rol_temp)
        self._draw(self._canvas_usage, self._usage_hist, self._rol_usage)

    def apply_estilo(self, estilo: Estilo) -> None:
        """Llamado por MonitorApp.apply_estilo() al cambiar de tema."""
        self.configure(bg=estilo.bg)
        self._draw(self._canvas_temp,  self._temp_hist,  self._rol_temp)
        self._draw(self._canvas_usage, self._usage_hist, self._rol_usage)

    # ─── Dibujo ──────────────────────────────────────────────────────────────

    def _draw(self, canvas: tk.Canvas, hist: deque, rol: str):
        canvas.delete("all")
        e       = self._app.estilo
        color   = _color(e, rol)          # resuelto contra el tema actual
        max_val = canvas._max_val

        inner_w = W - PAD * 2
        inner_h = H - PAD * 2

        for pct in (0.25, 0.5, 0.75):
            y = PAD + inner_h * (1 - pct)
            canvas.create_line(PAD, y, W - PAD, y,
                               fill=e.border, dash=(2, 4))

        if len(hist) < 2:
            canvas.create_text(W // 2, H // 2,
                               text="Recopilando datos…",
                               fill=e.muted, font=F_SMALL)
            return

        points = list(hist)
        n      = len(points)
        step   = inner_w / (HISTORY - 1)

        coords = []
        for i, val in enumerate(points):
            x = PAD + (HISTORY - n + i) * step
            y = PAD + inner_h * (1 - min(val, max_val) / max_val)
            coords.extend([x, y])

        last_x = coords[-2]
        fill_coords = [PAD, PAD + inner_h] + coords + [last_x, PAD + inner_h]
        canvas.create_polygon(fill_coords, fill=color, stipple="gray25", outline="")
        canvas.create_line(coords, fill=color, width=2, smooth=True)
        canvas.create_text(W - PAD, PAD,
                           text=f"{points[-1]:.1f}",
                           fill=color, font=F_SMALL, anchor="ne")
