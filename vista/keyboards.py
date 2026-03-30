# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Juan S.G. Castellanos

"""
vista/keyboards.py — teclados virtuales reutilizables para pantallas táctiles.

Clases disponibles:
    VirtualKeyboard  — QWERTY con acceso a símbolos (CharKeyboard interno)
    Numpad           — numérico para IPs, puertos, números

Firma común:
    Widget(estilo, parent, entry, **kwargs)

El parámetro `estilo` debe tener los atributos:
    bg, bg2, border, white, cyan, orange, muted, green

Los teclados se destruyen y recrean con _show_kb() — no usan pack_forget.
Ver manual_keyboards.md para el patrón de uso completo.
"""
import tkinter as tk

F_NORMAL = ("monospace", 9)
F_SMALL  = ("monospace", 8)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _btn(parent, text, width, fg, estilo, command, font=F_SMALL):
    """Botón plano reutilizable con colores del estilo."""
    return tk.Button(
        parent, text=text, width=width,
        bg=estilo.bg2, fg=fg,
        font=font, relief="flat", bd=0,
        activebackground=estilo.border,
        activeforeground=estilo.cyan,
        command=command,
    )


def _backspace_entry(entry: tk.Entry):
    """Borra el carácter anterior al cursor en un tk.Entry."""
    pos = entry.index("insert")
    if pos > 0:
        entry.delete(pos - 1, pos)


def _clear_entry(entry: tk.Entry):
    entry.delete(0, "end")


# ─── VirtualKeyboard ─────────────────────────────────────────────────────────

class VirtualKeyboard(tk.Frame):
    """
    Teclado QWERTY para texto libre.
    Incluye botón '123' para cambiar a Numpad y '#@' para símbolos (CharKeyboard).
    """

    _ROWS = [
        list("1234567890"),
        list("qwertyuiop"),
        list("asdfghjklñ"),
        list("zxcvbnm.-_"),
    ]

    def __init__(self, estilo, parent, entry: tk.Entry, **kwargs):
        super().__init__(parent, bg=estilo.bg, **kwargs)
        self._estilo  = estilo
        self._entry   = entry
        self._char_kb = None   # CharKeyboard instanciado lazy
        self._build()

    def _build(self):
        e = self._estilo

        for row in self._ROWS:
            rf = tk.Frame(self, bg=e.bg)
            rf.pack()
            for ch in row:
                _btn(rf, ch, 3, e.white, e,
                     command=lambda c=ch: self._type(c)).pack(
                    side="left", padx=1, pady=1)

        # Fila de acciones
        sp = tk.Frame(self, bg=e.bg)
        sp.pack(pady=(2, 0))

        self._btn_case = _btn(sp, "abc", 4, e.muted, e, self._toggle_case)
        self._btn_case.pack(side="left", padx=1)
        self._uppercase = False

        _btn(sp, "espacio", 8, e.white, e,
             lambda: self._type(" ")).pack(side="left", padx=1)

        _btn(sp, "⌫", 4, e.orange, e,
             lambda: _backspace_entry(self._entry)).pack(side="left", padx=1)

        _btn(sp, "Limpiar", 7, e.muted, e,
             lambda: _clear_entry(self._entry)).pack(side="left", padx=1)

        # Alternancia a símbolos y numpad
        sp2 = tk.Frame(self, bg=e.bg)
        sp2.pack(pady=(2, 0))

        _btn(sp2, "#@", 4, e.cyan, e,
             self._to_chars).pack(side="left", padx=1)

        _btn(sp2, "123", 4, e.cyan, e,
             self._to_numpad).pack(side="left", padx=1)

    def _type(self, ch: str):
        ch = ch.upper() if self._uppercase else ch
        pos = self._entry.index("insert")
        self._entry.insert(pos, ch)

    def _toggle_case(self):
        self._uppercase = not self._uppercase
        self._btn_case.config(text="ABC" if self._uppercase else "abc")

    def _to_chars(self):
        """Reemplaza este widget por CharKeyboard en el mismo contenedor."""
        parent = self.master
        self.destroy()
        CharKeyboard(self._estilo, parent, self._entry,
                     on_back=lambda: _show_kb(parent, self._estilo,
                                              self._entry, "qwerty")).pack()

    def _to_numpad(self):
        """Reemplaza este widget por Numpad en el mismo contenedor."""
        parent = self.master
        self.destroy()
        Numpad(self._estilo, parent, self._entry,
               on_back=lambda: _show_kb(parent, self._estilo,
                                        self._entry, "qwerty")).pack()


