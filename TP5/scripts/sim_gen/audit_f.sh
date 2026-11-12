#!/usr/bin/env bash
# Auditoría de las capas: mediciones sobre los mejores pares de outputs/pilot/mejores.txt. No toca las grillas del piloto.
# Uso, desde TP5/ y con target/tp5.jar compilado: bash scripts/sim_gen/audit_f.sh
set -euo pipefail
export PYTHONIOENCODING=utf-8
OUT=outputs/pilot/auditoria
AP=0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9
BP=0.25,0.5,0.75,1,1.5,2,2.5,3
mkdir -p "$OUT"
PAIRS=$(tr -d '\r' < outputs/pilot/mejores.txt | awk '$2 != "ecm1_relleno" {print tolower($1), $3, $4}' | sort -u)

# Contacto, lado, conmutaciones y evento reflejado. Sale de diagnostics/
java -cp target/tp5.jar ar.edu.itba.sds.tp5.diagnostics.LayerChecks audit data "$OUT/traza_capas.txt" \
    $(echo "$PAIRS" | awk '{print $1 ":" $2 ":" $3}')

# Horizonte de F (sin límite es grid_F.txt)
for H in 2.5 5; do
    java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer f --p1-values "$AP" --p2-values "$BP" --f-horizon "$H" --out "$OUT/grid_F_ta$H.txt" > /dev/null
done

# Convergencia: mejores pares con Δt_exp/128 (Δt_exp/64 está en las grillas)
echo "$PAIRS" | while read -r LAYER P1 P2; do
    java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer "$LAYER" --p1-values "$P1" --p2-values "$P2" --dt-div 128 --out "$OUT/dt128_${LAYER}_${P1}_${P2}.txt" > /dev/null
done
python scripts/graph_gen/audit_f.py > outputs/pilot/auditoria.txt
