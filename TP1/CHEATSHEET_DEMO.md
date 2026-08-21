# Cheat sheet — ciclo completo del TP1

> Ejecutar todo desde la raíz del proyecto. Los comandos de esta hoja usan Bash/Linux.
> En Windows, reemplazar `/` por `\` y `python3` por `python` si corresponde.

## Ruta corta de la demo

### 0. Preparar y compilar

```bash
java -version                 # requiere Java 21
mvn -version
mvn clean package
```

Resultado esperado al compilar: `BUILD SUCCESS` y `target/tp1.jar`.

Preparar Python la primera vez, solo si no están instaladas las dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install pandas matplotlib PyQt6
```

En corridas posteriores solo hace falta activar el entorno y comprobarlo:

```bash
source .venv/bin/activate
python3 -c "import pandas, matplotlib, PyQt6; print(matplotlib.get_backend())"
```

El backend mostrado debe ser interactivo, por ejemplo `qtagg`; si muestra `agg`,
Matplotlib solo podrá guardar imágenes y `--interactive` no abrirá una ventana.

### 1. Validar con el ejemplo de la cátedra

```bash
java -cp target/classes ar.edu.itba.sds.tp1.CimRunner \
  ArchivosEjemplo/Static100.txt \
  ArchivosEjemplo/Dynamic100.txt \
  --rc=6.0 \
  --out=validacion.txt
```

Mostrar los IDs más fáciles de verificar:

```bash
grep -E '^(9|16|91|100)(,|$)' validacion.txt
```

Salida esperada:

```text
9
16,30
91,22,41,84
100
```

Para comprobar automáticamente **todas las líneas publicadas** por la cátedra:

```bash
diff <(grep -Fxf validacion.txt ArchivosEjemplo/AlgunosVecinos_100_rc6.txt) \
     ArchivosEjemplo/AlgunosVecinos_100_rc6.txt
```

Si no imprime nada, todas coinciden.

> Decir: “El archivo de la cátedra es un extracto parcial, no un output de 100 líneas. Todas las entradas que publica coinciden exactamente con nuestro resultado.”

### 2. Generar un dataset reproducible

```bash
java -jar target/tp1.jar generate 500 20 1 demo_final
```

Para generar otra distribución controlando el directorio, pero no la semilla:

```bash
java -jar target/tp1.jar generate 500 20 auto demo_variante
```

> Decir: “Usamos rejection sampling. Proponemos una posición al azar y la descartamos si se superpone; permitimos hasta 100.000 intentos por partícula. Una seed numérica reproduce la corrida y `auto` usa `System.nanoTime()`.”

### 3. Ejecutar CIM sobre lo generado

```bash
java -cp target/classes ar.edu.itba.sds.tp1.CimRunner \
  demo_final/Static500.txt \
  demo_final/Dynamic500.txt \
  --rc=1.0 \
  --out=vecinos_final.txt
```

La consola debe informar `N`, `L`, `rc`, `M`, contorno, tiempo y archivo de salida. Al omitir `--m`, el programa elige la máxima `M` válida automáticamente.

> Static dice cuántas partículas hay, el tamaño del dominio y sus radios. Dynamic contiene las posiciones del instante. Siempre se usan juntos.

### 4. Visualizar y seleccionar una partícula

```bash
python3 scripts/visualize.py \
  demo_final/Static500.txt \
  demo_final/Dynamic500.txt \
  --out=vecinos_final.txt \
  --rc=1.0 \
  --interactive
```

Hacer clic en una partícula: queda roja, sus vecinos naranjas y se destacan las celdas recorridas. Volver a hacer clic la deselecciona.

Alternativa sin ventana:

```bash
python3 scripts/visualize.py \
  demo_final/Static500.txt demo_final/Dynamic500.txt \
  --out=vecinos_final.txt --rc=1.0 --highlight=1 --save=demo.png
```

### 5. Ejecutar la validación automatizada

```bash
mvn test
```

Resultado esperado:

```text
Tests run: 17, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

> Decir: “Comparamos CIM contra fuerza bruta en modo pared y periódico, con el dataset de la cátedra, uno generado y casos límite. Con `M=1`, toda la grilla es una sola celda: se comparan todos los pares, igual que en fuerza bruta.”

### 6. Forzar errores controlados

#### M inválido

```bash
java -cp target/classes ar.edu.itba.sds.tp1.CimRunner \
  demo_final/Static500.txt demo_final/Dynamic500.txt \
  --rc=1.0 --m=99 --out=x.txt
