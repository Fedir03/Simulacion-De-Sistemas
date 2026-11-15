#!/usr/bin/env bash
set -euo pipefail

# Igual que TP4/presentacion/build_presentacion.sh, con tres agregados para TP5:
#   - compila presentacion_tp5.tex (en TP5 no hay wrapper presentacion_imagen.tex + template);
#   - falla si el log tiene "Overfull \vbox" (contenido que no entra en la diapositiva);
#   - renombra el PDF con el nombre de la entrega: SdS_TP5_2026Q2G02CS_Presentación.pdf.
# Se puede correr desde cualquier carpeta, por ejemplo desde la raíz: bash presentacion/build_presentacion.sh

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/generated"
SOURCE="presentacion_tp5"
FINAL_NAME="SdS_TP5_2026Q2G02CS_Presentación.pdf"

if ! command -v latexmk >/dev/null 2>&1; then
  echo "Error: falta la dependencia 'latexmk'." >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
# Se borra el PDF anterior para que un fallo no deje copiar una versión vieja.
rm -f -- "$OUTPUT_DIR/$SOURCE.pdf" "$OUTPUT_DIR/$FINAL_NAME"

# -gg fuerza una recompilación completa ignorando el estado guardado por
# latexmk (.fdb_latexmk/.fls). Sin esto, si una corrida anterior falló a
# mitad de camino (ej. el PDF estaba abierto en un visor y no se pudo
# sobreescribir), latexmk puede creer erróneamente que el PDF ya está
# actualizado y no recompilar, aunque el .tex haya cambiado.
# Se compila desde SCRIPT_DIR porque las figuras se buscan con rutas relativas (figuras/...).
if ! (cd "$SCRIPT_DIR" && latexmk -pdf -gg -interaction=nonstopmode -halt-on-error \
  -outdir="$OUTPUT_DIR" "$SOURCE.tex"); then
  echo "Error: la compilación de $SOURCE.tex falló. Ver $OUTPUT_DIR/$SOURCE.log" >&2
  exit 1
fi

LOG="$OUTPUT_DIR/$SOURCE.log"
if [[ ! -f "$OUTPUT_DIR/$SOURCE.pdf" ]]; then
  echo "Error: latexmk terminó sin generar $OUTPUT_DIR/$SOURCE.pdf" >&2
  exit 1
fi
if grep -q "^Overfull \\\\vbox" "$LOG"; then
  echo "Error: hay contenido que no entra en la diapositiva (Overfull \\vbox):" >&2
  grep -A1 "^Overfull \\\\vbox" "$LOG" >&2
  exit 1
fi

# Se mueve (no se copia) para que en generated/ quede un solo PDF, con el nombre de la entrega.
mv -f -- "$OUTPUT_DIR/$SOURCE.pdf" "$OUTPUT_DIR/$FINAL_NAME"
echo "Presentacion generada en $OUTPUT_DIR/$FINAL_NAME"
