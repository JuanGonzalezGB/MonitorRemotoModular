#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from collections import deque

from estilo.estilizador import Estilo
from data.parser import fetch_async, get_latest, RamInfo, NetIface, LoadInfo, PowerInfo, ProcessInfo
from controlador.controladorTemas import ControladorTemas, etiquetar, ROL_BG2, ROL_MUTED, ROL_WHITE
from controlador.controladorGenerico import Cositas
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
INTERVAL = 2000


class MonitorApp:
    def __init__(self, estilo: Estilo):
        self.estilo = estilo
        self.core_widgets: dict = {}
        self._cores_are_mhz: bool = False
        self._has_gpu: bool = False
        self._cpu_detail = None
        self._gpu_detail = None
        self._paused: bool = False
        self._after_id = None
        self._freq_max_observed: float = 1.0 
        self._net_hist: dict[str, dict[str, list[float]]] = {}  # iface -> {rx, tx, peak_rx, peak_tx}

        self._ram_total_mib: float = 1024.0

        self._cpu_temp_hist:  deque = deque(maxlen=60)
        self._cpu_usage_hist: deque = deque(maxlen=60)
        self._gpu_temp_hist:  deque = deque(maxlen=60)
        self._gpu_usage_hist: deque = deque(maxlen=60)
        self._cpu_collecting: bool = False
        self._gpu_collecting: bool = False
        self._has_power: bool = False
        self._metric_dialogs: dict[str, object] = {}  # key → MetricDetail abierto
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

        # ── GPU — empieza oculto, se inserta antes de CPU DETAIL si hay datos ──
        self._gpu_panel = make_panel(scroll_frame, "GPU", self.estilo)
        self.gpu_label, self.gpu_bar = make_temp_widget(
            self._gpu_panel, self.estilo, on_click=self._open_gpu_detail)
        self._gpu_panel.pack_forget()

        # ── CPU DETAIL ──
        cores_panel = make_panel(scroll_frame, "CPU DETAIL", self.estilo)
        self._cores_panel_ref = cores_panel

        # Encabezado de tabla — se oculta en ARM (sin freq)
        self._cores_header = tk.Frame(cores_panel, bg=self.estilo.bg2)
        self._cores_header._bg_rol = "bg2"
        self._cores_header.pack(fill="x", padx=6, pady=(2, 0))
        """
        tk.Label(self._cores_header, text="", bg=self.estilo.bg2,
                fg=self.estilo.muted, font=F_SMALL, width=8, anchor="w"
                ).pack(side="left")  # columna nombre (vacía en header)"""
        lbl_h_core = tk.Label(self._cores_header, text="CPU/CORE",
                            bg=self.estilo.bg2, fg=self.estilo.muted,
                            font=F_SMALL, width=8, anchor="w")
        lbl_h_core.pack(side="left")
        etiquetar(lbl_h_core, ROL_BG2, ROL_MUTED)

        lbl_h_temp = tk.Label(self._cores_header, text="TEMP",
                              bg=self.estilo.bg2, fg=self.estilo.muted,
                              font=F_SMALL, width=10, anchor="e")
        etiquetar(lbl_h_temp, ROL_BG2, ROL_MUTED)
        lbl_h_temp.pack(side="left")
        self._lbl_h_freq = tk.Label(self._cores_header, text="FREQ",
                                    bg=self.estilo.bg2, fg=self.estilo.muted,
                                    font=F_SMALL, width=10, anchor="e")
        etiquetar(self._lbl_h_freq, ROL_BG2, ROL_MUTED)
        self._lbl_h_freq.pack(side="right")
        self._cores_header.pack_forget()  # oculto hasta Intel confirmado

        self.cores_frame = tk.Frame(cores_panel, bg=self.estilo.bg2)
        self.cores_frame._bg_rol = "bg2"
        self.cores_frame.pack(fill="x", padx=6, pady=(0, 6))

        # ── RAM ──
        ram_panel = make_panel(scroll_frame, "RAM", self.estilo)
        self._ram_label = tk.Label(ram_panel, text="--",
                                   bg=self.estilo.bg2, fg=self.estilo.white,
                                   font=F_NORMAL)
        etiquetar(self._ram_label, ROL_BG2, ROL_WHITE)
        self._ram_label.pack(anchor="w", padx=6)
        self._ram_bar = ttk.Progressbar(ram_panel, length=440, maximum=100,
                                        style="Ram.Horizontal.TProgressbar",
                                        cursor="hand2")
        self._ram_bar.bind("<Button-1>", lambda _: self._open_metric("ram_system",
            "RAM del sistema", "system.ram", ["used"], "MiB", "blue"))
        self._ram_bar.pack(padx=6, pady=(2, 6))

        # ── NET ──
        self._net_panel = make_panel(scroll_frame, "NET", self.estilo)
        self._net_widgets: dict[str, tuple[tk.Label, tk.Label, tk.Label]] = {}

        # ── LOAD AVERAGE ──
        load_panel = make_panel(scroll_frame, "LOAD AVG", self.estilo)
        self._load_frame = tk.Frame(load_panel, bg=self.estilo.bg2)
        self._load_frame._bg_rol = "bg2"
        self._load_frame.pack(fill="x", padx=6, pady=(2, 6))

        self._lbl_load1  = self._make_load_label(self._load_frame, "1 min")
        self._lbl_load5  = self._make_load_label(self._load_frame, "5 min")
        self._lbl_load15 = self._make_load_label(self._load_frame, "15 min")



        # ── TOP PROCESSES ──
        top_panel = make_panel(scroll_frame, "TOP PROCESSES", self.estilo)

        # Subencabezado CPU
        lbl_top_cpu_hdr = tk.Label(top_panel, text="CPU %",
                                   bg=self.estilo.bg2, fg=self.estilo.muted,
                                   font=F_SMALL, anchor="w")
        etiquetar(lbl_top_cpu_hdr, ROL_BG2, ROL_MUTED)
        lbl_top_cpu_hdr.pack(fill="x", padx=6, pady=(4, 0))

        self._top_cpu_frame = tk.Frame(top_panel, bg=self.estilo.bg2)
        self._top_cpu_frame._bg_rol = "bg2"
        self._top_cpu_frame.pack(fill="x", padx=6)

        sep_top = tk.Frame(top_panel, bg=self.estilo.border, height=1)
        sep_top._bg_rol = "border"
        sep_top.pack(fill="x", padx=6, pady=4)

        # Subencabezado RAM
        lbl_top_ram_hdr = tk.Label(top_panel, text="RAM MiB",
                                   bg=self.estilo.bg2, fg=self.estilo.muted,
                                   font=F_SMALL, anchor="w")
        etiquetar(lbl_top_ram_hdr, ROL_BG2, ROL_MUTED)

        lbl_top_ram_hdr.pack(fill="x", padx=6)

        self._top_ram_frame = tk.Frame(top_panel, bg=self.estilo.bg2)
        self._top_ram_frame._bg_rol = "bg2"
        self._top_ram_frame.pack(fill="x", padx=6, pady=(0, 6))

        self._top_cpu_widgets: list[tuple[tk.Label, tk.Label, tk.Label]] = []
        self._top_ram_widgets: list[tuple[tk.Label, tk.Label, tk.Label]] = []

        # Pre-crear 5 filas para cada lista
        for _ in range(5):
            self._top_cpu_widgets.append(
                self._make_proc_row(self._top_cpu_frame,show_rss_tag=False))
            self._top_ram_widgets.append(
                self._make_proc_row(self._top_ram_frame,show_rss_tag=True))

        # ── POWER — aparece solo si hay sensor de voltaje (Raspi) ──
        self._power_panel = make_panel(scroll_frame, "POWER", self.estilo)
        power_row = tk.Frame(self._power_panel, bg=self.estilo.bg2)
        etiquetar(power_row, ROL_BG2)
        power_row.pack(fill="x", padx=6, pady=(2, 6))

        lbl_power_name = tk.Label(power_row, text="Supply",
                                  bg=self.estilo.bg2, fg=self.estilo.muted,
                                  font=F_SMALL, width=8, anchor="w")
        etiquetar(lbl_power_name, ROL_BG2, ROL_MUTED)
        lbl_power_name.pack(side="left")

        self._lbl_power_dot = tk.Label(power_row, text="●",
                                       bg=self.estilo.bg2, fg=self.estilo.muted,
                                       font=F_NORMAL)
        etiquetar(self._lbl_power_dot, ROL_BG2, ROL_MUTED)
        self._lbl_power_dot.pack(side="left", padx=(4, 4))

        self._lbl_power_status = tk.Label(power_row, text="--",
                                          bg=self.estilo.bg2, fg=self.estilo.muted,
                                          font=F_SMALL)
        etiquetar(self._lbl_power_status, ROL_BG2, ROL_MUTED)
        self._lbl_power_status.pack(side="left")

        self._power_panel.pack_forget()  # oculto hasta confirmar sensor

    # ─── Helpers de construcción ─────────────────────────────────────────────

    def _make_load_label(self, parent: tk.Frame, period: str) -> tk.Label:
        row = tk.Frame(parent, bg=self.estilo.bg2)
        etiquetar(row, ROL_BG2)
        row.pack(fill="x")

        lbl_name = tk.Label(row, text=period, bg=self.estilo.bg2,
                            fg=self.estilo.muted, font=F_SMALL,
                            width=8, anchor="w")
        etiquetar(lbl_name, ROL_BG2, ROL_MUTED)
        lbl_name.pack(side="left")

        lbl_val = tk.Label(row, text="--", bg=self.estilo.bg2,
                           fg=self.estilo.white, font=F_SMALL)
        etiquetar(lbl_val, ROL_BG2, ROL_WHITE)
        lbl_val.pack(side="right")
        return lbl_val

    def _make_proc_row(self, parent: tk.Frame, show_rss_tag: bool = False) -> tuple[tk.Label, tk.Label, tk.Label]:
        row = tk.Frame(parent, bg=self.estilo.bg2)
        etiquetar(row, ROL_BG2)
        row.pack(fill="x")

        lbl_name = tk.Label(row, text="", bg=self.estilo.bg2,
                            fg=self.estilo.muted, font=F_SMALL,
                            anchor="w")
        etiquetar(lbl_name, ROL_BG2, ROL_MUTED)
        lbl_name.config(cursor="hand2")
        lbl_name.pack(side="left", fill="x", expand=True)

        lbl_val = tk.Label(row, text="", bg=self.estilo.bg2,
                        fg=self.estilo.white, font=F_SMALL,
                        width=9, anchor="e")
        etiquetar(lbl_val, ROL_BG2, ROL_WHITE)
        lbl_val.pack(side="right")

        lbl_rss_num = tk.Label(row, text="", bg=self.estilo.bg2,
                            fg=self.estilo.muted, font=F_SMALL,
                            width=9, anchor="e")
        etiquetar(lbl_rss_num, ROL_BG2, ROL_MUTED)
        lbl_rss_num.pack(side="right")

        if show_rss_tag:
            lbl_rss_tag = tk.Label(row, text="rss", bg=self.estilo.bg2,
                                fg=self.estilo.muted, font=F_SMALL,
                                anchor="e")
            etiquetar(lbl_rss_tag, ROL_BG2, ROL_MUTED)
            lbl_rss_tag.pack(side="right", padx=(0, 4))

        return lbl_name, lbl_val, lbl_rss_num

    # ─── Selectores ──────────────────────────────────────────────────────────

    def _open_theme_selector(self):
        from vista.selectema import ThemeSelector
        ThemeSelector(self.root, self)

    def _open_config(self):
        from vista.configview import ConfigView
        c = Cositas(self)
        c.pause()
        ConfigView(self.root, c, self)

    # ─── Diálogos de detalle ─────────────────────────────────────────────────

    def _open_cpu_detail(self):
        self._cpu_collecting = True
        if self._cpu_detail and self._cpu_detail.winfo_exists():
            self._cpu_detail.lift(); return
        from vista.detailview import DetailView
        self._cpu_detail = DetailView(
            self.root, self, title="CPU Detail",
            color_temp="red", color_usage="blue")
        for t, u in zip(self._cpu_temp_hist, self._cpu_usage_hist):
            self._cpu_detail.push(t, u)

    def _open_gpu_detail(self):
        if not self._has_gpu: return
        self._gpu_collecting = True
        if self._gpu_detail and self._gpu_detail.winfo_exists():
            self._gpu_detail.lift(); return
        from vista.detailview import DetailView
        self._gpu_detail = DetailView(
            self.root, self, title="GPU Detail",
            color_temp="red", color_usage="green")
        for t, u in zip(self._gpu_temp_hist, self._gpu_usage_hist):
            self._gpu_detail.push(t, u)

    # ─── Callback del controlador de temas ───────────────────────────────────

    def apply_estilo(self, nuevo_estilo: Estilo) -> None:
        c = Cositas(self)
        c.pause()
        self.estilo = nuevo_estilo
        self.root.configure(bg=nuevo_estilo.bg)
        self._ttk_style.configure("Ram.Horizontal.TProgressbar",
            troughcolor=nuevo_estilo.bg2, background=nuevo_estilo.blue)
        for detail in (self._cpu_detail, self._gpu_detail):
            if detail and detail.winfo_exists():
                self._controlador_temas._retemar_arbol(detail, nuevo_estilo)
                detail.apply_estilo(nuevo_estilo)
        for d in self._metric_dialogs.values():
            if d.winfo_exists():
                self._controlador_temas._retemar_arbol(d, nuevo_estilo)
                d.apply_estilo(nuevo_estilo)
        c.resume()

    # ─── Update loop ─────────────────────────────────────────────────────────

    def _schedule(self):
        fetch_async()
        self._after_id = self.root.after(INTERVAL, self._tick)

    def _tick(self):
        if self._paused:
            return
        cpu, gpu, cores, cpu_temp, cpu_usage, gpu_usage, ram, net, freq, load, power, procs_cpu, procs_ram = get_latest()

        # GPU panel: aparece/desaparece según datos
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
        self._refresh_freq(freq)
        self._refresh_ram(ram)
        if ram is not None:
            self._ram_total_mib = ram.total_mib        
        self._refresh_net(net)
        self._refresh_load(load)
        self._refresh_power(power)
        self._refresh_procs(self._top_cpu_widgets, procs_cpu, "", is_cpu=True)
        self._refresh_procs(self._top_ram_widgets, procs_ram, "", is_cpu=False)

        # Acumular historiales
        if self._cpu_collecting:
            if cpu_display is not None: self._cpu_temp_hist.append(cpu_display)
            if cpu_usage   is not None: self._cpu_usage_hist.append(cpu_usage)
        if self._gpu_collecting:
            if gpu       is not None: self._gpu_temp_hist.append(gpu)
            if gpu_usage is not None: self._gpu_usage_hist.append(gpu_usage)

        # Alimentar diálogos abiertos
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
                lbl_name.bind("<Button-1>", lambda e, n=iface.name: self._open_speed_panel(n))
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

            # ── historial para SpeedPanel ──
            h = self._net_hist.setdefault(iface.name, {
                "rx": [], "tx": [], "peak_rx": 0.0, "peak_tx": 0.0
            })
            h["rx"].append(iface.recv_kbps)
            h["tx"].append(iface.sent_kbps)
            if len(h["rx"]) > 30: h["rx"].pop(0)
            if len(h["tx"]) > 30: h["tx"].pop(0)
            if iface.recv_kbps > h["peak_rx"]: h["peak_rx"] = iface.recv_kbps
            if iface.sent_kbps > h["peak_tx"]: h["peak_tx"] = iface.sent_kbps

        to_delete = [n for n in self._net_widgets if n not in current]
        for name in to_delete:
            self._net_widgets[name][0].master.destroy()
            del self._net_widgets[name]

    @staticmethod
    def _fmt_net(kbps: float) -> str:
        if kbps >= 1024:
            return f"{kbps/1024:.1f} Mb/s"
        return f"{kbps:.1f} kb/s"

    def _refresh_load(self, load: LoadInfo | None):
        if load is None:
            for lbl in (self._lbl_load1, self._lbl_load5, self._lbl_load15):
                lbl.config(text="--", fg=self.estilo.white)
                lbl._fg_rol = ROL_WHITE
            return
        for lbl, val in ((self._lbl_load1,  load.load1),
                         (self._lbl_load5,  load.load5),
                         (self._lbl_load15, load.load15)):
            if val < 1.0:
                color, rol = self.estilo.green, "green"
            elif val < 2.0:
                color, rol = self.estilo.orange, "orange"
            else:
                color, rol = self.estilo.red, "red"
            lbl.config(text=f"{val:.2f}", fg=color)
            lbl._fg_rol = rol

    def _refresh_power(self, power: PowerInfo | None):
        if power is None:
            if self._has_power:
                self._has_power = False
                self._power_panel.pack_forget()
            return

        if not self._has_power:
            self._has_power = True
            self._power_panel.pack(fill="x", pady=3, padx=6)

        status = power.status
        if status == "ok":
            color, rol, text = self.estilo.green, "green", "OK"
        elif status == "critical":
            color, rol, text = self.estilo.red, "red", "Under-voltage"
        else:
            color, rol, text = self.estilo.orange, "orange", "Fault"

        self._lbl_power_dot.config(fg=color)
        self._lbl_power_dot._fg_rol = rol
        self._lbl_power_status.config(text=text, fg=color)
        self._lbl_power_status._fg_rol = rol

    def _freq_color(self, mhz: float) -> tuple[str, str]:
        if mhz > self._freq_max_observed:
            self._freq_max_observed = mhz
        pct = (mhz / self._freq_max_observed) * 100
        if pct >= 85:
            return self.estilo.red, "red"
        elif pct >= 50:
            return self.estilo.orange, "orange"
        return self.estilo.green, "green"

    def _refresh_freq(self, freq: list[tuple[str, float]]):
        """En Intel: actualiza columna FREQ con color semántico."""
        if self._cores_are_mhz or not freq:
            return
        freq_map = dict(freq)
        for name, widgets in self.core_widgets.items():
            lbl_freq = widgets[2]
            mhz = freq_map.get(name)
            if mhz is None:
                continue
            color, rol = self._freq_color(mhz)
            lbl_freq.config(text=f"{mhz:.0f}MHz", fg=color)
            lbl_freq._fg_rol = rol

    def _refresh_cores(self, cores: list[tuple[str, float]]):
        current_names = set()
        for name, val in cores:
            current_names.add(name)
            if name not in self.core_widgets:
                row = tk.Frame(self.cores_frame, bg=self.estilo.bg2)
                etiquetar(row, ROL_BG2)
                row.pack(fill="x")

                lbl_name = tk.Label(row, text=name, bg=self.estilo.bg2,
                                    fg=self.estilo.muted, font=F_SMALL,
                                    width=8, anchor="w")
                etiquetar(lbl_name, ROL_BG2, ROL_MUTED)
                lbl_name.pack(side="left")

                lbl_temp = tk.Label(row, text="--", bg=self.estilo.bg2,
                                    fg=self.estilo.white, font=F_SMALL,
                                    width=10, anchor="e")
                etiquetar(lbl_temp, ROL_BG2, ROL_WHITE)
                lbl_temp.pack(side="left")

                lbl_freq = tk.Label(row, text="", bg=self.estilo.bg2,
                                    fg=self.estilo.cyan, font=F_SMALL,
                                    width=10, anchor="e")
                etiquetar(lbl_freq, ROL_BG2, "cyan")
                lbl_freq.pack(side="right")

                self.core_widgets[name] = (lbl_name, lbl_temp, lbl_freq)

            lbl_name, lbl_temp, lbl_freq = self.core_widgets[name]

            if self._cores_are_mhz:
                # ARM: solo freq, sin encabezado
                self._cores_header.pack_forget()
                color, rol = self._freq_color(val)
                lbl_temp.config(text=f"{val:.0f} MHz", fg=color)
                lbl_temp._fg_rol = rol
                lbl_freq.config(text="")
            else:
                # Intel: temp en lbl_temp, freq en lbl_freq
                self._cores_header.pack(fill="x", padx=6, pady=(2, 0),
                                        before=self.cores_frame)
                color = temp_color(val, self.estilo)
                lbl_temp.config(text=f"{val:.1f}°C", fg=color)
                lbl_temp._fg_rol = temp_fg_rol(val)

        to_delete = [n for n in self.core_widgets if n not in current_names]
        for name in to_delete:
            self.core_widgets[name][0].master.destroy()
            del self.core_widgets[name]

    def _refresh_procs(self, widgets: list, procs: list[ProcessInfo], fmt: str, is_cpu: bool = False):
        for i, (lbl_name, lbl_val, lbl_rss) in enumerate(widgets):
            if i < len(procs):
                p = procs[i]
                name = p.name if len(p.name) <= 22 else p.name[:20] + "…"
                lbl_name.config(text=name)
                lbl_name.bind("<Button-1>", lambda e, n=p.name, cpu=is_cpu:
                    self._open_proc_metric(n, cpu))

                if is_cpu:
                    if p.value < 30:
                        color, rol = self.estilo.green, "green"
                    elif p.value < 70:
                        color, rol = self.estilo.orange, "orange"
                    else:
                        color, rol = self.estilo.red, "red"
                    lbl_val.config(text=f"{p.value:.1f}%", fg=color)
                    lbl_val._fg_rol = rol
                    lbl_rss.config(text="")
                else:
                    pct = (p.value / self._ram_total_mib) * 100
                    if pct < 30:
                        color, rol = self.estilo.green, "green"
                    elif pct < 70:
                        color, rol = self.estilo.orange, "orange"
                    else:
                        color, rol = self.estilo.red, "red"
                    lbl_val.config(text=f"{p.value:.0f} MiB", fg=color)
                    lbl_val._fg_rol = rol
                    lbl_rss.config(text=f"{p.rss:.0f} MiB", fg=self.estilo.muted)
                    lbl_rss._fg_rol = "muted"
            else:
                lbl_name.config(text="")
                lbl_val.config(text="")

                lbl_rss.config(text="")

    def _open_speed_panel(self, iface_name: str):
        from vista.speed_panel import SpeedPanel
        h = self._net_hist.get(iface_name, {"rx": [], "tx": [], "peak_rx": 0.0, "peak_tx": 0.0})
        from modelo.config import get_ip
        SpeedPanel(self.estilo, self.root,
                label=iface_name,
                ip=get_ip(),
                mac="",
                net_hist=h)
        
    def _open_metric(self, key: str, title: str, chart: str,
                     dims: list[str], unit: str, rol: str):
        from modelo.config import get_ip
        from vista.metric_detail import MetricDetail
        if key in self._metric_dialogs:
            d = self._metric_dialogs[key]
            if d.winfo_exists():
                d.lift(); return
        d = MetricDetail(
            self.root, self,
            title=title,
            ip=get_ip(),
            chart=chart,
            dims=dims,
            unit=unit,
            rol_line=rol,
        )
        self._metric_dialogs[key] = d
 
    def _open_proc_metric(self, group: str, is_cpu: bool):
        if is_cpu:
            key   = f"cpu_{group}"
            title = f"{group} — CPU"
            chart = f"app.{group}_cpu_utilization"
            dims  = ["user", "system"]
            unit  = "%"
            rol   = "cyan"
        else:
            key   = f"ram_{group}"
            title = f"{group} — RAM privada"
            chart = f"app.{group}_mem_private_usage"
            dims  = ["mem"]
            unit  = "MiB"
            rol   = "blue"
        self._open_metric(key, title, chart, dims, unit, rol)

    def _tick_clock(self):
        self.clock_lbl.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    def run(self):
        self._schedule()
        self._tick_clock()
        self.root.mainloop()