# ─── CharKeyboard ────────────────────────────────────────────────────────────

class CharKeyboard(tk.Frame):
    """
    Teclado de símbolos especiales.
    Normalmente se accede desde VirtualKeyboard con '#@'.
    Puede instanciarse directamente pasando on_back para volver al QWERTY.
    """

    _KEYS = [
        list("!@#$%^&*()"),
        list("[]{}<>/\\|"),
        list("+=~`"),
        list(".,:;\"'¿?"),
    ]

    def __init__(self, estilo, parent, entry: tk.Entry,
                 on_back=None, **kwargs):
        super().__init__(parent, bg=estilo.bg, **kwargs)
        self._estilo  = estilo
        self._entry   = entry
        self._on_back = on_back
        self._build()

    def _build(self):
        e = self._estilo

        for row in self._KEYS:
            rf = tk.Frame(self, bg=e.bg)
            rf.pack()
            for ch in row:
                _btn(rf, ch, 3, e.white, e,
                     lambda c=ch: self._entry.insert("insert", c)).pack(
                    side="left", padx=1, pady=1)

        sp = tk.Frame(self, bg=e.bg)
        sp.pack(pady=(2, 0))

        _btn(sp, "espacio", 8, e.white, e,
             lambda: self._entry.insert("insert", " ")).pack(side="left", padx=1)

        _btn(sp, "⌫", 4, e.orange, e,
             lambda: _backspace_entry(self._entry)).pack(side="left", padx=1)

        _btn(sp, "Limpiar", 7, e.muted, e,
             lambda: _clear_entry(self._entry)).pack(side="left", padx=1)

        if self._on_back:
            _btn(sp, "abc", 4, e.cyan, e,
                 self._on_back).pack(side="left", padx=1)


# ─── Numpad ───────────────────────────────────────────────────────────────────

class Numpad(tk.Frame):
    """
    Teclado numérico para IPs, puertos y números.
    Incluye: dígitos 0-9, punto '.', dos puntos ':', barra '/',
    borrar ⌫, limpiar y botón opcional para volver a QWERTY.
    """

    def __init__(self, estilo, parent, entry: tk.Entry,
                 on_back=None, **kwargs):
        super().__init__(parent, bg=estilo.bg, **kwargs)
        self._estilo  = estilo
        self._entry   = entry
        self._on_back = on_back
        self._build()

    def _build(self):
        e = self._estilo

        # Fila de dígitos
        rf1 = tk.Frame(self, bg=e.bg)
        rf1.pack()
        for ch in "1234567890":
            _btn(rf1, ch, 2, e.white, e,
                 lambda c=ch: self._entry.insert("insert", c),
                 font=F_NORMAL).pack(side="left", padx=1, pady=2)

        # Fila de acciones
        rf2 = tk.Frame(self, bg=e.bg)
        rf2.pack(pady=(2, 0))

        for text, fg, width, cmd in [
            (".",       e.white,  3, lambda: self._entry.insert("insert", ".")),
            (":",       e.white,  3, lambda: self._entry.insert("insert", ":")),
            ("/",       e.white,  3, lambda: self._entry.insert("insert", "/")),
            ("⌫",       e.orange, 3, lambda: _backspace_entry(self._entry)),
            ("Limpiar", e.muted,  7, lambda: _clear_entry(self._entry)),
        ]:
            _btn(rf2, text, width, fg, e, cmd).pack(side="left", padx=2)

        if self._on_back:
            _btn(rf2, "abc", 4, e.cyan, e,
                 self._on_back).pack(side="left", padx=2)


# ─── Helper público ───────────────────────────────────────────────────────────

def _show_kb(kb_frame: tk.Frame, estilo, entry: tk.Entry, kb_type: str):
    """
    Destruye el contenido de kb_frame y crea el teclado indicado.

    Uso:
        _show_kb(self._kb_frame, self.estilo, self._entry, "numpad")
        _show_kb(self._kb_frame, self.estilo, self._entry, "qwerty")
    """
    for w in kb_frame.winfo_children():
        w.destroy()

    if kb_type == "numpad":
        Numpad(estilo, kb_frame, entry,
               on_back=lambda: _show_kb(kb_frame, estilo, entry, "qwerty")).pack()
    else:
        VirtualKeyboard(estilo, kb_frame, entry).pack()
