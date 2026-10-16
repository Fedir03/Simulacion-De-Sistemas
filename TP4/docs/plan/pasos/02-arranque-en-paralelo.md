# Paso 02 — Arranque en paralelo

**Cuándo:** Vie 16/10 mañana (antes de la clase)
**Antes:** paso `01` · **Después:** paso `03`
**Todos los valores (dt, N, realizaciones, figuras, diapositivas):** `../DEFINICIONES.md`

## Estado al entrar
Definiciones cerradas el jueves (D1–D26, salvo las que van a la cátedra). Repo: no existe el módulo `tp4`. Fórmulas verificadas en `../referencia/FORMULAS-VERIFICADAS.md`.

## Objetivo
Cuatro frentes avanzando a la vez para llegar a la clase con algo corriendo.

## Tareas (en paralelo)
| Rol | Tarea | Entrega | Está hecho si |
|---|---|---|---|
| A | Crear módulo Maven `tp4` (pom, paquete `ar.edu.itba.sds.tp4` con Main, engine, models, io); copiar CIM de TP1 dentro (se usa con la grilla rearmada en cada paso, D25); esqueleto del motor S2 que compila | Módulo que compila con `mvn -q package` | Compila en carpeta limpia |
| B | Oscilador: solución analítica, 4 integradores (D17, fórmulas de `../referencia/FORMULAS-VERIFICADAS.md`), cálculo de ECM | Salida ECM por dt | Cada esquema reproduce la analítica a dt chico |
| C | Escribir `docs/formatos.md` (observables.txt, dynamic.txt, config con semilla) y runner; lanzar la medición de tiempos de TP3 **solo si** la máquina de D12 queda libre; si no, dejarlo para el sábado a la noche | `formatos.md` subido | Los otros roles lo leyeron |
| D | Copiar la plantilla de TP3 a TP4/presentacion/ (D27) y dejar el script de estilo de figuras (D28) listo; dibujar E1, E2 y E3 (DEFINICIONES.md §2) para que las marcas visuales del glosario existan; compilar la plantilla de TP4/presentacion/ con latexmk en una máquina con LaTeX y confirmar que no hay Overfull vbox | TP4/presentacion/ + script de estilo + E1–E3 | Se exporta a PDF sin Overfull vbox; E1–E3 en `presentacion/figuras/` |
| E | Imprimir la hoja de consultas del paso 03 y preparar el registro de respuestas | Hoja lista | Hoja impresa o abierta |

## Compuerta de salida
- [ ] Módulo `tp4` compila y está subido
- [ ] ECM del S1 calculado para al menos 2 esquemas
- [ ] `formatos.md` subido
- [ ] Esqueleto de la presentación exportable

## Si se traba
Si el módulo no compila antes de la clase, se va a la clase igual con las consultas.
