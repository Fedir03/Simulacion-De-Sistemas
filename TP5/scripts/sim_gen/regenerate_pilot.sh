#!/usr/bin/env bash
# Regenera el piloto completo y sus análisis con el motor actual, en el orden en que dependen entre sí.
# Uso, desde TP5/ y con target/tp5.jar compilado: bash scripts/sim_gen/regenerate_pilot.sh
set -euo pipefail
export PYTHONIOENCODING=utf-8
P=outputs/pilot
rm -rf "$P/sensitivity_v0" "$P/sensitivity_rho"
java -jar target/tp5.jar baseline --out outputs/baseline > /dev/null
bash scripts/sim_gen/pilot.sh > /dev/null
python scripts/graph_gen/pilot_analysis.py > "$P/analisis.txt"
python scripts/graph_gen/pilot_compare.py > "$P/comparacion_f.txt"
python scripts/graph_gen/per_event.py > "$P/por_evento.txt"
python scripts/graph_gen/cross_validation.py > "$P/validacion.txt"
bash scripts/sim_gen/sensitivity_rho.sh > /dev/null
bash scripts/sim_gen/sensitivity_v0_layers.sh > /dev/null
python scripts/graph_gen/trace_report.py > "$P/traza.txt"
