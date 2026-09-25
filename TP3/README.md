# TP3 — Motor de simulación dirigido por eventos

Para una explicación archivo por archivo, de las fórmulas y de las estructuras
de datos, consultar [MOTOR.md](MOTOR.md). Para recetas paso a paso (crear mapas,
simular, animar, barrer y graficar a mano), ver [GUIA.md](GUIA.md).

Implementación Java 21 del billar-metegol de `enunciado/TP3_Enunciado.pdf`,
con predicción y resolución de colisiones según `Molecular Dynamics Simulation
of Hard Spheres.pdf`. El motor produce archivos de texto; la animación se ejecuta
por separado con `scripts/animate.py` (MP4 o GIF).

## Animación rápida

Desde la raíz del repositorio, después de generar una trayectoria:

```bash
python3 -m pip install -r TP3/requirements.txt
python3 TP3/scripts/animate.py TP3/generated/simulation.txt --out TP3/generated/animacion.mp4
```

MP4 requiere FFmpeg. Para animar, simular con `--dt 0.01`: escribe estados exactos
cada 0.01 s, así el archivo pesa lo mismo (~1 MB por segundo simulado con N=100)
aunque el mapa produzca miles de choques por segundo. `--every 1` también es exacto,
pero con mapas densos genera archivos enormes. Usar `--speed 0.5` para cámara lenta
o `--speed 2` para acelerar.

```bash
java -jar TP3/target/tp3.jar generate --seed 1 --obstacles TP3/configs/funnel.txt --out TP3/generated/embudo_ic.txt
java -jar TP3/target/tp3.jar simulate --input TP3/generated/embudo_ic.txt --time 30 --dt 0.01 --out TP3/generated/embudo.txt
python3 TP3/scripts/animate.py TP3/generated/embudo.txt --out TP3/generated/embudo.mp4
```
Ver [scripts/README.md](scripts/README.md) para opciones y límites de interpolación.

## Estructura

| Archivo / carpeta | Responsabilidad |
|---|---|
| `src/main/java/ar/edu/itba/sds/tp3/Main.java` | Comandos `generate` y `simulate`. |
| `engine/StageGeneration.java` | Generación de posiciones y direcciones, validación del mapa. |
| `engine/CollisionSimulator.java` | Predicción de próximos eventos, avance y resolución de choques. |
| `engine/obstacles/` | Interfaz, algoritmos, relleno de regiones y registro de generación de obstáculos. |
| `engine/SimulationConfig.java` | Dimensiones y parámetros físicos. |
| `models/Particle.java` | Posición, velocidad, radio, masa, estado fresca/usada y contador de choques. |
| `models/Obstacle.java` | Centro y radio de un disco fijo de masa infinita. |
| `models/Event.java` | Tipo, instante absoluto, participantes y validez de una predicción. |
| `io/StageFile.java` | Lectura/escritura de condiciones iniciales y escritura de fotogramas. |
| `configs/central.txt` | Ejemplo de configuración con un obstáculo central, sin optimización. |
| `configs/funnel.txt` | Embudos hacia ambos arcos (`funnel`, largo 0.30 m), K=28. |
| `configs/semicircle_70.txt` | 70 % izquierdo bloqueado; libre solo el semicírculo de 0.36 m del arco derecho, K=31. |
| `configs/central_R0.32.txt` | Disco central de radio 0.32 m: divide la mesa en dos cámaras. |
| `configs/esquinas_R0.10.txt` | Un disco de radio 0.10 m en cada esquina, tangente a ambas paredes. |
| `configs/central_embudo_a0.05.txt`, `central_cuenco_Rf0.30.txt`, `central_palos_Rp0.02.txt` | Disco central con el mejor valor de cada planteo de embudo. |
| `scripts/sweep.py` | Barrido de parámetros: realizaciones, ⟨t90⟩ ± σ, goles y tiempo de ejecución. |
| `scripts/plot_sweep.py` | Gráfico de un barrido: ⟨t90⟩, runtime o goles ± σ vs el parámetro, con referencia opcional. |
| `scripts/check_map.py` | Verifica que un mapa no deje huecos sin salida a un arco y lo dibuja. |
| `generated/` | Condiciones iniciales y trayectorias regenerables, ignoradas por Git. |
| `src/test/java/` | Pruebas deterministas de física, generación, archivos y comandos. |
| `enunciado/`, `informe/`, `presentacion/`, `scripts/` | Consigna, documentación y trabajo posterior. |

