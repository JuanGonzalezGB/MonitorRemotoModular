#!/usr/bin/env python3
"""
MonitorApp: clase principal de la UI.
Recibe un Estilo inyectado desde main.py.
Gestiona el cambio de tema en caliente a través de ControladorTemas.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime

from estilo.estilizador import Estilo
from data.parser import parse
from controlador.controladorTemas import ControladorTemas
from vista.components import (
    apply_progressbar_styles,
    make_header,
    make_scroll_area,
    make_panel,
    make_temp_widget,
    make_core_row,
    temp_color,
    bar_style,
)


class MonitorApp:
    def __init__(self, estilo: Estilo):
        self.estilo = estilo
        self.core_widgets: dict = {}

        self._build_window()
        self._build_styles()
        self._build_ui()

        # El controlador necesita root, estilo, _ttk_style y _on_tema_changed
        self._controlador_temas = ControladorTemas(self)

    # ─── Construcción ────────────────────────────────────────────────────────

    def _build_window(self):
        self.root = tk.Tk()
        self.root.title("Monitor PRO")
        self.root.geometry("480x280")
        self.root.configure(bg=self.estilo.colorBg())
        self.root.resizable(False, True)

    def _build_styles(self):
        self._ttk_style = ttk.Style()
        self._ttk_style.theme_use("default")
        apply_progressbar_styles(self._ttk_style, self.estilo)

    def _build_ui(self):
        # Header con botón 🎨 (callback se asigna después de init del controlador)
        self.clock_lbl = make_header(
            self.root, self.estilo,
            on_theme=self._open_theme_selector,
        )

        # Área scrollable
        scroll_frame = make_scroll_area(self.root, self.estilo)

        # Paneles
        cpu_panel   = make_panel(scroll_frame, "CPU",   self.estilo)
        gpu_panel   = make_panel(scroll_frame, "GPU",   self.estilo)
        cores_panel = make_panel(scroll_frame, "CORES", self.estilo)

        # Widgets CPU / GPU
        self.cpu_label, self.cpu_bar = make_temp_widget(cpu_panel, self.estilo)
        self.gpu_label, self.gpu_bar = make_temp_widget(gpu_panel, self.estilo)

        # Frame interior de cores (los rows se crean dinámicamente)
        self.cores_frame = tk.Frame(cores_panel, bg=self.estilo.colorBg2())
        self.cores_frame.pack(fill="x", padx=6, pady=(2, 6))

    # ─── Selector de temas ───────────────────────────────────────────────────

    def _open_theme_selector(self):
        from vista.selectema import ThemeSelector
        ThemeSelector(self.root, self)

    # ─── Callback de retematización ──────────────────────────────────────────

    def _on_tema_changed(self, nuevo_estilo: Estilo):
        """
        Llamado por ControladorTemas después de aplicar el tema al árbol de
        widgets. Aquí actualizamos las referencias de color que se calculan
        en tiempo de update (barras de temperatura, cores dinámicos, etc.).
        """
        self.estilo = nuevo_estilo
        self.root.configure(bg=nuevo_estilo.colorBg())

    # ─── Update loop ─────────────────────────────────────────────────────────

    def _update(self):
        cpu, gpu, cores = parse()

        self._refresh_temp(self.cpu_label, self.cpu_bar, cpu)
        self._refresh_temp(self.gpu_label, self.gpu_bar, gpu)
        self._refresh_cores(cores)

        self.root.after(2000, self._update)

    def _refresh_temp(self, label: tk.Label, bar: ttk.Progressbar,
                      temp: float | None):
        if temp is not None:
            label.config(text=f"{temp:.1f}°C",
                         fg=temp_color(temp, self.estilo))
            bar["value"] = temp
            bar.config(style=bar_style(temp))
        else:
            label.config(text="--")
            bar["value"] = 0

    def _refresh_cores(self, cores: list[tuple[str, float]]):
        current_names = set()

        for name, temp in cores:
            current_names.add(name)

            if name not in self.core_widgets:
                lbl_name, lbl_temp = make_core_row(
                    self.cores_frame, name, self.estilo)
                self.core_widgets[name] = (lbl_name, lbl_temp)

            lbl_name, lbl_temp = self.core_widgets[name]
            lbl_temp.config(text=f"{temp:.1f}°C",
                            fg=temp_color(temp, self.estilo))

        # Eliminar cores que ya no existen
        to_delete = [n for n in self.core_widgets if n not in current_names]
        for name in to_delete:
            self.core_widgets[name][0].master.destroy()
            del self.core_widgets[name]

    def _tick_clock(self):
        self.clock_lbl.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    # ─── Arranque ────────────────────────────────────────────────────────────

    def run(self):
        self._update()
        self._tick_clock()
        self.root.mainloop()
