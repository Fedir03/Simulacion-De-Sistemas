# Guía de uso manual

Recetas para generar mapas, simular, animar y barrer parámetros a mano.
Para el detalle de cada opción ver [README.md](README.md); para la implementación,
[MOTOR.md](MOTOR.md). Todos los comandos se ejecutan **desde la raíz del repositorio**.

## 0. Preparar el entorno (una vez)

```bash
mvn -f TP3/pom.xml package                       # compila, corre los tests y crea TP3/target/tp3.jar
python3 -m pip install -r TP3/requirements.txt   # matplotlib; check_map.py usa además numpy y scipy
```

Recompilar con el mismo comando después de cambiar código Java. Para videos MP4 hace
falta `ffmpeg` en el PATH (sin él, pedir `.gif`).

Para acortar los comandos:

```bash
TP3="java -jar TP3/target/tp3.jar"
```

## 1. El flujo en tres pasos

```text
generate  →  condición inicial (obstáculos + partículas en t=0)
simulate  →  trayectoria + resultado final (t90, goles, eventos, runtime)
animate   →  video MP4/GIF
```

Los archivos intermedios son texto. Los nombres son libres; conviene guardarlos en
`TP3/generated/`, que Git ignora. Un archivo de salida existente se reemplaza.

## 2. Generar un mapa

Un "mapa" es la lista de obstáculos. `generate` los construye, ubica las N partículas
al azar y escribe la condición inicial. Con `--obstacles-out` guarda además los
obstáculos en formato de competencia (`x y radio` por línea), reutilizable después.

### 2.1 Con un algoritmo

```bash
# Mesa vacía
$TP3 generate --obstacle-algorithm none --out TP3/generated/vacia_ic.txt

# Un obstáculo: centro de la mesa por defecto; x, y y radio configurables
$TP3 generate --obstacle-algorithm single --obstacle-x 0.6 --obstacle-y 0.34 --obstacle-radius 0.32 \
    --out TP3/generated/centro_ic.txt --obstacles-out TP3/configs/mi_centro.txt

# Embudo recto hacia ambos arcos (esquinas triangulares), largo a ≤ L/2
$TP3 generate --obstacle-algorithm funnel --obstacle-funnel-length 0.2 --out TP3/generated/embudo_ic.txt
# ...con la frontera hacia la cancha hecha de discos de radio mínimo
$TP3 generate --obstacle-algorithm funnel --obstacle-funnel-length 0.2 --obstacle-edge-radius 0.0175 --out TP3/generated/embudo_ic.txt

# Zona libre semicircular alrededor del arco derecho (resto tapado)...
$TP3 generate --obstacle-algorithm semicircle --obstacle-free-radius 0.36 --out TP3/generated/semi_ic.txt
# ...o alrededor de ambos arcos (cuenco)
$TP3 generate --obstacle-algorithm semicircle --obstacle-goals both --obstacle-free-radius 0.40 --out TP3/generated/cuenco_ic.txt

# Red triangular de discos mínimos equidistantes (tablero de Galton), separación s > 0.07
$TP3 generate --obstacle-algorithm lattice --obstacle-spacing 0.12 --out TP3/generated/galton_ic.txt

# Mesa elíptica (focos en 0.3 y 0.9) con un objeto en cada foco: none | disc | line | lens
$TP3 generate --obstacle-algorithm ellipse --obstacle-focus-shape lens --obstacle-focus-size 0.10 \
    --obstacle-lens-width 0.05 --out TP3/generated/elipse_ic.txt

# Un disco en cada palo de los arcos
$TP3 generate --obstacle-algorithm posts --obstacle-radius 0.04 --out TP3/generated/palos_ic.txt

# K discos aleatorios de igual radio; --obstacle-seed fija el mapa aunque cambie --seed
$TP3 generate --obstacle-algorithm random --obstacle-count 3 --obstacle-radius 0.05 --obstacle-seed 17 \
    --out TP3/generated/random_ic.txt
```

Si no se indica ningún algoritmo ni archivo, se usa `random` con 2 discos de radio 0.05.
Cada algoritmo rechaza opciones `--obstacle-*` que no usa, así un error de tipeo no pasa
inadvertido. `$TP3 --help` lista todas las opciones.

### 2.2 A mano, escribiendo el archivo

Crear un `.txt` con una línea `x y radio` (metros) por obstáculo. Se admiten comentarios `#`:

```text
# TP3/configs/mi_mapa.txt
0.60 0.34 0.20   # disco central
0.15 0.10 0.05
0.15 0.58 0.05
```

```bash
$TP3 generate --obstacles TP3/configs/mi_mapa.txt --out TP3/generated/mi_mapa_ic.txt
```

Reglas que se validan: cada disco íntegramente dentro de la mesa, sin solaparse con otro
y con radio ≥ r = 0.0175 m. Si el mapa deja poco espacio libre, `generate` puede fallar
al ubicar las N partículas: informa el error y no escribe nada.

