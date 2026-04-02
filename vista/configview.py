"""
vista/configview.py — ventana de configuración general.
Por ahora gestiona la IP del dispositivo monitoreado.

Estructura:
  - Header fijo (título + botón ✕)
  - Área scrollable (body + teclado) — el usuario baja para ver el teclado
  - Footer fijo (Cancelar + Guardar)
"""
import tkinter as tk
from estilo.estiloFactory import EstiloFactory
from modelo import config
from vista.gui_dictionary import FORMATS
from vista.keyboards import _show_kb
from controlador.controladorTemas import (
    etiquetar,
    ROL_BG, ROL_BG2, ROL_BORDER, ROL_CYAN, ROL_MUTED, ROL_BOTON, ROL_WHITE,
)
F_TITLE  = FORMATS["F_TITLE"]
F_NORMAL = FORMATS["F_NORMAL"]
F_SMALL  = FORMATS["F_SMALL"]


class ConfigView(tk.Toplevel):
    def __init__(self, parent_window: tk.Tk, cositas ,app):
        super().__init__(parent_window)
        self._app = app
        self.estilo = EstiloFactory.definirEstilo(config.get_tema())
        self._cositas = cositas
        self.title("Configuración")
        self.geometry("480x260")
        self.resizable(False, True)
        self.configure(bg=self.estilo.bg)

        self.grab_set()
        self.focus_set()
        self._scroll_bindings = []

        self._build_ui()

    def _cerrar(self):
        #from data.parser import fetch_async, _lock, _latest
        # Limpiar último resultado para que no queden datos del dispositivo anterior
        import data.parser as p
        with p._lock:
            p._latest = p._EMPTY
        for detail in (self._app._cpu_detail, self._app._gpu_detail):
            if detail and detail.winfo_exists():
                detail.destroy()                
        # Limpiar historiales de gráficas
        self._app._cpu_temp_hist.clear()
        self._app._cpu_usage_hist.clear()
        self._app._gpu_temp_hist.clear()
        self._app._gpu_usage_hist.clear()
        # Resetear flags para que el diálogo no muestre datos viejos
        self._app._cpu_collecting = False
        self._app._gpu_collecting = False
        self._cositas.resume()
        self.destroy()    
    # ─── Build ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        e = self.estilo

        # ── Header fijo ──────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=e.bg)
        etiquetar(hdr, ROL_BG)
        hdr.pack(fill="x", padx=8, pady=(6, 0))

        lbl_title = tk.Label(hdr, text="CONFIGURACIÓN",
                             bg=e.bg, fg=e.cyan, font=F_TITLE)
        etiquetar(lbl_title, ROL_BG, ROL_CYAN)
        lbl_title.pack(side="left")

        btn_x = tk.Button(hdr, text="✕",
                          bg=e.bg, fg=e.muted,
                          relief="flat", bd=0, cursor="hand2",
                          activebackground=e.bg, activeforeground=e.cyan,
                          command=lambda: self._cerrar())
        etiquetar(btn_x, ROL_BG, ROL_MUTED)
        btn_x.pack(side="right")

        sep1 = tk.Frame(self, bg=e.border, height=1)
        sep1._bg_rol = ROL_BORDER
        sep1.pack(fill="x", padx=8, pady=4)

        # ── Área scrollable ──────────────────────────────────────────────────
        scroll_container = tk.Frame(self, bg=e.bg)
        etiquetar(scroll_container, ROL_BG)
        scroll_container.pack(fill="both", expand=True)
        scroll_container.configure(height=140)  # ajusta este valor
        scroll_container.pack_propagate(False)

        canvas = tk.Canvas(scroll_container, bg=e.bg,
                           highlightthickness=0)
        etiquetar(canvas, ROL_BG)
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical",
                                 command=canvas.yview)

        scroll_frame = tk.Frame(canvas, bg=e.bg)
        etiquetar(scroll_frame, ROL_BG)
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Scroll táctil
        canvas.bind("<Button-1>", lambda e: canvas.scan_mark(e.x, e.y))
        canvas.bind("<B1-Motion>",
                    lambda e: canvas.scan_dragto(e.x, e.y, gain=1))

        # Scroll mouse
        bid1 = self.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        bid2 = self.bind_all("<Button-4>",
            lambda e: canvas.yview_scroll(-1, "units"))
        bid3 = self.bind_all("<Button-5>",
            lambda e: canvas.yview_scroll(1, "units"))
        self._scroll_bindings = [("<MouseWheel>", bid1), ("<Button-4>", bid2), ("<Button-5>", bid3)]

        # ── Contenido del scroll ─────────────────────────────────────────────
        body = tk.Frame(scroll_frame, bg=e.bg)
        etiquetar(body, ROL_BG)
        body.pack(fill="x", padx=12, pady=(6, 0))

        lbl_ip = tk.Label(body, text="IP del dispositivo",
                          bg=e.bg, fg=e.muted, font=F_NORMAL, anchor="w")
        etiquetar(lbl_ip, ROL_BG, ROL_MUTED)
        lbl_ip.pack(fill="x", pady=(0, 4))

        self._ip_var = tk.StringVar(value=config.get_ip())
        self._entry = tk.Entry(
            body,
            textvariable=self._ip_var,
            bg=e.bg2, fg=e.white,
            insertbackground=e.cyan,
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=e.border,
            highlightcolor=e.cyan,
            font=F_NORMAL,
        )
        etiquetar(self._entry, ROL_BG2, ROL_WHITE)
        self._entry.pack(fill="x", ipady=6)
        self._entry.icursor("end")

        lbl_hint = tk.Label(body,
                            text='Usa "localhost" para monitorear este equipo',
                            bg=e.bg, fg=e.muted, font=F_SMALL, anchor="w")
        etiquetar(lbl_hint, ROL_BG, ROL_MUTED)
        lbl_hint.pack(fill="x", pady=(3, 0))

        self._lbl_status = tk.Label(body, text="",
                                    bg=e.bg, fg=e.green,
                                    font=F_SMALL, anchor="w")
        etiquetar(self._lbl_status, ROL_BG, ROL_MUTED)
        self._lbl_status.pack(fill="x")

        # Teclado dentro del scroll — el usuario baja para verlo
        self._kb_frame = tk.Frame(scroll_frame, bg=e.bg)
        etiquetar(self._kb_frame, ROL_BG)
        self._kb_frame.pack(pady=(8, 6))

        _show_kb(self._kb_frame, self.estilo, self._entry, "numpad")

        self._entry.bind("<Return>", lambda _: self._save())

        # ── Footer fijo ──────────────────────────────────────────────────────
        sep2 = tk.Frame(self, bg=e.border, height=1)
        sep2._bg_rol = ROL_BORDER
        sep2.pack(fill="x", padx=8, pady=1,anchor='s')

        ftr = tk.Frame(self, bg=e.bg)
        etiquetar(ftr, ROL_BG)
        
        ftr.pack(side="bottom", fill="x", padx=8, pady=(0, 6))

        btn_cancel = tk.Button(ftr, text="Cancelar",
                               bg=e.bg, fg=e.muted,
                               relief="flat", bd=0, cursor="hand2",
                               activebackground=e.bg, activeforeground=e.cyan,
                               command=lambda: self._cerrar())
        etiquetar(btn_cancel, ROL_BG, ROL_MUTED)
        btn_cancel.pack(side="left")

        btn_save = tk.Button(ftr, text="Guardar",
                             bg=e.boton, fg=e.cyan,
                             relief="flat", bd=0, padx=10, cursor="hand2",
                             command=self._save)
        etiquetar(btn_save, ROL_BOTON, ROL_CYAN)
        btn_save.pack(side="right")

    # ─── Acción ──────────────────────────────────────────────────────────────

    def destroy(self):
        for event, _ in self._scroll_bindings:
            self.unbind_all(event)
        super().destroy()
    def _save(self):
        ip = self._ip_var.get().strip()
        if not ip:
            self._lbl_status.config(text="La IP no puede estar vacía.",
                                    fg=self.estilo.red)
            return

        config.set_ip(ip)
        self._lbl_status.config(text=f"✓ Guardado. Conectando a: {ip}",
                                fg=self.estilo.green)
        
        self._cerrar()
        """
        def _cerrar():
            #from data.parser import fetch_async, _lock, _latest
            # Limpiar último resultado para que no queden datos del dispositivo anterior
            import data.parser as p
            with p._lock:
                p._latest = p._EMPTY
            for detail in (self._app._cpu_detail, self._app._gpu_detail):
                if detail and detail.winfo_exists():
                    detail.destroy()                
            # Limpiar historiales de gráficas
            self._app._cpu_temp_hist.clear()
            self._app._cpu_usage_hist.clear()
            self._app._gpu_temp_hist.clear()
            self._app._gpu_usage_hist.clear()
            # Resetear flags para que el diálogo no muestre datos viejos
            self._app._cpu_collecting = False
            self._app._gpu_collecting = False
            self._cositas.resume()
            self.destroy()"""

        self.after(1200, self._cerrar())

        config.set_ip(ip)
        self._lbl_status.config(
            text=f"✓ Guardado. Conectando a: {ip}",
            fg=self.estilo.green,
        )
        self.after(1200, self.destroy)
