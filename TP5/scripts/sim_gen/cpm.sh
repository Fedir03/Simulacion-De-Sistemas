#!/usr/bin/env bash
# Capas A, B y E sobre el CPM (--model cpm), con las mismas grillas que en el SFM, y comparación SFM contra CPM con los
# mismos parámetros (outputs/cpm/comparacion.md). Las grillas del SFM se leen de outputs/ped/grid_A.txt,
# outputs/ped/grid_B.txt (scripts/sim_gen/per_pedestrian.sh) y outputs/egg/grid_E.txt; si faltan, se corren acá.
# Uso, desde TP5/ y con target/tp5.jar compilado: bash scripts/sim_gen/cpm.sh   (PYTHON=... para elegir el intérprete)
set -euo pipefail
PYTHON="${PYTHON:-python3}"
OUT=outputs/cpm
TA=0.5,1,1.5,2,2.5,3,3.5,4,4.5,5
L=0,0.25,0.5,0.75,1,1.25,1.5,1.75,2,2.25,2.5
K=0,0.5,1,1.5,2,2.5,3,3.5,4
EA=0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6
EB=0.25,0.3,0.35,0.4,0.45,0.5
analysis() { java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain "$@"; }

# SFM (si no están)
[ -f outputs/ped/grid_A.txt ] || analysis grid --layer a --p1-values "$TA" --p2-values "$L" --out outputs/ped/grid_A.txt
[ -f outputs/ped/grid_B.txt ] || analysis grid --layer b --p1-values "$TA" --p2-values "$K" --out outputs/ped/grid_B.txt
[ -f outputs/egg/grid_E.txt ] || analysis grid --layer e --p1-values "$EA" --p2-values "$EB" --out outputs/egg/grid_E.txt
[ -f outputs/ped/none/ecm.txt ] || analysis baseline --out outputs/ped/none > /dev/null

# CPM
analysis baseline --model cpm --out "$OUT/none" > /dev/null
analysis grid --model cpm --layer a --p1-values "$TA" --p2-values "$L" --out "$OUT/grid_A.txt"
analysis grid --model cpm --layer b --p1-values "$TA" --p2-values "$K" --out "$OUT/grid_B.txt"
analysis grid --model cpm --layer e --p1-values "$EA" --p2-values "$EB" --out "$OUT/grid_E.txt"
# Corridas de los óptimos poblacionales del SFM (ECM 1 excl.) con los dos modelos, para las figuras de trayectorias
for spec in "a 3 0.5" "b 3.5 1" "e 3 0.25"; do
    read -r layer p1 p2 <<< "$spec"
    analysis baseline --model cpm --layer "$layer" --p1 "$p1" --p2 "$p2" --out "$OUT/${layer}_${p1}_${p2}" > /dev/null
    analysis baseline --layer "$layer" --p1 "$p1" --p2 "$p2" --out "$OUT/sfm_${layer}_${p1}_${p2}" > /dev/null
done
"$PYTHON" scripts/graph_gen/cpm_compare.py