### 2.3 Combinar un archivo con un algoritmo

Los obstáculos del archivo son la base y el algoritmo agrega otros alrededor, sin
solaparlos (`funnel`, `semicircle` y `random` los esquivan; `single` y `posts` usan
posiciones fijas y, si chocan, la validación lo informa):

```bash
$TP3 generate --obstacles TP3/configs/central_R0.32.txt \
    --obstacle-algorithm semicircle --obstacle-goals both --obstacle-free-radius 0.30 \
    --out TP3/generated/cuenco_ic.txt --obstacles-out TP3/configs/mi_cuenco.txt
```

### 2.4 Verificar y dibujar el mapa

Antes de invertir tiempo en simulaciones, comprobar que ninguna partícula pueda quedar
encerrada en un hueco sin salida a un arco:

```bash
python3 TP3/scripts/check_map.py TP3/generated/mi_mapa_ic.txt --png TP3/generated/mi_mapa.png
```

Informa K, área de obstáculos, área accesible, si cada arco es alcanzable y los
componentes sin arco (sale con código 1 si hay alguno). El PNG muestra obstáculos en gris,
zona accesible en celeste, partículas iniciales y arcos en verde. `--step 0.0001` hace
una verificación más fina.

### 2.5 Cambiar las partículas sin cambiar el mapa

`--seed` controla posiciones y direcciones iniciales. Para varias realizaciones del
mismo mapa, reutilizar el archivo de obstáculos y variar `--seed`:

```bash
for s in 1 2 3; do $TP3 generate --seed $s --obstacles TP3/configs/mi_mapa.txt --out TP3/generated/mi_mapa_s$s.txt; done
```

Opcionales: `--n` (100), `--speed` (1), y dimensiones con `--length`, `--width`, `--goal-width`,
`--radius`, `--mass`. Quedan escritos en la cabecera y `simulate` los toma de ahí.

## 3. Ejecutar una simulación

```bash
$TP3 simulate --input TP3/generated/mi_mapa_ic.txt --time 100 --every 1000000000 --out TP3/generated/mi_mapa_sim.txt
```

- `--time`: tiempo simulado en segundos (30 por defecto; la competencia usa 100).
- La consola muestra `eventos`, `goles`, `t90` (NaN si no se llegó al 90 %) y `runtime`,
  el tiempo real del ciclo de eventos en segundos. Lo mismo queda en la última línea del archivo.
- Qué estados se escriben:
  - `--every n`: cada n choques (1 por defecto). Un n enorme, como arriba, escribe solo el
    estado inicial y el final: lo más rápido si solo interesa t90.
  - `--dt 0.01`: el estado en t = 0, 0.01, 0.02, …. Es lo adecuado para animar y para el
    DCM. No altera la dinámica: el t90 es idéntico al de la corrida sin `--dt`.
- El resultado depende solo de la condición inicial: misma entrada, mismo t90.

## 4. Animar

```bash
$TP3 simulate --input TP3/generated/mi_mapa_ic.txt --time 30 --dt 0.01 --out TP3/generated/mi_mapa_anim.txt
python3 TP3/scripts/animate.py TP3/generated/mi_mapa_anim.txt --out TP3/generated/mi_mapa.mp4
```

- `--speed 0.5` cámara lenta, `--speed 2` al doble; `--fps` (30) y `--dpi` (120).
- Con `.gif` en `--out` no hace falta ffmpeg, pero consume más memoria.
- Tamaño: con N=100 y `--dt 0.01`, ~1 MB de texto por segundo simulado. Para videos
  largos simular menos tiempo: el script carga la trayectoria completa en memoria.
- No usar `--every` grande para animar: se pierden choques y las partículas atraviesan
  obstáculos (el script avisa).

### Reproducir en video una realización de un barrido

Cada fila de `runs.csv` tiene su `seed`. Con la misma semilla y el mismo mapa se obtiene
exactamente la misma corrida:

```bash
$TP3 generate --seed 122 --obstacles TP3/configs/central_cuenco_Rf0.30.txt --out TP3/generated/c_ic.txt
$TP3 simulate --input TP3/generated/c_ic.txt --time 17 --dt 0.01 --out TP3/generated/c.txt   # t90 = 13.55
python3 TP3/scripts/animate.py TP3/generated/c.txt --out TP3/generated/c.mp4
```

## 5. Muchas realizaciones: barridos

`sweep.py` repite generate + simulate por cada valor de un parámetro y cada semilla,
en paralelo, y resume ⟨t90⟩ ± σ. Todo lo que va después de `--` se pasa a `generate`;
`--param` es una opción de `generate` sin los guiones.

