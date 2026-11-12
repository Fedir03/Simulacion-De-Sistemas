#!/usr/bin/env bash
# Línea base sin capa: compila, prueba y corre los 19 eventos. Uso, desde TP5/: bash scripts/sim_gen/generate_baseline.sh
set -euo pipefail
mvn -q package
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain baseline --out outputs/baseline
