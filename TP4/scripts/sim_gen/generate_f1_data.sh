#!/usr/bin/env bash
set -euo pipefail

# Genera el barrido de ECM del Sistema 1 usado por F1. Ejecuta un barrido de
# calentamiento y otro significativo dentro de la misma JVM, tal como quedó
# documentado en docs/generacion-grafico-ecm-sistema1.md.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TP4_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
OUTPUT="$TP4_DIR/outputs/sistema1/ecm/ecm-dt-sweep.txt"
BUILD=true

usage() {
    cat <<'EOF'
Uso: generate_f1_data.sh [opciones]

Opciones:
  --output ARCHIVO  salida significativa
                    (predeterminado: TP4/outputs/sistema1/ecm/ecm-dt-sweep.txt)
  --skip-build      usar target/classes sin ejecutar Maven
  -h, --help        mostrar esta ayuda

El estudio usa los parámetros acordados:
  m=70 kg, k=10000 N/m, gamma=100 kg/s, A=1 m, tf=5 s,
  13 dt logarítmicos entre 1e-6 s y 5e-3 s, más 1e-2 s como
  control adicional fuera del rango pedido, y los cuatro esquemas.
EOF
}

while (($#)); do
    case "$1" in
        --output)
            (($# >= 2)) || { echo "Error: falta el valor de --output" >&2; exit 2; }
            OUTPUT="$2"
            shift 2
            ;;
        --skip-build) BUILD=false; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Error: opción desconocida: $1" >&2; usage >&2; exit 2 ;;
    esac
done

command -v java >/dev/null 2>&1 || { echo "Error: no se encontró java." >&2; exit 1; }
command -v diff >/dev/null 2>&1 || { echo "Error: no se encontró diff." >&2; exit 1; }

if [[ "$BUILD" == true ]]; then
    command -v mvn >/dev/null 2>&1 || {
        echo "Error: no se encontró mvn. Instalá Maven o usá --skip-build si target/classes ya existe." >&2
        exit 1
    }
    echo "Compilando TP4 y ejecutando tests..."
    (cd "$TP4_DIR" && mvn -q package)
fi

[[ -f "$TP4_DIR/target/classes/ar/edu/itba/sds/tp4/Main.class" ]] || {
    echo "Error: faltan las clases compiladas. Ejecutá 'mvn package'." >&2
    exit 1
}

TEMP_DIR="$(mktemp -d -t tp4-f1-XXXXXX)"
trap 'rm -rf -- "$TEMP_DIR"' EXIT
WARMUP="$TEMP_DIR/ecm-warmup-discard.txt"
JSHELL_SCRIPT="$TEMP_DIR/f1-study.jsh"
mkdir -p "$(dirname -- "$OUTPUT")"

export TP4_F1_WARMUP="$WARMUP"
export TP4_F1_OUTPUT="$OUTPUT"
export TP4_F1_CLASSES="$TP4_DIR/target/classes"

cat >"$JSHELL_SCRIPT" <<'EOF'
import ar.edu.itba.sds.tp4.Main;
import ar.edu.itba.sds.tp4.engine.oscillator.OscillatorStudy;
import java.util.stream.DoubleStream;
import java.util.stream.Collectors;
String dts = DoubleStream.concat(DoubleStream.of(1e-2), java.util.Arrays.stream(OscillatorStudy.logSpaced(1e-6, 5e-3, 13))).mapToObj(Double::toString).collect(Collectors.joining(","));

String[] common = new String[]{
    "oscillator-ecm",
    "--mass", "70",
    "--k", "1e4",
    "--gamma", "100",
    "--amplitude", "1",
    "--tf", "5",
    "--dts", dts,
    "--verlet-velocity", "backward",
    "--vv-velocity", "euler",
    "--acceleration-update", "predicted",
    "--out", ""
};

common[common.length - 1] = System.getenv("TP4_F1_WARMUP");
Main.execute(common);
common[common.length - 1] = System.getenv("TP4_F1_OUTPUT");
Main.execute(common);
/exit
EOF

echo "Ejecutando warmup y barrido significativo en la misma JVM..."
java \
    --class-path "$TP4_F1_CLASSES" \
    -Djava.util.prefs.userRoot="$TEMP_DIR/java-prefs" \
    --module jdk.jshell/jdk.internal.jshell.tool.JShellToolProvider \
    --execution local \
    --class-path "$TP4_F1_CLASSES" \
    "$JSHELL_SCRIPT"

[[ -s "$WARMUP" && -s "$OUTPUT" ]] || {
    echo "Error: JShell no produjo ambos archivos de ECM." >&2
    exit 1
}

# El warmup puede cambiar runtime_s, pero el método, dt, pasos y ECM deben ser
# idénticos. También se comprueba que existan 4 métodos × 14 dt = 56 filas.
awk '!/^#/ && $1 != "scheme" {print $1, $2, $3, $4}' "$WARMUP" >"$TEMP_DIR/warmup-values.txt"
awk '!/^#/ && $1 != "scheme" {print $1, $2, $3, $4}' "$OUTPUT" >"$TEMP_DIR/output-values.txt"
ROWS="$(wc -l <"$TEMP_DIR/output-values.txt")"
[[ "$ROWS" -eq 56 ]] || { echo "Error: se esperaban 56 resultados y se obtuvieron $ROWS." >&2; exit 1; }
diff -u "$TEMP_DIR/warmup-values.txt" "$TEMP_DIR/output-values.txt" >/dev/null || {
    echo "Error: el warmup y la corrida significativa difieren en esquema, dt, pasos o ECM." >&2
    exit 1
}

echo "Datos de F1 generados y validados: $OUTPUT"
echo "Filas: 56 (4 esquemas × 14 valores de dt)."
