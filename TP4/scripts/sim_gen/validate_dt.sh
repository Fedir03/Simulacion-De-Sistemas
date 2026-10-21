#!/usr/bin/env bash
set -euo pipefail

# Valida el dt candidato de 2.1.a en el caso más denso (D1/D6): N=714,
# obstáculos en x0=r y 10 s simulados. Calcula epsilon_E y falla si la corrida
# diverge o supera el umbral.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TP4_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
JAR="$TP4_DIR/target/tp4.jar"

N=714
SEED=1
X0=0.0175
DT=1e-5
DT2=0.04
TF=10
THRESHOLD=1e-3
OUTPUT=""
BUILD=true
FORCE=false

usage() {
    cat <<'EOF'
Uso: validate_dt.sh [opciones]

Opciones:
  --dt VALOR         dt candidato (predeterminado: 1e-5)
  --threshold VALOR  máximo epsilon_E admitido (predeterminado: 1e-3)
  --n N              partículas (predeterminado: 714)
  --seed SEMILLA     semilla (predeterminado: 1)
  --x0 METROS        posición de los obstáculos (predeterminado: 0.0175=r)
  --dt2 SEGUNDOS     intervalo de salida (predeterminado: 0.04)
  --tf SEGUNDOS      tiempo simulado (predeterminado: 10)
  --output DIR       carpeta de salida
  --skip-build       usar target/tp4.jar sin ejecutar Maven
  --force            repetir aunque exista una corrida terminada
  -h, --help         mostrar esta ayuda

La ejecución oficial no necesita opciones:
  ./scripts/sim_gen/validate_dt.sh

Prueba rápida del script (no valida el dt oficial):
  ./scripts/sim_gen/validate_dt.sh --skip-build --n 20 --tf 0.08 \
    --output /tmp/tp4-validacion-dt-prueba --force
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
        --dt) need_value "$@"; DT="$2"; shift 2 ;;
        --threshold) need_value "$@"; THRESHOLD="$2"; shift 2 ;;
        --n) need_value "$@"; N="$2"; shift 2 ;;
        --seed) need_value "$@"; SEED="$2"; shift 2 ;;
        --x0) need_value "$@"; X0="$2"; shift 2 ;;
        --dt2) need_value "$@"; DT2="$2"; shift 2 ;;
        --tf) need_value "$@"; TF="$2"; shift 2 ;;
        --output) need_value "$@"; OUTPUT="$2"; shift 2 ;;
        --skip-build) BUILD=false; shift ;;
        --force) FORCE=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Error: opción desconocida: $1" >&2; usage >&2; exit 2 ;;
    esac
done

if [[ -z "$OUTPUT" ]]; then
    OUTPUT="$TP4_DIR/outputs/validacion-dt/dt-$DT"
fi
OBSERVABLES="$OUTPUT/observables.txt"
SUMMARY="$OUTPUT/resultado-validacion.csv"

command -v java >/dev/null 2>&1 || { echo "Error: no se encontró java." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Error: no se encontró python3." >&2; exit 1; }

if [[ "$BUILD" == true ]]; then
    command -v mvn >/dev/null 2>&1 || {
        echo "Error: no se encontró mvn. Instalá Maven o usá --skip-build si el JAR ya existe." >&2
        exit 1
    }
    echo "Compilando TP4 y ejecutando tests..."
    (cd "$TP4_DIR" && mvn -q package)
fi

[[ -f "$JAR" ]] || { echo "Error: no existe $JAR. Ejecutá 'mvn package'." >&2; exit 1; }

if [[ "$FORCE" == false && -f "$OBSERVABLES" ]] && grep -q '^# fin estado=' "$OBSERVABLES"; then
    echo "Usando la corrida terminada que ya existe: $OBSERVABLES"
else
    echo "Validando dt=$DT con N=$N, x0=$X0, tf=$TF s y umbral=$THRESHOLD..."
    java -jar "$JAR" billiard \
        --n "$N" \
        --seed "$SEED" \
        --x0 "$X0" \
        --dt "$DT" \
        --dt2 "$DT2" \
        --tf "$TF" \
        --dynamic no \
        --out "$OUTPUT"
fi

python3 - \
    "$TP4_DIR/scripts/graph_gen" "$OBSERVABLES" "$SUMMARY" \
    "$N" "$SEED" "$X0" "$DT" "$DT2" "$TF" "$THRESHOLD" <<'PY'
import csv
import math
from pathlib import Path
import sys

module_dir, observables, summary = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
expected_n, expected_seed = int(sys.argv[4]), int(sys.argv[5])
expected_x0, expected_dt, expected_dt2, expected_tf, threshold = map(float, sys.argv[6:11])
sys.path.insert(0, str(module_dir))
from observables import read_run

try:
    run = read_run(observables)
except ValueError as error:
    raise SystemExit(f"Error al leer la validación: {error}")

actual = run.metadata
errors = []
if int(actual["N"]) != expected_n:
    errors.append(f"N={actual['N']} (esperado {expected_n})")
if int(actual["seed"]) != expected_seed:
    errors.append(f"seed={actual['seed']} (esperado {expected_seed})")
for key, expected in (("x0", expected_x0), ("dt", expected_dt), ("dt2", expected_dt2), ("tf", expected_tf)):
    try:
        value = float(actual[key])
    except ValueError:
        errors.append(f"{key}={actual[key]} no es numérico")
        continue
    if not math.isclose(value, expected, rel_tol=1e-12, abs_tol=1e-15):
        errors.append(f"{key}={value:g} (esperado {expected:g})")
if errors:
    raise SystemExit(
        "La corrida existente no corresponde a esta validación: " + "; ".join(errors)
        + ". Volvé a ejecutar con --force o elegí otra carpeta con --output."
    )

epsilon = run.epsilon if len(run.times) > 1 else math.nan
passed = run.status == "completa" and math.isfinite(epsilon) and epsilon <= threshold
summary.parent.mkdir(parents=True, exist_ok=True)
with summary.open("w", newline="", encoding="utf-8") as target:
    writer = csv.writer(target, lineterminator="\n")
    writer.writerow(("n", "seed", "x0", "dt", "dt2", "tf", "epsilon_E", "threshold", "status", "result"))
    writer.writerow((expected_n, expected_seed, expected_x0, expected_dt, expected_dt2, expected_tf,
                     "" if math.isnan(epsilon) else epsilon, threshold, run.status,
                     "APROBADO" if passed else "RECHAZADO"))

print(f"Estado de la simulación: {run.status}")
print(f"epsilon_E: {epsilon:.9g}" if math.isfinite(epsilon) else "epsilon_E: no medible")
print(f"Umbral: {threshold:g}")
print(f"Resultado: {'APROBADO' if passed else 'RECHAZADO'}")
print(f"Resumen: {summary}")
if not passed:
    raise SystemExit(3)
PY

echo "El dt=$DT queda validado para N=$N, x0=$X0 y tf=$TF s."
