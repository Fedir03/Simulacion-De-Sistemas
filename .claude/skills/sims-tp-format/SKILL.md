---
name: "sims-tp-format"
description: "Reglas de formato y contenido para informes y presentaciones de Simulación de Sistemas (72.25, ITBA): guías de la cátedra, clase de pre-entrega, correcciones de un grupo anterior (TP2 5,5; TP4 7), del propio grupo (TP2 6,5; TP3 6,5) y mail de la cátedra sobre IA. Usar SIEMPRE al armar, revisar o corregir un informe o presentación de un TP (TP2 a TP5, final): antes de escribir contenido nuevo, al cerrar una sección y antes de la entrega final."
---

# Formato de informes y presentaciones — Simulación de Sistemas (72.25, ITBA)

Reglas reunidas de: guías oficiales de la cátedra (GuiaInformes.pdf, GuiaPresentaciones.pdf, Formato_Informes.pdf, Formato_Presentaciones.pdf), una clase virtual de pre-entrega real donde la cátedra revisó presentaciones de otros grupos en vivo, las correcciones reales que recibió un TP2 de un cuatrimestre anterior (nota 5,5), las correcciones reales del TP4 de ese mismo grupo (G10, nota 7), las correcciones reales del propio TP2 de este grupo (nota 6,5), las correcciones oficiales del TP3 de este grupo (nota 6,5), y un mail de la cátedra sobre uso de IA en la preparación de presentaciones.

**Regla de oro:** informe y presentación comparten las mismas secciones y el mismo contenido de fondo, pero NO el mismo volumen de texto ni el mismo nivel de detalle. La presentación es visual y breve (13 minutos de exposición oral); el informe es el documento completo y autocontenido. Nunca copiar un párrafo del informe a una diapositiva sin comprimirlo a frases cortas.

## Modo revisión por sección

Cuando se pida revisar una sección en borrador (Simulaciones, un estudio de Resultados, Conclusiones, etc.), actuar como revisor que no escribió el texto: devolver SOLO una lista de ítems incumplidos, cada uno con la regla que rompe y dónde está, sin reescribir la sección. Decide la persona del grupo qué se arregla. Antes de la entrega, repetir sobre el PDF completo.

## Antes de escribir contenido nuevo

1. Leé `references/estructura-documentos.md` para saber en qué sección va cada cosa (es más fácil equivocarse de lo que parece — ver el error más común de todos abajo).
2. Si vas a insertar una figura o gráfico, leé `references/reglas-figuras.md` ANTES de generarla — varias reglas (título nunca embebido, leyenda adentro, tamaño de letra) son mucho más baratas de aplicar en el script de graficado que de corregir después.
3. Si el TP calcula un desvío estándar o barra de error combinando varias corridas/repeticiones, leé `references/metodologia-estadistica.md` ANTES de preguntarle a la cátedra — hay un error metodológico común y grave que la cátedra ya marcó explícitamente en una clase real, y puede ya estar resuelto ahí sin necesidad de esperar una respuesta.

Si alguna de estas referencias no está en la carpeta `references/` de la skill instalada, buscarla en `.claude/skills/sims-tp-format/references/` del repo del grupo, y si tampoco está, avisar en vez de asumir su contenido.

## El error más común: mezclar "Modelo" con "Simulaciones"

- **Modelo** = SOLO las ecuaciones abstractas del fenómeno. Cero geometría, cero parámetros numéricos concretos, cero nombres de clases o de sistema particular.
- **Simulaciones** = el sistema particular que se estudia: parámetros fijos/variables con sus valores reales, geometría con dibujo, definición de los observables que se van a medir.

Ejemplo de la cátedra: si simularan un sistema gravitatorio, "Modelo" es solo F=Gm₁m₂/r² — nada de "viaje a la Luna" ni "sistema solar", eso es Simulaciones.

## Reglas que rompen la nota más seguido (resumen — detalle completo en las referencias)

