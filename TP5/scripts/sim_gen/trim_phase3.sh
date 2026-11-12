#!/usr/bin/env bash
# Fase 3 del recorte (11/11): lo que no corre regenerate_pilot.sh, sobre el piloto ya regenerado con el recorte.
#   1. Pruebas 4a (recuperación) y 4c (lado por moneda) de diagnostics/LayerChecks, y su resumen.
#   2. Auditoría (traza de capas, horizonte de F y Δt_exp/128 en los mejores pares).
#   3. ρ de 0,7 a 1,1 cada 0,1 en los mejores pares, con y sin recorte (conmutaciones y d_min por evento).
#   4. Sensibilidad del recorte en los mejores pares, sin regrillar: A(45°), D(30°), D(60°), persistencia 3 y 7,
#      opción 2 (target propio), más D(45°) como control; también la línea base con cada variante.
# Uso, desde TP5/ con target/tp5.jar compilado y PYTHON con numpy: bash scripts/sim_gen/trim_phase3.sh
set -euo pipefail
export PYTHONIOENCODING=utf-8
PY="${PYTHON:-py}"
P=outputs/pilot
OLD=outputs/pilot_sin_recorte
X="$P/recorte_extra"
JAR=target/tp5.jar
mkdir -p "$P/pruebas" "$X/rho" "$X/variantes"

best() { tr -d '\r' < "$1/mejores.txt" | awk '$2 != "ecm1_relleno" {print tolower($1), $3, $4}' | sort -u; }

echo "== 1. Pruebas 4a y 4c =="
java -cp "$JAR" ar.edu.itba.sds.tp5.diagnostics.LayerChecks recovery data "$P/pruebas/recuperacion.txt"
java -cp "$JAR" ar.edu.itba.sds.tp5.diagnostics.LayerChecks coin data "$P/pruebas/moneda.txt" \
    $(best "$P" | awk '$1 != "f" {print $1 ":" $2 ":" $3}')
"$PY" scripts/graph_gen/layer_checks.py > "$P/pruebas.txt"

echo "== 2. Auditoría =="
PYTHON_SHIM="$(mktemp -d)"; trap 'rm -rf "$PYTHON_SHIM"' EXIT
printf '#!/usr/bin/env bash\nexec %s "$@"\n' "$PY" > "$PYTHON_SHIM/python"; chmod +x "$PYTHON_SHIM/python"
PATH="$PYTHON_SHIM:$PATH" bash scripts/sim_gen/audit_f.sh

echo "== 3. ρ cada 0,1 =="
for tag in con sin; do
    if [[ $tag == con ]]; then SRC=$P; TRIM=(); else SRC=$OLD; TRIM=(--trim off); fi
    best "$SRC" | while read -r L P1 P2; do
        for RHO in 0.7 0.8 0.9 1.0 1.1; do
            java -cp "$JAR" ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer "$L" --p1-values "$P1" --p2-values "$P2" --rho "$RHO" "${TRIM[@]}" \
                --out "$X/rho/${tag}_${L}_${P1}_${P2}_rho${RHO}.txt" > /dev/null
        done
    done
done

echo "== 4. Sensibilidad del recorte =="
VARIANTS=("D45:" "A45:--trim-persist 1" "D30:--trim-deg 30" "D60:--trim-deg 60" "p3:--trim-persist 3" "p7:--trim-persist 7" "own:--trim-target own")
for v in "${VARIANTS[@]}"; do
    NAME="${v%%:*}"; read -r -a OPTS <<< "${v#*:}"
    java -cp "$JAR" ar.edu.itba.sds.tp5.analysis.AnalysisMain baseline "${OPTS[@]}" --out "$X/variantes/$NAME/base" > /dev/null
    best "$P" | while read -r L P1 P2; do
        java -cp "$JAR" ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer "$L" --p1-values "$P1" --p2-values "$P2" "${OPTS[@]}" --out "$X/variantes/$NAME/${L}_${P1}_${P2}.txt" > /dev/null
    done
done
echo "listo: $X"
