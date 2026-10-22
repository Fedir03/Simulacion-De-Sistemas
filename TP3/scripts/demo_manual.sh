#!/usr/bin/env bash
# Una realización: generar -> simular hasta t90 -> animar, usando el venv activo.
set -euo pipefail

usage() {
    cat <<'EOF'
Uso: bash scripts/demo_manual.sh ARCHIVO_OBSTACULOS SEED

Ejemplo (desde TP3, con el .venv activado):
  bash scripts/demo_manual.sh configs/cuenco_fino_R0.34.txt 42
  TIME=30 UNTIL=time EVERY=10 bash scripts/demo_manual.sh configs/central.txt 123

Ejecuta una sola corrida y muestra los goles y t90 en la terminal.
Variables: N=100 TIME=100 UNTIL=t90 EVERY=100 FPS=30 ARROWS=1
UNTIL=time ejecuta todo TIME; UNTIL=t90 termina al alcanzar el 90 %.
Cada ejecución conserva sus archivos en generated/demo_manual/<carpeta única>/.
El MP4 se guarda en esa carpeta para abrirlo manualmente.
EOF
}
fail() { echo "Error: $*" >&2; exit 1; }
if [[ "${1:-}" == --help || "${1:-}" == -h ]]; then usage; exit 0; fi
[[ $# == 2 ]] || { usage >&2; exit 1; }
MAP=$1
SEED=$2
[[ -r "$MAP" && -f "$MAP" ]] || fail "No se puede leer el mapa: $MAP"
[[ "$SEED" =~ ^-?[0-9]+$ ]] || fail "La seed debe ser un entero."

MODULE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JAR="$MODULE/target/tp3.jar"
# Python resuelve el intérprete del entorno activado, también en Git Bash.
command -v python >/dev/null || fail "Activá tu .venv antes de ejecutar este script."
python -c 'import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)' \
    || fail "Activá tu .venv antes de ejecutar este script."
python -c 'import matplotlib, numpy' \
    || fail "Instalá las dependencias: python -m pip install -r \"$MODULE/requirements.txt\""
command -v ffmpeg >/dev/null || fail "FFmpeg debe estar instalado y disponible en PATH para crear el MP4."
SEED=$(python -c 'import sys; n=int(sys.argv[1]); sys.exit("Seed fuera del rango de 64 bits") if not -(2**63) <= n < 2**63 else print(n)' "$SEED")

N=${N:-100}
TIME=${TIME:-100}
UNTIL=${UNTIL:-t90}
EVERY=${EVERY:-100}
FPS=${FPS:-30}
ARROWS=${ARROWS:-1}
[[ "$UNTIL" == time || "$UNTIL" == t90 ]] || fail "UNTIL debe ser time o t90."

# Maven recompila si hubo cambios desde la última corrida.
mvn -q -f "$MODULE/pom.xml" package -DskipTests
mkdir -p "$MODULE/generated/demo_manual"
OUT=$(mktemp -d "$MODULE/generated/demo_manual/$(date +%Y%m%d_%H%M%S)_s${SEED}_XXXXXX")
IC="$OUT/ic_s${SEED}.txt"
SIM="$OUT/sim_s${SEED}.txt"
VIDEO="$OUT/realizacion_s${SEED}.mp4"

echo "Resultados: $OUT"
echo "1/3 Generando condición inicial (mapa: $MAP, seed: $SEED)..."
java -jar "$JAR" generate --n "$N" --seed "$SEED" --obstacles "$MAP" --out "$IC"

echo "2/3 Simulando (hasta $UNTIL, máximo $TIME segundos)..."
java -jar "$JAR" simulate --input "$IC" --time "$TIME" --until "$UNTIL" --every "$EVERY" --out "$SIM"

echo "3/3 Animando..."
ANIMATION_ARGS=()
[[ "$ARROWS" == 1 ]] && ANIMATION_ARGS+=(--arrows)
python "$MODULE/scripts/animate.py" "$SIM" --out "$VIDEO" --fps "$FPS" "${ANIMATION_ARGS[@]}"
echo "Listo. Video: $VIDEO"
