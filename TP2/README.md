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

## Estado actual

- `--model=voter` funciona completo.
- `--model=standard` **todavía no está conectado** — pendiente de una
  respuesta de la cátedra (viernes 21/08). Si se intenta usar, el comando
  falla con un mensaje explicativo en vez de correr silenciosamente.

## Formato del archivo de salida

```
model=voter N=5 L=10.0 rc=1.0 dt=1.0 v0=0.03 eta=0.5 periodic=true seedIC=1 seedLoop=1
t=0
1 7.3088 4.1008 1.3051
2 3.3272 9.6776 0.0384
3 9.6370 9.3987 5.9514
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

**Bloques de tiempo**: cada uno empieza con una línea `t=<n>`, seguida de
una línea por partícula: `id x y theta`, con `x`, `y`, `theta` formateados
a 4 decimales.

## Nota para el Paquete B

El archivo **no incluye el grafo de vecinos** — hay que recalcularlo con
`NeighborLookup` usando `L`/`rc`/`periodic` de la cabecera, porque
guardarlo en cada bloque de tiempo infla el tamaño del archivo sin
necesidad (se puede recalcular en O(N) con el CIM). Detalle completo en la
página de Notion "Material para Informe — TP2".

---

Para decisiones de diseño más profundas, ver `TP2/CLAUDE.md` y la página de
Notion del TP2.

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
vector y colorea cada vector según su ángulo. La visualización no muestra ejes,
parámetros ni barra de colores y usa el título fijo `Animación de Viseck`.
Durante la codificación se muestra una barra de progreso con el porcentaje y la
cantidad de cuadros procesados. Los MP4 no deben embeberse en el PDF de la
presentación: hay que subirlos por separado y agregar links explícitos.
