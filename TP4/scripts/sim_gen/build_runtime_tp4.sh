#!/usr/bin/env bash
set -euo pipefail

# Compila el motor (mvn package, con tests) y el benchmark de 2.1.b (TP4/bench) y registra el estado de git del build en
# target/bench-classes/build-info.properties (RuntimeBenchmark lo copia a meta.json). No mide: eso lo hace runtime_tp4.sh,
# que no compila, para que la compilación no caiga dentro de la medición.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TP4_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
JAR="$TP4_DIR/target/tp4.jar"
CLASSES="$TP4_DIR/target/bench-classes"
INFO="$CLASSES/build-info.properties"

for tool in mvn javac git; do
    command -v "$tool" >/dev/null 2>&1 || { echo "Error: no se encontró $tool." >&2; exit 1; }
done
to_path() { printf '%s' "$1"; }
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) to_path() { cygpath -m "$1"; } ;; esac

echo "Compilando TP4 y ejecutando tests..."
(cd "$TP4_DIR" && mvn -q -B package)
[[ -f "$JAR" ]] || { echo "Error: mvn package no generó $JAR." >&2; exit 1; }

rm -rf "$CLASSES"
mkdir -p "$CLASSES"
mapfile -t SOURCES < <(find "$TP4_DIR/bench/src" -name '*.java' | sort)
((${#SOURCES[@]})) || { echo "Error: no hay fuentes en $TP4_DIR/bench/src." >&2; exit 1; }
WIN_SOURCES=()
for s in "${SOURCES[@]}"; do WIN_SOURCES+=("$(to_path "$s")"); done
echo "Compilando el benchmark (${#SOURCES[@]} archivos, --release 21)..."
javac --release 21 -encoding UTF-8 -cp "$(to_path "$JAR")" -d "$(to_path "$CLASSES")" "${WIN_SOURCES[@]}"

STATUS="$(git -C "$TP4_DIR" status --porcelain | tr -d '\r')"
DIRTY=false
[[ -z "$STATUS" ]] || DIRTY=true
{
    echo "# Escrito por build_runtime_tp4.sh; RuntimeBenchmark lo copia a meta.json"
    echo "git_head=$(git -C "$TP4_DIR" rev-parse HEAD)"
    echo "git_branch=$(git -C "$TP4_DIR" rev-parse --abbrev-ref HEAD)"
    echo "git_dirty=$DIRTY"
    echo "git_status=$(printf '%s' "$STATUS" | tr '\n' ';')"
    echo "built_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "built_at_local=$(date +%Y-%m-%dT%H:%M:%S%z)"
    echo "javac=$(javac -version 2>&1 | tr -d '\r')"
    echo "maven=$(mvn -B -v 2>&1 | head -n 1 | tr -d '\r')"
    echo "jar=$(to_path "$JAR")"
    echo "jar_sha256=$(sha256sum "$JAR" | cut -d' ' -f1)"
} > "$INFO"

echo "Build listo:"
echo "  $JAR"
find "$CLASSES" -name '*.class' | sed 's/^/  /'
sed 's/^/  /' "$INFO"
if [[ "$DIRTY" == true ]]; then
    echo "AVISO: hay cambios sin commitear o archivos sin seguir; meta.json lo va a registrar (git_dirty=true)." >&2
fi
