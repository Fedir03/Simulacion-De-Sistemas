#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TP4_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
PYTHON="${PYTHON:-python3}"
if [[ -x "$TP4_DIR/../.venv/bin/python" && "$PYTHON" == python3 ]]; then
    PYTHON="$TP4_DIR/../.venv/bin/python"
fi
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/tp4-matplotlib}"
command -v ffmpeg >/dev/null
"$PYTHON" -c 'import numpy, matplotlib'
(cd "$TP4_DIR" && mvn -q package)
for case_name in sin_obstaculos con_obstaculos; do
    x0=none
    if [[ "$case_name" == con_obstaculos ]]; then x0=0.25; fi
    output="$TP4_DIR/generated/animaciones/$case_name"
    java -Xmx256m -jar "$TP4_DIR/target/tp4.jar" billiard \
        --n 100 --seed 1 --x0 "$x0" --dt 1e-5 --dt2 0.04 --tf 100 \
        --until tf --dynamic yes --out "$output"
    "$PYTHON" "$TP4_DIR/scripts/animation/animate.py" \
        --input "$output/dynamic.txt" --out "$output/animacion.mp4"
done
