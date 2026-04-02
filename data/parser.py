#!/usr/bin/env python3
import os
import sys
import subprocess
import threading
from dataclasses import dataclass


def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def get_data() -> str:
    from modelo.config import get_ip
    script_path = resource_path("monitor_pc.sh")
    if not os.path.exists(script_path):
        return ""
    env = os.environ.copy()
    env["MONITOR_IP"] = get_ip()
    try:
        return subprocess.check_output(
            ["bash", script_path], text=True, timeout=8, env=env)
    except Exception as e:
        print(f"Error en script: {e}")
        return ""


@dataclass
class RamInfo:
    used_mib:  float
    total_mib: float
    pct:       float


@dataclass
class NetIface:
    name:      str
    recv_kbps: float
    sent_kbps: float


ParseResult = tuple[
    float | None,
    float | None,
    list[tuple[str, float]],
    float | None,
    float | None,
    float | None,
    RamInfo | None,
    list[NetIface],
]

_EMPTY: ParseResult = (None, None, [], None, None, None, None, [])


def _parse_raw(raw: str) -> ParseResult:
    lines = raw.splitlines()
    cpu = gpu = cpu_temp = cpu_usage = gpu_usage = None
    ram: RamInfo | None = None
    cores: list[tuple[str, float]] = []
    net_raw: dict[str, dict[str, float]] = {}
    mode = None

    for line in lines:
        line = line.strip()
        if   line == "CPU:":       mode = "cpu";       continue
        elif line == "GPU:":       mode = "gpu";       continue
        elif line == "CORES:":     mode = "cores";     continue
        elif line == "CPU_TEMP:":  mode = "cpu_temp";  continue
        elif line == "CPU_USAGE:": mode = "cpu_usage"; continue
        elif line == "GPU_USAGE:": mode = "gpu_usage"; continue
        elif line == "RAM:":       mode = "ram";       continue
        elif line == "NET:":       mode = "net";       continue
        if not line:
            continue

        if mode == "cpu":
            try: cpu = float(line)
            except ValueError: pass
        elif mode == "gpu":
            try: gpu = float(line)
            except ValueError: pass
        elif mode == "cpu_temp":
            try: cpu_temp = float(line)
            except ValueError: pass
        elif mode == "cpu_usage":
            try: cpu_usage = float(line)
            except ValueError: pass
        elif mode == "gpu_usage":
            try: gpu_usage = float(line)
            except ValueError: pass
        elif mode == "ram":
            parts = line.split(":")
            if len(parts) == 3:
                try:
                    ram = RamInfo(float(parts[0]), float(parts[1]), float(parts[2]))
                except ValueError: pass
        elif mode == "net":
            # formato: iface:dimension:value
            parts = line.split(":")
            if len(parts) == 3:
                iface, dim, val_str = parts
                try:
                    val = abs(float(val_str))
                    net_raw.setdefault(iface, {})[dim] = val
                except ValueError: pass
        elif mode == "cores":
            if ":" in line:
                name, val = line.split(":", 1)
                try: cores.append((name.strip(), float(val)))
                except ValueError: pass

    net = [NetIface(iface, d.get("received", 0.0), d.get("sent", 0.0))
           for iface, d in net_raw.items()]
    return cpu, gpu, cores, cpu_temp, cpu_usage, gpu_usage, ram, net


# ─── API asíncrona ───────────────────────────────────────────────────────────

_lock   = threading.Lock()
_latest: ParseResult = _EMPTY
_running = False


def _worker():
    global _latest, _running
    raw = get_data()
    result = _parse_raw(raw) if raw else _EMPTY
    with _lock:
        _latest = result
    _running = False


def fetch_async():
    """Lanza el script en un thread si no hay uno en curso."""
    global _running
    with _lock:
        if _running:
            return
        _running = True
    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def get_latest() -> ParseResult:
    """Devuelve el último resultado disponible (nunca bloquea)."""
    with _lock:
        return _latest
