# TP2 — Autómatas Celulares: modelo de Vicsek (72.25, ITBA)

## Descripción
Simulación de bandadas (flocking) con el modelo de Vicsek: partículas que se
mueven a velocidad constante alineando su dirección con la de sus vecinos,
más ruido. Java 21 + Maven, multi-módulo con TP1 (ver `pom.xml` en la raíz
del repo).

> El detalle completo del enunciado y las decisiones de diseño vive en la
> página de Notion del TP2. Este archivo es memoria de trabajo, no la
> reemplaza.

## Parámetros confirmados
- `rc = 1` (confirmado en el paper real de la cátedra)
- `Δt = 1`
- `v₀ = 0.03` (a confirmar)
- `L = 10` fijo
- Densidades `ρ = 2, 4, 8` → `N = 200, 400, 800`

## Modelos
- **Estándar**: nuevo ángulo = promedio vectorial de los ángulos de los vecinos (+ ruido)
- **Votante**: nuevo ángulo = copia del ángulo de un vecino elegido al azar (+ ruido)

## División de trabajo (3 paquetes, interfaces vía archivo de texto)
- **Paquete A — motor** (`ar.edu.itba.sds.tp2.engine`): genera partículas,
  corre la simulación (ambos modelos), escribe posiciones/ángulos a texto
  por paso de tiempo.
- **Paquete B — observables** (`ar.edu.itba.sds.tp2.analysis`): lee el
  archivo de A, calcula polarización y clusters (BFS), detecta estado
  estacionario, hace benchmarking del CIM comparado con TP1.
- **Paquete C — visualización/experimentos** (`TP2/scripts/`, Python): lee
  los archivos de A y B, arma animaciones y gráficos finales. No es código
  Java.

Los 3 paquetes se comunican solo a través de los archivos de texto que
escribe A y luego B — no hay código Java compartido entre ellos.

## Reuso de TP1
TP2 reusa `NeighborFinder` / `BruteForceNeighborFinder` / `CellIndexMethod` /
`Particle` de TP1 **tal cual, sin modificarlos**, como dependencia Maven
declarada en `TP2/pom.xml` (no se copia código). El repo es un reactor
multi-módulo: correr Maven desde la raíz para que TP2 resuelva la
dependencia sobre TP1 automáticamente. Si se builda `TP2/` de forma
standalone, instalar TP1 antes al menos una vez: `cd TP1 && mvn install`.

**Cómo se conecta con el motor (Paquete A) — importante:**
`NeighborFinder.findNeighbors(...)` solo necesita posición, radio, L, rc y
periodicidad — es una pregunta geométrica sobre una foto congelada, no le
importan tiempo ni velocidad. Por eso NO hace falta tocar `Particle` de TP1
para agregarle ángulo/velocidad. El motor tiene su propia clase de partícula
Vicsek (con posición Y ángulo θ), y en cada paso de tiempo:
1. Convierte esa lista a `Particle` de TP1 (`id, x, y, radius=0`) — objeto
   liviano y descartable, solo para esa llamada puntual.
2. Llama a `findNeighbors(...)` con esa conversión.
3. Usa el `Map<Integer, Set<Integer>>` que devuelve para ir a buscar el
   ángulo de cada vecino en la lista ORIGINAL de partículas Vicsek (por id),
   no en la conversión.

`Particle` de TP1 y la partícula de Vicsek son dos clases separadas — no se
fusionan ni se extiende una a la otra. TP1 queda intacto (ya entregado y
demostrado, no se toca salvo necesidad real).
