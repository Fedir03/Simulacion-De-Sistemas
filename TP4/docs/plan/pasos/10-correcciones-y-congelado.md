# Paso 10 — Correcciones y congelado

**Cuándo:** Mar 20/10
**Antes:** paso `09` · **Después:** paso `11`
**Todos los valores (dt, N, realizaciones, figuras, diapositivas):** `../DEFINICIONES.md`

## Estado al entrar
Feedback aplicado en una lista. Motor todavía modificable.

## Objetivo
Resolver el feedback, decidir D22 (mapa de calor) y congelar el motor esa noche.

## Tareas (en paralelo)
| Rol | Tarea | Entrega | Está hecho si |
|---|---|---|---|
| Todos | Aplicar la lista del lunes | Lista cerrada | Cada ítem tachado |
| E · Fede | Decidir D22 con el estado real | D22 en `../DEFINICIONES.md` | — |
| Todos | Cerrar la auditoría cruzada (D30): cada revisor completa sus filas en `../auditoria-codigo.md` (Ruckauf → Fede, Fede → Lolo, Lolo → Ruckauf) | `../auditoria-codigo.md` | Todas las filas auditadas, sin 🔴 abiertos |
| Todos | Guardar los prompts del motor (D31) en `../../ia/prompts-motor.md`, cada entrada marcada "textual" o "reconstruido" (no hace falta cargar todos); Fede le pide a Ruckauf los del Sistema 1. Van como apéndice después de "Muchas gracias" (D31) | Archivo con entradas | Cada entrada tiene fecha, autor y marca textual/reconstruido |
| E · Fede | Escribir `TP4/README.md` chico (D26: compilar y un comando de ejemplo que corra de verdad; config de ejemplo mínimo en el ZIP o comando con todos los argumentos) y probarlo: alguien que no escribió el motor compila y corre solo con ese README | `TP4/README.md` | Otra persona compila y corre solo con ese README |
| E · Fede (audita Ruckauf) | Escribir `tools/build_zip.sh` y `.ps1`; construir el ZIP en carpeta aislada y compilarlo | ZIP < 100 KB | Compila y corre desde carpeta vacía |
| A · Ruckauf | **Congelar el motor a la noche**: tag en git, solo con la auditoría completa | Tag `motor-final` | Desde acá solo cambian scripts de figuras y texto |

## Compuerta de salida
- [ ] Auditoría cruzada completa (D30) **antes** de congelar
- [ ] Prompts del motor guardados (D31)
- [ ] Motor congelado con tag
- [ ] ZIP probado
- [ ] Feedback aplicado

## Si se traba
Si hay un bug del motor el miércoles, se arregla, se re-corren los estudios afectados y se avisa a todos.
