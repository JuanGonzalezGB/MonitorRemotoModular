#!/usr/bin/env python3
import os
import sys
import subprocess
from dataclasses import dataclass, field


def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def get_data() -> str:
    from modelo.config import get_ip
    script_path = resource_path("monitor_pc.sh")
    if not os.path.exists(script_path):
        print(f"Script no encontrado: {script_path}")
        return ""
    env = os.environ.copy()
    env["MONITOR_IP"] = get_ip()
    try:
        return subprocess.check_output(
            ["bash", script_path], text=True, timeout=5, env=env)
    except subprocess.TimeoutExpired:
        print("Timeout ejecutando script"); return ""
    except subprocess.CalledProcessError as e:
        print(f"Script terminó con error (código {e.returncode})"); return ""
    except Exception as e:
        print(f"Error inesperado: {e}"); return ""


@dataclass
class RamInfo:
    used_mib:  float        # RAM usada (sin cache/buffers)
    total_mib: float        # RAM total
    pct:       float        # porcentaje usado

@dataclass
class NetIface:
    name:     str
    recv_kbps: float        # kilobits/s recibidos (positivo)
    sent_kbps: float        # kilobits/s enviados (positivo)


def parse() -> tuple[
    float | None,           # cpu
    float | None,           # gpu
    list[tuple[str, float]],# cores
    float | None,           # cpu_temp
    float | None,           # cpu_usage
    float | None,           # gpu_usage
    RamInfo | None,         # ram
    list[NetIface],         # net
]:
    data = get_data().splitlines()

    cpu: float | None       = None
    gpu: float | None       = None
    cpu_temp: float | None  = None
    cpu_usage: float | None = None
    gpu_usage: float | None = None
    ram: RamInfo | None     = None
    cores: list[tuple[str, float]] = []
    net_raw: dict[str, dict[str, float]] = {}  # {iface: {received, sent}}
    mode: str | None = None

    for line in data:
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
            # formato: used:total:pct
            parts = line.split(":")
            if len(parts) == 3:
                try:
                    ram = RamInfo(
                        used_mib  = float(parts[0]),
                        total_mib = float(parts[1]),
                        pct       = float(parts[2]),
                    )
                except ValueError: pass

        elif mode == "net":
            # formato: iface:dimension:value
            parts = line.split(":")
            if len(parts) == 3:
                iface, dim, val_str = parts
                try:
                    val = abs(float(val_str))  # sent viene negativo en Netdata
                    if iface not in net_raw:
                        net_raw[iface] = {}
                    net_raw[iface][dim] = val
                except ValueError: pass

        elif mode == "cores":
            if ":" in line:
                name, val = line.split(":", 1)
                try: cores.append((name.strip(), float(val)))
                except ValueError: pass

    # Construir lista de interfaces
    net: list[NetIface] = []
    for iface, dims in net_raw.items():
        net.append(NetIface(
            name      = iface,
            recv_kbps = dims.get("received", 0.0),
            sent_kbps = dims.get("sent",     0.0),
        ))

    return cpu, gpu, cores, cpu_temp, cpu_usage, gpu_usage, ram, net
