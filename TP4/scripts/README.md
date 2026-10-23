# Scripts de F1, F2 y F3

Todos los comandos se ejecutan desde `TP4/`.

## F1 — ECM del Sistema 1

Se conservan los 13 pasos entre `1e-6` y `5e-3` s y se agrega `1e-2` s
como control adicional, fuera del rango estricto pedido (`dt < 1e-2`).
Son 56 resultados: 14 pasos por cada uno de los cuatro métodos.

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

- `presentacion/figuras/F2-energia-vs-t.pdf`: energía total en un único
  gráfico con todas las curvas. Escala vertical no lineal
  `asinh((E-E_ref)/1e-8 J)`, con `E_ref=N*m*v0²/2`; el eje muestra
  valores absolutos de energía en joules. La transformación es monótona
  y permite distinguir variaciones pequeñas sin ocultar la divergencia.
  Se exporta también a PNG. `dt=1e-2` es un control adicional fuera del rango pedido.
- `presentacion/figuras/F3-epsE-vs-dt.pdf`: `epsilon_E` contra `dt`, umbral `1e-3`
  y el mayor `dt < 1e-2` completo que lo cumple. La tolerancia del 0,1 % es
  propuesta por nosotros: no está fijada por el enunciado. El observable es
  `max_i |E(t_i)-E(0)|/E(0)`, sobre un intervalo común de 30 s para corridas completas.
- `outputs/2.1a/epsilon_energy.csv`: valores numéricos usados por F3.

Para repetir todas las simulaciones, incluso las terminadas, usar
`./scripts/sim_gen/generate_f2_f3_data.sh --force`. Después ejecutar ambos
generadores (F2 y F3). `--output /tmp/F2-prueba.pdf` también genera
`/tmp/F2-prueba.png`.

El lector rechaza archivos sin pie de finalización, energías incompatibles
con `E_tot = E_cin + E_el`, muestras faltantes y parámetros físicos distintos.
Los errores máximos se calculan sobre las salidas cada `dt2`, no sobre todos
los pasos internos. `dt=1e-2` es un control adicional fuera del rango estricto
`dt < 1e-2` del enunciado; si diverge antes de la segunda muestra, se informa
sin inventar una curva ni asignarle error cero en F3.

Tests del lector: `python -m unittest discover -s scripts/graph_gen -p 'test_*.py'`.

### Revisión del motor para F2 (22/10/2026)

Se revisaron `BilliardSimulator`, `ContactForces`, `BilliardConfig`,
`GridPlacement`, `CellIndexMethod` y `BilliardFiles` contra el enunciado
y las fórmulas de Verlet documentadas en `docs/plan/referencia/FORMULAS-VERIFICADAS.md`.
No se modificaron las ecuaciones del motor.

- Se sortean 300 sitios de una red hexagonal sin solapamientos, separados
  `2r + 0.1 mm`, con semilla 1; las direcciones son uniformes en `[0, 2π)`
  y el módulo inicial es `1 m/s`. Es una colocación aleatoria sobre grilla,
  no una distribución espacial continua uniforme.
- Se usan `R=0.51 m`, `r=0.0175 m`, `m=0.025 kg` y `k=10000 N/m`.
  Sin obstáculos ni disipación, la energía inicial esperada es `3.75 J`.
- Verlet calcula `r(t+dt)=2r(t)-r(t-dt)+F(t)dt²/m`, con inicialización
  `r(-dt)=r(0)-v(0)dt+F(0)dt²/(2m)`. La velocidad central y la energía
  elástica corresponden al mismo instante `t`.
- Los contactos aportan `k ξ²/2` una sola vez por par. Las fuerzas del par
  son opuestas; la pared aporta fuerza radial hacia dentro con
  `ξ=|r_i|+r-R`, consistente con su energía potencial.
- Se guarda por contador entero cada `dt2/dt` pasos, incluyendo cero y
  los 30 segundos finales: 751 muestras por corrida completa. El corte
  por divergencia ocurre si un centro sale del dominio o deja de ser finito.

La compilación con JDK 21 pasó los 48 tests Java, incluyendo choques,
rebotes, conservación, reproducibilidad y comparación CIM contra fuerza
bruta. El lector pasó 4 tests Python con casos truncados e inconsistentes.
Una repetición independiente de `dt=1e-3` reprodujo exactamente todas las
muestras y la divergencia a `t=4.811 s` de la nueva compilación.
Los archivos anteriores no son idénticos bit a bit a esta corrida: se
regeneran todos los datos del barrido y ambas figuras F2/F3 conjuntamente.
Estos chequeos respaldan el cálculo para este estudio; no sustituyen la
auditoría cruzada del grupo ni la validación posterior con N=714.

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

## F4 — tiempo de ejecución en función de N

La corrida completa genera o reanuda primero TP3 y después TP4, con 10 semillas
por N, una JVM calentada por motor y heap fijo de 2 GiB:

```bash
./scripts/sim_gen/generate_f4_data.sh
```

Escribe `outputs/runtime_tp3/runs.csv` y `outputs/runtime_tp4/runs.csv`. Puede
durar horas y dividirse en tandas reanudables:

```bash
./scripts/sim_gen/generate_f4_data.sh --batch 5
```

Si TP3 ya está completo, puede omitirse con `--skip-tp3`. Con ambas mediciones
completas, generar la figura mediante:

```bash
python scripts/graph_gen/generate_f4.py
```

F4 usa la mediana y barras p25–p75. Compara TP3 contra TP4 y muestra que TP4
se midió con `dt=1e-5 s`. Su salida es
`presentacion/figuras/F4-tiempo-vs-n.pdf`.
