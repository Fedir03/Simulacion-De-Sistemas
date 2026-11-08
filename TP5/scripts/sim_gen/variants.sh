#!/usr/bin/env bash
# Variantes declaradas de F (no reemplazan a F): F1 sin compuerta, F2 con d_ij entre bordes, F3 las dos. Grilla oficial.
# Uso, desde TP5/ y con target/tp5.jar compilado: bash scripts/sim_gen/variants.sh
set -euo pipefail
export PYTHONIOENCODING=utf-8
OUT=outputs/pilot/variantes
AP=0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9
BP=0.25,0.5,0.75,1,1.5,2,2.5,3
mkdir -p "$OUT"
java -jar target/tp5.jar grid --layer f --p1-values "$AP" --p2-values "$BP" --f-gate off --out "$OUT/grid_F1.txt" > /dev/null
java -jar target/tp5.jar grid --layer f --p1-values "$AP" --p2-values "$BP" --f-distance edges --out "$OUT/grid_F2.txt" > /dev/null
java -jar target/tp5.jar grid --layer f --p1-values "$AP" --p2-values "$BP" --f-gate off --f-distance edges --out "$OUT/grid_F3.txt" > /dev/null
python scripts/graph_gen/f_variants.py > outputs/pilot/variantes.txt
