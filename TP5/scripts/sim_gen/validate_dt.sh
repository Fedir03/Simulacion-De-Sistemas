#!/usr/bin/env bash
# Prueba de Δt de D11: los 19 eventos con Δt_exp/32, /64 y /128.
# Criterio (sección 7): el ECM 1 cambia menos de 1% al duplicar la resolución y la energía cinética no tiene saltos.
# Uso, desde TP5/ y con target/tp5.jar compilado: bash scripts/sim_gen/validate_dt.sh
set -euo pipefail
OUT=outputs/validate_dt
INTEGRATOR="${INTEGRATOR:-beeman}"
for div in 32 64 128; do
    java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain baseline --dt-div "$div" --integrator "$INTEGRATOR" --out "$OUT/div$div"
done
python scripts/graph_gen/compare_runs.py "div32=$OUT/div32" "div64=$OUT/div64" "div128=$OUT/div128" | tee "$OUT/comparacion.txt"
