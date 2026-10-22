#!/usr/bin/env bash
set -euo pipefail

# Genera las salidas del Sistema 2 para 2.1.b/2.4, 2.2 y 2.3 con el dt elegido (D1: 1e-5, D3: dt2 = 0.04 s).
# NO mide los tiempos de 2.1.b: esos se miden aparte con el protocolo de D12 (JVM calentada, máquina de Fede).
# Acá las corridas van en paralelo; el motor es determinista, así que (N, x0, semilla) da la misma simulación
# que en la medición. Reanudable: omite cada corrida cuyo observables.txt ya tenga el pie "# fin estado=".

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"
TP4_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
JAR="$TP4_DIR/target/tp4.jar"
OUT="$TP4_DIR/outputs"

DT=1e-5
DT2=0.04
JOBS=8
HEAP=256m
STUDIES="2.1b,2.2,2.3"
BUILD=true
DRY_RUN=false

# D7, D8, D9, D13
N_21B="50 100 200 300 400 500 600 714"
SEEDS_21B=10
N_22="100 20"
X0_22="0.0175 0.06 0.12 0.18 0.24 0.30 0.36 0.43 0.4925"
SEEDS_22=8
SEEDS_23=30

usage() {
    cat <<'EOF'
Uso: generate_studies_data.sh [opciones]

  2.1b  x0=r, N = 50 100 200 300 400 500 600 714, semillas 1-10, tf=30 s (Nu(t) para 2.4; dynamic en N=600 semilla 1)
  2.2   N = 100 y 20, 9 valores de x0 (D13), semillas 1-8, tmax=100 s con --until t100 (dynamic en N=100 semilla 1)
  2.3   N=100 sin obstáculos, semillas 1-30, tf=30 s, con dynamic.txt

Opciones:
  --studies LISTA   subconjunto separado por comas (predeterminado: 2.1b,2.2,2.3)
  --jobs J          corridas en paralelo (predeterminado: 8)
  --heap H          -Xmx de cada JVM (predeterminado: 256m)
  --skip-build      usar target/tp4.jar sin ejecutar Maven
  --dry-run         solo listar las corridas
  -h, --help        mostrar esta ayuda

Salidas: outputs/2.1b/n-N/seed-K, outputs/2.2/n-N/x0-X/seed-K, outputs/2.3/seed-K
EOF
}

while (($#)); do
    case "$1" in
        --studies) STUDIES="$2"; shift 2 ;;
        --jobs) JOBS="$2"; shift 2 ;;
        --heap) HEAP="$2"; shift 2 ;;
        --skip-build) BUILD=false; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Error: opción desconocida: $1" >&2; usage >&2; exit 2 ;;
    esac
done

if [[ "$BUILD" == true ]]; then
    echo "Compilando TP4 y ejecutando tests..."
    (cd "$TP4_DIR" && mvn -q package)
fi
[[ -f "$JAR" ]] || { echo "Error: no existe $JAR. Ejecutá 'mvn package'." >&2; exit 1; }

# Una línea por corrida: carpeta|opciones del comando billiard
jobs_file="$(mktemp)"
trap 'rm -f "$jobs_file"' EXIT
want() { [[ ",$STUDIES," == *",$1,"* ]]; }

if want 2.1b; then
    for n in $N_21B; do
        for seed in $(seq 1 "$SEEDS_21B"); do
            dyn=no; [[ "$n" == 600 && "$seed" == 1 ]] && dyn=yes
            echo "$OUT/2.1b/n-$n/seed-$seed|--n $n --seed $seed --x0 0.0175 --tf 30 --dynamic $dyn" >> "$jobs_file"
        done
    done
fi
if want 2.2; then
    for n in $N_22; do
        for x0 in $X0_22; do
            for seed in $(seq 1 "$SEEDS_22"); do
                dyn=no; [[ "$n" == 100 && "$seed" == 1 ]] && dyn=yes
                echo "$OUT/2.2/n-$n/x0-$x0/seed-$seed|--n $n --seed $seed --x0 $x0 --tf 100 --until t100 --dynamic $dyn" >> "$jobs_file"
            done
        done
    done
fi
if want 2.3; then
    for seed in $(seq 1 "$SEEDS_23"); do
        echo "$OUT/2.3/seed-$seed|--n 100 --seed $seed --x0 none --tf 30 --dynamic yes" >> "$jobs_file"
    done
fi

total=$(wc -l < "$jobs_file")
echo "Corridas: $total (dt=$DT, dt2=$DT2, $JOBS en paralelo, -Xmx$HEAP)"
if [[ "$DRY_RUN" == true ]]; then cat "$jobs_file"; exit 0; fi

run_one() {
    local dir="${1%%|*}" opts="${1#*|}"
    if [[ -f "$dir/observables.txt" ]] && grep -q '^# fin estado=' "$dir/observables.txt"; then
        echo "[omitida] $dir"; return 0
    fi
    mkdir -p "$(dirname "$dir")"
    # shellcheck disable=SC2086
    if java "-Xmx$HEAP" -jar "$JAR" billiard $opts --dt "$DT" --dt2 "$DT2" --out "$dir" > /dev/null 2> "$dir.err"; then
        rm -f "$dir.err"; echo "[ok] $dir"
    else
        echo "[ERROR] $dir (ver $dir.err)"; return 1
    fi
}
export -f run_one
export JAR DT DT2 HEAP

mkdir -p "$OUT"
# Las corridas largas primero (N grande), para que el paralelo no termine esperando a una sola
sort -t'|' -k1,1 -r "$jobs_file" | awk -F'|' '{n=$2; sub(/.*--n /,"",n); sub(/ .*/,"",n); print n "\t" $0}' \
    | sort -k1,1nr | cut -f2- | tr '\n' '\0' | xargs -0 -P "$JOBS" -I{} bash -c 'run_one "$1"' _ {}
echo "Listo. Salidas en $OUT/2.1b, $OUT/2.2 y $OUT/2.3"
