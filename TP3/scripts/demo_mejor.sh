#!/usr/bin/env bash
# Corre REALIZATIONS realizaciones del mejor mapa encontrado, cada una con una semilla al azar,
# informa sus t90, deja runs.csv y summary.csv (mismo formato que sweep.py) y anima cada una.
#
#   bash TP3/scripts/demo_mejor.sh             # desde cualquier carpeta
#   REALIZATIONS=3 EVERY=50 NO_OPEN=1 bash TP3/scripts/demo_mejor.sh
#   REALIZATIONS=3 bash TP3/scripts/demo_mejor.sh --only-initial
#   NO_OPEN=1 bash TP3/scripts/demo_mejor.sh --input condicion.txt
#   bash TP3/scripts/demo_mejor.sh --no-anim   # solo t90 y <t90> ± σ/√n; sin videos
#   bash TP3/scripts/demo_mejor.sh --live --no-anim   # demo en vivo: una corrida por vez, cada gol visible
#
# Etapas:
#   1. Todas las semillas en paralelo: generate con el mapa de MAP_ARGS y simulate hasta t90
#      (--until t90; TIME es el máximo si no se llega al 90 %). Cada corrida deja el estado completo
#      cada EVERY eventos (sim_s<seed>.txt) y todos los tiempos de colisión (sim_s<seed>_events.txt).
#      Cada t90 se informa apenas termina y se escriben runs.csv y summary.csv.
#   2. Se anima la primera semilla con todos los núcleos y se abre en cuanto está lista.
#   3. Se animan las demás en paralelo; cada video se abre al terminar.
# Con --no-anim termina después de la etapa 1, sin generar videos.
# Con --live la etapa 1 corre las semillas una por vez y muestra la salida del motor (cada gol y t90).
# Los videos terminan en t90: un cuadro cada EVERY eventos, sin interpolar.
# Salidas en TP3/generated/demo_mejor/<fecha>_<id>/; conserva ic_s<seed>.txt.
set -euo pipefail

# Mejor mapa hasta ahora: cuenco, semicírculo libre de radio 0.34 centrado en cada arco, con la
# frontera hecha de discos de radio r (<t90> = 13.3 ± 1.6 s, 50 realizaciones).
MAP_ARGS=(--obstacles "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/configs/cuenco_fino_R0.34cd tp  cd.txt")
REALIZATIONS=${REALIZATIONS:-5}
TIME=${TIME:-100}    # tiempo máximo si no se llega al 90 % [s]
EVERY=${EVERY:-100}  # estado completo cada EVERY eventos
FPS=${FPS:-30}       # cuadros por segundo de video
NO_OPEN=${NO_OPEN:-0} # 1 para no abrir los videos
ARROWS=${ARROWS:-1}   # 0 para no dibujar el pico de dirección de cada partícula
ONLY_INITIAL=0
ANIMATE=1
LIVE=0
INPUT=""
usage() {
    cat <<'EOF'
Uso: demo_mejor.sh [--only-initial | --input archivo.txt] [--no-anim] [--live]

  Sin flags       Genera, simula y anima REALIZATIONS corridas (por defecto 5).
  --only-initial  Genera únicamente REALIZATIONS archivos de condición inicial.
  --input ARCHIVO Simula y anima una sola condición inicial existente; ignora
                  REALIZATIONS y el mapa predeterminado. Conserva una copia.
  --no-anim       Simula e informa t90 y <t90> ± σ/√n, sin generar videos.
  --live          Simula las realizaciones una por vez mostrando cada gol y
                  su t90 (salida del motor). Sin este flag corren en paralelo.
  -h, --help      Muestra esta ayuda.

Siempre se conservan los archivos ic_s<semilla>.txt en la carpeta de resultados.
Variables: REALIZATIONS, TIME, EVERY, FPS, NO_OPEN y ARROWS.
EOF
}
fail() { echo "Error: $*" >&2; exit 1; }
while (( $# )); do
    case "$1" in
        --only-initial) ONLY_INITIAL=1; shift ;;
        --no-anim) ANIMATE=0; shift ;;
        --live) LIVE=1; shift ;;
        --input)
            (( $# >= 2 )) && [[ -n "$2" && "$2" != --* ]] || fail "Falta el archivo para --input."
            [[ -z "$INPUT" ]] || fail "--input solo puede indicarse una vez."
            INPUT=$2; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) fail "Argumento desconocido: $1. Usá --help para ver las opciones." ;;
    esac
done
(( ! (LIVE && ONLY_INITIAL) )) || fail "--live y --only-initial no se pueden combinar."
if [[ -n "$INPUT" ]]; then
    (( ONLY_INITIAL == 0 )) || fail "--only-initial y --input no se pueden combinar."
    [[ -f "$INPUT" && -r "$INPUT" ]] || fail "No se puede leer: $INPUT"
    # El formato tp3-v1 incluye la semilla original en su primera línea.
    seed=$(head -n 1 -- "$INPUT" | tr ' ' '\n' | sed -n 's/^seedIC=//p' | tr -d '\r')
    [[ "$seed" =~ ^-?[0-9]+$ ]] || fail "El archivo no tiene un seedIC válido."
    SEEDS=("$seed")
    REALIZATIONS=1
else
    [[ "$REALIZATIONS" =~ ^[1-9][0-9]*$ ]] && (( REALIZATIONS <= 2000000000 )) || fail "REALIZATIONS debe ser un entero entre 1 y 2000000000."
fi
# Git Bash en Windows: animate.py con --jobs > 1 usa multiprocessing 'fork', que no existe ahí,
# y la consola cp1252 no imprime σ. Se usa un proceso por video y salida UTF-8.
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) WINDOWS=1; export PYTHONUTF8=1 ;; *) WINDOWS=0 ;; esac

