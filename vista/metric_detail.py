#!/usr/bin/env python3
"""
vista/metric_detail.py — diálogo de gráfica histórica para una métrica.

Usos:
  - RAM del sistema (chart=system.ram, dim=used)
  - CPU de un grupo de procesos (chart=app.{group}_cpu_utilization, dims=user+system)
  - RAM privada de un grupo (chart=app.{group}_mem_private_usage, dim=mem)

Los datos se obtienen directamente de la API REST de Netdata,
funciona igual en Intel y ARM sin depender del .sh.
"""
import tkinter as tk
import threading
import urllib.request
import json
from collections import deque
from estilo.estilizador import Estilo
from controlador.controladorTemas import (
    etiquetar, _color,
    ROL_BG, ROL_BG2, ROL_BORDER, ROL_CYAN, ROL_MUTED,
)

F_TITLE = ("monospace", 10, "bold")
F_SMALL = ("monospace", 8)

HISTORY  = 60
W, H     = 420, 140
PAD      = 10


class MetricDetail(tk.Toplevel):
    def __init__(self, parent: tk.Tk, app,
                 title: str,
                 ip: str,
                 chart: str,
                 dims: list[str],       # dimensiones a sumar
                 unit: str,             # "%" o "MiB" etc
                 rol_line: str,         # rol semántico del color de línea
                 interval_ms: int = 2000):
        super().__init__(parent)
        self._app        = app
        self._ip         = ip
        self._chart      = chart
        self._dims       = dims
        self._unit       = unit
        self._rol_line   = rol_line
        self._interval   = interval_ms
        self._hist: deque[float] = deque(maxlen=HISTORY)
        self._after_id   = None
        self._destroyed  = False

        self.title(title)
        self.geometry("480x240")
        self.resizable(False, False)
        self.configure(bg=app.estilo.bg)
        self.after(100, self.grab_set)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui(app.estilo, title)
        self._fetch_history()   # carga los últimos 60s al abrir
        self._schedule()

    # ─── Build ───────────────────────────────────────────────────────────────

    def _build_ui(self, e: Estilo, title: str):
        hdr = tk.Frame(self, bg=e.bg)
        etiquetar(hdr, ROL_BG)
        hdr.pack(fill="x", padx=8, pady=(6, 0))

        lbl_title = tk.Label(hdr, text=title.upper(),
                             bg=e.bg, fg=e.cyan, font=F_TITLE)
        etiquetar(lbl_title, ROL_BG, ROL_CYAN)
        lbl_title.pack(side="left")

        btn_x = tk.Button(hdr, text="✕", bg=e.bg, fg=e.muted,
                          relief="flat", bd=0, cursor="hand2",
                          activebackground=e.bg, activeforeground=e.cyan,
                          command=self._on_close)
        etiquetar(btn_x, ROL_BG, ROL_MUTED)
        btn_x.pack(side="right")

        sep = tk.Frame(self, bg=e.border, height=1)
        sep._bg_rol = ROL_BORDER
        sep.pack(fill="x", padx=8, pady=4)

        block = tk.Frame(self, bg=e.bg)
        etiquetar(block, ROL_BG)
        block.pack(fill="x", padx=8)

        lbl_unit = tk.Label(block, text=self._unit,
                            bg=e.bg, fg=e.muted, font=F_SMALL)
        etiquetar(lbl_unit, ROL_BG, ROL_MUTED)
        lbl_unit.pack(anchor="w")

        self._canvas = tk.Canvas(block, width=W, height=H,
                                 bg=e.bg2, highlightthickness=0)
        etiquetar(self._canvas, ROL_BG2)
        self._canvas.pack(pady=(2, 0))

        self._lbl_current = tk.Label(self, text="--",
                                     bg=e.bg, fg=e.muted, font=F_SMALL)
        etiquetar(self._lbl_current, ROL_BG, ROL_MUTED)
        self._lbl_current.pack(anchor="e", padx=12)

    # ─── Datos ───────────────────────────────────────────────────────────────

    def _api_url(self, after: int = -1) -> str:
        return (f"http://{self._ip}:19999/api/v1/data"
                f"?chart={self._chart}&after={after}&format=json&points={HISTORY}")

    def _fetch_history(self):
        """Carga los últimos HISTORY segundos al abrir el diálogo."""
        def _worker():
            try:
                url = self._api_url(after=-HISTORY)
                with urllib.request.urlopen(url, timeout=5) as r:
                    data = json.loads(r.read())
                labels = data.get("labels", [])
                rows   = data.get("data",   [])
                idx = [labels.index(d) for d in self._dims if d in labels]
                points = []
                for row in reversed(rows):
                    val = sum(row[i] for i in idx if i < len(row))
                    points.append(max(0.0, val))
                if not self._destroyed:
                    self.after(0, lambda p=points: self._load_history(p))
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _load_history(self, points: list[float]):
        for p in points:
            self._hist.append(p)
        self._draw()

    def _fetch_latest(self):
        """Obtiene el último punto."""
        def _worker():
            try:
                url = self._api_url(after=-2)
                with urllib.request.urlopen(url, timeout=5) as r:
                    data = json.loads(r.read())
                labels = data.get("labels", [])
                rows   = data.get("data",   [])
                idx = [labels.index(d) for d in self._dims if d in labels]
                if rows:
                    row = rows[0]
                    val = sum(row[i] for i in idx if i < len(row))
                    val = max(0.0, val)
                    if not self._destroyed:
                        self.after(0, lambda v=val: self._push(v))
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _push(self, val: float):
        self._hist.append(val)
        self._draw()
        self._lbl_current.config(text=f"{val:.1f} {self._unit}")

    # ─── Dibujo ──────────────────────────────────────────────────────────────

    def _draw(self):
        canvas = self._canvas
        canvas.delete("all")
        e     = self._app.estilo
        color = _color(e, self._rol_line)

        inner_w = W - PAD * 2
        inner_h = H - PAD * 2

        if not self._hist:
            canvas.create_text(W // 2, H // 2,
                               text="Recopilando datos…",
                               fill=e.muted, font=F_SMALL)
            return

        max_val = max(self._hist) or 1.0

        # Grid
        for pct in (0.25, 0.5, 0.75):
            y = PAD + inner_h * (1 - pct)
            canvas.create_line(PAD, y, W - PAD, y,
                               fill=e.border, dash=(2, 4))
            canvas.create_text(PAD - 2, y,
                               text=f"{max_val * pct:.0f}",
                               fill=e.muted, font=F_SMALL,
                               anchor="e")

        points = list(self._hist)
        n      = len(points)
        step   = inner_w / (HISTORY - 1)

        coords = []
        for i, val in enumerate(points):
            x = PAD + (HISTORY - n + i) * step
            y = PAD + inner_h * (1 - min(val, max_val) / max_val)
            coords.extend([x, y])

        if len(coords) >= 4:
            last_x = coords[-2]
            fill_coords = ([PAD, PAD + inner_h]
                           + coords
                           + [last_x, PAD + inner_h])
            canvas.create_polygon(fill_coords,
                                  fill=color, stipple="gray25", outline="")
            canvas.create_line(coords, fill=color, width=2, smooth=True)

        last = points[-1]
        canvas.create_text(W - PAD, PAD,
                           text=f"{last:.1f}",
                           fill=color, font=F_SMALL, anchor="ne")

    # ─── Apply estilo ─────────────────────────────────────────────────────────

    def apply_estilo(self, estilo: Estilo):
        self.configure(bg=estilo.bg)
        self._draw()

    # ─── Loop ────────────────────────────────────────────────────────────────

    def _schedule(self):
        if not self._destroyed:
            self._after_id = self.after(self._interval, self._tick)

    def _tick(self):
        if self._destroyed:
            return
        self._fetch_latest()
        self._schedule()

    def _on_close(self):
        self._destroyed = True
        if self._after_id:
            self.after_cancel(self._after_id)
        self.destroy()
