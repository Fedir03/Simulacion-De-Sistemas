#!/usr/bin/env bash
# Calibración por peatón (punto c opcional, 4 parámetros) de las capas A y B, sobre la grilla oficial de la especificación.
# grid-ped corre, por evento, todas las combinaciones par del peatón izquierdo × par del derecho (A: 110² = 12 100;
# B: 90² = 8 100). La grilla de 2 parámetros y la línea base sin capa se corren solo para verificar y comparar.
# Después, tablas (outputs/ped/resumen.md) y figuras (outputs/ped/figs/). Tarda unos 2 minutos con 16 hilos.
# Uso, desde TP5/ y con target/tp5.jar compilado: bash scripts/sim_gen/per_pedestrian.sh   (PYTHON=... para elegir el intérprete)
set -euo pipefail
PYTHON="${PYTHON:-python3}"
OUT=outputs/ped
TA=0.5,1,1.5,2,2.5,3,3.5,4,4.5,5
L=0,0.25,0.5,0.75,1,1.25,1.5,1.75,2,2.25,2.5
K=0,0.5,1,1.5,2,2.5,3,3.5,4
analysis() { java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain "$@"; }
analysis baseline --data data --out "$OUT/none" > /dev/null
analysis grid --layer a --p1-values "$TA" --p2-values "$L" --out "$OUT/grid_A.txt"
analysis grid --layer b --p1-values "$TA" --p2-values "$K" --out "$OUT/grid_B.txt"
analysis grid-ped --layer a --p1-values "$TA" --p2-values "$L" --out "$OUT/grid_ped_A.txt"
analysis grid-ped --layer b --p1-values "$TA" --p2-values "$K" --out "$OUT/grid_ped_B.txt"
"$PYTHON" scripts/graph_gen/per_pedestrian.py "$OUT"
