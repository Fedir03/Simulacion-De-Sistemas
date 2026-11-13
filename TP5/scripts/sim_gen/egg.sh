#!/usr/bin/env bash
# Capa E (huevo): corridas de los 19 eventos sin capa, con la capa (a = 3 m, b = 0,35 m), con la capa y un paso grueso
# (Δt_exp/4), en el que los huevos se solapan más, con un huevo corto (a = 1 m, b = 0,35 m) y con el óptimo poblacional
# de la grilla de E (a = 3 m, b = 0,25 m, el mismo para ECM 1 y ECM 2). Después, el diagnóstico de solapes y tres
# animaciones de tres simulaciones cada una: la original, la del huevo corto y la del óptimo (eventos 2, 14 y 19).
# Uso, desde TP5/ y con target/tp5.jar compilado: bash scripts/sim_gen/egg.sh   (PYTHON=... para elegir el intérprete)
set -euo pipefail
PYTHON="${PYTHON:-python3}"
OUT=outputs/egg
run() { java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain baseline --data data --direction-series true "$@" > /dev/null; }
run --out "$OUT/none"
run --layer e --p1 3.0 --p2 0.35 --out "$OUT/e_3_0.35"
run --layer e --p1 3.0 --p2 0.35 --dt-div 4 --out "$OUT/e_3_0.35_dt4"
run --layer e --p1 1.0 --p2 0.35 --out "$OUT/e_1_0.35"
run --layer e --p1 3.0 --p2 0.25 --out "$OUT/e_3_0.25"
# carpeta a b (la de la línea base se mide con el huevo de referencia)
for spec in "none 3.0 0.35" "e_3_0.35 3.0 0.35" "e_3_0.35_dt4 3.0 0.35" "e_1_0.35 1.0 0.35" "e_3_0.25 3.0 0.25"; do
    read -r d a b <<< "$spec"
    echo "$d: $(grep poblacional "$OUT/$d/ecm.txt")"
    "$PYTHON" scripts/animation/egg_geometry.py "$OUT/$d" "$a" "$b" > "$OUT/$d/solapes.txt"
    tail -1 "$OUT/$d/solapes.txt"
done
"$PYTHON" scripts/animation/egg_animation.py "$OUT"
"$PYTHON" scripts/animation/egg_animation.py "$OUT" --a 1.0 --b 0.35 --panels e_1_0.35:2,e_1_0.35:14,e_1_0.35:19 \
    --out egg_corto_animation.mp4 --title "Capa E con huevo corto (a = 1 m, b = 0,35 m)"
"$PYTHON" scripts/animation/egg_animation.py "$OUT" --a 3.0 --b 0.25 --panels e_3_0.25:2,e_3_0.25:14,e_3_0.25:19 \
    --out egg_optimo_animation.mp4 --title "Capa E con el óptimo poblacional (a = 3 m, b = 0,25 m; ECM 1 y ECM 2)"
