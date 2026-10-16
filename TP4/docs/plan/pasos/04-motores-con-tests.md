# Paso 04 — Motores con tests

**Cuándo:** Vie 16 tarde → Sáb 17 mediodía
**Antes:** paso `03` · **Después:** paso `05`
**Todos los valores (dt, N, realizaciones, figuras, diapositivas):** `../DEFINICIONES.md`

## Estado al entrar
Respuestas de la cátedra anotadas; D5, D6, D17, D19 cerradas. Módulo `tp4` existe; S1 con 2+ esquemas.

## Objetivo
Que los dos motores pasen los tests de `../referencia/PLAN.md` §7 antes de correr cualquier experimento.

## Tareas (en paralelo)
| Rol | Tarea | Entrega | Está hecho si |
|---|---|---|---|
| A | Motor S2 completo: Verlet con primer paso por Euler, CIM, pared imagen recalculada en cada dt, obstáculos fijos, fresca→usada, salida en múltiplos de dt2, RSA y hexagonal con semilla | Tests del S2 en verde | CIM = fuerza bruta; una partícula conserva L y |v|; misma semilla = mismo archivo (cmp) |
| B | Los 4 esquemas terminados, F1 (ECM vs dt log-log) y la respuesta a 'cuál es el mejor'; medir tiempo de cómputo por integrador | F1 + una frase de respuesta | Pendientes coherentes con el orden esperado de cada esquema |
| C | Runner: lee una lista de casos (estudio, N, x₀, semilla), lanza, guarda en `outputs/<estudio>/<caso>/seed<k>/` | Runner que corre 1 caso | Reproduce el mismo output con la misma semilla |
| D | Redactar S01–S05 y S06 con F1; checklist de `../referencia/CORRECCIONES-CHECKS.md` aplicado a esas diapositivas | S01–S06 en el PDF | Revisión con la skill (modo revisión por sección) sin ítems abiertos |
| E | Tests de entrega: demo de punta a punta, comando exacto anotado | Comando en `docs/` | Corre desde carpeta limpia |

## Compuerta de salida
- [ ] Tests de §7 (S2) todos en verde, incluido CIM vs fuerza bruta
- [ ] F1 y respuesta de S1 listas
- [ ] Runner reproducible
- [ ] S01–S06 revisadas por la skill

## Si se traba
Si a las 18hs del sábado el S2 no pasa los tests, se activa el plan B del paso 08.
