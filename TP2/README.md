# TP2 — Modelo de Vicsek

Simulación de bandadas (flocking) con el modelo de Vicsek: partículas que se
mueven a velocidad constante alineando su dirección con la de sus vecinos,
más ruido. Dos variantes: **estándar** (promedio vectorial de los vecinos) y
**votante** (copia el ángulo de un vecino al azar). Reusa el Cell Index
Method (CIM) de TP1 para la búsqueda de vecinos.

## Compilar

Desde la **raíz del repo** [Simulacion-De-Sistemas]:

```
mvn clean package
```
_ya corre los tests como parte del ciclo de vida normal._

Esto genera `TP2/target/tp2.jar`, un jar ejecutable (shaded) que ya incluye
las clases de TP1 — no hace falta armar el classpath a mano.

## Correr una simulación

```
java -jar TP2/target/tp2.jar simulate --model=voter --n=400 --eta=0.5 --steps=1000 --seedIC=1 --seedLoop=1 --out=corrida.txt
```

| Flag | Obligatorio | Default | Descripción |
|---|---|---|---|
| `--model` | Sí | — | `voter` o `standard` (ver estado actual abajo) |
| `--n` | Sí | — | Cantidad de partículas |
| `--eta` | Sí | — | Magnitud del ruido angular |
| `--steps` | Sí | — | Cantidad de pasos de tiempo a simular (además del `t=0` inicial) |
| `--seedIC` | Sí | — | Semilla para las posiciones/ángulos iniciales (entero o `auto`) |
| `--seedLoop` | Sí | — | Semilla para el ruido angular de cada paso (entero o `auto`) |
| `--out` | Sí | — | Path del archivo de salida |
| `--l` | No | `10.0` | Lado de la caja cuadrada `[0,L] x [0,L]` |
| `--rc` | No | `1.0` | Radio de interacción |
| `--dt` | No | `1.0` | Paso temporal |
| `--v0` | No | `0.03` | Velocidad (constante para todas las partículas) |
| `--periodic` | No | `true` | Condiciones de contorno periódicas (`true`/`false`) |
| `--theta0` | No | `random` | Ángulo inicial: `random` (uno al azar por partícula) o un ángulo en radianes común a todas |

## Condición inicial: `--theta0`

Con el mismo `--seedIC`, las **posiciones** iniciales son idénticas se use
`--theta0=random` o `--theta0=<ángulo>`: el ángulo al azar se saca del generador
igual aunque después se descarte. Eso permite comparar dos corridas que arrancan
del mismo estado de partida y difieren únicamente en los ángulos iniciales
(ver "Parámetro de orden y gráficos").

## Formato del archivo de salida

```
model=voter N=5 L=10.0 rc=1.0 dt=1.0 v0=0.03 eta=0.5 periodic=true seedIC=1 seedLoop=1 theta0=random
t=0
1 7.308781907032909 4.100808114922017 1.3051324661903892
2 3.3271947079107615 9.677559094571917 0.03845680581211974
3 9.637047970232077 9.398653887819098 5.951431685227902
```

**Cabecera** (primera línea, `clave=valor` separados por espacio):

| Campo | Significado |
|---|---|
| `model` | `voter` o `standard` |
| `N` | Cantidad de partículas |
| `L` | Lado de la caja |
| `rc` | Radio de interacción |
| `dt` | Paso temporal |
| `v0` | Velocidad |
| `eta` | Magnitud del ruido angular |
| `periodic` | Condiciones de contorno periódicas |
| `seedIC` | Semilla de condiciones iniciales |
| `seedLoop` | Semilla del ruido angular por paso |
| `theta0` | `random` o el ángulo inicial común (las corridas viejas no traen este campo: se asumen `random`) |

**Bloques de tiempo**: cada uno empieza con una línea `t=<n>`, seguida de
una línea por partícula: `id x y theta`, en precisión completa de `double`.

## Nota para el Paquete B

