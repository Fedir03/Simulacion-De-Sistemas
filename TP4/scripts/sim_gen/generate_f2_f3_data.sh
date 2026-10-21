#!/usr/bin/env bash
set -euo pipefail

# Genera los observables del estudio 2.1.a usados por F2 y F3.
# Puede ejecutarse desde cualquier directorio. Las corridas terminadas se omiten,
# por lo que es seguro volver a lanzarlo después de una interrupción.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TP4_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
JAR="$TP4_DIR/target/tp4.jar"

N=300
SEED=1
TF=30
DT2=0.04
DTS_CSV="1e-2,1e-3,1e-4,1e-5,1e-6"
OUTPUT_DIR="$TP4_DIR/outputs/2.1a"
BUILD=true
FORCE=false

usage() {
    cat <<'EOF'
Uso: generate_f2_f3_data.sh [opciones]

Genera un observables.txt por cada dt para las figuras F2 y F3.

Opciones:
  --n N             partículas (predeterminado: 300)
  --seed SEMILLA    misma semilla para todas las corridas (predeterminado: 1)
  --tf SEGUNDOS     tiempo simulado (predeterminado: 30)
  --dt2 SEGUNDOS    intervalo de salida (predeterminado: 0.04)
  --dts LISTA       valores separados por coma
                    (predeterminado: 1e-2,1e-3,1e-4,1e-5,1e-6)
  --output DIR      carpeta de salida (predeterminado: TP4/outputs/2.1a)
  --skip-build      usar target/tp4.jar sin ejecutar Maven
  --force           volver a ejecutar también las corridas terminadas
  -h, --help        mostrar esta ayuda

Prueba rápida (no genera datos válidos para la entrega):
  ./scripts/sim_gen/generate_f2_f3_data.sh \
    --tf 0.08 --dts 1e-3,1e-4 --output /tmp/tp4-2.1a-prueba
EOF
}

need_value() {
    if (($# < 2)); then
        echo "Error: falta el valor de $1" >&2
        exit 2
    fi
}

while (($#)); do
    case "$1" in
        --n) need_value "$@"; N="$2"; shift 2 ;;
        --seed) need_value "$@"; SEED="$2"; shift 2 ;;
        --tf) need_value "$@"; TF="$2"; shift 2 ;;
        --dt2) need_value "$@"; DT2="$2"; shift 2 ;;
        --dts) need_value "$@"; DTS_CSV="$2"; shift 2 ;;
        --output) need_value "$@"; OUTPUT_DIR="$2"; shift 2 ;;
        --skip-build) BUILD=false; shift ;;
        --force) FORCE=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Error: opción desconocida: $1" >&2; usage >&2; exit 2 ;;
    esac
done

command -v java >/dev/null 2>&1 || { echo "Error: no se encontró java." >&2; exit 1; }

if [[ "$BUILD" == true ]]; then
    command -v mvn >/dev/null 2>&1 || {
        echo "Error: no se encontró mvn. Instalá Maven o usá --skip-build si el JAR ya existe." >&2
        exit 1
    }
    echo "Compilando TP4 y ejecutando tests..."
    # La fase package ya incluye test; indicar ambas fases ejecutaría los tests dos veces.
    (cd "$TP4_DIR" && mvn -q package)
fi

[[ -f "$JAR" ]] || { echo "Error: no existe $JAR. Ejecutá 'mvn package'." >&2; exit 1; }
mkdir -p "$OUTPUT_DIR"

IFS=',' read -r -a DTS <<< "$DTS_CSV"
if ((${#DTS[@]} == 0)); then
    echo "Error: la lista de dt está vacía." >&2
    exit 2
fi

echo "Estudio 2.1.a: N=$N, seed=$SEED, tf=$TF, dt2=$DT2, sin obstáculos"
for raw_dt in "${DTS[@]}"; do
    dt="${raw_dt//[[:space:]]/}"
    [[ -n "$dt" ]] || { echo "Error: hay un dt vacío en --dts." >&2; exit 2; }
    case_dir="$OUTPUT_DIR/dt-$dt"
    observables="$case_dir/observables.txt"

    if [[ "$FORCE" == false && -f "$observables" ]] && grep -q '^# fin estado=' "$observables"; then
        echo "[omitida] dt=$dt: ya tiene una corrida terminada en $observables"
        continue
    fi

    echo "[corriendo] dt=$dt -> $case_dir"
    java -jar "$JAR" billiard \
        --n "$N" \
        --seed "$SEED" \
        --x0 none \
        --dt "$dt" \
        --dt2 "$DT2" \
        --tf "$TF" \
        --dynamic no \
        --out "$case_dir"
done

echo "Datos disponibles en: $OUTPUT_DIR"
echo "Siguiente paso: ejecutar los scripts de scripts/graph_gen/."