```bash
# Un mapa fijo, 20 realizaciones (semillas 1..20)
python3 TP3/scripts/sweep.py --name mi_mapa --realizations 20 -- --obstacles TP3/configs/mi_mapa.txt

# Barrer un parámetro de un algoritmo
python3 TP3/scripts/sweep.py --name centro_x --param obstacle-x --values 0.3 0.45 0.6 \
    --realizations 20 -- --obstacle-algorithm single --obstacle-radius 0.2

# Barrer un algoritmo sobre una base fija
python3 TP3/scripts/sweep.py --name cuenco --param obstacle-free-radius --values 0.3 0.35 0.4 \
    --realizations 50 --seed-base 101 -- --obstacles TP3/configs/central_R0.32.txt \
    --obstacle-algorithm semicircle --obstacle-goals both

# Tiempo de ejecución vs N (punto 1.1): --jobs 1 para medir sin competencia por la CPU
python3 TP3/scripts/sweep.py --name runtime --param n --values 25 50 100 200 \
    --realizations 10 --time 30 --jobs 1 -- --obstacle-algorithm none
```

- Resultados en `TP3/generated/sweeps/<name>/`: `runs.csv` (una fila por corrida),
  `summary.csv` (una por valor) y `meta.json` (el comando). Se imprime una tabla al final.
- `--time` (100 por defecto), `--seed-base` (1) y `--jobs` (núcleos − 1).
- Para comparar configuraciones de forma pareada, usar el mismo `--seed-base` y
  `--realizations` en todos los barridos.
- Si una generación falla (partículas que no entran), la corrida queda en `runs.csv`
  con su error y no se cuenta; la columna `failed` de `summary.csv` lo indica.
- `reached_t90` cuenta las realizaciones que llegaron al 90 %; la media de t90 usa solo esas.

## 6. Graficar

```bash
python3 TP3/scripts/plot_sweep.py TP3/generated/sweeps/centro_x/summary.csv \
    --xlabel 'Posición x del obstáculo [m]' \
    --reference TP3/generated/sweeps/mi_mapa/summary.csv --reference-label 'Mesa vacía' \
    --out TP3/generated/centro_x.png
```

- `--y t90|runtime|goals`; varias series pasando varios `summary.csv` y `--labels`.
- `--reference` recibe un barrido sin `--param` y lo dibuja como recta ± σ.
- Las barras son el desvío de una realización; el error de la media es σ/√M.
- Sin título embebido, según las reglas de la cátedra: el título va en el caption.

## 7. Receta completa: probar una idea de mapa

```bash
# 1. Escribir TP3/configs/idea.txt a mano (o generarlo con --obstacles-out)
# 2. Verificar que no encierre partículas
$TP3 generate --seed 1 --obstacles TP3/configs/idea.txt --out TP3/generated/idea_ic.txt
python3 TP3/scripts/check_map.py TP3/generated/idea_ic.txt --png TP3/generated/idea.png
# 3. Medir contra la mejor configuración conocida con las mismas semillas
python3 TP3/scripts/sweep.py --name idea --realizations 50 --seed-base 101 -- --obstacles TP3/configs/idea.txt
python3 TP3/scripts/sweep.py --name mejor --realizations 50 --seed-base 101 -- --obstacles TP3/configs/central_cuenco_Rf0.30.txt
# 4. Verla en video
$TP3 simulate --input TP3/generated/idea_ic.txt --time 20 --dt 0.01 --out TP3/generated/idea.txt
python3 TP3/scripts/animate.py TP3/generated/idea.txt --out TP3/generated/idea.mp4
```

## Configuraciones guardadas (`TP3/configs/`)

| Archivo | Descripción | ⟨t90⟩ (50 realizaciones) |
|---|---|---|
| `central_cuenco_Rf0.30.txt` | Disco central R=0.32 + cuenco Rf=0.30 en ambos arcos | 13.5 ± 1.5 s |
| `central_R0.32.txt` | Disco central R=0.32: dos cámaras | 16.4 ± 1.9 s |
| `esquinas_R0.10.txt` | Un disco R=0.10 en cada esquina | 29.0 ± 2.9 s |
| `galton_s0.25.txt`, `galton_s0.10.txt` | Red de Galton de discos mínimos, s=0.25 y s=0.10 | 23.6 ± 3.1 s / 48.7 ± 7.4 s |
| `embudo_min_a0.05.txt` | Embudo a=0.05 con frontera de discos mínimos | 22.8 ± 2.6 s |
| `central_embudo_a0.05.txt` | Disco central + embudo recto a=0.05 | 17.4 ± 1.8 s |
| `central_palos_Rp0.02.txt` | Disco central + palos Rp=0.02 | 22.4 ± 2.6 s |
| `funnel.txt` | Embudo recto a=0.30, sin disco central | 30.3 ± 3.7 s (10 real.) |
| `semicircle_70.txt` | 70 % izquierdo tapado, semicírculo libre de 0.36 | 41.0 ± 6.2 s (10 real.) |
| `central.txt` | Ejemplo: un disco en el centro, R=0.08 | — |

Referencia: mesa vacía 22.6 ± 2.6 s (semillas 101–150).
