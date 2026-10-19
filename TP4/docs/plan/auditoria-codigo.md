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
| Motor S2 (Verlet, contactos, pared imagen, obstáculos, fresca→usada, energía, salida cada dt2) | Ruckauf | Lolo | | | pendiente (sin código) |
| CIM copiado de TP1 (+R, validación \|r\|≤R, obstáculos y pared fuera de la grilla; D25) | Fede | Ruckauf | | | pendiente (sin código) |
| Colocación por grilla única y medición del N máx (D5, D6) | Fede | Ruckauf | | | pendiente (sin código) |
| `StageGeneration` de TP3 adaptado a la grilla (D7) | Fede | Ruckauf | | | pendiente (sin código) |
| Estudio del Sistema 1 (ECM vs dt, F1, calentamiento de JVM) | Lolo | Fede | | | pendiente (sin código) |
| Scripts de `analysis/` (runner, observables, ajuste MB, figuras, animaciones) | Lolo | Fede | | | pendiente (sin código) |
| README del motor y script del ZIP (D26) | Fede | Ruckauf | | | pendiente (sin código) |