```

Explicación corta:

1. Para partículas puntuales alcanza con `L/M > rc`.
2. Con radios, los centros pueden estar separados hasta `rc + r1 + r2`.
3. Como `M` es global, se cubre el peor par posible.
4. Por eso se exige **`L/M > rc + 2·rMax`**.

#### Periodicidad inválida

```bash
java -cp target/classes ar.edu.itba.sds.tp1.CimRunner \
  demo_final/Static500.txt demo_final/Dynamic500.txt \
  --rc=15.0 --periodic --out=x.txt
```

> Decir: “Evitamos que una partícula interactúe con su propia imagen periódica. Por eso exigimos `L > 2·(rc + 2·rMax)`.”

#### Dataset demasiado denso para el generador

```bash
java -jar target/tp1.jar generate 1200 20 1 x
```

> Decir: “El generador abandona limpiamente si no logra ubicar una partícula tras 100.000 intentos. El límite observado es propio del rejection sampling/RSA, no el óptimo geométrico de empaquetamiento.”

## Benchmark rápido pedido en vivo

```bash
java -jar target/tp1.jar benchmark-m \
  300 20 0.23 0.26 1.0 false 100 1 demo.csv

python3 scripts/plot_benchmark.py demo.csv --out=demo.png
```

Orden de parámetros de `benchmark-m`:

```text
N L radiusMin radiusMax rc periodic repetitions seed outputCsv
```

Usar 100 repeticiones durante la demo. Los gráficos oficiales pueden usar 1000; tienen menos ruido, pero tardan bastante más.

## Regenerar los gráficos finales

### Punto 3 — tiempo vs. M

```bash
java -jar target/tp1.jar benchmark-m 500 20 0.23 0.26 1.0 false 1000 1 punto3_500.csv
java -jar target/tp1.jar benchmark-m 1000 20 0.23 0.26 1.0 false 1000 1 punto3_1000.csv
python3 scripts/plot_benchmark.py punto3_500.csv punto3_1000.csv --out=punto3_regenerado.png
```

> Lectura: con `M` muy chica, la grilla ahorra pocas comparaciones y agrega overhead. Al aumentar `M`, el CIM supera a fuerza bruta y se estabiliza cerca de la máxima `M` válida.

### Punto 4 — tiempo vs. N, densidad libre y fija

```bash
java -jar target/tp1.jar benchmark-n 20 0.23 0.26 1.0 false libre 1000 1 punto4_libre.csv 10,25,50,100,200,300,500,700,850,1000
java -jar target/tp1.jar benchmark-n 20 0.23 0.26 1.0 false fija 1000 1 punto4_fija.csv 10,25,50,100,200,300,500,700,850,1000
python3 scripts/plot_benchmark.py punto4_libre.csv punto4_fija.csv --out=punto4_regenerado.png
```

> Lectura: con `L` fijo aumenta la densidad y también el trabajo por celda. Con densidad fija, `L` crece con `N`, la ocupación media por celda permanece aproximadamente constante y aparece el comportamiento lineal esperado.

### Verificación periódica

Primero deben existir `punto4_libre.csv` y `punto4_fija.csv` del bloque anterior.

```bash
java -jar target/tp1.jar benchmark-n 20 0.23 0.26 1.0 true libre 100 1 verif_libre_periodico.csv 10,25,50,100,200,300,500,700,850,1000
java -jar target/tp1.jar benchmark-n 20 0.23 0.26 1.0 true fija 100 1 verif_fija_periodico.csv 10,25,50,100,200,300,500,700,850,1000
python3 scripts/plot_benchmark.py \
  punto4_libre.csv punto4_fija.csv \
  verif_libre_periodico.csv verif_fija_periodico.csv \
  --out=verificacion_regenerada.png
```

> Lectura: la periodicidad cambia la resolución del índice vecino (`floorMod` frente al chequeo de rango), ambas operaciones O(1), por lo que no cambia la forma esperada de las curvas.

Para una regeneración rápida, reemplazar `1000` por `100` en la posición de `repetitions` y aclarar que habrá más ruido.

## Cierre de 20 segundos

> “Implementamos y validamos el Cell Index Method contra fuerza bruta. Resolvimos tres dificultades no triviales: el criterio de `M` para partículas con radio, la autointerferencia bajo contorno periódico y una comparación de rendimiento consistente entre implementaciones. Los 17 tests pasan y el ejemplo publicado por la cátedra coincide.”

## Salvavidas

```bash
# Ver ayuda general
java -jar target/tp1.jar

# Sintaxis de CIM
java -cp target/classes ar.edu.itba.sds.tp1.CimRunner \
  STATIC DYNAMIC --rc=RC [--m=M] [--periodic] --out=SALIDA

# Limpiar artefactos de la demo y recompilar (solo si realmente se desea borrarlos)
mvn clean package
```
