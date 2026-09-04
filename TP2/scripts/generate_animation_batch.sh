#!/usr/bin/env bash
set -euo pipefail

# Genera las 12 combinaciones:
#   modelos: standard, voter
#   densidades: rho = 2, 4, 8 (con L = 10)
#   ruido: eta = 1, 2
#
# Por cada corrida produce:
#   generated/runs/batch/<nombre>.txt
#   generated/animations/batch/<nombre>.mp4 (1920x1080, 16:9)
#   generated/animations/batch/<nombre>.png (fotograma central)

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"

STEPS=1000
FPS=30
L=10
SEED_IC=1
SEED_LOOP=1

RUNS_DIR="$REPO_ROOT/generated/runs/batch"
ANIMATIONS_DIR="$REPO_ROOT/generated/animations/batch"
JAR="$REPO_ROOT/TP2/target/tp2.jar"
PYTHON="$REPO_ROOT/.venv/bin/python"
ANIMATE_SCRIPT="$REPO_ROOT/TP2/scripts/animate.py"

usage() {
  printf '%s\n' \
    "Uso: $0 [--steps CANTIDAD] [--fps CANTIDAD]" \
    "" \
    "Opciones:" \
    "  --steps N   Pasos por corrida (default: 1000)." \
    "  --fps N     Cuadros por segundo (default: 30)." \
    "  -h, --help  Mostrar esta ayuda."
}

require_positive_integer() {
  local option="$1"
  local value="$2"
  if [[ ! "$value" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: $option debe ser un entero positivo; se recibió '$value'." >&2
    exit 2
  fi
}

while (($# > 0)); do
  case "$1" in
    --steps)
      [[ $# -ge 2 ]] || { echo "Error: falta el valor de --steps." >&2; exit 2; }
      STEPS="$2"
      shift 2
      ;;
    --fps)
      [[ $# -ge 2 ]] || { echo "Error: falta el valor de --fps." >&2; exit 2; }
      FPS="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: opción desconocida '$1'." >&2
      usage >&2
      exit 2
      ;;
  esac
done

require_positive_integer "--steps" "$STEPS"
require_positive_integer "--fps" "$FPS"

for command in java ffmpeg ffprobe; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Error: falta el comando requerido '$command'." >&2
    exit 1
  fi
done

if [[ ! -f "$JAR" ]]; then
  echo "Error: no se encontró $JAR. Compilá TP2 antes de ejecutar el batch." >&2
  exit 1
fi

if [[ ! -x "$PYTHON" ]]; then
  echo "Error: no se encontró el intérprete ejecutable $PYTHON." >&2
  exit 1
fi

if [[ ! -f "$ANIMATE_SCRIPT" ]]; then
  echo "Error: no se encontró $ANIMATE_SCRIPT." >&2
  exit 1
fi

mkdir -p "$RUNS_DIR" "$ANIMATIONS_DIR"

TEMP_DIR="$(mktemp -d /tmp/vicsek-animation-batch-XXXXXX)"
cleanup() {
  rm -rf -- "$TEMP_DIR"
}
trap cleanup EXIT

models=(standard voter)
densities=(2 4 8)
etas=(0.5 2)
total=$(( ${#models[@]} * ${#densities[@]} * ${#etas[@]} ))
current=0

for model in "${models[@]}"; do
  for rho in "${densities[@]}"; do
    n=$((rho * L * L))

    for eta in "${etas[@]}"; do
      current=$((current + 1))
      name="${model}_rho${rho}_eta${eta}"
      run_file="$RUNS_DIR/${name}.txt"
      video="$ANIMATIONS_DIR/${name}.mp4"
      image="$ANIMATIONS_DIR/${name}.png"
      raw_video="$TEMP_DIR/${name}-raw.mp4"

      printf '\n[%d/%d] Simulando %s (N=%d, L=%d, eta=%s)...\n' \
        "$current" "$total" "$model" "$n" "$L" "$eta"

      java -jar "$JAR" simulate \
        --model="$model" \
        --n="$n" \
        --l="$L" \
        --eta="$eta" \
        --steps="$STEPS" \
        --seedIC="$SEED_IC" \
        --seedLoop="$SEED_LOOP" \
        --out="$run_file"

      echo "Renderizando animación a $FPS FPS..."
      MPLCONFIGDIR="$TEMP_DIR/matplotlib" "$PYTHON" "$ANIMATE_SCRIPT" \
        "$run_file" \
        --out="$raw_video" \
        --fps="$FPS"

      duration="$(ffprobe -v error -show_entries format=duration \
        -of default=noprint_wrappers=1:nokey=1 "$raw_video")"
      midpoint="$(awk -v duration="$duration" 'BEGIN { printf "%.6f", duration / 2 }')"

      echo "Extrayendo fotograma central sin barras..."
      ffmpeg -hide_banner -loglevel error -y \
        -ss "$midpoint" \
        -i "$raw_video" \
        -frames:v 1 \
        "$image"

      echo "Convirtiendo video a 16:9 (1920x1080)..."
      ffmpeg -hide_banner -loglevel error -y \
        -i "$raw_video" \
        -vf "scale=1080:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1" \
        -c:v libx264 \
        -pix_fmt yuv420p \
        -movflags +faststart \
        -map_metadata -1 \
        "$video"

      echo "Listo: $video"
      echo "Imagen: $image"
    done
  done
done

printf '\nBatch completo.\nCorridas: %s\nAnimaciones e imágenes: %s\n' \
  "$RUNS_DIR" "$ANIMATIONS_DIR"
