# Correcciones reales de la cátedra — TP3 (nota 6,5, recibidas 03/10/2026)

Fuente: `TPE3 - Correcciones.txt` (Drive, carpeta U3). Grupo 2 (2026Q2G02). Misma nota que TP2: la cátedra valoró la exploración, pero la forma de presentarla restó. Máxima prioridad junto con correcciones-reales-tp2.md.

## Comentario general (el más importante)
Probaron muchísimas configuraciones ("lo cual está muy bueno"), pero con tan poco tiempo se termina entendiendo poco el trabajo. **Menos ejemplos con más dedicación.** Si se quiere mostrar todo: mandar el detalle a un apéndice después del final de la presentación, o hacer un "pantallazo" de otras configuraciones mostrando solo sus esquemas.

## Reglas generales (con la diapositiva donde se originó)
1. **Introducción = fenómenos y metodología en general, sin el sistema particular ni el objetivo** (D3). El sistema y el objetivo vienen después.
2. **No mezclar elementos del sistema particular en la explicación del método general** (D4: ni el arco ni los estados fresco/usado en la explicación de event-driven MD). Terminología precisa: "tiempo hasta la colisión", no "tiempo de contacto" (sugiere duración del contacto).
3. **Definir cada símbolo una sola vez** (D5/D6): una vez dicho Δr o Δv, no volver a explicitarlo en la diapositiva siguiente.
4. **No explicar técnicas que se dan por sabidas** (D9, invalidación perezosa), salvo que se hayan aprendido explícitamente para ese TP.
5. **Barridos de saturación/escalado: tomar más partículas** (D16); la cátedra contó en clase la solución (grilla hexagonal).
6. **Un recuadro, un tipo de contenido** (D17): no mezclar parámetros del sistema, resultados de la simulación y descripción de la animación en el mismo recuadro gris. Los resultados van después, con un gráfico.
7. **Elegir valores/radios que permitan ver más datos** (D18) y **explicar en la propia diapositiva cualquier punto faltante** (D18: ¿y el dato de x=90 cm?).
8. **Orden de un barrido: (1) esquema → (2) curvas Fu(t) para distintos valores del parámetro → (3) observable (t90) vs parámetro** (D18-D20 estaban en orden raro).
9. **Todo parámetro nuevo lleva ayuda visual en el esquema** (D22 `a`, D24 `Rf`). Refuerza la regla de reglas-figuras.md.
10. **Declarar siempre qué queda fijo y qué varía en cada barrido** (D23: "¿K cuánto vale? ¿Está fijo o varía si varío s?").
11. **Si hubo un ajuste, decir explícitamente con qué método** (D31: faltó mostrar que se hizo con el método de Teórica 0).

## Código / motor
- Al terminar, el motor avanzaba todas las partículas hasta tmax y escribía ese estado, **que no es un evento** (CollisionSimulator.java líneas 94-95). Lección: nunca escribir al output un estado que no corresponda a un tiempo propio del método.
- Observable: cada cuadro sale del motor con `Ng=` y `Fu=` en el encabezado (StageFile.java línea 26) → OK.
- Visualización: OK.

## Checklist rápido antes de entregar un TP
- [ ] ¿Cada barrido sigue esquema → curvas temporales → observable vs parámetro?
- [ ] ¿Cada parámetro nuevo está marcado en el esquema y se dice si es fijo o variable?
- [ ] ¿La introducción es general (sin el sistema)?
- [ ] ¿Algún símbolo definido dos veces? ¿Alguna técnica conocida explicada de más?
- [ ] ¿Algún recuadro mezcla tipos de contenido?
- [ ] ¿Los puntos faltantes del barrido están explicados?
- [ ] ¿El método de ajuste está nombrado?
- [ ] ¿El output tiene estados que no corresponden al método?
