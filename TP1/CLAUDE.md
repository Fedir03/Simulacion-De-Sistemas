# TP1 — Cell Index Method (Simulación de Sistemas 72.25, ITBA)

## Descripción
Búsqueda eficiente de partículas vecinas: Cell Index Method vs fuerza bruta.
Java 21 + Maven. Demo en vivo + informe con benchmarking.

## Dominio
- Espacio: cuadrado [0, L] × [0, L]
- Defaults: L=20, rc=1, ri ~ U[0.23, 0.26]
- Distancia: borde-a-borde = dist(centros) - r_i - r_j
- Criterio M válido: L/M > rc + 2·radioMáximo
- Con/sin condiciones periódicas de contorno (flag booleano)

## Formatos de archivo
**Static** (estático):
  Línea 1: N (cantidad de partículas)
  Línea 2: L (tamaño del espacio)
  Líneas 3..N+2: radio  propiedad  (propiedad se descarta)

**Dynamic** (dinámico):
  Línea 1: t0 (se descarta, como property del estático)
  Líneas 2..N+1: x  y  (sin velocidades)

**Output**:
  N líneas siempre; "id,vecino1,vecino2,..." o solo "id" si sin vecinos. IDs 1-indexed.

## Decisiones de diseño
1. `Particle` = record inmutable (id, x, y, radius)
2. Dynamic reader: solo t0, no multi-frame, no velocidades; t0 se descarta
3. Interfaz `NeighborFinder` compartida por BruteForce y CIM
4. CIM: grilla List<Particle>[][] con @SuppressWarnings("unchecked")
5. Media vecindad: cada celda + 4 vecinas, nunca doble conteo
6. M se valida al ejecutar findNeighbors(), no al construir. M inválido → mensaje limpio, sin stack trace
7. Generador: rejection sampling, máx 100.000 intentos/partícula; falla define N_max empírico
8. CLI: una línea para la demo en vivo; script batch separado para los barridos del informe
9. Exportadores: OvitoExporter (XYZ extendido) + CsvExporter, builder compartido de ParticleData
10. visualize.py: --save (PNG estático para informe) + --interactive (mplcursors clickeable)

## Archivos de ejemplo
- ArchivosEjemplo/Static100.txt, Dynamic100.txt — N=100, L=100, r=0.37 (ejemplo genérico de la cátedra)
- ArchivosEjemplo/AlgunosVecinos_100_rc6.txt — extracto parcial del output esperado (rc=6), no el formato completo
- ArchivosEjemplo/FormatoOutput_CIM.txt — descripción del formato de output
