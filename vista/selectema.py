"""
vista/selectema.py — selector de temas estilo dashboard.
Se abre como Toplevel desde MonitorApp al hacer click en 🎨.
"""
import tkinter as tk
from vista.gui_dictionary import FORMATS, TEMAS
from controlador.controladorTemas import (
    ControladorTemas, etiquetar,
    ROL_BG, ROL_BG2, ROL_CYAN, ROL_MUTED, ROL_BOTON,
)

F_TITLE  = FORMATS["F_TITLE"]
F_NORMAL = FORMATS["F_NORMAL"]
F_SMALL  = FORMATS["F_SMALL"]


class ThemeSelector(tk.Toplevel):
    def __init__(self, parent_window: tk.Tk, app):
        """
        parent_window : tk.Tk (ventana principal)
        app           : MonitorApp — tiene .estilo y ._controlador_temas
        """
        super().__init__(parent_window)
        self._app = app
        self.estilo = app.estilo
        self._controlador = app._controlador_temas
        self._tema_original = self.estilo.getNombre()

        self.title("Themes")
        self.geometry("480x255")
        self.resizable(False, False)
        self.configure(bg=self.estilo.colorBg())

        # Bloquea la ventana principal mientras el selector está abierto
        self.grab_set()
        self.focus_set()

        self.tipo = tk.StringVar(value=self._codigo_a_display(self._tema_original))
        self._build_ui()

    # ─── Build ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        e = self.estilo  # alias corto

        # Header
        hdr = tk.Frame(self, bg=e.colorBg())
        etiquetar(hdr, ROL_BG)
        hdr.pack(fill="x", padx=8, pady=(6, 0))

        lbl_title = tk.Label(hdr, text="THEMES",
                             bg=e.colorBg(), fg=e.colorCyan(), font=F_TITLE)
        etiquetar(lbl_title, ROL_BG, ROL_CYAN)
        lbl_title.pack(side="left")

        btn_x = tk.Button(hdr, text="✕",
                          bg=e.colorBg(), fg=e.colorMuted(),
                          relief="flat", bd=0, cursor="hand2",
                          activebackground=e.colorBg(),
                          activeforeground=e.colorCyan(),
                          command=self._cancel)
        etiquetar(btn_x, ROL_BG, ROL_MUTED)
        btn_x.pack(side="right")

        sep1 = tk.Frame(self, bg=e.colorBorder(), height=1)
        sep1._bg_rol = "border"
        sep1.pack(fill="x", padx=8, pady=4)

        # Body
        body = tk.Frame(self, bg=e.colorBg())
        etiquetar(body, ROL_BG)
        body.pack(fill="both", expand=True, padx=12, pady=10)

        lbl_sel = tk.Label(body, text="Seleccionar tema",
                           bg=e.colorBg(), fg=e.colorMuted(),
                           font=F_NORMAL, anchor="w")
        etiquetar(lbl_sel, ROL_BG, ROL_MUTED)
        lbl_sel.pack(fill="x", pady=(0, 6))

        self.menu = tk.OptionMenu(body, self.tipo,
                                  *TEMAS.keys(),
                                  command=self._preview)
        self.menu.config(
            bg=e.colorBg2(), fg=e.colorCyan(),
            activebackground=e.colorBg2(), activeforeground=e.colorCyan(),
            highlightthickness=1, highlightbackground=e.colorBorder(), bd=0,
        )
        etiquetar(self.menu, ROL_BG2, ROL_CYAN)
        self.menu.pack(fill="x", pady=(0, 10))

        self.lbl_preview = tk.Label(body, text="Vista previa del tema",
                                    bg=e.colorBg2(), fg=e.colorMuted(),
                                    font=F_SMALL, height=4)
        etiquetar(self.lbl_preview, ROL_BG2, ROL_MUTED)
        self.lbl_preview.pack(fill="x", pady=6)

        sep2 = tk.Frame(self, bg=e.colorBorder(), height=1)
        sep2._bg_rol = "border"
        sep2.pack(fill="x", padx=8, pady=4)

        # Footer
        ftr = tk.Frame(self, bg=e.colorBg())
        etiquetar(ftr, ROL_BG)
        ftr.pack(fill="x", padx=8, pady=(0, 6))

        btn_cancel = tk.Button(ftr, text="Cancelar",
                               bg=e.colorBg(), fg=e.colorMuted(),
                               relief="flat", bd=0, cursor="hand2",
                               activebackground=e.colorBg(),
                               activeforeground=e.colorCyan(),
                               command=self._cancel)
        etiquetar(btn_cancel, ROL_BG, ROL_MUTED)
        btn_cancel.pack(side="left")

        btn_apply = tk.Button(ftr, text="Aplicar",
                              bg=e.colorBoton(), fg=e.colorCyan(),
                              relief="flat", bd=0, padx=10, cursor="hand2",
                              command=self._apply)
        etiquetar(btn_apply, ROL_BOTON, ROL_CYAN)
        btn_apply.pack(side="right")

    # ─── Acciones ────────────────────────────────────────────────────────────

    def _codigo_a_display(self, codigo: str) -> str:
        """Dado un código interno devuelve el nombre visible del dropdown."""
        return next((k for k, v in TEMAS.items() if v == codigo), list(TEMAS)[0])

    def _preview(self, _=None):
        codigo = TEMAS.get(self.tipo.get(), "dark")
        self._controlador.aplicarTema(codigo)
        # Actualizar referencia local al estilo para que el arbol de
        # esta ventana también se retematice
        self.estilo = self._app.estilo
        self._controlador._retemar_arbol(self, self.estilo)

    def _cancel(self):
        self._controlador.aplicarTema(self._tema_original)
        self.estilo = self._app.estilo
        self.destroy()

    def _apply(self):
        codigo = TEMAS.get(self.tipo.get(), "dark")
        self._controlador.aceptarTema(codigo)
        self.destroy()