MODULE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JAR="$MODULE/target/tp3.jar"
mkdir -p "$MODULE/generated/demo_mejor"
OUT=$(mktemp -d "$MODULE/generated/demo_mejor/$(date +%Y%m%d_%H%M%S)_XXXXXX")

if [[ ! -f "$JAR" ]]; then
    echo "Compilando $JAR..."
    mvn -q -f "$MODULE/pom.xml" package -DskipTests
fi

open_video() {
    [[ "$NO_OPEN" == 1 ]] && return
    if (( WINDOWS )); then
        cmd.exe //c start "" "$(cygpath -w "$1")"
    elif grep -qi microsoft /proc/version 2>/dev/null && command -v explorer.exe >/dev/null; then
        explorer.exe "$(wslpath -w "$1")" || true  # explorer.exe devuelve 1 aunque abra el archivo
    elif command -v xdg-open >/dev/null; then
        xdg-open "$1" >/dev/null 2>&1 &
    elif command -v open >/dev/null; then
        open "$1"
    fi
}

t90_of() { grep '^# tf=' "$1" | tail -1 | tr ' ' '\n' | sed -n 's/^t90=//p'; }

generate_one() {
    local seed=$1 ic="$OUT/ic_s$1.txt"
    java -jar "$JAR" generate --seed "$seed" "${MAP_ARGS[@]}" --out "$ic" > /dev/null || return
    echo "  condición inicial: $(basename "$ic")"
}

simulate_one() {
    local seed=$1 ic="$OUT/ic_s$1.txt" sim="$OUT/sim_s$1.txt"
    if [[ -n "$INPUT" ]]; then
        cp -- "$INPUT" "$ic" || return
    else
        generate_one "$seed" || return
    fi
    if (( LIVE )); then
        # UTF-8 explícito: en Windows la consola de Java usa cp1252 y "partícula" sale mal en Git Bash.
        java -Dstdout.encoding=UTF-8 -jar "$JAR" simulate --input "$ic" --time "$TIME" --until t90 --every "$EVERY" --out "$sim" || return
    else
        java -jar "$JAR" simulate --input "$ic" --time "$TIME" --until t90 --every "$EVERY" --out "$sim" > /dev/null || return
    fi
    echo "  semilla $seed: t90 = $(t90_of "$sim") s"
}

animate_one() {
    local seed=$1 jobs=$2 video="$OUT/realizacion_s$1.mp4"
    python3 "$MODULE/scripts/animate.py" "$OUT/sim_s$seed.txt" --out "$video" --fps "$FPS" --jobs "$jobs" \
        $( (( ARROWS )) && echo --arrows ) > /dev/null
    echo "  video listo: $(basename "$video")"
    open_video "$video"
}

if [[ -n "$INPUT" ]]; then
    echo "Condición inicial: $INPUT"
