#!/usr/bin/env python3
import subprocess
import os
import sys


def resource_path(relative_path: str) -> str:
    """
    Devuelve la ruta correcta tanto en desarrollo como en PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def get_data() -> str:
    script_path = resource_path("monitor_pc.sh")

    try:
        return subprocess.check_output(
            ["bash", script_path],
            text=True
        )
    except Exception as e:
        print("Error ejecutando script:", e)
        return ""


def parse() -> tuple[float | None, float | None, list[tuple[str, float]]]:
    data = get_data().splitlines()

    cpu = None
    gpu = None
    cores = []
    mode = None

    for line in data:
        line = line.strip()

        if line == "CPU:":
            mode = "cpu"
            continue
        elif line == "GPU:":
            mode = "gpu"
            continue
        elif line == "CORES:":
            mode = "cores"
            continue

        if not line:
            continue

        if mode == "cpu":
            try:
                cpu = float(line)
            except ValueError:
                pass

        elif mode == "gpu":
            try:
                gpu = float(line)
            except ValueError:
                pass

        elif mode == "cores":
            if ":" in line:
                name, val = line.split(":", 1)
                try:
                    cores.append((name.strip(), float(val)))
                except ValueError:
                    pass

    return cpu, gpu, cores