# TP4 — Dinámica molecular regida por el paso temporal

## Requisitos
- JDK 21 o más nuevo (`java -version`).
- Maven 3.6.3 o más nuevo (`mvn -version`).
- Para los scripts: Bash (Linux, macOS o Git Bash en Windows) y Python 3 con numpy y matplotlib.

## Compilar
```bash
mvn package
```
Compila y genera `target/tp4.jar`. Los tests no van en el ZIP; en el repositorio, `mvn package` también los corre.

## Ejemplo
```bash
java -jar target/tp4.jar billiard --n 100 --x0 0.0175 --dt 1e-5 --dt2 0.04 --tf 1 --out salida
```
Escribe `salida/observables.txt` (t, E_tot, E_cin, E_el y Nu cada dt2). `java -jar target/tp4.jar --help` lista todos los comandos y opciones.

## Benchmark de tiempos de ejecución (2.1.b)
El código está en `bench/` y se compila aparte del motor.

Dentro del repositorio:
```bash
./scripts/sim_gen/build_runtime_tp4.sh
./scripts/sim_gen/runtime_tp4.sh --allow-other-machine --out outputs/runtime_tp4_prueba \
    --ns 100,200 --rounds 1 --tf 0.48 --dt 1e-4 --dt2 0.04 --warmup 100:0.08
```
- `build_runtime_tp4.sh` corre `mvn package` y compila el benchmark. Usa git para registrar en `target/bench-classes/build-info.properties` el commit compilado y si había cambios sin commitear, por eso solo funciona dentro de un repositorio git.
- `runtime_tp4.sh` no compila. Compara la máquina (hostname, CPU y versión de Java) con `bench/maquina_tp3.properties` y aborta si no coincide. En otra PC, o fuera del repositorio, hay que agregar `--allow-other-machine`. Los tiempos medidos así no valen como medición de la máquina de TP3.

Fuera del repositorio (por ejemplo, desde este ZIP), después de `mvn package`:
```bash
mkdir -p target/bench-classes
javac --release 21 -encoding UTF-8 -cp target/tp4.jar -d target/bench-classes $(find bench/src -name '*.java')
java -Xms2g -Xmx2g -cp "target/tp4.jar:target/bench-classes" ar.edu.itba.sds.tp4.bench.Tp4Case \
    --out runtime_prueba --ns 100,200 --rounds 1 --tf 0.48 --dt 1e-4 --dt2 0.04 --warmup 100:0.08
```
En Windows, el separador de `-cp` es `;` en lugar de `:`.

## Scripts
- `scripts/animation/`: módulo independiente para exportar las trayectorias del billar a MP4.
- `scripts/sim_gen/`: generan los datos de cada estudio a partir del motor (`generate_f1_data.sh`, `generate_f2_f3_data.sh`, `validate_dt.sh`, `generate_studies_data.sh`, `generate_f4_data.sh`, `runtime_tp4.sh`). `control_tp3.sh` necesita el TP3 del repositorio y no corre desde el ZIP.
- `scripts/graph_gen/`: generan las figuras a partir de los outputs.
- `analysis/`: análisis de los tiempos de ejecución de TP3 (`runtime_tp3.py`, `runtime_tp3_ab.py`).

## Animaciones del billar

Requieren FFmpeg en PATH y las dependencias de `requirements.txt` (`python3 -m pip install -r requirements.txt`). Desde TP4:

```bash
bash scripts/sim_gen/generate_animations.sh
```

Compila y verifica el motor, ejecuta dos simulaciones completas de 100 s con N=100, semilla 1, Δt=1e-5 s y salida cada 0.04 s, y exporta los videos. Un caso no tiene obstáculos; el otro tiene sus centros en (±0.25 m, 0). Las salidas quedan en `generated/animaciones/{sin_obstaculos,con_obstaculos}/`: `observables.txt`, `dynamic.txt` y `animacion.mp4`. El script usa el Python de `.venv` del repositorio si existe; se puede elegir otro con la variable `PYTHON`.

Para animar una trayectoria guardada, sin volver a simular:

```bash
python3 scripts/animation/animate.py --input ruta/dynamic.txt --out ruta/animacion.mp4
```

La animación lee los parámetros del archivo, mantiene los radios a escala y muestra el tiempo simulado y el contador `Usadas: Nu/N` (por ejemplo, `Usadas: 55/100`), sin título ni ejes cartesianos. Las usadas son rojas y las no usadas azules. N y Δt se indican al costado del fotograma en la presentación. Sin obstáculos, todas permanecen azules. La velocidad de reproducción es real: con dt2=0.04 s se exportan 25 cuadros/s. Los 2501 estados, incluido el final, producen un MP4 de 100.04 s. No se interpolan estados ni se ejecuta el motor durante el render.

Pruebas del lector:

```bash
python3 -m unittest discover -s scripts/animation -p 'test_*.py'
```
