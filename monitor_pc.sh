#!/bin/bash

IP="${MONITOR_IP:-192.168.0.101}"

if [ "$IP" = "localhost" ]; then
    IP="127.0.0.1"
fi

DATA=$(curl -s "http://$IP:19999/api/v1/allmetrics?format=prometheus")

# ─── CPU TOTAL ────────────────────────────────────────────────────────────────
echo "CPU:"

CPU_VAL=$(echo "$DATA" | grep "Package id 0" | grep input | grep -v alarm | grep -v '^#' | \
    sed -E "s/.* ([0-9.]+) .*/\1/" | head -1)

if [ -z "$CPU_VAL" ]; then
    USER=$(echo "$DATA" | grep 'netdata_system_cpu_percentage_average' | grep -v '^#' | \
        grep 'dimension="user"' | sed -E 's/.* ([0-9.]+) [0-9]+$/\1/')
    SYSTEM=$(echo "$DATA" | grep 'netdata_system_cpu_percentage_average' | grep -v '^#' | \
        grep 'dimension="system"' | sed -E 's/.* ([0-9.]+) [0-9]+$/\1/')
    if [ -n "$USER" ] && [ -n "$SYSTEM" ]; then
        CPU_VAL=$(LC_ALL=C awk "BEGIN {printf \"%.7f\", $USER + $SYSTEM}")
    fi
fi
echo "${CPU_VAL:-0}"

# ─── CORES ────────────────────────────────────────────────────────────────────
echo "CORES:"

CORES_INTEL=$(echo "$DATA" | grep "Core" | grep input | grep -v alarm | grep -v '^#' | \
    sed -E 's/.*label="([^"]+)".* ([0-9.]+) [0-9]+$/\1:\2/')

if [ -z "$CORES_INTEL" ]; then
    FREQ_LINES=$(echo "$DATA" | grep 'netdata_cpufreq_cpufreq_MHz_average' | grep -v '^#' | \
        sed -E 's/.*dimension="cpu([0-9]+)"[^}]*\} ([0-9.]+) [0-9]+$/Cpu \1:\2/')
    UNIQUE_FREQS=$(echo "$FREQ_LINES" | sed -E 's/Cpu [0-9]+://' | sort -u | wc -l)
    if [ "$UNIQUE_FREQS" -eq 1 ]; then
        FREQ_VAL=$(echo "$FREQ_LINES" | sed -E 's/Cpu [0-9]+://' | head -1)
        echo "CPU Freq:$FREQ_VAL"
    else
        echo "$FREQ_LINES"
    fi
else
    echo "$CORES_INTEL"
fi

# ─── GPU ──────────────────────────────────────────────────────────────────────
echo "GPU:"
GPU_VAL=$(echo "$DATA" | grep 'netdata_nvidia_smi_gpu_temperature_Celsius_average' | grep -v '^#' | \
    sed -E 's/.*\} ([0-9.]+) [0-9]+$/\1/' | head -1)
echo "${GPU_VAL:-}"

# ─── CPU TEMP (sensor térmico ARM) ───────────────────────────────────────────
echo "CPU_TEMP:"
CPU_TEMP=$(echo "$DATA" | \
    grep 'netdata_system_hw_sensor_temperature_input_degrees_Celsius_average' | grep -v '^#' | \
    grep -v alarm | \
    sed -E 's/.*\} ([0-9.]+) [0-9]+$/\1/' | head -1)
echo "${CPU_TEMP:-}"

# ─── CPU USAGE % ─────────────────────────────────────────────────────────────
echo "CPU_USAGE:"
CPU_USER=$(echo "$DATA" | grep 'netdata_system_cpu_percentage_average' | grep -v '^#' | \
    grep 'dimension="user"' | sed -E 's/.* ([0-9.]+) [0-9]+$/\1/')
CPU_SYS=$(echo "$DATA" | grep 'netdata_system_cpu_percentage_average' | grep -v '^#' | \
    grep 'dimension="system"' | sed -E 's/.* ([0-9.]+) [0-9]+$/\1/')
