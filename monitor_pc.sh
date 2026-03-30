#!/bin/bash

# IP se puede sobreescribir via variable de entorno (lo hace parser.py).
# Si no se pasa, usa el valor hardcodeado como fallback.
IP="${MONITOR_IP:-192.168.0.101}"

# localhost apunta a 127.0.0.1 nativamente, pero lo normalizamos por claridad
if [ "$IP" = "localhost" ]; then
    IP="127.0.0.1"
fi

DATA=$(curl -s http://$IP:19999/api/v1/allmetrics?format=prometheus)

echo "CPU:"
echo "$DATA" | grep "Package id 0" | grep input | grep -v alarm | \
sed -E "s/.* ([0-9.]+) .*/\1/"

echo "CORES:"
echo "$DATA" | grep "Core" | grep input | grep -v alarm | \
sed -E "s/.*label=\"([^\"]+)\".* ([0-9.]+) .*/\1:\2/"

echo "GPU:"
echo "$DATA" | grep "nvidia_smi_gpu_temperature_Celsius_average" | \
sed -E "s/.* ([0-9.]+) .*/\1/"
