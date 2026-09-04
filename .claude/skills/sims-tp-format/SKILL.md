---
name: sims-tp-format
description: "Reglas de formato y contenido para informes y presentaciones de Simulación de Sistemas (72.25, ITBA) — compiladas de las guías oficiales de la cátedra, una clase de pre-entrega real, y correcciones reales de un grupo anterior (nota 5.5, TP2 2025Q2G10). Usar SIEMPRE que se arme, revise o corrija un informe o presentación de un TP de esta materia (TP2, TP3, TP4, TP5, final) — antes de escribir contenido nuevo, antes de dar por terminada una sección, y antes de la entrega final. Cubre estructura de secciones, qué va en Modelo vs Simulaciones, reglas de figuras (nunca título embebido, leyendas, escalas), metodología de desvío estándar correcta, notación matemática, y checklist de entrega (nombres de archivo, alcance del ZIP de código)."
---

# Formato de informes y presentaciones — Simulación de Sistemas (72.25, ITBA)

Reglas reunidas de: guías oficiales de la cátedra (GuiaInformes.pdf, GuiaPresentaciones.pdf, Formato_Informes.pdf, Formato_Presentaciones.pdf), una clase virtual de pre-entrega real donde la cátedra revisó presentaciones de otros grupos en vivo, y las correcciones reales que recibió un TP2 de un cuatrimestre anterior (nota 5.5).

**Regla de oro:** informe y presentación comparten las mismas secciones y el mismo contenido de fondo, pero NO el mismo volumen de texto ni el mismo nivel de detalle. La presentación es visual y breve (13 minutos de exposición oral); el informe es el documento completo y autocontenido. Nunca copiar un párrafo del informe a una diapositiva sin comprimirlo a frases cortas.

## Antes de escribir contenido nuevo

1. Leé `references/estructura-documentos.md` para saber en qué sección va cada cosa (es más fácil equivocarse de lo que parece — ver el error más común de todos abajo).
2. Si vas a insertar una figura o gráfico, leé `references/reglas-figuras.md` ANTES de generarla — varias reglas (título nunca embebido, leyenda adentro) son mucho más baratas de aplicar en el script de graficado que de corregir después.
3. Si el TP calcula un desvío estándar o barra de error combinando varias corridas/repeticiones, leé `references/metodologia-estadistica.md` — hay un error metodológico común y grave que la cátedra ya marcó explícitamente en una clase real.

## El error más común: mezclar "Modelo" con "Simulaciones"

- **Modelo** = SOLO las ecuaciones abstractas del fenómeno. Cero geometría, cero parámetros numéricos concretos, cero nombres de clases o de sistema particular.
- **Simulaciones** = el sistema particular que se estudia: parámetros fijos/variables con sus valores reales, geometría con dibujo, definición de los observables que se van a medir.

Ejemplo de la cátedra: si simularan un sistema gravitatorio, "Modelo" es solo F=Gm₁m₂/r² — nada de "viaje a la Luna" ni "sistema solar", eso es Simulaciones.

## Reglas que rompen la nota más seguido (resumen — detalle completo en las referencias)

- **Nunca interpretar en Resultados.** Solo descriptivo ("hay un mínimo en X"), nunca explicativo ("hay un mínimo porque...") salvo que se diseñe un experimento específico para validar esa explicación.
- **Nunca título/subtítulo embebido dentro de una figura** (ni siquiera para distinguir paneles de una figura combinada — si hace falta distinguir, son figuras separadas con su propio caption, no una figura con texto interno).
- **Definir todas las variantes del modelo desde el principio**, nunca diferirlas a una sección posterior — es el error #1 que le costó puntos al grupo de referencia.
- **En conclusiones, siempre aclarar a qué variante/modelo se refiere cada afirmación** — nunca asumir que todas las variantes responden igual a un mismo cambio de parámetro.
- **Parámetros sin unidades** si el modelo es adimensional (confirmarlo con la cátedra si hay dudas, no asumir).
- Ver `references/reglas-figuras.md` para todo lo de escalas de ejes, leyendas, paleta de colores, animaciones vivo-vs-entrega.

## Checklist de entrega — ver `references/checklist-entrega.md`

Nombres de archivo exactos, qué va en el ZIP de código (mucho menos de lo que parece), y la distinción entre el PDF que se entrega (sin animaciones embebidas, solo links) y la presentación que se expone en vivo.

## Correcciones reales de un grupo anterior (nota 5.5)

Ver `references/correcciones-nash.md` para la lista completa, con contexto de por qué cada corrección importa — no son reglas abstractas, son errores reales que ya le costaron puntos a alguien con este mismo enunciado tipo.
