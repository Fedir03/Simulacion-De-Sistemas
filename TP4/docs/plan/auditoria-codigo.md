# Auditoría cruzada del código (D30)

La cátedra pide coordinar y auditar los códigos del motor y del análisis (anuncio "Criterios de Evaluación TP4 y TP5").

**Regla:** nadie audita su propio código. Los pares son los de D23:
- Ruckauf audita a Fede.
- Fede audita a Lolo.
- Lolo audita a Ruckauf (Sistema 1 y Sistema 2, que no escribió).

**Qué mira el revisor:** contra la letra del enunciado y de la Teórica 4 (`auditoria-integradores.md`, `referencia/FORMULAS-VERIFICADAS.md`), no contra intuición física; contra las decisiones de `DEFINICIONES.md` (citar la D); nada de interpolación. Cada hallazgo se marca 🔴 error / 🟡 duda / 🟢 ok, con archivo:línea.

**Compuerta:** todas las filas en "auditado" (sin 🔴 abiertos) **antes del paso 10** (congelado del motor).

| Módulo / archivo | Autor | Revisor | Fecha | Hallazgos | Estado |
|---|---|---|---|---|---|
| Motor S1: `engine/oscillator/*`, `models/Oscillator`, `io/OscillatorFiles` (38e890b) | fedir03 (Ruckauf) | Lolo | | | pendiente |
| Motor S2 (Verlet, contactos, pared imagen, obstáculos, fresca→usada, energía, salida cada dt2): `models/BilliardConfig`, `engine/billiard/ContactForces`, `engine/billiard/BilliardSimulator`, `io/BilliardFiles`, comando `billiard` en `Main`; tests `engine/billiard/*Test` (incluye `CimVsBruteForceSimulationTest`), `io/BilliardFilesTest`. Etapas 1–4 | Ruckauf | Lolo | | | pendiente de auditoría (código del 20/10, sin commit) |
| CIM copiado de TP1 (+R, validación \|r\|≤R, obstáculos y pared fuera de la grilla; D25): `engine/cim/CellIndexMethod`, `NeighborFinder`, `Particle`; tests `engine/cim/CellIndexMethodTest` (+ `BruteForceNeighborFinder`, solo test) | Fede | Ruckauf | | | pendiente de auditoría (código del 20/10, sin commit) |
| Colocación por grilla única y medición del N máx (D5, D6): `engine/GridPlacement`, `engine/GridCapacity`, comando `grid-nmax` en `Main`; tests `engine/GridPlacementTest` | Fede | Ruckauf | | | pendiente de auditoría (código del 20/10, sin commit) |
| TP3: `StageGeneration.generateGrid` / `gridSites` (red hex, s = 2r + 0,1 mm, ancla `corner` con margen de 0,1 mm a las paredes, D7); test `engine/GridGenerationTest` | Fede | Ruckauf | | | pendiente de auditoría (código del 20/10, sin commit) |
| TP3: `Main` (`generate --placement random\|grid --grid-anchor --grid-margin`, comando `grid-nmax`; `random` por defecto, sin cambios en el original) | Fede | Ruckauf | | | pendiente de auditoría (código del 20/10, sin commit) |
| TP3: paquete `bench` (`TimedCase`, `Tp3Case`, `RuntimeBenchmark`: JVM calentada y reutilizada, heap fijo, orden mezclado, reanudable, control; D11, D12) | Fede | Lolo | | | pendiente de auditoría (código del 20/10, sin commit) |
| Estudio del Sistema 1 (ECM vs dt, F1, calentamiento de JVM) | Lolo | Fede | | | pendiente (sin código) |
| Scripts de `analysis/` (runner, observables, ajuste MB, figuras, animaciones) | Lolo | Fede | | | pendiente (sin código) |
| README del motor y script del ZIP (D26) | Fede | Ruckauf | | | pendiente (sin código) |
