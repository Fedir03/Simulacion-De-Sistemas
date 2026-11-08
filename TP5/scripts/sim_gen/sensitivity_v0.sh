#!/usr/bin/env bash
# Sensibilidad de D12: repite la línea base ajustando v0 con 3, 5 y 7 frames e informa cuánto cambia el ECM.
# Uso, desde TP5/ y con target/tp5.jar compilado: bash scripts/sim_gen/sensitivity_v0.sh
set -euo pipefail
OUT=outputs/sensitivity_v0
for frames in 3 5 7; do
    java -jar target/tp5.jar baseline --v0-frames "$frames" --out "$OUT/v0_$frames"
done
{
    python scripts/graph_gen/compare_runs.py "v0_3=$OUT/v0_3" "v0_5=$OUT/v0_5"
    echo
    python scripts/graph_gen/compare_runs.py "v0_7=$OUT/v0_7" "v0_5=$OUT/v0_5"
} | tee "$OUT/comparacion.txt"
