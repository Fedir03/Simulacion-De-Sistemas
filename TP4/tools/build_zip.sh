#!/usr/bin/env bash
# Arma el ZIP de código del TP4 (entregable "c"): solo pom.xml + src/main/java del motor (D26).
# Afuera: bench/, src/main/java/.../bench/ (benchmark de 2.1.b), tests, scripts, analysis, docs, presentacion,
# outputs y README.
# Verifica: < 100 KB, que compila solo en una carpeta aislada y que el motor del ZIP reproduce la corrida
# (x0 = r, N = 100, semilla 1) de outputs/runtime_tp4_obs.
# Uso: bash TP4/tools/build_zip.sh    Salida: TP4/entrega/SdS_TP4_2026Q2G02CS_Codigo.zip
set -euo pipefail
GRUPO="${GRUPO:-02}"; COMISION="${COMISION:-S}"
ZIP_NAME="SdS_TP4_2026Q2G${GRUPO}C${COMISION}_Codigo.zip"
MAX_KB=100
TP4="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$TP4/entrega"
REF="$TP4/outputs/runtime_tp4_obs/runs/n100_s1/observables.txt"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
STAGE="$WORK/${ZIP_NAME%.zip}"

echo "== 1. Staging =="
mkdir -p "$STAGE/src/main"
cp -r "$TP4/src/main/java" "$STAGE/src/main/"
rm -rf "$STAGE/src/main/java/ar/edu/itba/sds/tp4/bench"   # benchmark de 2.1.b: no es el motor

# pom de entrega derivado del pom del repo: se sacan las dependencias (solo JUnit, de test) y el plugin de
# surefire, porque los tests no se entregan. Plugins, versiones, release y mainClass quedan iguales.
awk '
    /<dependencies>/ { skip = 1 }
    skip { if (/<\/dependencies>/) { skip = 0; drop_blank = 1 } next }
    /<plugin>/ { buf = $0 ORS; inplugin = 1; next }
    inplugin { buf = buf $0 ORS; if (/<\/plugin>/) { inplugin = 0; if (buf !~ /maven-surefire-plugin/) printf "%s", buf } next }
    drop_blank && /^[[:space:]]*$/ { drop_blank = 0; next }
    { drop_blank = 0; print }
' "$TP4/pom.xml" > "$STAGE/pom.xml"
if grep -qiE 'junit|surefire' "$STAGE/pom.xml"; then echo "ERROR: el pom de entrega todavía menciona JUnit o surefire" >&2; exit 1; fi
grep -q '<mainClass>ar.edu.itba.sds.tp4.Main</mainClass>' "$STAGE/pom.xml" || { echo "ERROR: falta mainClass" >&2; exit 1; }
echo "-- diff pom del repo -> pom de entrega:"
diff --strip-trailing-cr "$TP4/pom.xml" "$STAGE/pom.xml" || true   # el pom del repo tiene CRLF; el de entrega, LF

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
(cd "$BUILD" && mvn -q package && test -f target/tp4.jar)
echo "OK: compila solo desde el ZIP"

echo "== 4. Reproducción de (x0 = r, N = 100, semilla 1) de runtime_tp4_obs =="
if [[ ! -f "$REF" ]]; then echo "AVISO: no está $REF; se omite la comparación"; exit 0; fi
java -jar "$BUILD/target/tp4.jar" billiard --n 100 --seed 1 --x0 0.0175 --dt 1e-5 --dt2 0.04 --tf 30 \
    --dynamic no --out "$WORK/run" > /dev/null
NEW="$WORK/run/observables.txt"
if cmp -s "$REF" "$NEW"; then
    echo "cmp: idéntico byte a byte"
else
    echo "cmp: difiere -> $(cmp "$REF" "$NEW" || true)"
    # El pie trae runtime_s, que cambia en cada corrida: se compara sin ese campo
    strip() { sed -E 's/ runtime_s=[^ ]*$//' "$1"; }
    if cmp -s <(strip "$REF") <(strip "$NEW"); then
        echo "cmp sin runtime_s del pie: idéntico byte a byte"
    else
        echo "ERROR: difiere también sin runtime_s" >&2; diff <(strip "$REF") <(strip "$NEW") | head >&2; exit 1
    fi
fi
