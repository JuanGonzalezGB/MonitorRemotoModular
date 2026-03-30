#!/usr/bin/env python3
import subprocess


def get_data() -> str:
    try:
        return subprocess.check_output(["./monitor_pc.sh"]).decode()
    except Exception:
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
            mode = "cpu"; continue
        elif line == "GPU:":
            mode = "gpu"; continue
        elif line == "CORES:":
            mode = "cores"; continue

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