Las rutas `engine/`, `models/` e `io/` de la tabla son relativas al paquete
`src/main/java/ar/edu/itba/sds/tp3/`.

## Ejecución

Desde la raíz del repositorio:

```bash
mvn -f TP3/pom.xml package

# Mesa vacía: 100 partículas y condición inicial reproducible.
java -jar TP3/target/tp3.jar generate --n 100 --seed 42 --obstacle-algorithm none
java -jar TP3/target/tp3.jar simulate --input TP3/generated/initial.txt --time 30 --every 10

# Misma separación de etapas, con obstáculos elegidos explícitamente.
java -jar TP3/target/tp3.jar generate --n 100 --seed 42 --obstacles TP3/configs/central.txt --out TP3/generated/central_initial.txt
java -jar TP3/target/tp3.jar simulate --input TP3/generated/central_initial.txt --time 100 --every 100 --out TP3/generated/central_run.txt
```

Desde `TP3/`, usar `mvn package`, `target/tp3.jar`, `configs/...` y `generated/...`.
Las salidas predeterminadas siempre se ubican en el `generated/` del módulo TP3,
incluso ejecutando desde la raíz. Los caminos explícitos se interpretan respecto
del directorio de ejecución. Si se copia el JAR fuera del módulo, indicar `--out`.
Los archivos de salida existentes se reemplazan; usar nombres distintos para
conservar realizaciones. Entrada y salida de `simulate` deben ser diferentes.

`generate` permite `--length`, `--width`, `--goal-width`, `--radius`, `--mass`
y `--speed`. Los valores por defecto del enunciado son L=1.20 m, W=0.68 m,
d=0.20 m, r=0.0175 m, m=0.025 kg y v0=1 m/s. La configuración queda registrada
en el archivo inicial. `simulate` toma esos parámetros del archivo, con tiempo
final `--time` en segundos (30 por defecto) y frecuencia `--every` en cantidad
de colisiones válidas (1 por defecto). Alternativamente, `--dt` escribe los estados
en t = k·dt, exactos porque entre eventos el movimiento es rectilíneo uniforme;
excluye `--every`. Se calculan sobre copias: la dinámica, y por lo tanto t90, es
idéntica con o sin `--dt`. Sirve para animaciones y para el DCM, que requiere tiempos uniformes.

Cada obstáculo se define con una línea `x y radio`, en metros, compatible con
el entregable de competencia. Se aceptan líneas vacías y comentarios `#`.
Sin `--obstacles`, se usa `--obstacle-algorithm random` por defecto: dos obstáculos
de radio 0.05 m. Para la mesa vacía del punto 1.1 usar `--obstacle-algorithm none`. Los obstáculos se
validan íntegramente dentro del rectángulo, sin solapamientos y con radio ≥ r.

Las partículas se ubican por rechazo uniforme en toda el área disponible;
las direcciones son uniformes en [0, 2π), usando `java.util.Random` con semilla.
Si una partícula no puede ubicarse tras 100000 intentos, se informa un error:
este límite no demuestra que el empaquetamiento sea geométricamente imposible.
También se pueden editar las filas del archivo inicial para probar una
distribución específica: el lector valida IDs únicos, geometría y valores
finitos. Las velocidades deben expresarse como componentes vx, vy.

## Algoritmos de obstáculos

Cada algoritmo vive en un archivo separado dentro de `engine/obstacles/`:

- `ObstacleGenerator.java`: contrato `generate(config, seed)` que devuelve obstáculos.
- `RandomObstacleGenerator.java` (`random`): centros aleatorios uniformes por rechazo, sin solapamientos.
- `EmptyObstacleGenerator.java` (`none`): mesa vacía.
- `SingleObstacleGenerator.java` (`single`): un obstáculo en `--obstacle-x`, `--obstacle-y`
  (centro de la mesa por defecto) de radio `--obstacle-radius` (0.1). Sirve para barrer un
  obstáculo grande sobre el eje longitudinal.
