# Arquitectura UML del TP2 — Modelo de Vicsek

Este documento representa la arquitectura implementada actualmente. Separa la vista de
componentes —responsabilidades y flujo de datos— de la vista de clases del núcleo Java.

## 1. Vista simplificada

![Arquitectura simplificada del TP2](arquitectura_tp2.svg)

Esta es la vista recomendada para el informe o la presentación: muestra ejecutables,
archivos intermedios, procesamiento y resultados sin entrar en todas las clases.

## 2. Diagrama de componentes detallado

```mermaid
flowchart LR
    user([Usuario])

    subgraph CLI[Interfaz de línea de comandos — Java]
        Main[Main / despachador]
        Simulate[simulate]
        GenerateIC[generate-ic]
        Clusters[clusters]
        Benchmark[benchmark-cim]
        Main --> Simulate
        Main --> GenerateIC
        Main --> Clusters
        Main --> Benchmark
    end

    subgraph A[Paquete A — Motor de simulación]
        IC[Condición inicial]
        Simulation[Motor Vicsek]
        Strategy{Estrategia de dirección}
        Standard[Modelo estándar]
        Voter[Modelo votante]
        Lookup[Adaptador NeighborLookup]

        IC --> Simulation
        Standard --> Strategy
        Voter --> Strategy
        Strategy --> Simulation
        Lookup --> Simulation
    end

    subgraph TP1[Dependencia Maven — TP1]
        NF[NeighborFinder]
        CIM[CellIndexMethod]
        BF[BruteForceNeighborFinder]
        Particle[Particle geométrica]
        CIM -. implementa .-> NF
        BF -. implementa .-> NF
        Particle --> NF
    end

    subgraph B[Paquete B — Análisis Java]
        Reader[SimulationReader]
        ClusterAnalysis[ClusterAnalysis / BFS]
        CimMeasurement[Medición del CIM]
        Reader --> ClusterAnalysis
        Reader --> CimMeasurement
    end

    subgraph C[Paquete C — Experimentos y visualización Python]
        Sweep[sweep.py]
        PyReader[simulation_io.py]
        Order[order_parameter.py]
        Plots[plot_*.py]
        Animate[animate.py]
        Batch[generate_animation_batch.sh]

        Sweep -->|ejecuta procesos| Main
        PyReader --> Order
        Order --> Plots
        PyReader --> Animate
        Batch -->|ejecuta| Main
        Batch --> Animate
    end

    ICFile[(Condición inicial .txt)]
    Trajectory[(Trayectoria .txt)]
    ClusterFiles[(S.csv / miembros.txt)]
    Series[(va.csv / runs.csv)]
    Outputs[(PDF / PNG / MP4)]

    user --> Main
    GenerateIC --> IC
    IC --> ICFile
    ICFile --> Simulate
    Simulate --> Simulation
    Simulation --> Trajectory

    Lookup -->|adapta VicsekParticle a Particle| NF
    NF --> Lookup

    Trajectory --> Reader
    Clusters --> Reader
    Clusters --> ClusterAnalysis
    ClusterAnalysis --> Lookup
    ClusterAnalysis --> ClusterFiles
    Benchmark --> CimMeasurement
    CimMeasurement --> Lookup

    Trajectory --> PyReader
    Order --> Series
    Series --> Plots
    Trajectory --> Animate
    ClusterFiles -. resaltado opcional .-> Animate
    Plots --> Outputs
    Animate --> Outputs
```

### Lectura de la arquitectura

- `Main` es el único punto de entrada del JAR y delega en cuatro comandos.
- El **Paquete A** genera o lee la condición inicial, ejecuta la simulación y escribe una
  trayectoria en texto. El algoritmo de actualización angular es intercambiable mediante
  `DirectionUpdateStrategy`.
- `NeighborLookup` es la frontera entre TP2 y TP1. Convierte temporalmente cada
  `VicsekParticle(id, x, y, theta)` en una `Particle(id, x, y, radius=0)` y delega la
  búsqueda geométrica en `NeighborFinder`, normalmente `CellIndexMethod`.
- El **Paquete B** vuelve a leer la trayectoria en streaming. Recalcula el grafo de vecinos
  para obtener clusters por BFS y para medir el rendimiento real del CIM.
- El **Paquete C** consume archivos, no clases Java. Automatiza corridas, calcula el parámetro
  de orden, produce gráficos y renderiza animaciones.
- Los archivos de texto y CSV desacoplan simulación, análisis y visualización: no es necesario
  conservar toda una trayectoria en memoria ni enlazar Python con la JVM.

## 3. Diagrama de clases del núcleo

