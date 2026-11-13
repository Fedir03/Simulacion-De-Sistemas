#!/usr/bin/env bash
# Capa E (huevo): corridas de los 19 eventos sin capa, con la capa (a = 3 m, b = 0,35 m) y con la capa y un paso grueso
# (Δt_exp/4), en el que los huevos se solapan más. Después, el diagnóstico de solapes y la animación de tres simulaciones.
# Uso, desde TP5/ y con target/tp5.jar compilado: bash scripts/sim_gen/egg.sh   (PYTHON=... para elegir el intérprete)
set -euo pipefail
PYTHON="${PYTHON:-python3}"
OUT=outputs/egg
run() { java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain baseline --data data --direction-series true "$@" > /dev/null; }
run --out "$OUT/none"
run --layer e --p1 3.0 --p2 0.35 --out "$OUT/e_3_0.35"
run --layer e --p1 3.0 --p2 0.35 --dt-div 4 --out "$OUT/e_3_0.35_dt4"
for d in none e_3_0.35 e_3_0.35_dt4; do
    echo "$d: $(grep poblacional "$OUT/$d/ecm.txt")"
    "$PYTHON" scripts/animation/egg_geometry.py "$OUT/$d" 3.0 0.35 > "$OUT/$d/solapes.txt"
    tail -1 "$OUT/$d/solapes.txt"
done
"$PYTHON" scripts/animation/egg_animation.py "$OUT"
