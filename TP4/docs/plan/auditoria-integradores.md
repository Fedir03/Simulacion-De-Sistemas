# Auditoría de integradores (D29)

La cátedra pide revisar que los integradores hagan exactamente lo de la teórica y explicitar toda adaptación, discutiéndola con la cátedra antes de presentar; como la clase del 19/10 ya pasó, se consulta por mail (paso 09) (anuncio "Criterios de Evaluación TP4 y TP5").

- **Fórmulas:** verificadas por el grupo contra `docs/enunciado/Teorica_4.pdf` (versión subida el 16/10, commit 90ffd06). Detalle en `referencia/FORMULAS-VERIFICADAS.md`.
- **Código:** el chequeo línea por línea contra estas fórmulas lo hace el revisor asignado en D30 (`auditoria-codigo.md`). Las referencias archivo:línea son del commit 38e890b.
- **"Consultado con la cátedra":** se completa con la fecha y la respuesta de la cátedra al mail (consulta (b) del paso 09).

Rutas: `Scheme.java` = `TP4/src/main/java/ar/edu/itba/sds/tp4/engine/oscillator/Scheme.java`; `OscillatorStudy.java` = misma carpeta.

## Verlet original (Sistema 1 y Sistema 2)
| Diapo | Fórmula | Archivo:línea | Adaptación | Justificación | Consultado con la cátedra (fecha) |
|---|---|---|---|---|---|
| 13–15 | r(t+Δt) = 2r(t) − r(t−Δt) + (Δt²/m)·f(t) | `Scheme.java:44` | — | — | |
| 13–15 | v(t) = [r(t+Δt) − r(t−Δt)] / (2Δt) | — | No se usa en el S1 para evaluar f | Con f = −kr − γv, la v central necesita r(t+Δt), que a su vez necesita f(t): es circular | 22/10 (M1): aceptada como adaptación |
| 14 | r(−Δt) por Euler evaluado en −Δt | `Scheme.java:36` | — | Lo dice la diapo 14 | |
| — | v(t) ≈ [r(t) − r(t−Δt)] / Δt para evaluar f(t) | `Scheme.java:38-42` | Diferencia hacia atrás | D17; fuerza dependiente de v | 22/10 (M1): aceptada como adaptación; M2: se mantiene la estimación |
| 13 | Sistema 2: r(t+Δt) = 2r(t) − r(t−Δt) + (Δt²/m)·f(t) | `BilliardSimulator.java:90` | — | En el billar f no depende de v: no hace falta estimar la velocidad | |
| 14 | Sistema 2: r(−Δt) por Euler evaluado en −Δt | `BilliardSimulator.java:84` | — | Con la grilla de D5 no hay contactos en t=0 (F(0)=0), así que el paso es exacto (test `gridInitialConditionHasNoContactsAndExactInitialSpeed`) | |
| 13 | Sistema 2: v(t) = [r(t+Δt) − r(t−Δt)]/(2Δt), solo para E_cin y la salida | `BilliardSimulator.java:96` | — | — | |

## Velocity Verlet
| Diapo | Fórmula | Archivo:línea | Adaptación | Justificación | Consultado con la cátedra (fecha) |
|---|---|---|---|---|---|
| 17 | r(t+Δt) = r(t) + Δt·v(t) + (Δt²/(2m))·f(t) | `Scheme.java:57` | — | Δt²/(2m): errata de la versión anterior del PDF, confirmada (consulta 8, D19) | |
| 17 | v(t+Δt) = v(t) + (Δt/(2m))·(f(t) + f(t+Δt)) | `Scheme.java:63` | — | — | |
| — | f(t+Δt) evaluada con v_pred = v(t) + a(t)·Δt | `Scheme.java:58-62` | v predicha por Euler | f(t+Δt) necesita v(t+Δt); D17 | 22/10 (M1): aceptada como adaptación; M2: se mantiene la estimación |

## Beeman predictor-corrector
| Diapo | Fórmula | Archivo:línea | Adaptación | Justificación | Consultado con la cátedra (fecha) |
|---|---|---|---|---|---|
| 19–20 | r(t+Δt) = r + vΔt + (2/3)aΔt² − (1/6)a(t−Δt)Δt² | `Scheme.java:18` | — | — | |
| 20 | v_pred = v + (3/2)aΔt − (1/2)a(t−Δt)Δt | `Scheme.java:19` | — | — | |
| 20 | a(t+Δt) = f(r(t+Δt), v_pred)/m | `Scheme.java:20` | — | — | |
| 20 | v_corr = v + (1/3)a(t+Δt)Δt + (5/6)aΔt − (1/6)a(t−Δt)Δt | `Scheme.java:21` | — | — | |
| — | a(−Δt) por Euler hacia atrás | `Scheme.java:16` | Estimación del primer paso | La diapo 14 lo dice solo para Verlet; se usa el mismo criterio | 22/10 (M1): aceptada como adaptación |

## Euler predictor-corrector
| Diapo | Fórmula | Archivo:línea | Adaptación | Justificación | Consultado con la cátedra (fecha) |
|---|---|---|---|---|---|
| 22–23 | v_p = v + aΔt; r_p = r + vΔt | `Scheme.java:78` | — | — | |
| 22–23 | a(t+Δt) = f(r_p, v_p)/m | `Scheme.java:79` | — | — | |
| 22–23 | v = v + a(t+Δt)Δt; r = r + v(t+Δt)Δt | `Scheme.java:80-81` | Sin adaptación conocida | Verificado: r se corrige con la **v ya corregida** (línea 80 actualiza v antes que la 81) | |

## Adaptaciones generales
| Tema | Teoría / enunciado | Archivo:línea | Adaptación | Justificación | Consultado con la cátedra (fecha) |
|---|---|---|---|---|---|
| ECM | Suma sobre todos los pasos / n° de pasos (enunciado 1.2) | `OscillatorStudy.java:21-29` | Suma desde n=1 y divide por `steps` (t=0 excluido) | En t=0 el error es 0 por construcción | 22/10 (M1): aceptada como adaptación |
| N° de pasos | tf/dt | `OscillatorStudy.java:12-16` | round(tf/dt) cuando dt no divide a tf | La corrida termina a menos de Δt/2 de tf | 22/10 (M1): aceptada como adaptación; M3: aceptado el redondeo |
| Guardado cada Δt2 | Guardar si t/Δt2 = round(t/Δt2) (diapo 33) | `BilliardSimulator.java:93` | Contador entero: guardar cuando `paso % n == 0` | La comparación con t flotante es frágil; equivalente en aritmética exacta | 22/10 (M1): aceptada como adaptación |
| Paso inicial (D17) | — | análisis (no está en el código) | Un punto del ECM fuera de tendencia por el primer paso de Euler se descarta | Se aclara en la presentación | 22/10 (M1): aceptada como adaptación |
