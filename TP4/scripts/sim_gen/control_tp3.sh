#!/usr/bin/env bash
set -euo pipefail

# Control de máquina con el motor de TP3 (D12): N=400, semilla 1, tf=30 s, después del calentamiento de la tanda A.
# Corre con --control-only sobre una COPIA de la tanda A (TP4/outputs/runtime_tp3 -> runtime_tp3_control_trabajo),
# porque --control-only reescribe sessions.jsonl, summary.csv y meta.json de su carpeta. La original no se toca.
# Criterio: 38,80 s <= runtime <= 42,88 s (40,84 s ± 5 %) y eventos = 811948 (la misma simulación que en A).
# Con --ref-s SEGUNDOS el criterio de tiempo pasa a ser SEGUNDOS ± 5 % (D12: referencia de la sesión limpia, ~26–27 s);
# los eventos se exigen siempre. Sin --ref-s, todo queda como arriba.
# Uso: control_tp3.sh antes|despues [--allow-other-machine] [--ref-s SEGUNDOS]
# Salida: 0 pasa · 3 falla 'antes' (no medir) · 4 falla 'despues' (todo queda escrito) · 5 otra máquina · 1 otro error.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TP4_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
ROOT_DIR="$(cd -- "$TP4_DIR/.." && pwd)"
ORIGINAL="$TP4_DIR/outputs/runtime_tp3"
WORK="$TP4_DIR/outputs/runtime_tp3_control_trabajo"
JAR="$ROOT_DIR/TP3/target/tp3.jar"
REF="$TP4_DIR/bench/maquina_tp3.properties"
LOW=38.80
HIGH=42.88
EVENTS=811948
# 5d2882d: último commit que tocó TP3/src antes de la tanda A; 91fe505: git_head registrado en el meta.json de A
CODE_REFS=(5d2882d 91fe505)