El archivo **no incluye el grafo de vecinos** — hay que recalcularlo con
`NeighborLookup` usando `L`/`rc`/`periodic` de la cabecera, porque
guardarlo en cada bloque de tiempo infla el tamaño del archivo sin
necesidad (se puede recalcular en O(N) con el CIM). Detalle completo en la
página de Notion "Material para Informe — TP2".

## Parámetro de orden y gráficos

El parámetro de orden (polarización) es

```
v_a = (1 / (N·v0)) · |Σ_i v_i| = (1 / N) · |Σ_i (cos θ_i, sin θ_i)|
```

Como todas las partículas tienen el mismo módulo de velocidad `v0`, ese factor se
cancela y `v_a` queda entre 0 (desordenado) y 1 (todas alineadas).

Los scripts viven en `TP2/scripts/` y no necesitan más dependencias que Matplotlib:

| Script | Qué hace |
|---|---|
| `simulation_io.py` | Parsea el archivo del motor (entero o en streaming). No se corre solo. |
| `order_parameter.py` | Calcula `v_a(t)` de una corrida y la guarda como CSV. |
| `sweep.py` | Corre varias simulaciones y deja las series de `v_a` listas. |
| `plot_va.py` | Grafica `v_a` vs. tiempo, superponiendo una curva por corrida. |
| `plot_va_vs_eta.py` | Grafica el `v_a` estacionario vs. `η` con barras de error. |

Los gráficos, mapeados a los puntos del enunciado. **El enunciado fija `L = 10`** y pide
las tres densidades `ρ = 2, 4, 8`, o sea `N = ρ·L² = 200, 400, 800`.

### Punto (b) — Evolución temporal y criterio de estacionario

El enunciado pide mostrar evoluciones temporales características, explicitar en qué tiempos
se toman los promedios y **marcar con líneas verticales el inicio del estacionario**.

El criterio usado es de convergencia desde condiciones iniciales opuestas: se corren dos
simulaciones con el mismo `--seedIC` y el mismo `--seedLoop` (mismas posiciones iniciales,
mismo ruido) pero una con `--theta0=random` y otra con `--theta0=0`. Una arranca de
`v_a ≈ 0` y la otra de `v_a = 1`; cuando las dos curvas se juntan, el sistema se olvidó de
la condición inicial y de ahí en adelante se puede promediar.

```bash
for pair in "200 2" "400 4" "800 8"; do set -- $pair
  python3 TP2/scripts/sweep.py theta0 --model=standard --n=$1 --l=10 --eta=1.0 --steps=3000 \
      --seedIC=1 --seedLoop=1 --no-keep-traj --outdir=generated/b_theta0_rho$2
done

python3 TP2/scripts/plot_va.py \
    generated/b_theta0_rho4/theta0_random.csv generated/b_theta0_rho4/theta0_alineado.csv \
    --label-by=theta0 --transient=500 \
    --out=TP2/presentacion/figuras/evolucion-temporal.pdf
```

`--transient` es lo que dibuja la línea vertical, y además imprime el `<v_a>` de la cola.

### Punto (c) — `v_a` vs. `η` con barras de error, para las tres densidades

```bash
for pair in "200 2" "400 4" "800 8"; do set -- $pair
  python3 TP2/scripts/sweep.py eta --model=standard --n=$1 --l=10 --steps=3000 \
      --etas=0,0.5,1.0,1.5,2.0,2.5,3.0,3.5,4.0,4.5,5.0 --runs=5 --no-keep-traj \
      --outdir=generated/c_eta_rho$2
done

python3 TP2/scripts/plot_va_vs_eta.py generated/c_eta_rho*/runs.csv --group-by=density \
    --transient=500 --out=TP2/presentacion/figuras/relacion-parametro-observable.pdf
```

`plot_va_vs_eta.py` acepta varios `runs.csv` y dibuja **una curva por grupo**: con
`--group-by=density` sale una por densidad, con `--group-by=model` sale la comparación
estándar vs. votante que pide el punto (f), y con `--group-by=n` el barrido de tamaño.
Con `--group-by=auto` elige solo el campo que difiere entre las corridas.

