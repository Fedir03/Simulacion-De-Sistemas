# Correcciones recibidas → check en TP4

## TP2 (nota 6,5)
- Leyenda con letra chica → leyenda afuera o fuente ≥ 10 pt efectivos; mirar el PDF a tamaño real.
- Tiempos de ejecución en Simulaciones → van solo en Resultados/Conclusiones (2.1.b).
- Orden del algoritmo distinto al enunciado → revisor compara el motor contra la letra del enunciado y de Teórica 4; ningún reorden "porque tiene sentido físico".
- Etiquetas que suenan a IA → cortas y escritas a mano ("tiempo (s)", "Fu").
- Parámetros repetidos en cada gráfico → se dicen una vez; en el gráfico solo lo que varía.
- Explicaciones sin evidencia → Resultados solo descriptivos.
- Observable sin definir → definir en Simulaciones todos: Fu, Nu, t90, t100, energía, f(v), ECM, densidad, tiempo de ejecución.
- Desvío mal calculado → bolsa de datos para promedios sobre partículas; σ vs σ/√N por caso.
- Demasiados ejemplos → 1 (a lo sumo 2) corridas representativas por estudio.

## Grupo Nash (5,5)
- Variantes definidas tarde → Modelo define ambos sistemas y los 4 integradores desde el principio.
- Títulos genéricos → cada título dice qué muestra.
- Orden de resultados → animación → evolución temporal → observable vs parámetro (excepto 2.1.a, el estudio de dt, que no lleva animación).
- No mostrar fórmulas generales de media/desvío; figuras numeradas y citadas; leyenda solo con lo que varía; URL de animación visible en el PDF; animaciones colgadas de cada estudio; conclusiones nombran variante y parámetro; ZIP solo con el código fuente Java del motor (pom, Main, engine, models, io y solo las clases de TP1 que use) más el README chico (D26), generado por script.

## TP3 (nota 6,5)
- Pocos ejemplos con más dedicación; intro sin el sistema particular (sin billar, obstáculos ni fresca/usada); terminología revisada con Teórica 4; no re-explicar CIM; una caja gris = un tipo de contenido.
- Símbolos: cada símbolo o término nuevo se explica en texto y con una marca visual en la primera diapositiva donde aparece; ver DEFINICIONES.md §5.
- **Saturación / llenado:** usar más partículas; otros grupos pusieron N>1000 y fue bien visto. En TP4 llegar al N máx medido con la grilla (D6).
- Elegir valores de barrido que muestren la tendencia; todo punto faltante se explica (ej. Fu(tmax) si no llega a 0,9).
- Esquema → curvas Fu(t) → ⟨t90⟩ vs x0; marcar x0, R, r en el dibujo; decir qué se fija y qué se varía.
- Declarar el método de ajuste (Teórica 0) en el MB 2D.
- Salida solo en múltiplos de dt2, sin estado final extra.

## TP4 de Nash (grupo 10, nota 7) — correcciones reales sobre el mismo TP
- No redactar tanto: solo algunas ideas principales. Diapositivas con figura y mínimo texto.
- Para el estudio de dt no hace falta animación: 2.1.a solo energía vs tiempo y observable vs dt.
- No era necesario implementar 3 integradores, pero ya que lo hicieron: ¿cuál tenía el mejor tiempo de cómputo? Medir tiempo de cómputo por integrador en el oscilador (mismo dt, mismas corridas) y tener la respuesta lista. El enunciado limita la diapositiva del Sistema 1 a ECM vs dt: el dato va en la respuesta oral o en Conclusiones, no como figura extra en esa diapositiva.
- (IMPORTANTE) Faltaron las animaciones de los casos representativos; sin ellas no se puede verificar el funcionamiento de la implementación. 3 animaciones de casos típicos: 2.2, 2.3 y 2.4; 2.2 y 2.4 con fresca/usada coloreada; 2.3 (sin obstáculos) sin esa coloración. La de 2.4 (N=600, x₀=r) sirve también para 2.1.b porque 2.4 usa los outputs de 2.1.b. 2.1.a no lleva (Nash). Confirmado por la cátedra (Q11, 16/10). Link visible en el PDF. No contradice "pocos ejemplos": 1 animación por estudio, no una por cada valor del barrido.
- Una vez elegido dt, no hace falta escribirlo en todas las páginas: se declara una sola vez.
- Las conclusiones del dt no son parte del estudio del trabajo: Conclusiones no menciona el dt elegido ni su justificación (eso queda en 2.1.a).

## Proceso
- Fórmulas desde la diapositiva (foto), no de memoria.
- "Arreglo mostrado" ≠ "aplicado": verificar con diff real y probar el comando exacto de la demo.
- Reproducibilidad: `cmp` entre dos corridas.
- Ir a las clases de consulta (vie 16/10 y lun 19/10) con material.
- Pauta de IA: la producción parte de la comprensión propia; texto de diapositivas mínimo, a partir de la figura.

## Checklist por sección de la presentación (13 min, ~14–16 diapositivas)
- [ ] Intro + Modelo (≤3): fenómeno y método general; ecuaciones de ambos sistemas e integradores; sin geometría ni parámetros.
- [ ] Implementación (1): diagrama del motor, formato de salida, semilla.
- [ ] Simulaciones (1–2): esquema con R, r, x0; parámetros fijos y variables; definición de todos los observables.
- [ ] Sistema 1 (exactamente 1): ECM vs dt, 4 métodos, log-log, "¿cuál es el mejor?".
- [ ] 2.1.a: energía vs tiempo para varios dt → observable vs dt → dt elegido.
- [ ] 2.1.b: tiempo ± σ vs N con obstáculos (x₀=r), TP3 superpuesto con la misma grilla hasta su N máx; las curvas se cruzan.
- [ ] 2.2: esquema → Fu(t) → ⟨t90⟩ vs x0 con barras → comparación con N=20.
- [ ] 2.3: f(v) a varios tiempos → ajuste MB 2D → comparación con m⟨v²⟩/2.
- [ ] 2.4.a: ⟨t90⟩ y ⟨t100⟩ vs densidad, "¿hay densidad óptima?". 2.4.b solo si sobra tiempo.
- [ ] Conclusiones por sistema/variante. Última diapositiva: declaración de IA.
- [ ] Nombres de archivo, links abiertos en incógnito, ZIP < 100 KB.
