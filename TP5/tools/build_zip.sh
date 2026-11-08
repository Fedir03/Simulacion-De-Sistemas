#!/usr/bin/env bash
# Arma el ZIP de código del TP5 (entregable "c"): solo pom.xml + src/main/java del motor.
# Afuera: tests, scripts, docs, presentacion, data, outputs y README.
# Verifica: < 100 KB, que compila solo en una carpeta aislada y que el motor del ZIP reproduce la corrida
# del evento 3 de outputs/baseline. Los datos no van al ZIP: la corrida de control los lee del repo.
# Uso: bash TP5/tools/build_zip.sh    Salida: TP5/entrega/SdS_TP5_2026Q2G02CS_Codigo.zip
set -euo pipefail
GRUPO="${GRUPO:-02}"; COMISION="${COMISION:-S}"
ZIP_NAME="SdS_TP5_2026Q2G${GRUPO}C${COMISION}_Codigo.zip"
MAX_KB=100
TP5="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$TP5/entrega"
REF="$TP5/outputs/baseline/evento_03.txt"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
STAGE="$WORK/${ZIP_NAME%.zip}"

echo "== 1. Staging =="
mkdir -p "$STAGE/src/main"
cp -r "$TP5/src/main/java" "$STAGE/src/main/"
rm -rf "$STAGE/src/main/java/ar/edu/itba/sds/tp5/diagnostics"   # traza de análisis: no es el motor

# pom de entrega derivado del pom del repo: se sacan las dependencias (solo JUnit, de test) y el plugin de
# surefire, porque los tests no se entregan. Plugins, versiones, release y mainClass quedan iguales.
awk '
    /<dependencies>/ { skip = 1 }
    skip { if (/<\/dependencies>/) { skip = 0; drop_blank = 1 } next }
    /<plugin>/ { buf = $0 ORS; inplugin = 1; next }
    inplugin { buf = buf $0 ORS; if (/<\/plugin>/) { inplugin = 0; if (buf !~ /maven-surefire-plugin/) printf "%s", buf } next }
    drop_blank && /^[[:space:]]*$/ { drop_blank = 0; next }
    { drop_blank = 0; print }
' "$TP5/pom.xml" > "$STAGE/pom.xml"
if grep -qiE 'junit|surefire' "$STAGE/pom.xml"; then echo "ERROR: el pom de entrega todavía menciona JUnit o surefire" >&2; exit 1; fi
grep -q '<mainClass>ar.edu.itba.sds.tp5.Main</mainClass>' "$STAGE/pom.xml" || { echo "ERROR: falta mainClass" >&2; exit 1; }
echo "-- diff pom del repo -> pom de entrega:"
diff --strip-trailing-cr "$TP5/pom.xml" "$STAGE/pom.xml" || true   # el pom del repo puede tener CRLF; el de entrega, LF

echo "== 2. ZIP =="
mkdir -p "$DEST"; rm -f "$DEST/$ZIP_NAME"
(cd "$WORK" && zip -qr "$DEST/$ZIP_NAME" "$(basename "$STAGE")")
KB=$(( ($(wc -c < "$DEST/$ZIP_NAME") + 1023) / 1024 ))
echo "$ZIP_NAME: ${KB} KB"
unzip -l "$DEST/$ZIP_NAME"
(( KB < MAX_KB )) || { echo "ERROR: el ZIP pesa ${KB} KB (límite ${MAX_KB} KB)" >&2; exit 1; }

echo "== 3. Compilación aislada =="
mkdir -p "$WORK/test"
(cd "$WORK/test" && unzip -q "$DEST/$ZIP_NAME")
BUILD="$WORK/test/$(basename "$STAGE")"
(cd "$BUILD" && mvn -q package && test -f target/tp5.jar)
echo "OK: compila solo desde el ZIP"

echo "== 4. Reproducción del evento 3 de outputs/baseline =="
if [[ ! -f "$REF" ]]; then echo "ERROR: no está $REF; correr antes scripts/sim_gen/generate_baseline.sh" >&2; exit 1; fi
java -jar "$BUILD/target/tp5.jar" run --event 3 --data "$TP5/data" --out "$WORK/run" > /dev/null
if cmp -s "$REF" "$WORK/run/evento_03.txt"; then
    echo "cmp: idéntico byte a byte"
else
    echo "ERROR: difiere -> $(cmp "$REF" "$WORK/run/evento_03.txt" || true)" >&2; exit 1
fi