```mermaid
classDiagram
    direction LR

    class Command {
        <<interface>>
        +execute(args)
    }
    class Main
    class SimulateCommand
    class GenerateIcCommand
    class ClustersCommand
    class BenchmarkCimCommand

    Main o-- Command : registra y despacha
    Command <|.. SimulateCommand
    Command <|.. GenerateIcCommand
    Command <|.. ClustersCommand
    Command <|.. BenchmarkCimCommand

    class VicsekSimulation {
        -initialParticles
        -neighborLookup
        -strategy
        -dt
        -v0
        -eta
        -steps
        +run(output)
        -advance(current)
    }
    class VicsekParticle {
        <<record>>
        +id
        +x
        +y
        +theta
    }
    class DirectionUpdateStrategy {
        <<interface>>
        +nextAngle(self, neighbors, eta, random)
    }
    class StandardModel {
        -includeSelf
        +nextAngle(self, neighbors, eta, random)
    }
    class VoterModel {
        +nextAngle(self, neighbors, eta, random)
    }
    class NeighborLookup {
        -neighborFinder
        -l
        -rc
        -periodic
        +findNeighbors(particles)
    }
    class InitialConditionGenerator {
        +generate(n, l, random, theta0)
    }
    class InitialConditionFile {
        +read(path)
        +write(path, n, l, seed, particles)
    }
    class AngleMath {
        +normalize(theta)
        +vectorialAverage(thetas)
        +addNoise(theta, eta, random)
    }
    class PeriodicBoundary {
        +wrap(coordinate, l)
    }

    DirectionUpdateStrategy <|.. StandardModel
    DirectionUpdateStrategy <|.. VoterModel
    VicsekSimulation *-- DirectionUpdateStrategy
    VicsekSimulation *-- NeighborLookup
    VicsekSimulation o-- "1..*" VicsekParticle
    VicsekSimulation ..> PeriodicBoundary
    StandardModel ..> AngleMath
    VoterModel ..> AngleMath
    InitialConditionGenerator ..> VicsekParticle : crea
    InitialConditionFile ..> VicsekParticle : serializa
    SimulateCommand ..> InitialConditionGenerator
    SimulateCommand ..> InitialConditionFile
    SimulateCommand ..> VicsekSimulation : construye
    SimulateCommand ..> StandardModel
    SimulateCommand ..> VoterModel

    class NeighborFinder {
        <<interface, TP1>>
        +findNeighbors(particles, l, rc, periodic)
    }
    class CellIndexMethod {
        <<TP1>>
    }
    class BruteForceNeighborFinder {
        <<TP1>>
    }
    class Particle {
        <<record, TP1>>
        +id
        +x
        +y
        +radius
    }

    NeighborFinder <|.. CellIndexMethod
    NeighborFinder <|.. BruteForceNeighborFinder
    NeighborLookup *-- NeighborFinder
    NeighborLookup ..> Particle : adapta a

    class SimulationReader {
        +open(path)
        +header()
        +next() Frame
        +close()
    }
    class RunHeader {
        <<record>>
        +model
        +n
        +l
        +rc
        +eta
        +density()
    }
    class Frame {
        <<record>>
        +step
        +particles
    }
    class ClusterAnalysis {
        +of(particles, lookup) ClusterStats
    }
    class ClusterStats {
        <<record>>
        +largestSize
        +clusterCount
        +n
        +largestMembers
        +s()
    }

    SimulationReader *-- RunHeader
    SimulationReader ..> Frame : produce
    Frame o-- "1..*" VicsekParticle
    ClusterAnalysis ..> Frame
    ClusterAnalysis ..> NeighborLookup
    ClusterAnalysis ..> ClusterStats : produce
    ClustersCommand ..> SimulationReader
    ClustersCommand ..> ClusterAnalysis
    BenchmarkCimCommand ..> SimulationReader
    BenchmarkCimCommand ..> NeighborLookup
```

## 4. Flujo de una simulación

1. `Main` recibe `simulate` y delega en `SimulateCommand`.
2. El comando genera partículas con `InitialConditionGenerator` o las lee mediante
   `InitialConditionFile`.
3. Selecciona `StandardModel` o `VoterModel`, crea un `CellIndexMethod` y lo envuelve en
   `NeighborLookup`.
4. En cada paso, `VicsekSimulation` mueve todas las partículas con su dirección actual.
5. Si el contorno es periódico, `PeriodicBoundary` devuelve las coordenadas a `[0,L)`.
6. `NeighborLookup` convierte la fotografía del sistema al tipo `Particle` de TP1 y pide el
   grafo de vecinos al CIM.
7. La estrategia calcula simultáneamente los nuevos ángulos a partir de esa fotografía y
   agrega ruido mediante `AngleMath`.
8. El motor escribe el nuevo estado en la trayectoria `.txt` y continúa hasta `steps`.
9. Java o Python leen luego esa trayectoria para clusters, métricas, gráficos o animaciones.

## 5. Decisiones de diseño para explicar en una presentación

- **Strategy:** `StandardModel` y `VoterModel` implementan la misma interfaz; el bucle de
  simulación no contiene condicionales dependientes del modelo.
- **Adapter:** `NeighborLookup` permite reutilizar TP1 sin modificar `Particle` ni mezclarla
  con `VicsekParticle`.
- **Command:** cada operación del JAR implementa `Command` y `Main` solo resuelve y ejecuta
  el comando solicitado.
- **Procesamiento en streaming:** `VicsekSimulation` escribe un cuadro por vez y
  `SimulationReader` lo lee del mismo modo, evitando cargar corridas grandes completas.
- **Pipeline basado en archivos:** facilita ejecutar experimentos por lotes, repetir análisis
  sin recalcular simulaciones y mantener desacoplados Java y Python.
