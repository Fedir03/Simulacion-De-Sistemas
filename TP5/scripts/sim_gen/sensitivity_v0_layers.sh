#!/usr/bin/env bash
# Sensibilidad de D12 sobre los mejores pares del piloto: repite cada par con 3, 5 y 7 frames.
# Lee outputs/pilot/mejores.txt y mejores_exploratoria.txt, que escribe scripts/graph_gen/pilot_analysis.py.
# Uso, desde TP5/ y con target/tp5.jar compilado: bash scripts/sim_gen/sensitivity_v0_layers.sh
set -euo pipefail
OUT=outputs/pilot/sensitivity_v0
cat outputs/pilot/mejores.txt outputs/pilot/mejores_exploratoria.txt | tr -d '\r' | awk '{print $1, $3, $4}' | sort -u | while read -r layer p1 p2; do
    for frames in 3 5 7; do
        java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain baseline --layer "$layer" --p1 "$p1" --p2 "$p2" --v0-frames "$frames" \
            --out "$OUT/${layer}_${p1}_${p2}/v0_$frames" > /dev/null
    done
done
for frames in 3 5 7; do
    java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain baseline --v0-frames "$frames" --out "$OUT/base/v0_$frames" > /dev/null
done
python scripts/graph_gen/pilot_sensitivity.py | tee outputs/pilot/sensibilidad_v0.txt