- `FunnelObstacleGenerator.java` (`funnel`): embudos hacia ambos arcos. Bloquea las cuatro
  esquinas detrás de rectas que van de cada palo del arco a la pared larga, a
  `--obstacle-funnel-length` (0.30 m) de la pared corta; debe ser ≤ L/2. Con
  `--obstacle-edge-radius ρ`, la recta que da a la cancha es una cadena de discos de radio ρ
  (por ejemplo r = 0.0175, el mínimo) y solo el interior de las esquinas usa discos más grandes.
- `SemicircleObstacleGenerator.java` (`semicircle`): deja libre solo el semicírculo de
  radio `--obstacle-free-radius` (0.36 m = 0.3 L) centrado en el arco derecho y bloquea
  el resto, arco izquierdo incluido. Con `--obstacle-goals both` deja libre un semicírculo
  en cada arco: un cuenco, es decir un embudo de pared curva.
- `PostsObstacleGenerator.java` (`posts`): un disco de radio `--obstacle-radius` (0.05) en
  cada palo de ambos arcos, tangente a la pared corta; estrecha la entrada del arco.
- `LatticeObstacleGenerator.java` (`lattice`): red triangular de discos equidistantes
  (tablero de Galton), separados `--obstacle-spacing` (0.1) y de radio `--obstacle-radius`
  (r, el mínimo por defecto). Centrada y simétrica; omite discos que dejarían un paso ≤ 2r
  contra una pared o un obstáculo existente, y rechaza separaciones sin paso entre vecinos.
- `EllipseObstacleGenerator.java` (`ellipse`): mesa elíptica con vértices en los arcos y focos
  en x = `--obstacle-focus-x` (0.3) y L − focus-x. El borde es una cadena de discos de radio
  `--obstacle-edge-radius` (r) y el exterior se rellena. En cada foco, `--obstacle-focus-shape`:
  `none`, `disc` (disco concéntrico de radio `--obstacle-focus-size`), `line` (recta vertical
  de discos mínimos de semilargo focus-size) o `lens` (lente biconvexa vertical de semialto
  focus-size y semiancho `--obstacle-lens-width`, 0.03).
- `DiscChain.java`: cadena de discos iguales sobre una curva, sin solapes y con huecos menores
  que 2r; la usan la elipse, la lente y la recta.
- `RegionFill.java`: relleno que usan `funnel` y `semicircle` (ver abajo).
- `ObstacleGenerators.java`: registro de nombres y de las opciones que acepta cada uno.

Cada algoritmo rechaza las opciones `--obstacle-*` que no utiliza.

### Combinar obstáculos

`--obstacles base.txt` junto con `--obstacle-algorithm` suma al archivo los obstáculos
del algoritmo. `funnel`, `semicircle` y `random` los ubican respetando los del archivo;
`single` y `posts` los agregan en posiciones fijas y la validación rechaza solapamientos.

```bash
# Disco central de radio 0.32 con cuenco alrededor de cada arco.
java -jar TP3/target/tp3.jar generate --obstacles TP3/configs/central_R0.32.txt \
    --obstacle-algorithm semicircle --obstacle-goals both --obstacle-free-radius 0.30 \
    --obstacles-out TP3/configs/central_cuenco_Rf0.30.txt
```

### Relleno de regiones bloqueadas

Los obstáculos deben ser discos, así que "tapar" una zona significa rellenarla con
discos. El riesgo es que queden huecos cerrados donde entre una partícula: como las
posiciones iniciales se sortean en toda el área disponible, una partícula que nace
ahí queda atrapada y t90 puede no alcanzarse nunca.

`RegionFill` recorre una grilla de la región bloqueada y, en cada paso, coloca el
disco más grande posible centrado en un punto donde todavía entra el centro de una
partícula (acotado por paredes, discos ya colocados, `--obstacle-max-radius` y la zona
libre, que puede invadir hasta r). Termina cuando no queda ningún punto así. Repite
con grillas de `--obstacle-grid` (1 mm), la mitad y la cuarta parte para cubrir
huecos menores que la grilla. Como solo coloca discos donde cabe una partícula,
todos cumplen Rk ≥ r. El resultado es determinista: no depende de la semilla.

