# Paso 04 — Motores con tests

**Cuándo:** en curso (19/10). Sistema 1 hecho (38e890b). Sistema 2, simulación completa CIM vs fuerza bruta, medición del N máx y generador de TP3: pendiente, antes del vie 23
**Antes:** paso `03` · **Después:** paso `05`
**Todos los valores (dt, N, realizaciones, figuras, diapositivas):** `../DEFINICIONES.md`

## Estado al entrar
Respuestas de la cátedra anotadas; D5, D6, D17, D19 cerradas. Módulo `tp4` existe; S1 con 2+ esquemas.

## Objetivo
Que los dos motores pasen los tests de `../referencia/PLAN.md` §7 antes de correr cualquier experimento.

## Tareas (en paralelo)
| Rol | Tarea | Entrega | Está hecho si |
|---|---|---|---|
| A · Ruckauf | Motor S2: Verlet con primer paso por Euler, pared imagen recalculada en cada dt, obstáculos fijos, fresca→usada, energía, salida en múltiplos de dt2. **Depende de la interfaz del CIM acordada con Fede** (qué recibe y qué devuelve, coordenadas desplazadas en +R, D25): se acuerda antes de escribir el cálculo de fuerzas | Tests del S2 en verde | Una partícula conserva L y |v|; misma semilla = mismo archivo (cmp) |
| Fede | CIM y grilla: copiar de TP1 `CellIndexMethod`, `NeighborFinder` y `Particle` con el desplazamiento +R y la validación \|r\|≤R (D25); colocación por grilla única (D5) con semilla; la interfaz del CIM se acuerda con Ruckauf | CIM y colocación integrados al motor | CIM = fuerza bruta en aceleraciones (incluye partículas en x<0 e y<0); auditado por Ruckauf (D30) |
| Fede | Script que mide el N máx colocable con la grilla, sin obstáculos y con obstáculos en x₀=r, y define el tamaño de la grilla a partir de esa medición (sin topes teóricos) | N máx de cada caso + tamaño de grilla, anotados en D5/D6 | Medido con código y con varias semillas |
| Fede | Simulación completa CIM vs fuerza bruta, con la misma semilla y el mismo estado inicial (detalle abajo); la audita Ruckauf (D30) | Comando + resultado anotados abajo | Las 6 combinaciones (3 casos × 2 M) pasan |
| Fede | Adaptar el generador de TP3 (`StageGeneration`) a la grilla única, para volver a correr TP3 con la misma grilla hasta el N máx (D7). Lo necesita el paso 06 | Generador de TP3 con grilla | TP3 coloca el N máx de cancha vacía con semilla; la misma semilla da la misma colocación |
| B · Lolo | F1 (ECM vs dt log-log) y la respuesta a '¿cuál es el mejor?' sobre el código del Sistema 1 ya escrito (38e890b, autor Ruckauf); el tiempo por integrador se mide en el paso 05 | F1 + una frase de respuesta | Pendientes coherentes con el orden esperado de cada esquema |
| C | Runner: lee una lista de casos (estudio, N, x₀, semilla), lanza, guarda en `outputs/<estudio>/<caso>/seed<k>/` | Runner que corre 1 caso | Reproduce el mismo output con la misma semilla |
| D | Redactar S01–S05 y S06 con F1; checklist de `../referencia/CORRECCIONES-CHECKS.md` aplicado a esas diapositivas | S01–S06 en el PDF | Revisión con la skill (modo revisión por sección) sin ítems abiertos |
| E | Tests de entrega: demo de punta a punta, comando exacto anotado | Comando en `docs/` | Corre desde carpeta limpia |