- **Nunca interpretar en Resultados.** Solo descriptivo ("hay un mínimo en X"), nunca explicativo ("hay un mínimo porque...") salvo que se diseñe un experimento específico para validar esa explicación.
- **Nunca título/subtítulo embebido dentro de una figura** (ni siquiera para distinguir paneles de una figura combinada — si hace falta distinguir, son figuras separadas con su propio caption, no una figura con texto interno).
- **Definir todas las variantes del modelo desde el principio**, nunca diferirlas a una sección posterior — es el error #1 que le costó puntos al grupo de referencia.
- **Definir explícitamente TODOS los observables que se muestran**, incluso los que parecen obvios por contexto — al propio grupo le marcaron un observable sin definir en TP2.
- **En conclusiones, siempre aclarar a qué variante/modelo se refiere cada afirmación** — nunca asumir que todas las variantes responden igual a un mismo cambio de parámetro.
- **Parámetros sin unidades** si el modelo es adimensional (confirmarlo con la cátedra si hay dudas, no asumir).
- **No mostrar más ejemplos de los necesarios.** Si hay muchas variantes de un mismo estudio (muchas densidades, muchos radios, etc.), elegir 1 (o a lo sumo 2) representativa para mostrar animación/evolución temporal — no repetir la secuencia completa para cada variante. La cátedra lo marcó dos veces en el propio TP2: "podían elegir solo 1 para mostrar" y "no hace falta mostrar 3 evoluciones, basta con 1 o 2 típicas". Esta regla convive con la de TP4: una animación por estudio (de 1 o 2 casos representativos) NO la viola; lo que la viola es mostrar una animación o evolución por cada valor del barrido.
- **No armar una figura que no fue pedida**, y menos con menos puntos de los que hacen falta para sostener la afirmación que hace (ej. llamar "barrido" a algo con 2-3 valores).
- **Consistencia de representación entre figuras del mismo tipo de dato** — si una figura de una comparación lleva barras de error en ambos ejes, las demás comparaciones del mismo tipo deberían seguir el mismo criterio, salvo razón explícita.
- **Cada figura de resultados debe indicar, al costado o en su caption/parambox, con qué parámetros/configuración/seed se generó** — no asumir que se sobreentiende por el contexto de la diapo.
- **Cada dato repetitivo (como el número de realizaciones) se dice comprimido una sola vez**, no repetido en cada diapositiva que lo use (ej. "Nro. de realizaciones: 5" una vez, no una frase larga cada vez).
- Ver `references/reglas-figuras.md` para todo lo de escalas de ejes, leyendas, paleta de colores, animaciones vivo-vs-entrega.

## Correcciones oficiales del TP3 (nota 6,5) — se mantienen en TP4 y siguientes

- **Pocos ejemplos con más dedicación**: menos estudios mostrados en detalle; los secundarios van al apéndice o solo como esquema.
- **La introducción habla del fenómeno y del método general**, nunca del sistema particular (nada de billar, obstáculos ni partículas frescas/usadas).
- **Terminología exacta**: armar un glosario del grupo antes de escribir y revisar cada término contra la teórica.
- **Cada símbolo se define UNA sola vez**; no redefinirlo en otra diapositiva.
- **No re-explicar técnicas ya conocidas de TPs anteriores** (ej. Cell Index Method): se mencionan y se sigue.
- **Saturación con pocas partículas**: si un observable satura (ej. Fu(tmax), t90 vs densidad), usar más partículas. Otros grupos llenaron el dominio con N > 1000 en TP3 y la cátedra lo marcó como bien analizado: llenar el dominio lo más posible.
- **Una caja gris = un tipo de contenido.**
- **Valores de barrido que dejen ver la tendencia**, y toda ausencia (punto faltante, observable que no llega a su umbral) se explica en la diapositiva.
- **Orden de cada estudio**: esquema → (en TP4, animación de un caso representativo, ver abajo) → curvas temporales para varios valores → observable vs parámetro.
- **Todo parámetro nuevo se marca en el esquema** la primera vez que aparece.
- **Cada estudio dice qué se fija y qué se varía.**
- **Los métodos de ajuste se declaran** (ej. el de la Teórica 0).
- **El estado de salida debe caer en los tiempos que define el método** (ej. múltiplos de dt2); nunca un estado extra al final fuera de ese muestreo.

## Reglas específicas de TP4 (dinámica molecular por paso temporal)

