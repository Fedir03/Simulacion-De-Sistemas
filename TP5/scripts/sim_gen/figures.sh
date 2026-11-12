#!/usr/bin/env bash
# Corridas de los mejores pares con la serie de direcciones (motor) y figuras comparativas de A, B y F.
# Las figuras necesitan matplotlib: PYTHON apunta a un intérprete que lo tenga (por defecto, el del TP4).
# Uso, desde TP5/ y con target/tp5.jar compilado: bash scripts/sim_gen/figures.sh
set -euo pipefail
PYTHON="${PYTHON:-../TP4/.venv/Scripts/python.exe}"
OUT=outputs/pilot/figs/datos
mkdir -p "$OUT"
tr -d '\r' < outputs/pilot/mejores.txt | awk '$2 != "ecm1_relleno" {print tolower($1), $3, $4}' | sort -u | while read -r LAYER P1 P2; do
    java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain baseline --layer "$LAYER" --p1 "$P1" --p2 "$P2" --direction-series true --out "$OUT/${LAYER}_${P1}_${P2}" > /dev/null
done
"$PYTHON" scripts/graph_gen/f_figures.py
"$PYTHON" scripts/graph_gen/f_animation.py 12
