#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/generated"

if ! command -v latexmk >/dev/null 2>&1; then
  echo "Error: falta la dependencia 'latexmk'." >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
# -gg fuerza una recompilación completa ignorando el estado guardado por
# latexmk (.fdb_latexmk/.fls). Sin esto, si una corrida anterior falló a
# mitad de camino (ej. el PDF estaba abierto en un visor y no se pudo
# sobreescribir), latexmk puede creer erróneamente que el PDF ya está
# actualizado y no recompilar, aunque el .tex haya cambiado.
latexmk -pdf -gg -interaction=nonstopmode -halt-on-error \
  -outdir="$OUTPUT_DIR" "$SCRIPT_DIR/presentacion_imagen.tex"

echo "Presentacion generada en $OUTPUT_DIR/presentacion_imagen.pdf"

