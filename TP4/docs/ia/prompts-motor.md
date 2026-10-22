# Prompts enviados al agente para construir el motor (D31)

Anexo de la declaración de uso de IA (anuncio de la cátedra "Criterios de Evaluación TP4 y TP5").

**Reglas:**
- Solo prompts usados para construir el **motor**: Sistema 1, Sistema 2, CIM, grilla y formatos de entrada/salida. No van los de análisis, figuras, presentación ni plan.
- Cada entrada lleva fecha, autor y una marca: **"textual"** (copiado tal cual, sin corregir ni resumir) o **"reconstruido"** (reconstruido a partir del plan, cuando no se guardó el original).
- No hace falta cargar todos los prompts usados: alcanza con los que muestran cómo se construyó cada parte del motor.
- Cada integrante completa su sección.
- Va como apéndice después de "Muchas gracias" (D31). Si va dentro del PDF o aparte: consulta (a) del paso 09.

Plantilla por entrada:

```
### AAAA-MM-DD · <autor> · <parte del motor> · <agente/modelo> · textual | reconstruido
<prompt (textual o reconstruido)>
```

## Fede

### 2026-10-20 · Fede · CIM, grilla y N máx · Claude Code
Reconstruido por el agente a partir de la conversación; no es el texto original del prompt.

Pedido: copiar del TP1 al módulo TP4 `CellIndexMethod`, `NeighborFinder` y `Particle`, y revisar qué devuelve el CIM; agregar dentro del CIM el corrimiento +R y la validación |r| ≤ R; escribir el script que mide el N máximo con la grilla (cuadrada y hexagonal, medido con código y no con cuentas teóricas); escribir el test CIM contra fuerza bruta con la misma semilla, comparando los pares de contacto en cada paso. Pedido explícito: explicar todo el código aplicado.

Decisiones tomadas ante las preguntas del agente:
- Test de vuelo libre ahora (sin fuerzas, con partículas en x<0 e y<0, pegadas a la pared, en bordes de celda y superpuestas); la corrida completa con el S2 queda pendiente en el paso 04.
- Medir las dos redes, con la hexagonal por defecto; paquete `engine.cim`.
- Radio del obstáculo tomado del obstáculo, no supuesto igual a r; al menos dos anclajes de la red; L = 2R con tolerancia de 1e-12.
- Medir el tiempo del test y bajar los pasos si tarda; no dar los tests por verdes si Maven no corre.
- Distancias de −1e-17 con separación 0: redondeo, no solapamiento.
- Grilla elegida con la medición: hex, s = 2r + 0,1 mm, sitio en el origen (N máx 721 / 714).

### 2026-10-20 · Fede · Grilla del TP3 y medición de tiempos (2.1.b) · Claude Code · reconstruido
Reconstruido por el agente a partir de la conversación; no es el texto original del prompt.

Pedido: leer el generador de escenarios del TP3 (`StageGeneration` y lo que lo usa) y proponer un plan corto para que el TP3 genere la condición inicial con la misma grilla que el TP4 (`GridPlacement`: hexagonal, sitio en el origen, s = 2r + 0,1 mm) y volver a correr el TP3 en esta computadora. Condiciones: pedir confirmación antes de tocar código del TP3 que no sea el generador; misma máquina, sin otras cargas, con calentamiento descartado; corrida por tandas y reanudable; salidas fuera del repo o ignoradas por git; avisar en vez de decidir si la grilla contradice al TP3 original; sin commit ni push.

Decisiones tomadas ante las preguntas del agente:
- Ancla: se midieron las dos con código (`center` 703 sitios, `corner` 737). Se eligió `corner` con un margen de 0,1 mm a las paredes, porque con margen 0 había 19–23 eventos de pared y 1–2 goles a t = 0 por semilla.
- Mesa vacía, como el estudio de tiempo original del TP3.
- Autorizado `Main` del TP3 (`--placement`, `--grid-anchor`, `grid-nmax`).
- Medición en una sola JVM calentada y reutilizada, en vez de una JVM por corrida: clase nueva en el TP3, reutilizable para el S2 del TP4. Calentamiento hasta variar menos del 5 %, `System.gc()` entre corridas, orden mezclado, heap fijo `-Xms1g -Xmx1g` y corrida de control (N = 400, semilla 1) con el criterio de media ± 2σ.
- Tope en N = 600, por el costo medido: N = 700 tarda unos 53 min y N = 737 unas 2,3 h por corrida (φ ≈ 0,87).

## Federico Ruckauf

### 2026-10-16 · Federico Ruckauf · Módulo TP4 y Sistema 1 · Claude Code (Opus 5.5) · reconstruido
Reconstruido por el agente a partir de la conversación; no es el texto original del prompt.

Pedido: leer el enunciado, Teórica 4 y el plan del grupo (`docs/plan/`: `DEFINICIONES.md`, `referencia/FORMULAS-VERIFICADAS.md`, `referencia/PLAN.md` y los pasos) y resumir lo entendido antes de escribir código. Después, crear el módulo Maven `TP4` con la estructura de TP3 e implementar el Sistema 1 a partir de lo que el grupo ya había definido: las fórmulas de los 4 esquemas verificadas contra las diapositivas, la estimación de la velocidad para la fuerza −kx − γv propuesta en D17, Δt²/(2m) en Velocity Verlet (D19) y el barrido de Δt y la definición de ECM de D18. Pedido explícito: que la estimación de la velocidad no quede fija en el código, sino como opción fácil de cambiar, aunque la intención es no cambiarla.

Decisiones tomadas en la conversación:
- Empezar por el módulo y el Sistema 1, porque no depende de nada más y da resultados para llevar a la consulta Q6 en la clase.
- D17 como valor por defecto, expuesto como opciones con nombre (enums y flags de CLI: `--verlet-velocity backward|euler`, `--vv-velocity euler|half-step`).
- Opción propuesta por el agente y aceptada: `--acceleration-update predicted|corrected`, para decidir si a(t+Δt) en Beeman y Velocity Verlet se re-evalúa con la velocidad corregida. Por defecto `predicted`, como en las diapos 17 y 20.
- ECM sobre los pasos 1..n (t = 0 no se cuenta), con n = round(tf/Δt).
- Tests: la analítica se reproduce a Δt chico; pendientes del ECM (4 para Beeman y Velocity Verlet, 2 para Verlet con v hacia atrás y para Euler PC); Verlet y Velocity Verlet coinciden sin amortiguamiento.
- Hallazgo que se llevó a la consulta Q6: con v predicha por Euler, Verlet pasa a pendiente 4 e iguala a Velocity Verlet, así que la elección de la velocidad cambia cuál esquema resulta mejor.
- Resultado: commits 214678c (módulo) y 38e890b (Sistema 1).

## Lolo

_(sin entradas)_
