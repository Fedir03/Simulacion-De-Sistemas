#!/usr/bin/env bash
set -euo pipefail

# Genera las corridas extra de 2.4 (D22, D33) con el dt elegido (D1: 1e-5, D3: dt2 = 0.04 s), tf = 30 s, sin --until.
#   complemento  2.4.a: x0 = r, N = 25 50 75 125 150, semillas 1-10 -> outputs/runtime_tp4_complemento/runs/nN_sK
#   barrido      2.4.b: x0 de D13 salvo r, N = 100..600 y N máx (713; 714 en R-r), semillas 1-3
#                -> outputs/runtime_tp4_barrido/runs/x0-X/nN_sK  (x0 = r se toma de runtime_tp4_obs)
# NO mide tiempos de ejecución: corre en paralelo y en otra máquina que la del benchmark (D12).
# Reanudable por (x0, N, semilla): omite cada corrida cuyo observables.txt ya tenga el pie "# fin estado=".
# Cada corrida terminada agrega una línea a progress.csv.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"
TP4_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
JAR="$TP4_DIR/target/tp4.jar"

DT=1e-5
DT2=0.04
TF=30
JOBS=16
HEAP=128m
STUDY=""
DRY_RUN=false

# D33
N_COMP="150 125 75 50 25"
SEEDS_COMP=10
# D22 (x0 = 0.0175 = r sale de runtime_tp4_obs, semillas 1-3)
X0_BARR="0.06 0.12 0.18 0.24 0.30 0.36 0.43 0.4925"
N_BARR="100 200 300 400 500 600"
SEEDS_BARR=3

usage() {
    cat <<'EOF'
Uso: generate_2_4_data.sh --study complemento|barrido [opciones]

  complemento  x0=r, N = 25 50 75 125 150, semillas 1-10 (D33)
  barrido      x0 = 0.06 ... 0.4925 (D13 sin r), N = 100 ... 600 y N máx
               (713; 714 en x0 = R-r), semillas 1-3 (D22)

Opciones:
  --jobs J      corridas en paralelo (predeterminado: 16)
  --heap H      -Xmx de cada JVM (predeterminado: 128m)
  --dry-run     solo listar las corridas
  -h, --help    mostrar esta ayuda

No compila: usa target/tp4.jar tal como está (su sha256 queda en meta.json).
Salidas: outputs/runtime_tp4_complemento/ y outputs/runtime_tp4_barrido/
EOF
}

need_value() { (($# >= 2)) || { echo "Error: falta el valor de $1" >&2; exit 2; }; }
while (($#)); do
    case "$1" in
        --study) need_value "$@"; STUDY="$2"; shift 2 ;;
        --jobs) need_value "$@"; JOBS="$2"; shift 2 ;;
        --heap) need_value "$@"; HEAP="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Error: opción desconocida: $1" >&2; usage >&2; exit 2 ;;
    esac
done

case "$STUDY" in
    complemento) OUT="$TP4_DIR/outputs/runtime_tp4_complemento" ;;
    barrido) OUT="$TP4_DIR/outputs/runtime_tp4_barrido" ;;
    *) echo "Error: --study debe ser complemento o barrido" >&2; usage >&2; exit 2 ;;
esac
[[ -f "$JAR" ]] || { echo "Error: no existe $JAR. Ejecutá 'mvn package'." >&2; exit 1; }

# Una línea por corrida: x0|N|semilla|carpeta, N grande primero para que el paralelo no termine esperando a una sola
jobs_file="$(mktemp)"
trap 'rm -f "$jobs_file"' EXIT
if [[ "$STUDY" == complemento ]]; then
    for n in $N_COMP; do
        for seed in $(seq 1 "$SEEDS_COMP"); do
            echo "0.0175|$n|$seed|$OUT/runs/n${n}_s${seed}" >> "$jobs_file"
        done
    done
else
    for x0 in $X0_BARR; do
        nmax=713; [[ "$x0" == 0.4925 ]] && nmax=714
        for n in $N_BARR $nmax; do
            for seed in $(seq 1 "$SEEDS_BARR"); do
                echo "$x0|$n|$seed|$OUT/runs/x0-$x0/n${n}_s${seed}" >> "$jobs_file"
            done
        done
    done
fi
sort -t'|' -k2,2nr -s -o "$jobs_file" "$jobs_file"

total=$(wc -l < "$jobs_file")
echo "Corridas ($STUDY): $total (dt=$DT, dt2=$DT2, tf=$TF s, $JOBS en paralelo, -Xmx$HEAP)"
if [[ "$DRY_RUN" == true ]]; then cat "$jobs_file"; exit 0; fi

mkdir -p "$OUT/runs"
cp "$jobs_file" "$OUT/plan.txt"
[[ -f "$OUT/progress.csv" ]] || echo "x0,n,seed,status,wall_s,steps,nu_final,engine_runtime_s,finished_at_local" > "$OUT/progress.csv"