- **Δt es un parámetro del método, no una variable de estudio del sistema**: se estudia y se elige en su propia sección (2.1.a), no mezclado con las variables físicas.
- **El Sistema 1 va en UNA sola diapositiva** (ECM vs Δt, ejes log-log, los 4 esquemas como mínimo), con la respuesta a "cuál es el mejor esquema".
- **Los tiempos de ejecución van solo en Resultados/Conclusiones**, nunca en Simulaciones/Parámetros. Se mide el tiempo de cómputo por integrador (oscilador) y se dice cuál es el más rápido, en la respuesta oral o en Conclusiones; no como figura extra en la diapositiva del Sistema 1.
- **Declarar cómo se estimó la velocidad** en los esquemas cuando la fuerza depende de ella (Verlet, Velocity Verlet) y qué variante de Beeman se usó.
- **Animaciones**: cada estudio del Sistema 2 lleva una animación de un caso representativo, salvo 2.1.a (estudio de Δt), que no lleva ninguna. Orden dentro de cada estudio: esquema → animación → evolución temporal → observable vs parámetro.
- **La última diapositiva lleva la declaración de uso de IA**.
- **El ZIP lleva solo lo necesario para compilar y correr el motor final** (< 100 KB): `pom.xml`, `src/main/java` del módulo TP4 (Main, engine, models, io) y las clases de TP1 que use (ej. CIM, copiadas dentro del módulo para que compile solo). Se genera con script (`tools/build_zip.sh` / `tools/build_zip.ps1`) y se prueba descomprimiéndolo y compilándolo en una carpeta limpia.

## Correcciones del TP4 de Nash (G10, nota 7)

Feedback real sobre el TP4 del mismo grupo de referencia del TP2; aplica tal cual a nuestro TP4.

- **Escribir menos**: texto mínimo en diapositivas e informe; partir de la figura.
- **Sin animación para el estudio de Δt** (2.1.a): no aporta y se marcó como sobrante.
- **Decir qué integrador tuvo mejor tiempo de cómputo**, no solo cuál tuvo menor error.
- **Animaciones de casos representativos de cada estudio del Sistema 2**: son necesarias para verificar que la implementación es correcta; su ausencia se penaliza.
- **No repetir Δt en cada página**: Δt se elige en 2.1.a, se declara una sola vez y se aclara después solo cuando cambia.
- **Las conclusiones sobre Δt no forman parte de las conclusiones del estudio**: Δt es parámetro del método; su conclusión va en su propia sección y no se mezcla con las conclusiones físicas de los estudios.

## Etiquetas y texto que "suenan generados por IA"

La cátedra señaló explícitamente, en una corrección real de este mismo grupo, una etiqueta de eje por sonar "nombrada por la IA": demasiado descriptiva/técnica (ej. "Tiempo t = paso × Δt [unidades de tiempo del modelo, Δt = 1]") en vez de una decisión humana simple ("tiempo (s)" o "tiempo (pasos)"). Esto aplica a cualquier texto generado con ayuda de un agente:

- Etiquetas de ejes: cortas, como las escribiría uno mismo a mano. Nunca meter unidades/aclaraciones/fórmulas completas en la etiqueta si un pie de figura o el propio eje puede decirlo más simple.
- Texto de diapositivas: mínimo, a partir de la figura — nunca un párrafo generado y luego recortado. Si suena a redacción genérica o repite lo que ya muestra la figura sin agregar nada, sobra.
- Antes de aceptar cualquier texto/eje/leyenda que generó un agente, revisarlo con criterio humano y reescribirlo si suena robótico — la cátedra activamente lo nota y lo señala en las correcciones.

## Uso de agentes de IA — pauta de la cátedra (mail, no solo la guía de referencia)

