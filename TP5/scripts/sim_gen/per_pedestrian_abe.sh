#!/usr/bin/env bash
# Experimento nuevo y aislado: cuatro calibraciones de A, B y E.
# Uso: PYTHON=.venv/bin/python bash scripts/sim_gen/per_pedestrian_abe.sh [carpeta NUEVA]
# Nunca reutiliza ni sobrescribe una carpeta existente. Copia el motor para fijar la versión usada.
set -euo pipefail
PYTHON=${PYTHON:-.venv/bin/python}
OUT=${1:-outputs/ped_abe_$(date +%Y%m%d_%H%M%S)}
"$PYTHON" -c 'import numpy, matplotlib'
mkdir "$OUT"
cp target/tp5.jar "$OUT/tp5.jar"
TA=0.5,1,1.5,2,2.5,3,3.5,4,4.5,5
L=0,0.25,0.5,0.75,1,1.25,1.5,1.75,2,2.25,2.5
K=0,0.5,1,1.5,2,2.5,3,3.5,4
EA=0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6
EB=0.25,0.3,0.35,0.4,0.45,0.5
COMMON=(--data data --model sfm --integrator beeman --dt-div 64 --v0-frames 5 --delta-a 0.1 --rho 0.9
        --trim on --trim-deg 45 --trim-persist 5 --trim-half 2 --trim-target common --trim-shared on --trim-shared-x 1.5)
analysis() {
    printf '%q ' java -cp "$OUT/tp5.jar" ar.edu.itba.sds.tp5.analysis.AnalysisMain "$@" "${COMMON[@]}" >> "$OUT/comandos.txt"
    printf '\n' >> "$OUT/comandos.txt"
    java -cp "$OUT/tp5.jar" ar.edu.itba.sds.tp5.analysis.AnalysisMain "$@" "${COMMON[@]}" | tee -a "$OUT/corridas.log"
}
sha256sum "$OUT/tp5.jar" > "$OUT/motor.sha256"
analysis baseline --out "$OUT/none"
for layer in A B E; do
    case "$layer" in
        A) P1=$TA; P2=$L ;;
        B) P1=$TA; P2=$K ;;
        E) P1=$EA; P2=$EB ;;
    esac
    analysis grid --layer "$layer" --p1-values "$P1" --p2-values "$P2" --out "$OUT/grid_$layer.txt"
    analysis grid-ped --layer "$layer" --p1-values "$P1" --p2-values "$P2" --out "$OUT/grid_ped_$layer.txt"
done
"$PYTHON" scripts/graph_gen/per_pedestrian_abe.py "$OUT"
printf 'Experimento aislado: %s\n' "$OUT"
