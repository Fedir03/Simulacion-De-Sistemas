#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/generated"
BUILD_DIR="$(mktemp -d /tmp/tp2-presentacion-XXXXXX)"

cleanup() {
  rm -rf -- "$BUILD_DIR"
}
trap cleanup EXIT

for dependency in latexmk pdftoppm python3 libreoffice; do
  if ! command -v "$dependency" >/dev/null 2>&1; then
    echo "Error: falta la dependencia '$dependency'." >&2
    exit 1
  fi
done

if [[ ! -f "$SCRIPT_DIR/template_presentacion_tp2.tex" ]]; then
  echo "Error: no se encontró template_presentacion_tp2.tex en $SCRIPT_DIR." >&2
  exit 1
fi

mkdir -p "$BUILD_DIR/latex" "$BUILD_DIR/rendered" "$BUILD_DIR/pptx" "$OUTPUT_DIR"

echo "[1/4] Compilando PDF de entrega..."
cd "$SCRIPT_DIR"
latexmk \
  -pdf \
  -interaction=nonstopmode \
  -halt-on-error \
  -outdir="$BUILD_DIR/latex" \
  presentacion_imagen.tex

echo "[2/4] Renderizando las 28 diapositivas para Google Slides..."
pdftoppm \
  -png \
  -r 144 \
  -f 1 \
  -l 28 \
  "$BUILD_DIR/latex/presentacion_imagen.pdf" \
  "$BUILD_DIR/rendered/slide" \
  >/dev/null 2>&1

echo "[3/4] Generando PPTX importable en Google Slides..."
python3 "$SCRIPT_DIR/create_google_slides_sources.py" \
  --renders "$BUILD_DIR/rendered" \
  --outdir "$BUILD_DIR/pptx"

install -m 0644 \
  "$BUILD_DIR/latex/presentacion_imagen.pdf" \
  "$OUTPUT_DIR/TP2_Vicsek_entrega.pdf"
install -m 0644 \
  "$BUILD_DIR/pptx/TP2_Vicsek_videos.pptx" \
  "$OUTPUT_DIR/TP2_Vicsek_para_Google_Slides.pptx"

echo "[4/4] Limpiando archivos auxiliares..."
latexmk -C \
  "$SCRIPT_DIR/template_presentacion_tp2.tex" \
  "$SCRIPT_DIR/presentacion_imagen.tex" \
  >/dev/null 2>&1 || true

find "$SCRIPT_DIR" -maxdepth 1 -type f \
  \( -name '*.aux' -o -name '*.fdb_latexmk' -o -name '*.fls' \
     -o -name '*.log' -o -name '*.nav' -o -name '*.out' \
     -o -name '*.snm' -o -name '*.synctex.gz' -o -name '*.toc' \) \
  -delete

# Elimina las copias de una ejecución anterior, cuando los resultados se
# guardaban directamente junto a las fuentes.
rm -f -- \
  "$SCRIPT_DIR/TP2_Vicsek_entrega.pdf" \
  "$SCRIPT_DIR/TP2_Vicsek_para_Google_Slides.pptx"

echo
echo "Presentaciones generadas correctamente en:"
echo "  $OUTPUT_DIR/TP2_Vicsek_entrega.pdf"
echo "  $OUTPUT_DIR/TP2_Vicsek_para_Google_Slides.pptx"
