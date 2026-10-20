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

## Federico Ruckauf

_(sin entradas)_

> **Pendiente:** preguntarle a Federico Ruckauf por los prompts usados para el Sistema 1 (commit 38e890b).

## Lolo

_(sin entradas)_
