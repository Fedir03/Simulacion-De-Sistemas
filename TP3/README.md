# TP3 — Motor de simulación dirigido por eventos

Para una explicación archivo por archivo, de las fórmulas y de las estructuras
de datos, consultar [MOTOR.md](MOTOR.md).

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

MP4 requiere FFmpeg. Para ver los rebotes con fidelidad, ejecutar `simulate`
con `--every 1`. Usar `--speed 0.5` para cámara lenta o `--speed 2` para acelerar.
Ver [scripts/README.md](scripts/README.md) para opciones y límites de interpolación.

## Estructura

| Archivo / carpeta | Responsabilidad |
|---|---|
| `src/main/java/ar/edu/itba/sds/tp3/Main.java` | Comandos `generate` y `simulate`. |
| `engine/StageGeneration.java` | Generación de posiciones y direcciones, validación del mapa. |
| `engine/CollisionSimulator.java` | Predicción de próximos eventos, avance y resolución de choques. |
| `engine/obstacles/` | Interfaz, algoritmos y registro de generación de obstáculos. |
| `engine/SimulationConfig.java` | Dimensiones y parámetros físicos. |
| `models/Particle.java` | Posición, velocidad, radio, masa, estado fresca/usada y contador de choques. |
| `models/Obstacle.java` | Centro y radio de un disco fijo de masa infinita. |
| `models/Event.java` | Tipo, instante absoluto, participantes y validez de una predicción. |
| `io/StageFile.java` | Lectura/escritura de condiciones iniciales y escritura de fotogramas. |
| `configs/central.txt` | Ejemplo de configuración con un obstáculo central, sin optimización. |
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
de colisiones válidas (1 por defecto).

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
- `RandomObstacleGenerator.java`: centros aleatorios uniformes por rechazo, sin solapamientos.
- `EmptyObstacleGenerator.java`: mesa vacía (`none`).
- `ObstacleGenerators.java`: registro de nombres seleccionables por CLI.

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
# tf=30.0 outputEvery=10 events=12345 Ng=95 t90=24.7
```

Los números del comentario son ilustrativos. `t90=NaN` indica que no se alcanzó
el 90%. Los intervalos entre bloques son variables: deben utilizarse los tiempos
escritos, no un dt constante. En contactos simultáneos pueden aparecer bloques
con el mismo tiempo. La escritura es incremental; no se almacena la trayectoria
completa en memoria.

## Verificación

```bash
mvn -f TP3/pom.xml test
```

Se verifican predicciones, conservación de energía y momento, rebotes contra
obstáculos y esquinas, invalidación de eventos, goles únicos, reproducibilidad,
lectura/escritura, errores de entrada y una corrida con 100 partículas que
controla paredes y ausencia de solapamientos.
