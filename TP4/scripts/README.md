# Scripts de F1, F2 y F3

Todos los comandos se ejecutan desde `TP4/`.

## F1 — ECM del Sistema 1

Generar el barrido de ECM:

```bash
./scripts/sim_gen/generate_f1_data.sh
```

El script compila y prueba el motor. Después ejecuta un barrido de calentamiento
y otro significativo dentro de la misma JVM. Comprueba que ambos tengan los
mismos valores de esquema, `dt`, pasos y ECM, y guarda el segundo en:

```text
outputs/sistema1/ecm/ecm-dt-sweep.txt
```

Generar la figura log-log:

```bash
python scripts/graph_gen/generate_f1.py
```

Salida:

```text
presentacion/figuras/F1-ecm-vs-dt.pdf
```

## F2 y F3 — energía del Sistema 2

### 1. Generar los datos

```bash
./scripts/sim_gen/generate_f2_f3_data.sh
```

El script compila y prueba el motor, y luego escribe una corrida por `dt` en
`outputs/2.1a/dt-*/observables.txt`. Usa la misma condición inicial en todas:
N=300, semilla 1, sin obstáculos, `tf=30 s` y `dt2=0.04 s`. Es reanudable:
omite cada archivo que ya tenga un pie `# fin estado=...`.

La corrida con `dt=1e-6` ejecuta unos 30 millones de pasos y puede tardar horas.
Para verificar el pipeline con dos corridas pequeñas:

```bash
./scripts/sim_gen/generate_f2_f3_data.sh \
  --tf 0.08 --dts 1e-3,1e-4 --output /tmp/tp4-2.1a-prueba
```

### 2. Generar las figuras

Con el entorno virtual activado y Matplotlib instalado:

```bash
python scripts/graph_gen/generate_f2.py
python scripts/graph_gen/generate_f3.py
```

Las salidas son:

- `presentacion/figuras/F2-energia-vs-t.pdf`: `(E(t)-E(0))/E(0)` para cada `dt`.
- `presentacion/figuras/F3-epsE-vs-dt.pdf`: `epsilon_E` contra `dt`, umbral `1e-3`
  y el mayor `dt` completo que lo cumple.
- `outputs/2.1a/epsilon_energy.csv`: valores numéricos usados por F3.

### 3. Validar el dt elegido

Después de generar F3, ejecutar el candidato en el caso más denso:

```bash
./scripts/sim_gen/validate_dt.sh
```

Por defecto valida `dt=1e-5` con N=714, `x0=r=0.0175`, `tf=10 s` y el
umbral `epsilon_E <= 1e-3`. Escribe:

```text
outputs/validacion-dt/dt-1e-5/observables.txt
outputs/validacion-dt/dt-1e-5/resultado-validacion.csv
```

El comando termina exitosamente y muestra `APROBADO` solo si la simulación se
completa y cumple el umbral. Si se rechaza, hay que probar el siguiente `dt`:

```bash
./scripts/sim_gen/validate_dt.sh --dt 1e-6
```

Para graficar la prueba corta sin reemplazar las figuras oficiales:

```bash
python scripts/graph_gen/generate_f2.py \
  --input /tmp/tp4-2.1a-prueba --output /tmp/F2-prueba.pdf
python scripts/graph_gen/generate_f3.py \
  --input /tmp/tp4-2.1a-prueba --output /tmp/F3-prueba.pdf
```
