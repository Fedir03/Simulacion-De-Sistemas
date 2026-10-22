#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TP4_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
ROOT_DIR="$(cd -- "$TP4_DIR/.." && pwd)"
OUT="$TP4_DIR/outputs/runtime_tp4"
TP3_OUT="$TP4_DIR/outputs/runtime_tp3"
NS="100,200,300,400,500,600,714"
TP3_NS="100,200,300,400,500,600"
SEEDS=10
TF=30
DT=1e-5
DT2=0.04
X0=0.0175
BATCH=2147483647
WARMUP="300:5,600:0.32"
TP3_WARMUP="300:5,600:0.3"
BUILD=true
RUN_TP3=true

usage() {
    cat <<'EOF'
Uso: generate_f4_data.sh [opciones]
  --out DIR          salida (predeterminado: outputs/runtime_tp4)
  --tp3-out DIR      salida de TP3 (predeterminado: outputs/runtime_tp3)
  --ns LISTA         N separados por coma (predeterminado: 100,...,600,714)
  --tp3-ns LISTA     N de TP3 (predeterminado: 100,...,600)
  --seeds N          realizaciones por N (predeterminado: 10)
  --tf SEGUNDOS      tiempo simulado (predeterminado: 30)
  --dt SEGUNDOS      paso de integración (predeterminado: 1e-5)
  --dt2 SEGUNDOS     intervalo de observación (predeterminado: 0.04)
  --x0 METROS        obstáculos en ±x0 (predeterminado: 0.0175=r)
  --batch N          ejecutar como máximo N casos; permite tandas cortas
  --warmup LISTA     pares N:tf (predeterminado: 300:5,600:0.32)
  --tp3-warmup LISTA pares N:tf de TP3 (predeterminado: 300:5,600:0.3)
  --skip-build       usar el JAR existente
  --skip-tp3         no generar/reanudar los datos de TP3
  -h, --help         mostrar esta ayuda

La medición es reanudable: repetí exactamente el mismo comando para continuar.
Prueba corta:
  ./scripts/sim_gen/generate_f4_data.sh --ns 20,30 --tp3-ns 20,30 --seeds 2 --tf 0.08 \
    --warmup 20:0.08 --tp3-warmup 20:0.08 --out /tmp/tp4-f4-prueba \
    --tp3-out /tmp/tp3-f4-prueba
EOF
}

need_value() { (($# >= 2)) || { echo "Error: falta el valor de $1" >&2; exit 2; }; }
while (($#)); do
    case "$1" in
        --out) need_value "$@"; OUT="$2"; shift 2 ;;
        --tp3-out) need_value "$@"; TP3_OUT="$2"; shift 2 ;;
        --ns) need_value "$@"; NS="$2"; shift 2 ;;
        --tp3-ns) need_value "$@"; TP3_NS="$2"; shift 2 ;;
        --seeds) need_value "$@"; SEEDS="$2"; shift 2 ;;
        --tf) need_value "$@"; TF="$2"; shift 2 ;;
        --dt) need_value "$@"; DT="$2"; shift 2 ;;
        --dt2) need_value "$@"; DT2="$2"; shift 2 ;;
        --x0) need_value "$@"; X0="$2"; shift 2 ;;
        --batch) need_value "$@"; BATCH="$2"; shift 2 ;;
        --warmup) need_value "$@"; WARMUP="$2"; shift 2 ;;
        --tp3-warmup) need_value "$@"; TP3_WARMUP="$2"; shift 2 ;;
        --skip-build) BUILD=false; shift ;;
        --skip-tp3) RUN_TP3=false; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Error: opción desconocida: $1" >&2; usage >&2; exit 2 ;;
    esac
done

if [[ "$BUILD" == true ]]; then
    command -v mvn >/dev/null 2>&1 || { echo "Error: no se encontró mvn." >&2; exit 1; }
    (cd "$ROOT_DIR" && mvn -q -pl TP3,TP4 package)
fi
[[ -f "$TP4_DIR/target/tp4.jar" ]] || { echo "Error: falta target/tp4.jar." >&2; exit 1; }

if [[ "$RUN_TP3" == true ]]; then
    [[ -f "$ROOT_DIR/TP3/target/tp3.jar" ]] || { echo "Error: falta TP3/target/tp3.jar." >&2; exit 1; }
    echo "F4 TP3: N=$TP3_NS, semillas=$SEEDS, tf=$TF s"
    java -Xms2g -Xmx2g -cp "$ROOT_DIR/TP3/target/tp3.jar" ar.edu.itba.sds.tp3.bench.Tp3Case \
        --out "$TP3_OUT" --ns "$TP3_NS" --seeds "$SEEDS" --tf "$TF" --batch "$BATCH" \
        --warmup "$TP3_WARMUP" --grid-anchor corner --grid-margin 1e-4
fi

echo "F4 TP4: dt=$DT s, N=$NS, semillas=$SEEDS, tf=$TF s, x0=$X0"
java -Xms2g -Xmx2g -cp "$TP4_DIR/target/tp4.jar" ar.edu.itba.sds.tp4.bench.Tp4RuntimeBenchmark \
    --out "$OUT" --ns "$NS" --seeds "$SEEDS" --tf "$TF" --dt "$DT" --dt2 "$DT2" --x0 "$X0" \
    --batch "$BATCH" --warmup "$WARMUP"
