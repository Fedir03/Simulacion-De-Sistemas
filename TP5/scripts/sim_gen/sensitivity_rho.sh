#!/usr/bin/env bash
# Sensibilidad a ρ (D10) en los mejores pares del piloto. El par queda fijo: no se recalibra para cada ρ.
# Lee outputs/pilot/mejores.txt y mejores_exploratoria.txt, que escribe scripts/graph_gen/pilot_analysis.py.
# Uso, desde TP5/ y con target/tp5.jar compilado: bash scripts/sim_gen/sensitivity_rho.sh
set -euo pipefail
OUT=outputs/pilot/sensitivity_rho
cat outputs/pilot/mejores.txt outputs/pilot/mejores_exploratoria.txt | tr -d '\r' | awk '{print $1, $3, $4}' | sort -u | while read -r layer p1 p2; do
    for rho in 0.7 0.9 1.1; do
        java -jar target/tp5.jar baseline --layer "$layer" --p1 "$p1" --p2 "$p2" --rho "$rho" \
            --out "$OUT/${layer}_${p1}_${p2}/rho_$rho" > /dev/null
    done
done
python scripts/graph_gen/pilot_rho.py | tee outputs/pilot/sensibilidad_rho.txt