# meta.json: se reescribe en cada lanzamiento (el jar y la máquina tienen que ser los mismos al reanudar)
JVM_FLAGS="-Xmx$HEAP -XX:+UseSerialGC -XX:CICompilerCount=2"
STUDY="$STUDY" OUT="$OUT" JAR="$JAR" TP4_DIR="$TP4_DIR" JVM_FLAGS="$JVM_FLAGS" JOBS="$JOBS" TOTAL="$total" \
JAR_SHA="$(sha256sum "$JAR" | cut -d' ' -f1)" \
GIT_HEAD="$(git -C "$TP4_DIR" rev-parse HEAD)" \
GIT_DIRTY="$(git -C "$TP4_DIR" status --porcelain -- src/main pom.xml | wc -l)" \
ENGINE_COMMIT="$(git -C "$TP4_DIR" log -1 --format=%H -- src/main pom.xml)" \
JAVA_VERSION="$(java -version 2>&1)" \
python - <<'EOF'
import json, os, platform, datetime
e = os.environ
meta = {
    "study": e["STUDY"],
    "purpose": "Nu(t) para 2.4 (D22/D33); sin medición de tiempos",
    "started_at_local": datetime.datetime.now().astimezone().isoformat(),
    "case": {"dt": 1e-5, "dt2": 0.04, "tf": 30.0, "until": "tf", "R": 0.51, "r": 0.0175},
    "runs_planned": int(e["TOTAL"]),
    "jobs": int(e["JOBS"]),
    "jvm_flags": e["JVM_FLAGS"],
    "jar": e["JAR"],
    "jar_sha256": e["JAR_SHA"],
    "git_head": e["GIT_HEAD"],
    "engine_source_commit": e["ENGINE_COMMIT"],
    "engine_source_dirty": int(e["GIT_DIRTY"]) > 0,
    "java_version_output": e["JAVA_VERSION"],
    "machine": {"hostname": platform.node(), "processor": platform.processor()},
    "notes": [
        "Corridas con Java 25.0.4; runtime_tp4_obs se corrió con Oracle Java 21.0.10 (otra máquina, ASUS_Fede).",
        "Determinismo verificado el 22/10: (x0=r, N=100, semilla 1) con este jar y estas banderas da un observables.txt idéntico al de runtime_tp4_obs, salvo runtime_s.",
        "runtime_s del pie y wall_s de progress.csv no valen como tiempos de ejecución (paralelo, otra máquina).",
    ],
}
if e["STUDY"] == "barrido":
    meta["reused"] = {"x0": 0.0175, "source": "outputs/runtime_tp4_obs/runs/n{N}_s{1,2,3}", "ns": [100, 200, 300, 400, 500, 600, 714]}
with open(os.path.join(e["OUT"], "meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
EOF

run_one() {
    local x0 n seed dir
    IFS='|' read -r x0 n seed dir <<< "$1"
    if [[ -f "$dir/observables.txt" ]] && grep -q '^# fin estado=' "$dir/observables.txt"; then
        echo "[omitida] $dir"; return 0
    fi
    mkdir -p "$dir"
    local start end foot
    start=$(date +%s.%N)
    # shellcheck disable=SC2086
    if java $JVM_FLAGS -jar "$JAR" billiard --n "$n" --seed "$seed" --x0 "$x0" --dt "$DT" --dt2 "$DT2" --tf "$TF" \
            --out "$dir" > /dev/null 2> "$dir.err"; then
        end=$(date +%s.%N)
        rm -f "$dir.err"
        foot=$(tail -1 "$dir/observables.txt")
        local status steps nu rt
        status=$(sed -n 's/.*estado=\([^ ]*\).*/\1/p' <<< "$foot")
        steps=$(sed -n 's/.*pasos=\([^ ]*\).*/\1/p' <<< "$foot")
        nu=$(sed -n 's/.*Nu=\([^ ]*\).*/\1/p' <<< "$foot")
        rt=$(sed -n 's/.*runtime_s=\([^ ]*\).*/\1/p' <<< "$foot")
        echo "$x0,$n,$seed,$status,$(awk -v a="$start" -v b="$end" 'BEGIN{printf "%.3f", b-a}'),$steps,$nu,$rt,$(date +%Y-%m-%dT%H:%M:%S%z)" >> "$OUT/progress.csv"
        echo "[ok] $dir"
    else
        echo "$x0,$n,$seed,error,,,,,$(date +%Y-%m-%dT%H:%M:%S%z)" >> "$OUT/progress.csv"
        echo "[ERROR] $dir (ver $dir.err)"; return 1
    fi
}
export -f run_one
export JAR DT DT2 TF JVM_FLAGS OUT

tr '\n' '\0' < "$jobs_file" | xargs -0 -P "$JOBS" -I{} bash -c 'run_one "$1"' _ {}
echo "Listo. Salidas en $OUT (progreso en $OUT/progress.csv)"
