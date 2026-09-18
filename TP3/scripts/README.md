# Scripts de experimentacion y analisis

Guardar aqui scripts reproducibles para lanzar barridos, leer salidas,
calcular observables, producir tablas y generar figuras. El codigo del motor
de simulacion pertenece a `src/`, no a esta carpeta.

Practicas esperadas:

- Recibir rutas, parametros y semillas por argumentos de linea de comandos.
- Incluir ayuda (`--help`) y fallar claramente ante datos invalidos.
- Separar lectura, calculo y visualizacion para facilitar pruebas.
- Escribir resultados regenerables fuera del codigo fuente, normalmente en
  un directorio `generated/` ignorado por Git.
- Registrar metadatos suficientes para repetir cada experimento.
- Agregar pruebas pequenas para parsers y calculos cientificos sensibles.


## Barridos (`sweep.py`)

Genera y simula `--realizations` corridas por cada valor de `--param` (una opción de
`generate`, sin guiones) y escribe en `TP3/generated/sweeps/<name>/`:

- `runs.csv`: una fila por realización (semilla, K, t90, goles, eventos, runtime, estado).
- `summary.csv`: por valor, ⟨t90⟩ y σ muestral entre las realizaciones que alcanzaron el
  90 %, cuántas lo alcanzaron, ⟨Ng⟩ ± σ, runtime medio ± σ y eventos medios.
- `meta.json`: comando, parámetros y duración del barrido.

Lo que va después de `--` se pasa sin cambios a `generate`. La realización k usa
`--seed seed-base + k`, así que los mismos valores de semilla se repiten entre puntos del
barrido. Las trayectorias no se guardan: se simula sin estados intermedios.

```bash
# 1.2: largo del embudo.
python3 TP3/scripts/sweep.py --name embudo_largo --param obstacle-funnel-length \
    --values 0.1 0.2 0.3 0.4 0.5 0.6 --realizations 10 -- --obstacle-algorithm funnel
# Configuración guardada contra la mesa vacía.
python3 TP3/scripts/sweep.py --name semicirculo_70 --realizations 10 -- --obstacles TP3/configs/semicircle_70.txt
python3 TP3/scripts/sweep.py --name vacia --realizations 10 -- --obstacle-algorithm none
# 1.1: runtime vs N. Usar --jobs 1: en paralelo las corridas compiten por la CPU.
python3 TP3/scripts/sweep.py --name runtime --param n --values 50 100 200 400 \
    --realizations 10 --time 30 --jobs 1 -- --obstacle-algorithm none
```

Sale con código 1 si alguna generación o simulación falló; esas filas quedan en
`runs.csv` con su error y no entran en las estadísticas.

## Gráficos de barridos (`plot_sweep.py`)

Grafica uno o más `summary.csv` (`--y t90|runtime|goals`) con barras de ±σ. Un barrido
sin `--param` se puede agregar como `--reference`: recta en su media y banda de ±σ.
Avisa si en algún punto no todas las realizaciones alcanzaron t90, porque esa media
promedia solo las que sí lo alcanzaron. No agrega título: va en el caption.

```bash
python3 TP3/scripts/plot_sweep.py TP3/generated/sweeps/embudo_largo/summary.csv \
    --xlabel 'Largo del embudo [m]' --reference TP3/generated/sweeps/vacia/summary.csv \
    --reference-label 'Mesa vacía' --out TP3/generated/embudo_largo.png
python3 TP3/scripts/plot_sweep.py TP3/generated/sweeps/runtime/summary.csv --y runtime \
    --xlabel 'N' --out TP3/generated/runtime.png
```

## Verificación de mapas (`check_map.py`)

Ver la sección "Relleno de regiones bloqueadas" del README de TP3.

## Animación

Desde la raíz del repositorio:

```bash
python3 -m pip install -r TP3/requirements.txt
python3 TP3/scripts/animate.py TP3/generated/simulation.txt
python3 TP3/scripts/animate.py TP3/generated/simulation.txt --out TP3/generated/animacion.mp4 --fps 30 --speed 0.5
# GIF no requiere FFmpeg:
python3 TP3/scripts/animate.py TP3/generated/simulation.txt --out TP3/generated/animacion.gif
```

MP4 requiere `ffmpeg` instalado y disponible en PATH. Sin `--out`, el video
se guarda junto a la entrada con extensión `.mp4`. Las salidas existentes se
reemplazan. `--speed 1` reproduce a tiempo real, `2` al doble y `0.5` a la mitad.
`--dpi` controla la resolución (120 por defecto). Consultar `--help`.

Se dibujan discos con sus radios físicos, obstáculos grises y arcos verdes.
Las partículas frescas son azules y las usadas rojas. El título muestra tiempo,
goles, fracción usada y eventos acumulados.

Para conservar los rebotes, generar la trayectoria con `simulate --dt 0.01`
(estados exactos cada 0.01 s, tamaño independiente de la cantidad de choques)
o con `simulate --every 1` (todos los choques; archivos enormes en mapas densos).
El video muestrea tiempos uniformes e interpola posiciones entre estados;
los colores y contadores cambian al alcanzar cada evento guardado. Acepta eventos
simultáneos y condiciones iniciales de un solo cuadro. Si faltan choques entre
estados separados por más de 0.01 s, la interpolación puede atravesar obstáculos:
el script avisa en ese caso. Los FPS limitan qué instantes se ven.

El lector (`simulation_io.py`) carga la trayectoria completa en memoria; para
corridas grandes conviene animar una simulación más corta. GIF también acumula
los cuadros en memoria, por lo que se recomienda MP4 para videos largos.

Pruebas del lector, del muestreo temporal y del resumen de barridos:

```bash
python3 -m unittest discover -s TP3/scripts -p 'test_*.py'
```
