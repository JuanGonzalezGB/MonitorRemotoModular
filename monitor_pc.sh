#!/bin/bash

IP="192.168.0.101"

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
