#!/usr/bin/env bash
# Corre REALIZATIONS realizaciones del mejor mapa encontrado, cada una con una semilla al azar,
# informa sus t90, deja runs.csv y summary.csv (mismo formato que sweep.py) y anima cada una.
#
#   bash TP3/scripts/demo_mejor.sh             # desde cualquier carpeta
#   REALIZATIONS=3 EVERY=50 NO_OPEN=1 bash TP3/scripts/demo_mejor.sh
#
# Etapas:
#   1. Todas las semillas en paralelo: generate con el mapa de MAP_ARGS y simulate hasta t90
#      (--until t90; TIME es el máximo si no se llega al 90 %). Cada corrida deja el estado completo
#      cada EVERY eventos (sim_s<seed>.txt) y todos los tiempos de colisión (sim_s<seed>_events.txt).
#      Cada t90 se informa apenas termina y se escriben runs.csv y summary.csv.
#   2. Se anima la primera semilla con todos los núcleos y se abre en cuanto está lista.
#   3. Se animan las demás en paralelo; cada video se abre al terminar.
# Los videos terminan en t90: un cuadro cada EVERY eventos, sin interpolar.
# Salidas en TP3/generated/demo_mejor/<fecha>/.
set -euo pipefail

# Mejor mapa hasta ahora: cuenco, semicírculo libre de radio 0.34 centrado en cada arco, con la
# frontera hecha de discos de radio r (<t90> = 13.3 ± 1.6 s, 50 realizaciones).
MAP_ARGS=(--obstacles "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/configs/cuenco_fino_R0.34.txt")
REALIZATIONS=${REALIZATIONS:-5}
TIME=${TIME:-100}    # tiempo máximo si no se llega al 90 % [s]
EVERY=${EVERY:-100}  # estado completo cada EVERY eventos
FPS=${FPS:-30}       # cuadros por segundo de video
NO_OPEN=${NO_OPEN:-0} # 1 para no abrir los videos

MODULE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JAR="$MODULE/target/tp3.jar"
OUT="$MODULE/generated/demo_mejor/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT"

if [[ ! -f "$JAR" ]]; then
    echo "Compilando $JAR..."
    mvn -q -f "$MODULE/pom.xml" package -DskipTests
fi

open_video() {
    [[ "$NO_OPEN" == 1 ]] && return
    if grep -qi microsoft /proc/version 2>/dev/null && command -v explorer.exe >/dev/null; then
        explorer.exe "$(wslpath -w "$1")" || true  # explorer.exe devuelve 1 aunque abra el archivo
    elif command -v xdg-open >/dev/null; then
        xdg-open "$1" >/dev/null 2>&1 &
    elif command -v open >/dev/null; then
        open "$1"
    fi
}

t90_of() { grep '^# tf=' "$1" | tail -1 | tr ' ' '\n' | sed -n 's/^t90=//p'; }

simulate_one() {
    local seed=$1 ic="$OUT/ic_s$1.txt" sim="$OUT/sim_s$1.txt"
    java -jar "$JAR" generate --seed "$seed" "${MAP_ARGS[@]}" --out "$ic" > /dev/null
    java -jar "$JAR" simulate --input "$ic" --time "$TIME" --until t90 --every "$EVERY" --out "$sim" > /dev/null
    echo "  semilla $seed: t90 = $(t90_of "$sim") s"
}

animate_one() {
    local seed=$1 jobs=$2 video="$OUT/realizacion_s$1.mp4"
    python3 "$MODULE/scripts/animate.py" "$OUT/sim_s$seed.txt" --out "$video" --fps "$FPS" --jobs "$jobs" > /dev/null 2>&1
    echo "  video listo: $(basename "$video")"
    open_video "$video"
}

mapfile -t SEEDS < <(shuf -i 1-2000000000 -n "$REALIZATIONS")
echo "Mapa: ${MAP_ARGS[*]}"
echo "Semillas: ${SEEDS[*]}"
echo "Simulando $REALIZATIONS realizaciones hasta t90..."
pids=()
for seed in "${SEEDS[@]}"; do simulate_one "$seed" & pids+=($!); done
status=0
for pid in "${pids[@]}"; do wait "$pid" || status=1; done
[[ $status == 0 ]] || { echo "Falló alguna realización; ver $OUT" >&2; exit 1; }

python3 - "$MODULE/scripts" "$OUT" "${SEEDS[@]}" <<'EOF'
import math
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import sweep

out, seeds = Path(sys.argv[2]), [int(s) for s in sys.argv[3:]]
rows = []
for seed in seeds:
    rows.append({'param': '', 'value': '', 'seed': seed, 'status': 'ok', 'K': sweep.count_obstacles(out / f'ic_s{seed}.txt'),
                 **sweep.parse_result(out / f'sim_s{seed}.txt'), 'video': f'realizacion_s{seed}.mp4',
                 'trajectory': f'sim_s{seed}.txt', 'events_log': f'sim_s{seed}_events.txt'})
summary = sweep.summarize(rows)
s = summary[0]
# Error de la media (SEM): desvío estándar entre realizaciones sobre raíz de la cantidad que llegó al 90 %.
s['t90_sem'] = s['t90_std'] / math.sqrt(s['reached_t90']) if s['reached_t90'] > 1 else math.nan
sweep.write_csv(out / 'runs.csv', sweep.RUN_FIELDS + ['video', 'trajectory', 'events_log'], rows)
sweep.write_csv(out / 'summary.csv', sweep.SUMMARY_FIELDS + ['t90_sem'], summary)
print(f"<t90> = {s['t90_mean']:.2f} ± {s['t90_sem']:.2f} s (± = σ/√n, n = {s['reached_t90']}; {s['reached_t90']}/{s['realizations']} llegaron al 90 %)")
print(f"σ(t90) = {s['t90_std']:.2f} s (desvío estándar entre realizaciones)")
EOF
echo "Resultados: $OUT/runs.csv y summary.csv"

echo "Animando la primera realización..."
animate_one "${SEEDS[0]}" "$(nproc)"
if (( REALIZATIONS > 1 )); then
    echo "Animando las otras $((REALIZATIONS - 1)) en paralelo..."
    jobs_each=$(( $(nproc) / (REALIZATIONS - 1) )); (( jobs_each >= 1 )) || jobs_each=1
    pids=()
    for seed in "${SEEDS[@]:1}"; do animate_one "$seed" "$jobs_each" & pids+=($!); done
    for pid in "${pids[@]}"; do wait "$pid" || status=1; done
fi
rm -f "$OUT"/ic_s*.txt
echo "Listo: $OUT"
echo "  realizacion_s*.mp4, sim_s*.txt (estado cada $EVERY eventos hasta t90), sim_s*_events.txt (todos los eventos hasta t90)"
exit $status
