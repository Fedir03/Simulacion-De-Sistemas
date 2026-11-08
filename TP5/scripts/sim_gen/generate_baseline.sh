#!/usr/bin/env bash
# Línea base sin capa: compila, prueba y corre los 19 eventos. Uso, desde TP5/: bash scripts/sim_gen/generate_baseline.sh
set -euo pipefail
mvn -q package
java -jar target/tp5.jar baseline --out outputs/baseline