Cada punto es el promedio sobre las `--runs` semillas del promedio de la cola estacionaria
de esa corrida, y la barra de error es el desvío muestral entre semillas.

### Punto (f) — comparación con el modelo votante

Los mismos comandos con `--model=voter` y otro `--outdir`; después se grafican los dos
juntos:

```bash
python3 TP2/scripts/plot_va_vs_eta.py generated/c_eta_rho4/runs.csv generated/f_voter_rho4/runs.csv \
    --group-by=model --transient=500 --out=TP2/presentacion/figuras/comparacion-modelos.pdf
```

### Extra — barrido de tamaño a densidad fija

No lo pide el enunciado (que fija `L = 10`), pero es la figura 2(a) del paper de Vicsek y
sirve para el slide 21 del template ("Barrido de tamaño o densidad"): se mantiene `ρ` fija
y se varía `L`, de modo que `N = ρ·L²`.

```bash
# ejemplo para rho = 4: L = 5, 10, 20  ->  N = 100, 400, 1600
python3 TP2/scripts/sweep.py eta --model=standard --n=100 --l=5  --steps=3000 ... --outdir=generated/size_rho4_L5
python3 TP2/scripts/sweep.py eta --model=standard --n=400 --l=10 --steps=3000 ... --outdir=generated/size_rho4_L10
python3 TP2/scripts/sweep.py eta --model=standard --n=1600 --l=20 --steps=3000 ... --outdir=generated/size_rho4_L20

python3 TP2/scripts/plot_va_vs_eta.py generated/size_rho4_L*/runs.csv --group-by=n \
    --transient=500 --out=TP2/presentacion/figuras/barrido-variable.pdf
```

### Puntos (d) y (e) — clusters y componente gigante

Un cluster es una **componente conexa del grafo de vecinos**: un conjunto de partículas donde
todo par está unido por una cadena de saltos entre partículas a distancia menor que `rc`. El
observable es `S`, la fracción de partículas que caen en el cluster más grande.

Lo calcula un comando nuevo del motor, que **lee el archivo de texto de una corrida** (no
invoca al simulador):

```
java -jar TP2/target/tp2.jar clusters --in=corrida.txt --out=S.csv [--stride=5]
```

`--stride=5` calcula `S` cada 5 pasos en vez de en todos: 600 puntos por corrida alcanzan de
sobra para las curvas y para promediar la cola, y el cálculo baja 5 veces. El CSV que escribe
tiene la misma forma que los de `v_a`, así que `plot_va.py` y `plot_va_vs_eta.py` lo grafican
sin cambios (la etiqueta del eje sale del nombre de la columna).

**Densidades**: el anuncio de la cátedra del 21/08 extiende el estudio de clusters a
`ρ = 1/π, 1/(2π), 1/(3π)`. No es un capricho: con `rc = 1` el número medio de vecinos es
`π·rc²·ρ`, o sea **1, ½ y ⅓** — muy por debajo del umbral de percolación en 2D (~4.5 vecinos,
`ρ_c ≈ 1.44`). Las densidades 2, 4 y 8 del enunciado están todas percoladas y ahí `S ≈ 1`
para todo `η`. Como esas densidades dan un `N` no entero con `L = 10` (31.8, 15.9 y 10.6),
se fija **N = 400** y se despeja `L = √(N/ρ)` → 35.449, 50.133 y 61.400.

```bash
# barrido de las densidades bajas
python3 TP2/scripts/sweep.py eta --model=standard --n=400 --l=35.449077 --steps=3000 \
    --etas=0,0.5,1.0,1.5,2.0,2.5,3.0,3.5,4.0,4.5,5.0 --runs=5 --no-keep-traj \
    --outdir=generated/d_eta_rho1pi

# S sobre un barrido ya hecho: re-simula con las semillas del indice y agrega la columna s_csv
python3 TP2/scripts/sweep.py clusters --index=generated/d_eta_rho1pi/runs.csv --stride=5
```

Hay que volver a simular porque `S` se calcula desde las posiciones y las trayectorias se
borran con `--no-keep-traj`. Es reproducible al bit: las semillas están en el `runs.csv`.