PHASE=""
ALLOW=false
REF_S=""
USAGE="Uso: control_tp3.sh antes|despues [--allow-other-machine] [--ref-s SEGUNDOS]"
while (($#)); do
    case "$1" in
        antes|despues) PHASE="$1"; shift ;;
        --allow-other-machine) ALLOW=true; shift ;;
        --ref-s)
            (($# >= 2)) || { echo "$USAGE" >&2; exit 1; }
            REF_S="$2"; shift 2 ;;
        *) echo "$USAGE" >&2; exit 1 ;;
    esac
done
[[ -n "$PHASE" ]] || { echo "$USAGE" >&2; exit 1; }
CRITERION="criterio $LOW-$HIGH s y $EVENTS eventos"
if [[ -n "$REF_S" ]]; then
    if [[ ! "$REF_S" =~ ^[0-9]+([.][0-9]+)?$ ]] || ! awk -v r="$REF_S" 'BEGIN { exit !(r > 0) }'; then
        echo "Error: --ref-s espera segundos positivos (p. ej. 26.7): $REF_S" >&2; exit 1
    fi
    LOW="$(awk -v r="$REF_S" 'BEGIN { printf "%.2f", r * 0.95 }')"
    HIGH="$(awk -v r="$REF_S" 'BEGIN { printf "%.2f", r * 1.05 }')"
    CRITERION="criterio $LOW-$HIGH s (referencia $REF_S s ± 5 %) y $EVENTS eventos"
fi
FAIL=3
[[ "$PHASE" == despues ]] && FAIL=4
command -v java >/dev/null 2>&1 || { echo "Error: no se encontró java." >&2; exit 1; }

source "$SCRIPT_DIR/check_machine_tp3.sh"
check_machine_tp3 "$REF" "$ALLOW"

# Mismo código que la tanda A: el árbol de trabajo (no solo HEAD) contra los dos commits, y sin archivos sin seguir
for ref in "${CODE_REFS[@]}"; do
    git -C "$ROOT_DIR" diff --quiet "$ref" -- TP3/src TP3/pom.xml \
        || { echo "Error: TP3/src o TP3/pom.xml difieren de $ref (código de la tanda A)." >&2; exit 1; }
done
[[ -z "$(git -C "$ROOT_DIR" status --porcelain -- TP3/src TP3/pom.xml)" ]] \
    || { echo "Error: hay archivos sin seguir o modificados en TP3/src." >&2; exit 1; }

if [[ "$PHASE" == antes ]]; then
    command -v mvn >/dev/null 2>&1 || { echo "Error: no se encontró mvn." >&2; exit 1; }
    echo "Compilando TP3..."
    (cd "$ROOT_DIR" && mvn -q -B -f TP3/pom.xml package)
fi
[[ -f "$JAR" ]] || { echo "Error: falta $JAR (correr primero control_tp3.sh antes)." >&2; exit 1; }
NEWER="$(find "$ROOT_DIR/TP3/src" "$ROOT_DIR/TP3/pom.xml" -type f -newer "$JAR")"
[[ -z "$NEWER" ]] || { echo "Error: tp3.jar es más viejo que estos fuentes:"$'\n'"$NEWER" >&2; exit 1; }

[[ -f "$ORIGINAL/protocol.json" ]] || { echo "Error: no está la tanda A en $ORIGINAL." >&2; exit 1; }
if [[ ! -d "$WORK" ]]; then
    cp -r "$ORIGINAL" "$WORK"
    echo "Copia de la tanda A en $WORK"
fi
RECHECKS="$WORK/control_rechecks.jsonl"
BEFORE=0
[[ -f "$RECHECKS" ]] && BEFORE="$(grep -c . "$RECHECKS" || true)"

# Mismos argumentos que la tanda A (sessions.jsonl de A), lanzados desde la raíz como entonces, más --control-only
echo "Control TP3 ($PHASE): N=400, semilla 1, tf=30 s, en $WORK"
set +e
(cd "$ROOT_DIR" && java -Xms2g -Xmx2g -cp TP3/target/tp3.jar ar.edu.itba.sds.tp3.bench.Tp3Case \
    --out TP4/outputs/runtime_tp3_control_trabajo --ns 100,200,300,400,500,600 --seeds 10 --tf 30 \
    --warmup 300:5,600:0.3 --grid-anchor corner --grid-margin 1e-4 --control-only true)
JAVA_EXIT=$?
set -e

AFTER=0
[[ -f "$RECHECKS" ]] && AFTER="$(grep -c . "$RECHECKS" || true)"
RUNTIME="" FOUND_EVENTS="" RESULT="FALLA"
if ((JAVA_EXIT == 0 && AFTER == BEFORE + 1)); then
    LINE="$(grep . "$RECHECKS" | tail -n 1)"
    RUNTIME="$(sed -n 's/.*"runtime_s": \([0-9.eE+-]*\).*/\1/p' <<< "$LINE")"
    FOUND_EVENTS="$(sed -n 's/.*"events": \([0-9]*\).*/\1/p' <<< "$LINE")"
    if [[ -n "$RUNTIME" && "$FOUND_EVENTS" == "$EVENTS" ]] \
        && awk -v t="$RUNTIME" -v lo="$LOW" -v hi="$HIGH" 'BEGIN { exit !(t >= lo && t <= hi) }'; then
        RESULT="PASA"
    fi
fi
NOTE=""
[[ "$MACHINE_CHECK" == omitido ]] && NOTE=" | --allow-other-machine: otra PC, el tiempo no valida la máquina de TP3"
LOG_LINE="$(date '+%Y-%m-%dT%H:%M:%S%z') fase=$PHASE resultado=$RESULT runtime_s=${RUNTIME:-?} eventos=${FOUND_EVENTS:-?} \
($CRITERION) java_exit=$JAVA_EXIT lineas_nuevas=$((AFTER - BEFORE)) \
maquina=$MACHINE_CHECK host=$(hostname | tr -d '\r') cpu=${PROCESSOR_IDENTIFIER:-?}$NOTE"
echo "$LOG_LINE" >> "$WORK/control_tp3.log"
echo "$LOG_LINE" >&2
if [[ "$RESULT" != PASA ]]; then
    if [[ "$PHASE" == antes ]]; then
        echo "Control previo FUERA de criterio: no medir." >&2
    else
        echo "Control posterior FUERA de criterio: posible deriva de la máquina durante la tanda; los datos quedan escritos." >&2
    fi
    exit "$FAIL"
fi