`scripts/check_map.py` verifica un mapa ya generado de forma independiente:

```bash
python3 TP3/scripts/check_map.py TP3/generated/initial.txt --step 0.0001 --png TP3/generated/mapa.png
```

Informa el área accesible para centros de partícula, si cada arco es alcanzable y las
componentes conexas sin salida a ningún arco (sale con código 1 si existe alguna).

### Configuraciones guardadas

`--obstacles-out archivo.txt` escribe los obstáculos generados en el formato de
competencia (`x y radio`); solo se escribe si las N partículas se pudieron ubicar.

```bash
java -jar TP3/target/tp3.jar generate --obstacle-algorithm funnel --obstacles-out TP3/configs/funnel.txt
java -jar TP3/target/tp3.jar generate --obstacle-algorithm semicircle --obstacles-out TP3/configs/semicircle_70.txt
```

En `semicircle_70.txt` el área libre queda cerca del límite del muestreo por rechazo
para N=100: en 400 semillas falló la generación en 3 (0.75 %). Con
`--obstacle-free-radius 0.37` no falló ninguna. Cuando falla, `generate` informa el error
y no escribe nada; se repite con otra semilla.

```bash
# Por defecto: dos obstáculos aleatorios de radio 0.05 m.
java -jar TP3/target/tp3.jar generate --seed 42

# Elegir algoritmo, cantidad y radio; mantener fija la configuración al variar --seed.
java -jar TP3/target/tp3.jar generate --obstacle-algorithm random --obstacle-count 3 --obstacle-radius 0.04 --obstacle-seed 17 --seed 1 --out TP3/generated/random_initial.txt
```

`--obstacle-seed` usa el valor de `--seed` si se omite. Se utilizan generadores
aleatorios independientes para obstáculos y partículas. Para comparar varias
realizaciones sobre el mismo mapa, fijar `--obstacle-seed` y variar `--seed`.
Las coordenadas y radios concretos quedan guardados en la condición inicial;
para reproducir la generación desde cero, conservar también el comando utilizado.

`--obstacles archivo.txt` sigue disponible y excluye las opciones `--obstacle-*`.
El algoritmo `none` no acepta cantidad, radio ni semilla de obstáculos.
El aleatorio limita a 100000 los intentos por obstáculo y falla si no logra
ubicarlo. Luego `StageGeneration` valida el mapa e intenta ubicar las N
partículas; una configuración que no permite completar esa etapa produce un
error, sin guardar una condición inicial parcial.

Para agregar otro algoritmo:

1. Crear una clase que implemente `ObstacleGenerator` en su propio archivo.
2. Implementar `generate(SimulationConfig config, long seed)`; recibir parámetros
   particulares en el constructor.
3. Agregar un `case` con su nombre y constructor en `ObstacleGenerators.create`.
4. Si necesita opciones nuevas, incorporarlas al parser de `Main` y pasarlas al constructor.

No es necesario modificar la generación de partículas ni el motor de colisiones.
Desde Java también se puede pasar el resultado del algoritmo directamente a
`StageGeneration.generate(config, n, particleSeed, generator.generate(config, obstacleSeed))`.

## Dinámica

El término autopropulsadas se interpreta aquí conforme a la consigna:
movimiento rectilíneo uniforme entre choques, sin fuerza motriz adicional.
El módulo de la velocidad es v0 **al inicio**; no se renormaliza después de un
choque entre partículas. Todas las colisiones conservan la energía cinética.
Los choques entre partículas también conservan el momento lineal; paredes y
obstáculos intercambian momento con las partículas y permanecen inmóviles.

