#!/usr/bin/env bash
set -euo pipefail

# Ejecuta el benchmark de 2.1.b (Tp4Case) en una JVM con -Xms2g -Xmx2g (D12). No compila: antes correr
# build_runtime_tp4.sh. Corre desde TP4/, así que un --out relativo queda dentro de TP4/.
# Uso: runtime_tp4.sh [--allow-other-machine] --out DIR --ns LISTA --rounds R --warmup N:tf,... [--tf 30] [--dt 1e-5]
#      [--dt2 0.04] [--x0 0.0175] [--order-seed 20261022] [--batch k] [--warmup-tol 0.05] [--warmup-max 30] [--warmup-seed 1000]
# Producción: runtime_tp4.sh --out outputs/runtime_tp4_obs --ns 100,200,300,400,500,600,714 --rounds 10 --tf 30 --dt 1e-5 \
#      --dt2 0.04 --warmup 300:1,600:0.5
# Reanudable: relanzar el mismo comando continúa donde quedó.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TP4_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
JAR="$TP4_DIR/target/tp4.jar"
CLASSES="$TP4_DIR/target/bench-classes"
INFO="$CLASSES/build-info.properties"
REF="$TP4_DIR/bench/maquina_tp3.properties"

ALLOW=false
ARGS=()
for a in "$@"; do
    if [[ "$a" == --allow-other-machine ]]; then ALLOW=true; else ARGS+=("$a"); fi
done
if ((${#ARGS[@]} == 0)) || [[ "${ARGS[0]}" == -h || "${ARGS[0]}" == --help ]]; then
    sed -n '4,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 2
fi
command -v java >/dev/null 2>&1 || { echo "Error: no se encontró java." >&2; exit 1; }

source "$SCRIPT_DIR/check_machine_tp3.sh"
check_machine_tp3 "$REF" "$ALLOW"

fail() {
    echo "Error: $*" >&2
    echo "  Correr ./scripts/sim_gen/build_runtime_tp4.sh y volver a lanzar." >&2
    exit 1
}
[[ -f "$JAR" ]] || fail "falta $JAR."
[[ -f "$CLASSES/ar/edu/itba/sds/tp4/bench/Tp4Case.class" ]] || fail "faltan las clases del benchmark en $CLASSES."
[[ -f "$INFO" ]] || fail "falta $INFO."
NEWER="$(find "$TP4_DIR/src/main" "$TP4_DIR/pom.xml" -type f -newer "$JAR")"
[[ -z "$NEWER" ]] || fail "el jar es más viejo que estos fuentes:"$'\n'"$NEWER"
NEWER="$(find "$TP4_DIR/bench/src" -type f -newer "$INFO")"
[[ -z "$NEWER" ]] || fail "las clases del benchmark son más viejas que estos fuentes:"$'\n'"$NEWER"
[[ -z "$(find "$JAR" -newer "$INFO")" ]] || fail "el jar se recompiló después del build del benchmark (build-info no lo describe)."

SEP=":"
to_path() { printf '%s' "$1"; }
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) SEP=";"; to_path() { cygpath -m "$1"; } ;; esac

cd "$TP4_DIR"
exec java -Xms2g -Xmx2g -Dbench.machine_check="$MACHINE_CHECK" -Dbench.machine_reference="$(to_path "$REF")" \
    -cp "$(to_path "$JAR")$SEP$(to_path "$CLASSES")" ar.edu.itba.sds.tp4.bench.Tp4Case "${ARGS[@]}"