else
    mapfile -t SEEDS < <(shuf -i 1-2000000000 -n "$REALIZATIONS")
    (( ${#SEEDS[@]} == REALIZATIONS )) || fail "No se pudieron generar las semillas."
    echo "Mapa: ${MAP_ARGS[*]}"
fi
echo "Semillas: ${SEEDS[*]}"
if (( ONLY_INITIAL )); then
    echo "Generando $REALIZATIONS condiciones iniciales..."
    pids=()
    for seed in "${SEEDS[@]}"; do generate_one "$seed" & pids+=($!); done
    status=0
    for pid in "${pids[@]}"; do wait "$pid" || status=1; done
    [[ $status == 0 ]] || fail "Falló alguna generación; ver $OUT"
    echo "Listo: $OUT"
    echo "  ic_s*.txt (condiciones iniciales; sin simulaciones ni videos)"
    exit 0
fi
status=0
if (( LIVE )); then
    echo "Simulando $REALIZATIONS realizaciones hasta t90, una por vez..."
    k=0
    for seed in "${SEEDS[@]}"; do
        k=$((k + 1))
        echo; echo "=== Realización $k/$REALIZATIONS (semilla $seed) ==="
        simulate_one "$seed" || { status=1; break; }
    done
    echo
else
    echo "Simulando $REALIZATIONS realizaciones hasta t90..."
    pids=()
    for seed in "${SEEDS[@]}"; do simulate_one "$seed" & pids+=($!); done
    for pid in "${pids[@]}"; do wait "$pid" || status=1; done
fi
[[ $status == 0 ]] || { echo "Falló alguna realización; ver $OUT" >&2; exit 1; }

python3 - "$MODULE/scripts" "$OUT" "$ANIMATE" "${SEEDS[@]}" <<'EOF'
import math
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import sweep

out, animate, seeds = Path(sys.argv[2]), sys.argv[3] == '1', [int(s) for s in sys.argv[4:]]
rows = []
for seed in seeds:
    rows.append({'param': '', 'value': '', 'seed': seed, 'status': 'ok', 'K': sweep.count_obstacles(out / f'ic_s{seed}.txt'),
                 **sweep.parse_result(out / f'sim_s{seed}.txt'), 'video': f'realizacion_s{seed}.mp4' if animate else '',
                 'trajectory': f'sim_s{seed}.txt', 'events_log': f'sim_s{seed}_events.txt',
                 'initial_condition': f'ic_s{seed}.txt'})
summary = sweep.summarize(rows)
s = summary[0]
sweep.write_csv(out / 'runs.csv', sweep.RUN_FIELDS + ['video', 'trajectory', 'events_log', 'initial_condition'], rows)
# Error de la media: desvío muestral de los t90 sobre la raíz de las n realizaciones que llegaron al 90 %.
s['t90_sem'] = s['t90_std'] / math.sqrt(s['reached_t90']) if s['reached_t90'] > 1 else math.nan
sweep.write_csv(out / 'summary.csv', sweep.SUMMARY_FIELDS + ['t90_sem'], summary)
print(f"<t90> = {s['t90_mean']:.2f} ± {s['t90_sem']:.2f} s (± = σ/√n, n = {s['reached_t90']}; {s['reached_t90']}/{s['realizations']} llegaron al 90 %)")
EOF
echo "Resultados: $OUT/runs.csv y summary.csv"

if (( ! ANIMATE )); then
    echo "Listo (sin animar): $OUT"
    echo "  ic_s*.txt (condición inicial), sim_s*.txt (estado cada $EVERY eventos hasta t90), sim_s*_events.txt (todos los eventos hasta t90)"
    exit 0
fi

echo "Animando la primera realización..."
if (( WINDOWS )); then first_jobs=1; else first_jobs=$(nproc); fi
animate_one "${SEEDS[0]}" "$first_jobs"
if (( REALIZATIONS > 1 )); then
    echo "Animando las otras $((REALIZATIONS - 1)) en paralelo..."
    jobs_each=$(( $(nproc) / (REALIZATIONS - 1) )); (( jobs_each >= 1 && ! WINDOWS )) || jobs_each=1
    pids=()
    for seed in "${SEEDS[@]:1}"; do animate_one "$seed" "$jobs_each" & pids+=($!); done
    for pid in "${pids[@]}"; do wait "$pid" || status=1; done
fi
echo "Listo: $OUT"
echo "  ic_s*.txt (condición inicial), realizacion_s*.mp4, sim_s*.txt (estado cada $EVERY eventos hasta t90), sim_s*_events.txt (todos los eventos hasta t90)"
exit $status
