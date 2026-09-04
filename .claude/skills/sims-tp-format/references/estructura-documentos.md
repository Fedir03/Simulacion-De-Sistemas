# Estructura de secciones — Informe vs Presentación

## Estructura común (mismas secciones, distinto volumen)

1. **Introducción** — motivación del fenómeno, contexto, qué se va a estudiar. Sin ecuaciones.
2. **Modelo** — SOLO ecuaciones abstractas de TODAS las variantes que se van a estudiar, definidas desde el principio (nunca diferir la definición de una variante a una sección posterior — ver correcciones-nash.md, es el error #1). Cero geometría, cero parámetros numéricos, cero nombres de clases.
3. **Implementación** — arquitectura del motor (diagrama, no pseudocódigo detallado si ya se explicó en un TP anterior — mencionar y no repetir). Formato de datos/reproducibilidad si aplica.
4. **Simulaciones** — parámetros fijos/variables con valores reales, geometría del sistema (con dibujo), definición matemática de los observables.
5. **Resultados** — una subsección por cada figura/estudio, siguiendo el orden: animación característica → evolución temporal (para justificar criterio de estado estacionario) → observable escalar vs parámetro variable. Solo descriptivo, nunca interpretativo.
6. **Conclusiones** — siempre aclarando a qué modelo/variante se refiere cada punto.
7. **Referencias** — sin numerar como sección, al final.

## Diferencias clave informe vs presentación

| | Informe | Presentación |
|---|---|---|
| Introducción+Modelo | secciones separadas, todo el detalle | fusionadas, máximo 3 diapositivas en total |
| Texto | párrafos completos, oraciones | frases cortas, sin redactar (fragmentos telegráficos) |
| Ecuaciones | todas, incluidas las intermedias (ej. fórmula de promedio vectorial con atan2) | solo las esenciales que distinguen variantes; omitir fórmulas intermedias de implementación |
| Figuras | pueden llevar figuras separadas por cada aspecto | resumir — la cátedra pidió explícitamente 1-2 figuras resumen para comparaciones entre modelos, no una por cada combinación |
| Animaciones | NO se embeben — solo un link explícito visible en el texto | SÍ se reproducen en vivo durante la exposición oral (con PowerPoint/Google Slides con video insertado, no como PDF) |

## Alcance de una figura combinada (multi-panel) vs figuras separadas

Si varias curvas/paneles necesitan distinguirse con texto (ej. "ρ=2", "ρ=4"), ese texto va en el **caption externo** de LaTeX o en la **leyenda dentro del área del gráfico** (leyenda ≠ título — una leyenda con series de colores está permitida, un título repitiendo qué se muestra no). Si distinguir requiere un título/subtítulo por panel dentro de la imagen, la solución es separar en figuras independientes, cada una con su propio caption — nunca dejar el título embebido dentro del área graficada.