if [ -n "$CPU_USER" ] && [ -n "$CPU_SYS" ]; then
    LC_ALL=C awk "BEGIN {printf \"%.4f\", $CPU_USER + $CPU_SYS}"
fi
echo ""

# ─── GPU USAGE % ─────────────────────────────────────────────────────────────
echo "GPU_USAGE:"
GPU_USAGE=$(echo "$DATA" | grep 'netdata_nvidia_smi_gpu_utilization_percent_average' | grep -v '^#' | \
    sed -E 's/.*\} ([0-9.]+) [0-9]+$/\1/' | head -1)
echo "${GPU_USAGE:-}"

# ─── RAM ─────────────────────────────────────────────────────────────────────
echo "RAM:"
RAM_FREE=$(echo "$DATA"    | grep 'netdata_system_ram_MiB_average' | grep -v '^#' | grep 'dimension="free"'    | sed -E 's/.*\} ([0-9.]+) [0-9]+$/\1/')
RAM_USED=$(echo "$DATA"    | grep 'netdata_system_ram_MiB_average' | grep -v '^#' | grep 'dimension="used"'    | sed -E 's/.*\} ([0-9.]+) [0-9]+$/\1/')
RAM_CACHED=$(echo "$DATA"  | grep 'netdata_system_ram_MiB_average' | grep -v '^#' | grep 'dimension="cached"'  | sed -E 's/.*\} ([0-9.]+) [0-9]+$/\1/')
RAM_BUFFERS=$(echo "$DATA" | grep 'netdata_system_ram_MiB_average' | grep -v '^#' | grep 'dimension="buffers"' | sed -E 's/.*\} ([0-9.]+) [0-9]+$/\1/')
if [ -n "$RAM_FREE" ] && [ -n "$RAM_USED" ] && [ -n "$RAM_CACHED" ] && [ -n "$RAM_BUFFERS" ]; then
    LC_ALL=C awk "BEGIN {
        used    = $RAM_USED
        cached  = $RAM_CACHED
        buffers = $RAM_BUFFERS
        free    = $RAM_FREE
        total   = used + cached + buffers + free
        pct     = (used / total) * 100
        printf \"%.1f:%.1f:%.1f\", used, total, pct
    }"
fi
echo ""

# ─── RED (interfaces reales) ──────────────────────────────────────────────────
# dimension viene antes que device en el output de Netdata, se extrae con dos greps
echo "NET:"
echo "$DATA" | grep 'netdata_net_net_kilobits_persec_average' | grep -v '^#' | \
    grep 'interface_type="real"' | \
    sed -E 's/.*dimension="([^"]+)".*device="([^"]+)".*\} ([0-9.]+) [0-9]+$/\2:\1:\3/'

# ─── FRECUENCIA POR CORE (Intel y ARM) ───────────────────────────────────────
echo "FREQ:"
echo "$DATA" | grep 'netdata_cpufreq_cpufreq_MHz_average' | grep -v '^#' | \
    sed -E 's/.*dimension="cpu([0-9]+)"[^}]*\} ([0-9.]+) [0-9]+$/Core \1:\2/'

# ─── LOAD AVERAGE ─────────────────────────────────────────────────────────────
echo "LOAD:"
LOAD1=$(echo "$DATA"  | grep 'netdata_system_load_load_average' | grep -v '^#' | \
    grep 'dimension="load1"'  | sed -E 's/.*\} ([0-9.]+) [0-9]+$/\1/')
LOAD5=$(echo "$DATA"  | grep 'netdata_system_load_load_average' | grep -v '^#' | \
    grep 'dimension="load5"'  | sed -E 's/.*\} ([0-9.]+) [0-9]+$/\1/')
LOAD15=$(echo "$DATA" | grep 'netdata_system_load_load_average' | grep -v '^#' | \
    grep 'dimension="load15"' | sed -E 's/.*\} ([0-9.]+) [0-9]+$/\1/')
if [ -n "$LOAD1" ] && [ -n "$LOAD5" ] && [ -n "$LOAD15" ]; then
    echo "${LOAD1}:${LOAD5}:${LOAD15}"
fi