- El objetivo de la materia no es el resultado final (código, PDF) sino el proceso: la elección de tiempo hasta el estacionario, la forma de calcular promedios/barras de error, la metodología para aplicar CIM, observables extra — eso tiene que salir del propio análisis, no delegarse entero a un agente.
- "Poco texto en las diapositivas" significa partir de la figura y agregar el mínimo texto para identificar los puntos clave — el camino inverso (dejar que el agente genere todo el texto y después recortarlo) no cumple este objetivo aunque el resultado visual sea similar.
- Ir a las clases de "discusión de resultados" antes de la presentación final — la cátedra espera haber visto avances discutidos antes del día de la entrega, no solo un resultado terminado.
- Un agente puede ayudar con código, gráficos más claros, síntesis — pero la producción tiene que partir de la propia comprensión primero, no al revés.

## Verificar el orden algorítmico contra la letra exacta del enunciado, nunca contra intuición física

El hallazgo más grave de las correcciones reales de este grupo fue un bug de orden temporal en el motor: el código movía todas las partículas antes de recalcular vecinos, cuando el enunciado definía la actualización a partir del vecindario en la posición *anterior*. El código "parecía" físicamente razonable pero no seguía la letra exacta del enunciado. Antes de aceptar cualquier orden de operaciones en el motor (incluidas propuestas de compañeros de grupo para reordenar guardado de estado, resolución de colisiones, etc.), comparar línea por línea contra la definición textual del enunciado — nunca aprobar un reorden solo porque "tiene sentido físicamente".

## Checklist de entrega — ver `references/checklist-entrega.md`

Nombres de archivo exactos, qué va en el ZIP de código (mucho menos de lo que parece, pero SÍ debe incluir todo el código usado para generar animaciones/figuras a partir de los outputs primarios, no solo el motor, salvo que el enunciado del TP diga lo contrario, como en TP4: solo lo necesario para compilar y correr el motor final), y la distinción entre el PDF que se entrega (sin animaciones embebidas, solo links) y la presentación que se expone en vivo.

## No permitir ningún tipo de interpolación en TPs de Event-Driven Simulation

Cuando el TP es una simulación dirigida por eventos (Event-Driven Simulation), la cátedra prohíbe explícitamente cualquier interpolación, búsqueda o uso de tiempos que no correspondan a eventos reales — ni para animar, ni para ningún otro fin (calcular observables, samplear, etc.). Esto aplica a TODO el código, no solo al motor: revisar también scripts de animación y de post-procesamiento de figuras. El código usado para generar animaciones debe entregarse junto con el motor, precisamente porque la cátedra ya vio este error en otros grupos.

## Demo en vivo: verificar el requisito end-to-end, no solo en el componente aislado

Si la cátedra pide una demo en vivo con salida específica en consola (ej. imprimir cada conversión y el resultado final), no alcanza con verificar que el componente que genera esa salida funciona aislado (ej. corriendo el motor directamente) — hay que verificar que el script/wrapper que efectivamente se va a usar en la demo real no la esté suprimiendo (ej. redirigiendo a /dev/null para no ensuciar una ejecución en paralelo). Probar siempre el comando exacto que se va a correr el día de la demo.

## Correcciones reales de un grupo anterior (TP2, nota 5,5)

Ver `references/correcciones-nash.md` para la lista completa, con contexto de por qué cada corrección importa — no son reglas abstractas, son errores reales que ya le costaron puntos a alguien con este mismo enunciado tipo. Las del TP4 de ese grupo (nota 7) están resumidas arriba, en su propia sección.

## Correcciones reales del propio TP2 (nota 6,5)

Ver `references/correcciones-reales-tp2.md` — feedback directo sobre trabajo propio, máxima prioridad. Incluye el hallazgo más importante de toda la skill: el orden de un algoritmo se verifica contra la letra exacta del enunciado, nunca contra "lo que parece físicamente razonable". Si el archivo no está en `references/`, está en `.claude/skills/sims-tp-format/references/` del repo del grupo.

## Entregables: no asumir que se repiten de un TP a otro

TP2 pedía informe, TP3 no. Releer la lista de entregables de cada enunciado nuevo — ver `references/checklist-entrega.md`.

## Referencias adicionales

- `references/correcciones-reales-tp3.md`: lecciones de proceso del TP3.
- `references/correcciones-reales-tp3-nota.md`: devolución oficial del TP3 (nota 6,5).
- `references/uso-de-agentes-ia.md`: pauta de la cátedra sobre el uso de agentes de código.
