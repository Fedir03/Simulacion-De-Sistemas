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

Para conservar los rebotes, generar la trayectoria con `simulate --every 1`.
El video muestrea tiempos uniformes e interpola posiciones entre estados;
los colores y contadores cambian al alcanzar cada evento guardado. Acepta eventos
simultáneos y condiciones iniciales de un solo cuadro. Con `--every` mayor que 1
se pierden choques y la interpolación puede atravesar obstáculos: el script
avisa cuando detecta eventos omitidos. Los FPS limitan qué instantes se ven.

El lector (`simulation_io.py`) carga la trayectoria completa en memoria; para
corridas grandes conviene animar una simulación más corta. GIF también acumula
los cuadros en memoria, por lo que se recomienda MP4 para videos largos.

Pruebas del lector y del muestreo temporal:

```bash
python3 -m unittest discover -s TP3/scripts -p 'test_*.py'
```