```bash
# S(t) - punto (d)
python3 TP2/scripts/plot_va.py generated/d_eta_rho1pi/eta1_seed1_S.csv --transient=500 \
    --width=16 --height=5 --out=TP2/presentacion/figuras/clusters-temporal.pdf

# <S> vs eta, una curva por densidad - punto (d)
python3 TP2/scripts/plot_va_vs_eta.py generated/d_eta_rho*/runs.csv --group-by=density \
    --observable=s_csv --transient=500 \
    --out=TP2/presentacion/figuras/clusters-vs-eta.pdf

# v_a vs S - punto (e)
python3 TP2/scripts/plot_va_vs_s.py generated/d_eta_rho*/runs.csv --transient=500 \
    --out=TP2/presentacion/figuras/va-vs-s.pdf
```

### Unidades del eje temporal

El modelo es adimensional: el eje x de los gráficos temporales es `t = paso × Δt`, en las
unidades de tiempo propias del modelo. Como `Δt = 1`, el valor del eje coincide
numéricamente con el número de paso. Para darle escala física: con `v0 = 0.03` y `L = 10`,
una partícula recorre 0.03 unidades de longitud por unidad de tiempo, o sea que tarda ~33
unidades de tiempo en recorrer un radio de interacción (`rc = 1`) y ~333 en cruzar la caja
entera. Una corrida de 3000 pasos son unos 9 cruces de caja.

### Detalles útiles

- Tanto `plot_va.py` como `order_parameter.py` aceptan indistintamente una trayectoria
  `.txt` del motor o un `.csv` ya calculado. El CSV evita reparsear archivos de cientos
  de MB cada vez que se retoca un gráfico.
- Sin `--out`, los scripts de gráficos abren una ventana en vez de guardar el archivo.
- `plot_va.py --logy` pone el eje vertical en escala logarítmica (útil para ver el
  crecimiento inicial de `v_a` cuando arranca de una condición desordenada).
- `plot_va.py --width` y `--height` (en pulgadas, default 9×6) controlan el tamaño de la
  figura. Subir la relación ancho/alto estira el eje temporal sin cambiar el rango de
  datos: con `--width=16 --height=5` el transitorio inicial deja de verse como una pared
  vertical. `--panels-by=density` parte la figura en un panel por densidad.
- El orden de las curvas y de los colores es el orden en que se pasan los archivos: con un
  glob `theta0_*.csv` manda el orden alfabético (alineado antes que random).
- Las trayectorias son grandes (N=400 × 3000 pasos ≈ 75 MB). `sweep.py` estima el espacio
  antes de arrancar y acepta `--no-keep-traj` para borrar cada `.txt` después de extraer
  la serie de `v_a`; con `--skip-existing` se retoma un barrido interrumpido.
- Correr los tests de Python: `cd TP2/scripts && python3 -m unittest discover -p "test_*.py"`.

## Generar animaciones

El módulo de animación es independiente del motor: recibe una corrida ya
terminada y genera un archivo MP4. Requiere Python 3, Matplotlib y FFmpeg.

Desde la raíz del repositorio, instalar la dependencia de Python:

```bash
python3 -m pip install -r TP2/requirements.txt
```

Generar una animación:

```bash
python3 TP2/scripts/animate.py corrida.txt \
  --out=generated/animations/voter_rho4_eta05.mp4
```

Para corridas largas, `--stride=5` toma un cuadro cada cinco pasos (y conserva
siempre el último). También se pueden ajustar `--fps=30` y `--dpi=150`.

La animación usa ejes fijos `[0,L] x [0,L]`, representa la velocidad con un
vector y colorea cada vector según su ángulo. El título informa modelo,
densidad, ruido y tiempo físico. Durante la codificación se muestra una barra
de progreso con el porcentaje y la cantidad de cuadros procesados. Los MP4 no
deben embeberse en el PDF de la presentación: hay que subirlos por separado y
agregar links explícitos.

---

Para decisiones de diseño más profundas, ver `TP2/CLAUDE.md` y la página de
Notion del TP2.