Una `PriorityQueue<Event>` ordena los tiempos absolutos de colisión. Al extraer
un evento válido se avanza el sistema hasta ese instante, se resuelve el choque
y se recalculan las predicciones de las partículas afectadas. Cada evento guarda
los contadores de colisiones de sus participantes para descartar predicciones
obsoletas. La búsqueda inicial es O(N² + NK); cada colisión recalcula O(N+K)
predicciones más el costo de la cola y el avance de N partículas. La cola se
limpia de eventos obsoletos cuando supera un umbral de tamaño.

Las paredes cortas siguen siendo sólidas en los arcos: al contacto se invierte
vx. Si `abs(y-W/2) <= d/2` y la partícula era fresca, suma un gol y pasa a roja.
Nunca se elimina ni vuelve a sumar. Se calcula t90 en el evento exacto aunque
ese evento no se escriba por la frecuencia de salida. La simulación continúa
hasta el tiempo final, aun si ya alcanzó el 90%.

Se incluyen contactos inmediatos para resolver esquinas. Colisiones simultáneas
se procesan secuencialmente con desempate estable; no se implementa una solución
colectiva de impactos múltiples, conforme a la simplificación del material de
referencia. La tangencia exacta sin impacto normal no genera evento.

## Formato de texto `tp3-v1`

Mantiene la organización de TP2 (`clave=valor`, bloques `t=...`), con columnas
propias del TP3; los lectores de TP2 necesitan adaptación para este formato.

```text
format=tp3-v1 N=1 K=1 L=1.2 W=0.68 d=0.2 r=0.0175 m=0.025 v0=1.0 seedIC=42
obstacle 0.6 0.34 0.08
t=0.0 events=0 Ng=0 Fu=0.0
1 0.2 0.34 1.0 0.0 0.0175 0.025 0 0 255
```

Después de la cabecera aparecen K filas `obstacle x y radio`. Cada bloque
empieza con `t`, número acumulado de eventos, goles `Ng` y fracción usada `Fu`,
seguido de N filas:

```text
id x y vx vy radio masa rojo verde azul
```

Azul `(0,0,255)` significa fresca; rojo `(255,0,0)` significa usada.
La condición inicial contiene solamente el bloque de t=0. La trayectoria agrega
los estados posteriores a cada múltiplo de `--every`, siempre el estado inicial
y el estado final, y termina con un comentario:

```text
# tf=30.0 outputEvery=10 events=12345 Ng=95 t90=24.7 runtime=0.41
```

`runtime` es el tiempo real en segundos del ciclo de eventos, escritura incluida,
sin el arranque de la JVM ni la lectura de la condición inicial.

Con `--dt`, el comentario dice `outputInterval=<dt>` en lugar de `outputEvery`.
Los números del comentario son ilustrativos. `t90=NaN` indica que no se alcanzó
el 90%. Los intervalos entre bloques son variables: deben utilizarse los tiempos
escritos, no un dt constante. En contactos simultáneos pueden aparecer bloques
con el mismo tiempo. La escritura es incremental; no se almacena la trayectoria
completa en memoria.

## Barridos

`scripts/sweep.py` genera y simula varias realizaciones por valor de un parámetro
de `generate` y resume ⟨t90⟩ ± σ, goles y tiempo de ejecución. Ver `--help` y
[scripts/README.md](scripts/README.md).

```bash
python3 TP3/scripts/sweep.py --name embudo_largo --param obstacle-funnel-length \
    --values 0.1 0.2 0.3 0.4 0.5 0.6 --realizations 10 -- --obstacle-algorithm funnel
python3 TP3/scripts/sweep.py --name vacia --realizations 10 -- --obstacle-algorithm none
python3 TP3/scripts/plot_sweep.py TP3/generated/sweeps/embudo_largo/summary.csv \
    --xlabel 'Largo del embudo [m]' --reference TP3/generated/sweeps/vacia/summary.csv \
    --reference-label 'Mesa vacía' --out TP3/generated/embudo_largo.png
```

## Verificación

```bash
mvn -f TP3/pom.xml test
```

Se verifican predicciones, conservación de energía y momento, rebotes contra
obstáculos y esquinas, invalidación de eventos, goles únicos, reproducibilidad,
lectura/escritura, errores de entrada y una corrida con 100 partículas que
controla paredes y ausencia de solapamientos.