## Prueba de simulación completa CIM vs fuerza bruta
Misma semilla y mismo estado inicial para los dos métodos.
- **Casos:** (a) N=300 sin obstáculos; (b) N máx medido con obstáculos en x₀=r; (c) partículas pegadas a la pared y en x<0 e y<0.
- **Qué se compara:** (1) en cada paso, que el conjunto de pares en contacto sea idéntico; (2) en los primeros ~1000 pasos, posiciones y velocidades iguales dentro de una tolerancia chica; (3) en toda la corrida, curvas de energía total comparables. No se exige igualdad bit a bit en la trayectoria larga, porque el orden de suma distinto amplifica el redondeo.
- **Dos tamaños de celda:** M máximo válido y uno más grueso. Si falla alguna combinación, el CIM está mal configurado.
- **Tiempo:** se mide el de cada método, para ver desde qué N el CIM le gana a la fuerza bruta (sirve para la discusión de 2.1.b).
- **Comando:** `mvn -o test -Dtest=CimVsBruteForceSimulationTest` (desde `TP4/`; imprime una línea por caso y M)
- **Resultado (20/10, Ruckauf, sin auditar):** **pasan las 6 combinaciones.** Pares idénticos en todos los pasos; dt = 1e-4, cuadro cada 10 pasos.

  | Caso | M | Pasos | Pares/paso | \|Δr\| máx (1000 pasos) | \|Δv\| máx | \|ΔE\|/E0 máx | Búsqueda: fuerza bruta → CIM (µs/paso) |
  |---|---|---|---|---|---|---|---|
  | (a) N=300 sin obstáculos | 29 | 3001 | 31 | 0 | 0 | 0 | 200 → 100 (×2,0) |
  | (a) | 7 | 3001 | 31 | 0 | 0 | 0 | 200 → 72 (×2,8) |
  | (b) N=714, x₀=r | 29 | 2001 | 799 | 1,6e-15 | 1,1e-12 | 5,8e-11 | 1042 → 193 (×5,4) |
  | (b) | 7 | 2001 | 799 | 0 | 0 | 2e-16 | 1042 → 422 (×2,5) |
  | (c) pared + racimo x<0, y<0 (N=70, x₀=0,3) | 29 | 5001 | 2 | 0 | 0 | 0 | 16 → 20 (×0,8) |
  | (c) | 7 | 5001 | 2 | 0 | 0 | 0 | 16 → 9 (×1,8) |

  Tolerancias del test: \|Δr\| < 1e-9 m, \|Δv\| < 1e-6 m/s, \|ΔE\|/E0 < 1e-6, Nu idéntico en cada cuadro. Las diferencias de (b) con M=29 son de redondeo: los mismos pares se suman en otro orden (orden de iteración de los `HashSet`). Tiempos de una sola corrida, sin calentamiento de la JVM y en una máquina con ruido: sirven para ver la tendencia (con N chico el CIM no gana; con N=714 gana ×5), no para 2.1.b.

**Hecho 20/10 (Fede): test de vuelo libre, sin el S2.** `CellIndexMethodTest` (`mvn -o test -Dtest=CellIndexMethodTest`). Las partículas avanzan `x += v·dt` sin fuerzas, con rebote especular en la pared, así que se traslapan libremente. En cada paso, los pares del CIM (`forCircle(M, R).findContacts`, rc = 0) son idénticos a los de la fuerza bruta. Casos: (a) N=300 sin obstáculos, 1000 pasos; (b) N máx (714, hex, x₀=r), 200 pasos; (c) anillo pegado a la pared + racimo superpuesto en x<0, y<0, 2000 pasos; cada uno con M ∈ {29, 10, 1}. Además, un test estático con pares que cruzan bordes de celda en x, en y y en la diagonal (−1,+1), y una partícula con |r| = R. **Resultado: pasa todo** (22/22 tests del módulo el 20/10; 43/43 el 21/10, con el motor S2); la clase tarda 8–15 s.

**Hecho 20/10 (Ruckauf): la corrida completa de arriba** (`engine/billiard/CimVsBruteForceSimulationTest`), con misma semilla, mismos pares de contacto en cada paso, casos (a)–(c) × 2 M, y posiciones, velocidades y energía como se describe arriba. Condición para el S2: el motor tiene que recibir un `NeighborFinder` (CIM o fuerza bruta), para poder correr la misma simulación con los dos y comparar. Con fuerzas, la trayectoria depende de los pares, así que son dos corridas con la misma semilla, no una sola consultada por los dos como en vuelo libre.

## Compuerta de salida
- [ ] Tests de §7 (S2) todos en verde, incluido CIM vs fuerza bruta
- [x] Simulación completa CIM vs fuerza bruta: las 6 combinaciones pasan; comando y resultado anotados arriba (20/10, falta la auditoría de Lolo, D30)
- [ ] N máx medido (con y sin obstáculos) y tamaño de grilla anotados en D5/D6
- [ ] Generador de TP3 con la grilla única listo para el paso 06
- [ ] F1 y respuesta de S1 listas
- [ ] Runner reproducible
- [ ] S01–S06 revisadas por la skill

## Si se traba
Si el S2 no pasa los tests a tiempo para correr los estudios antes del vie 23, se decide en el grupo qué estudios se recortan (pendiente, antes del vie 23).
