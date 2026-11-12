#!/usr/bin/env bash
# Diagnóstico del error de A(3; 0,5): pruebas de v_0, trazas de lado y análisis (solo lectura sobre el motor).
# Uso, desde TP5/: bash scripts/sim_gen/diag_a.sh
set -euo pipefail
OUT=outputs/pilot/diagnostico_A/corridas
DIAG=ar.edu.itba.sds.tp5.diagnostics
PY=${PYTHON:-py}

mvn -q package
mkdir -p "$OUT/traza"

# V0Probe con el ajuste de D12 tiene que reproducir byte a byte la corrida oficial de A(3; 0,5)
java -cp target/tp5.jar $DIAG.V0Probe --mode fit --layer a --p1 3 --p2 0.5 --out "$OUT/A_ajuste"
diff -r "$OUT/A_ajuste" outputs/pilot/sensitivity_rho/A_3_0.5/rho_0.9 > /dev/null || { echo "V0Probe no reproduce la corrida oficial" >&2; exit 1; }

for mode in vd_target vd_fitdir; do
  java -cp target/tp5.jar $DIAG.V0Probe --mode $mode --layer a --p1 3 --p2 0.5 --out "$OUT/A_$mode"
done
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain baseline --layer a --p1 3 --p2 0.5 --v0-frames 2 --out "$OUT/A_primer_cuadro"

for e in $(seq 1 19); do
  java -cp target/tp5.jar $DIAG.RunTrace --event "$e" --layer a --p1 3 --p2 0.5 > "$OUT/traza/a_$e.txt"
  java -cp target/tp5.jar $DIAG.RunTrace --event "$e" --layer b --p1 3.5 --p2 1 > "$OUT/traza/b_$e.txt"
done

PYTHONPATH=scripts/graph_gen "$PY" scripts/graph_gen/diag_a.py
