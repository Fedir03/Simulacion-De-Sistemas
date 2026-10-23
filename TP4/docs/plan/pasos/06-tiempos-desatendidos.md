# Paso 06 — Tiempos desatendidos

**Cuándo:** no empezado; pendiente, antes del vie 23 (de noche, con la máquina de D12 libre)
**Antes:** paso `05` · **Después:** paso `07`
**Todos los valores (dt, N, realizaciones, figuras, diapositivas):** `../DEFINICIONES.md`

## Estado al entrar
dt y dt2 cerrados. Máquina de D12 libre.

## Objetivo
Medir tiempos de ejecución sin ninguna otra carga (D12; D11 reemplazado).

## Tareas (en paralelo)
| Rol | Tarea | Entrega | Está hecho si |
|---|---|---|---|
| Fede | Lanzar 2.1.b (D7, D8: N = 100, 200, 300, 400, 500, 600, 714 × 10 rondas, con obstáculos en x₀=r) en una JVM calentada y reutilizada con `-Xms2g -Xmx2g` (D12): `control_tp3.sh antes`, `runtime_tp4.sh` (calentamiento 300:1,600:0.52, `order_seed` 20261025), `control_tp3.sh despues`, en la máquina de TP3. En la misma sesión, re-medir TP3 (tanda limpia, `outputs/runtime_tp3_limpia`, mismos argumentos que la tanda A). La tanda A (20/10) queda como referencia histórica: se midió con la máquina cargada (D12) | Outputs | Termina sin errores durante la noche |
| Todos | No usar la máquina de medición mientras corre | — | — |
| A · Ruckauf (auditoría de D30) | Revisar en otra computadora la colocación por grilla de Fede (D5) hasta el N máx medido, con semillas distintas | Informe de N máximo real | Ninguna colocación falla |
| D | Redactar S07–S09 con texto mínimo (las figuras F4 llegan mañana) | S07–S09 en el PDF | Revisión con la skill |

## Compuerta de salida
- [ ] 2.1.b y la tanda limpia de TP3 terminados
- [ ] Sin errores en los logs; controles de TP3 dentro de ±5 % de la referencia de la sesión limpia (~26–27 s, D12)
- [ ] F4 compara TP4 contra la tanda limpia de TP3 (si la limpia no se completa o no pasa el control, contra la tanda A con advertencia, D7)
- [ ] Las curvas de TP3 y TP4 se cruzan; si no, se extienden las dos (D7)

## Si se traba
Si la corrida no termina, se acorta a N ≤ 500 y se avisa en la diapositiva; no se descartan datos en silencio.
