#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/generated"

if ! command -v latexmk >/dev/null 2>&1; then
  echo "Error: falta la dependencia 'latexmk'." >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -outdir="$OUTPUT_DIR" "$SCRIPT_DIR/presentacion_template.tex"

echo "Presentacion generada en $OUTPUT_DIR/presentacion_template.pdf"

