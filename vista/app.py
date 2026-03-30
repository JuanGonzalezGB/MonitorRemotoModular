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
    temp_fg_rol,
    bar_style,
)


class MonitorApp:
    def __init__(self, estilo: Estilo):
        self.estilo = estilo
        self.core_widgets: dict = {}

        self._build_window()
        self._build_styles()
        self._build_ui()
        self._controlador_temas = ControladorTemas(self)

    # ─── Construcción ────────────────────────────────────────────────────────

    def _build_window(self):
        self.root = tk.Tk()
        self.root.title("Monitor PRO")
        self.root.geometry("480x280")
        self.root.configure(bg=self.estilo.bg)
        self.root.resizable(False, True)

    def _build_styles(self):
        self._ttk_style = ttk.Style()
        self._ttk_style.theme_use("default")
        apply_progressbar_styles(self._ttk_style, self.estilo)

    def _build_ui(self):
        self.clock_lbl = make_header(
            self.root, self.estilo,
            on_theme=self._open_theme_selector,
            on_config=self._open_config,
        )
        scroll_frame = make_scroll_area(self.root, self.estilo)

        cpu_panel   = make_panel(scroll_frame, "CPU",   self.estilo)
        gpu_panel   = make_panel(scroll_frame, "GPU",   self.estilo)
        cores_panel = make_panel(scroll_frame, "CORES", self.estilo)

        self.cpu_label, self.cpu_bar = make_temp_widget(cpu_panel, self.estilo)
        self.gpu_label, self.gpu_bar = make_temp_widget(gpu_panel, self.estilo)

        self.cores_frame = tk.Frame(cores_panel, bg=self.estilo.bg2)
        self.cores_frame._bg_rol = "bg2"
        self.cores_frame.pack(fill="x", padx=6, pady=(2, 6))

    # ─── Selector de temas ───────────────────────────────────────────────────

    def _open_theme_selector(self):
        from vista.selectema import ThemeSelector
        ThemeSelector(self.root, self)

    def _open_config(self):
        from vista.configview import ConfigView
        ConfigView(self.root, self)

    # ─── Callback del controlador (API pública requerida por el manual) ───────

    def apply_estilo(self, nuevo_estilo: Estilo) -> None:
        """
        Llamado por ControladorTemas antes de recorrer el árbol.
        Actualiza la referencia de estilo y el bg de la ventana raíz.
        """
        self.estilo = nuevo_estilo
        self.root.configure(bg=nuevo_estilo.bg)

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
            color = temp_color(temp, self.estilo)
            label.config(text=f"{temp:.1f}°C", fg=color)
            # Actualizar rol para que el próximo cambio de tema respete el estado
            label._fg_rol = temp_fg_rol(temp)
            bar["value"] = temp
            bar.config(style=bar_style(temp))
        else:
            label.config(text="--", fg=self.estilo.white)
            label._fg_rol = "white"
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
            color = temp_color(temp, self.estilo)
            lbl_temp.config(text=f"{temp:.1f}°C", fg=color)
            # Actualizar rol semántico dinámico
            lbl_temp._fg_rol = temp_fg_rol(temp)

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
