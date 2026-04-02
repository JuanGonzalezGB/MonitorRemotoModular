#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from datetime import datetime

from estilo.estilizador import Estilo
from data.parser import fetch_async, get_latest, RamInfo, NetIface
from controlador.controladorTemas import ControladorTemas, etiquetar, ROL_BG2, ROL_MUTED, ROL_WHITE
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

F_NORMAL = ("monospace", 10)
F_SMALL  = ("monospace", 8)
INTERVAL = 2000   # ms entre actualizaciones


class MonitorApp:
    def __init__(self, estilo: Estilo):
        self.estilo = estilo
        self.core_widgets: dict = {}
        self._cores_are_mhz: bool = False
        self._has_gpu: bool = False          # se detecta en primer update
        self._cpu_detail = None
        self._gpu_detail = None
        self._paused: bool = False
        self._after_id = None

        # Historiales independientes por canal — empiezan a acumular
        # solo cuando se abre el diálogo por primera vez
        from collections import deque
        self._cpu_temp_hist:  deque = deque(maxlen=60)
        self._cpu_usage_hist: deque = deque(maxlen=60)
        self._gpu_temp_hist:  deque = deque(maxlen=60)
        self._gpu_usage_hist: deque = deque(maxlen=60)
        self._cpu_collecting: bool = False
        self._gpu_collecting: bool = False

        self._build_window()
        self._build_styles()
        self._build_ui()
        self._controlador_temas = ControladorTemas(self)

    # ─── Construcción ────────────────────────────────────────────────────────

    def _build_window(self):
        self.root = tk.Tk()
        self.root.title("Monitor PRO")
        self.root.geometry("480x260")
        self.root.configure(bg=self.estilo.bg)
        self.root.resizable(False, True)

    def _build_styles(self):
        self._ttk_style = ttk.Style()
        self._ttk_style.theme_use("default")
        apply_progressbar_styles(self._ttk_style, self.estilo)
        self._ttk_style.configure("Ram.Horizontal.TProgressbar",
            troughcolor=self.estilo.bg2, background=self.estilo.blue)

    def _build_ui(self):
        self.clock_lbl = make_header(
            self.root, self.estilo,
            on_theme=self._open_theme_selector,
            on_config=self._open_config,
        )
        scroll_frame = make_scroll_area(self.root, self.estilo)

        # ── CPU ──
        cpu_panel = make_panel(scroll_frame, "CPU", self.estilo)
        self.cpu_label, self.cpu_bar = make_temp_widget(
            cpu_panel, self.estilo, on_click=self._open_cpu_detail)

        # ── GPU — se oculta si no hay datos, se reinserta antes de cores ──
        self._gpu_panel = make_panel(scroll_frame, "GPU", self.estilo)
        self.gpu_label, self.gpu_bar = make_temp_widget(
            self._gpu_panel, self.estilo, on_click=self._open_gpu_detail)
        self._gpu_panel.pack_forget()   # empieza oculto hasta confirmar GPU

        # ── CPU DETAIL ──
        cores_panel = make_panel(scroll_frame, "CPU DETAIL", self.estilo)
        self._cores_panel_ref = cores_panel   # referencia para pack(before=)
        self.cores_frame = tk.Frame(cores_panel, bg=self.estilo.bg2)
        self.cores_frame._bg_rol = "bg2"
        self.cores_frame.pack(fill="x", padx=6, pady=(2, 6))

        # ── RAM ──
        ram_panel = make_panel(scroll_frame, "RAM", self.estilo)
        self._ram_label = tk.Label(ram_panel, text="--",
                                   bg=self.estilo.bg2, fg=self.estilo.white,
                                   font=F_NORMAL)
        etiquetar(self._ram_label, ROL_BG2, ROL_WHITE)
        self._ram_label.pack(anchor="w", padx=6)
        self._ram_bar = ttk.Progressbar(ram_panel, length=440, maximum=100,
                                        style="Ram.Horizontal.TProgressbar")
        self._ram_bar.pack(padx=6, pady=(2, 6))

        # ── NET ──
        self._net_panel = make_panel(scroll_frame, "NET", self.estilo)
        self._net_widgets: dict[str, tuple[tk.Label, tk.Label, tk.Label]] = {}

    # ─── Pausa ───────────────────────────────────────────────────────────────

    def pause(self):
        self._paused = True
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None

    def resume(self):
        self._paused = False
        self._schedule()

    # ─── Selectores ──────────────────────────────────────────────────────────

    def _open_theme_selector(self):
        from vista.selectema import ThemeSelector
        ThemeSelector(self.root, self)

    def _open_config(self):
        from vista.configview import ConfigView
        self.pause()
        ConfigView(self.root, self)

    # ─── Diálogos de detalle ─────────────────────────────────────────────────

    def _open_cpu_detail(self):
        self._cpu_collecting = True   # empieza a acumular desde ahora
        if self._cpu_detail and self._cpu_detail.winfo_exists():
            self._cpu_detail.lift(); return
        from vista.detailview import DetailView
        self._cpu_detail = DetailView(
            self.root, self, title="CPU Detail",
            color_temp="red", color_usage="blue")
        # Vuelca historial acumulado al diálogo recién abierto
        for t, u in zip(self._cpu_temp_hist, self._cpu_usage_hist):
            self._cpu_detail.push(t, u)

    def _open_gpu_detail(self):
        if not self._has_gpu: return
        self._gpu_collecting = True   # empieza a acumular desde ahora
        if self._gpu_detail and self._gpu_detail.winfo_exists():
            self._gpu_detail.lift(); return
        from vista.detailview import DetailView
        self._gpu_detail = DetailView(
            self.root, self, title="GPU Detail",
            color_temp="red", color_usage="green")
        # Vuelca historial acumulado al diálogo recién abierto
        for t, u in zip(self._gpu_temp_hist, self._gpu_usage_hist):
            self._gpu_detail.push(t, u)

    # ─── Callback del controlador ─────────────────────────────────────────────

    def apply_estilo(self, nuevo_estilo: Estilo) -> None:
        # Pausar el loop durante el retematizado para evitar
        # condiciones de carrera entre _tick y _retemar_arbol
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None

        self.estilo = nuevo_estilo
        self.root.configure(bg=nuevo_estilo.bg)
        self._ttk_style.configure("Ram.Horizontal.TProgressbar",
            troughcolor=nuevo_estilo.bg2, background=nuevo_estilo.blue)
        for detail in (self._cpu_detail, self._gpu_detail):
            if detail and detail.winfo_exists():
                self._controlador_temas._retemar_arbol(detail, nuevo_estilo)
                detail.apply_estilo(nuevo_estilo)

        # Reanudar solo si no estamos en pausa explícita (ej: ConfigView abierto)
        if not self._paused:
            self._schedule()

    # ─── Update loop ─────────────────────────────────────────────────────────

    def _schedule(self):
        """Lanza fetch en background y programa la próxima lectura de resultado."""
        fetch_async()
        self._after_id = self.root.after(INTERVAL, self._tick)

    def _tick(self):
        """Lee el último resultado disponible y reprograma."""
        if self._paused:
            return
        cpu, gpu, cores, cpu_temp, cpu_usage, gpu_usage, ram, net = get_latest()

        # GPU panel: mostrar justo después del CPU panel, antes de cores
        if gpu is not None:
            if not self._has_gpu:
                self._has_gpu = True
                self._gpu_panel.pack(fill="x", pady=3, padx=6,
                                     before=self._cores_panel_ref)
        else:
            if self._has_gpu:
                self._has_gpu = False
                self._gpu_panel.pack_forget()

        cpu_display = cpu_temp if cpu_temp is not None else cpu
        self._refresh_temp(self.cpu_label, self.cpu_bar, cpu_display)
        self._refresh_temp(self.gpu_label, self.gpu_bar, gpu)

        if cores:
            self._cores_are_mhz = cores[0][1] > 200
        self._refresh_cores(cores)
        self._refresh_ram(ram)
        self._refresh_net(net)

        # Acumular en historiales independientes
        if self._cpu_collecting:
            if cpu_display is not None: self._cpu_temp_hist.append(cpu_display)
            if cpu_usage   is not None: self._cpu_usage_hist.append(cpu_usage)
        if self._gpu_collecting:
            if gpu       is not None: self._gpu_temp_hist.append(gpu)
            if gpu_usage is not None: self._gpu_usage_hist.append(gpu_usage)

        # Alimentar diálogos solo si están abiertos
        if self._cpu_detail and self._cpu_detail.winfo_exists():
            if cpu_display is not None: self._cpu_detail.push(cpu_display, cpu_usage)
        if self._gpu_detail and self._gpu_detail.winfo_exists():
            if gpu is not None: self._gpu_detail.push(gpu, gpu_usage)

        self._schedule()

    # ─── Refresh helpers ─────────────────────────────────────────────────────

    def _refresh_temp(self, label: tk.Label, bar: ttk.Progressbar,
                      temp: float | None):
        if temp is not None:
            color = temp_color(temp, self.estilo)
            label.config(text=f"{temp:.1f}°C", fg=color)
            label._fg_rol = temp_fg_rol(temp)
            bar["value"] = temp
            bar.config(style=bar_style(temp))
        else:
            label.config(text="--", fg=self.estilo.white)
            label._fg_rol = "white"
            bar["value"] = 0

    def _refresh_ram(self, ram: RamInfo | None):
        if ram is None:
            self._ram_label.config(text="--", fg=self.estilo.white)
            self._ram_bar["value"] = 0
            return
        if ram.pct < 60:
            color, fg_rol = self.estilo.green, "green"
        elif ram.pct < 85:
            color, fg_rol = self.estilo.orange, "orange"
        else:
            color, fg_rol = self.estilo.red, "red"
        self._ram_label.config(
            text=f"{ram.used_mib:.0f} / {ram.total_mib:.0f} MiB  ({ram.pct:.1f}%)",
            fg=color)
        self._ram_label._fg_rol = fg_rol
        self._ram_bar["value"] = ram.pct
        self._ttk_style.configure("Ram.Horizontal.TProgressbar", background=color)

    def _refresh_net(self, net: list[NetIface]):
        current = set()
        for iface in net:
            current.add(iface.name)
            if iface.name not in self._net_widgets:
                row = tk.Frame(self._net_panel, bg=self.estilo.bg2)
                etiquetar(row, ROL_BG2)
                row.pack(fill="x", padx=6, pady=(2, 0))

                lbl_name = tk.Label(row, text=iface.name,
                                    bg=self.estilo.bg2, fg=self.estilo.muted,
                                    font=F_SMALL, width=8, anchor="w")
                etiquetar(lbl_name, ROL_BG2, ROL_MUTED)
                lbl_name.pack(side="left")

                lbl_recv = tk.Label(row, text="",
                                    bg=self.estilo.bg2, fg=self.estilo.green,
                                    font=F_SMALL, width=14, anchor="e")
                etiquetar(lbl_recv, ROL_BG2, "green")
                lbl_recv.pack(side="left", padx=(4, 0))

                lbl_sent = tk.Label(row, text="",
                                    bg=self.estilo.bg2, fg=self.estilo.cyan,
                                    font=F_SMALL, width=14, anchor="e")
                etiquetar(lbl_sent, ROL_BG2, "cyan")
                lbl_sent.pack(side="left", padx=(4, 0))

                self._net_widgets[iface.name] = (lbl_name, lbl_recv, lbl_sent)

            _, lbl_recv, lbl_sent = self._net_widgets[iface.name]
            lbl_recv.config(text=f"↓ {self._fmt_net(iface.recv_kbps)}")
            lbl_sent.config(text=f"↑ {self._fmt_net(iface.sent_kbps)}")

        to_delete = [n for n in self._net_widgets if n not in current]
        for name in to_delete:
            self._net_widgets[name][0].master.destroy()
            del self._net_widgets[name]

    @staticmethod
    def _fmt_net(kbps: float) -> str:
        if kbps >= 1024:
            return f"{kbps/1024:.1f} Mb/s"
        return f"{kbps:.1f} kb/s"

    def _refresh_cores(self, cores: list[tuple[str, float]]):
        current_names = set()
        for name, val in cores:
            current_names.add(name)
            if name not in self.core_widgets:
                lbl_name, lbl_val = make_core_row(
                    self.cores_frame, name, self.estilo)
                self.core_widgets[name] = (lbl_name, lbl_val)
            lbl_name, lbl_val = self.core_widgets[name]
            if self._cores_are_mhz:
                lbl_val.config(text=f"{val:.0f} MHz", fg=self.estilo.white)
                lbl_val._fg_rol = "white"
            else:
                color = temp_color(val, self.estilo)
                lbl_val.config(text=f"{val:.1f}°C", fg=color)
                lbl_val._fg_rol = temp_fg_rol(val)
        to_delete = [n for n in self.core_widgets if n not in current_names]
        for name in to_delete:
            self.core_widgets[name][0].master.destroy()
            del self.core_widgets[name]

    def _tick_clock(self):
        self.clock_lbl.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    def run(self):
        self._schedule()
        self._tick_clock()
        self.root.mainloop()
