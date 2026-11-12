#!/usr/bin/env bash
# Piloto de capas (D2). Grilla oficial = la de la especificación, sobre los 19 eventos.
# outputs/pilot/exploratoria/ es la zona fuera de esa grilla: se eligió después de ver los datos y se reporta aparte.
# Uso, desde TP5/ y con target/tp5.jar compilado: bash scripts/sim_gen/pilot.sh
set -euo pipefail
OUT=outputs/pilot
TA=0.5,1,1.5,2,2.5,3,3.5,4,4.5,5
L=0,0.25,0.5,0.75,1,1.25,1.5,1.75,2,2.25,2.5
K=0,0.5,1,1.5,2,2.5,3,3.5,4
AP=0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9
BP=0.25,0.5,0.75,1,1.5,2,2.5,3
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer a --p1-values "$TA" --p2-values "$L" --out "$OUT/grid_A.txt"
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer b --p1-values "$TA" --p2-values "$K" --out "$OUT/grid_B.txt"
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer f --p1-values "$AP" --p2-values "$BP" --out "$OUT/grid_F.txt"
# F con el desempate angular de la versión original de la especificación, para comparar
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer f --p1-values "$AP" --p2-values "$BP" --f-tie angular --frontal-deg 5 --out "$OUT/grid_F_angular5.txt"
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer f --p1-values "$AP" --p2-values "$BP" --f-tie angular --frontal-deg 1 --out "$OUT/grid_F_angular1.txt"

# Exploratoria (post-hoc)
E="$OUT/exploratoria"
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer a --p1-values 2,2.5,3,3.5 --p2-values 2.5,2.75,3,3.5,4,5 --out "$E/A.txt"
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer b --p1-values 2,2.5,3 --p2-values 4,4.5,5,6,8,12 --out "$E/B.txt"
WIDE_AP=0.3,0.4,0.5,0.6,0.7,0.8,0.9,0.95,0.99
WIDE_BP=3,4,6,8,10,15,20,30,60,1000
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer f --p1-values "$WIDE_AP" --p2-values "$WIDE_BP" --out "$E/F_amplia.txt"
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer f --p1-values "$WIDE_AP" --p2-values "$WIDE_BP" --f-tie angular --frontal-deg 5 --out "$E/F_amplia_angular5.txt"
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer f --p1-values "$WIDE_AP" --p2-values "$WIDE_BP" --f-tie angular --frontal-deg 1 --out "$E/F_amplia_angular1.txt"
