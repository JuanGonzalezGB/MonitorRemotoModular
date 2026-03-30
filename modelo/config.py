"""
modelo/config.py — lee y escribe config.json.
Único responsable de la persistencia; el resto de la app no toca el archivo.
"""
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
CONFIG_PATH = os.path.normpath(CONFIG_PATH)

_DEFAULTS = {
    "tema": "dark",
}


def _load() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULTS)


def _save(data: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─── API pública ─────────────────────────────────────────────────────────────

def get_tema() -> str:
    return _load().get("tema", _DEFAULTS["tema"])


def set_tema(codigo: str) -> None:
    data = _load()
    data["tema"] = codigo
    _save(data)
