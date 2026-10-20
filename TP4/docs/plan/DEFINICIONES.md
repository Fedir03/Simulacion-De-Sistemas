# Definiciones del TP4 — qué se corre, qué se grafica, qué va en cada diapositiva

**Estado: PROPUESTA del 15/10 (noche); actualizado 19/10 con las respuestas de la cátedra (16/10) y las decisiones del grupo (19/10). Las PROPUESTA que no dependían de la cátedra ni de una medición se adoptaron tal cual como "DECIDIDO por defecto 19/10".** Las Q siguen la numeración de la task de Notion "TP4: llevar preguntas a la cátedra". Un valor pasa a CERRADO cuando en la columna Estado figura una fecha. Si algo cambia, se cambia acá y en ningún otro lado: todos los pasos (`pasos/NN`) apuntan a este archivo.
Roles: **A** motor Sistema 2 · **B** Sistema 1 · **C** experimentos y análisis · **D** figuras y presentación · **E** cumplimiento y estado (ver `referencia/PLAN.md` §5).

## 1. Decisiones

| # | Tema | Propuesta | Estado | Se cierra |
|---|---|---|---|---|
| D1 | Criterio para elegir dt (2.1.a) | Observable ε_E = máx_t \|E(t)−E(0)\|/E(0). Umbral **1e-3** escrito y commiteado **antes** de ver curvas. dt elegido = el mayor del barrido que cumple, verificado también en el N máx medido (D6) con x₀=r. Valor esperado: ~1e-4. Criterio de la cátedra (Q15): primero 30 s para todos los dt; con esa vista, los que hagan falta se siguen hasta un estado estacionario (la curva se aplana o se dispara) y se corta cuando difiere 1–2 % del último punto tomado. La energía se grafica relativa al valor inicial, (E(t)−E(0))/E(0) | PROPUESTA | pendiente |
| D2 | Barrido de dt en 2.1.a | N=300, sin obstáculos (lo pide el enunciado en 2.1.a), tf=30 s, **misma condición inicial para todos los dt**. dt ∈ {1e-2, 3e-3, 1e-3, 3e-4, 1e-4, 3e-5, 1e-5, 3e-6, 1e-6}. Se espera inestable en 1e-2 y 3e-3 (límite teórico 2,2e-3). dt=1e-6 son ≈3·10⁷ pasos: corre en segundo plano y el análisis no la espera (paso 05) | DECIDIDO 19/10 (Q15) | — |
| D3 | dt2 | **0,04 s** (25 cuadros/s), n = dt2/dt entero con el dt elegido (n=400 si dt=1e-4). Resolución de t90/t100 = 0,04 s. Ningún estado fuera de múltiplos de dt2 | DECIDIDO por defecto 19/10 (valor por defecto; se ajusta con D1) | — |
| D4 | Qué escribe el motor | Siempre `observables.txt` (t, E_tot, E_cin, Nu) cada dt2. `dynamic.txt` (id, x, y, vx, vy, estado) solo si la config lo pide (animaciones y 2.3). 2.4 sale de los `observables.txt` de 2.1.b | DECIDIDO por defecto 19/10 | — |
| D5 | Condición inicial | **Grilla única para todo N** (Q5): una grilla de sitios fija donde entran más partículas que el N máx; se excluyen los sitios que solapan con los obstáculos o la pared; se sortean N sitios sin reemplazo con la semilla; direcciones de velocidad uniformes en [0, 2π). El tamaño de la grilla se define con la medición del paso 04, no con cuentas teóricas. Se declara en Simulaciones. **Medido el 20/10 con el comando `grid-nmax`:** red hexagonal, s = 2r + 0,1 mm, un sitio en el origen (`engine/GridPlacement`, `Lattice.HEX`, `Anchor.SITE_AT_ORIGIN`). Con separación extra 0 entran los mismos sitios, pero aparecen distancias de −4e-17 por el redondeo de √3; el 0,1 mm lo evita | CERRADO 16/10 (Q5) | — |
| D6 | N máximo | **N máx = 721 sin obstáculos y 714 con obstáculos en x₀=r** (713 en el peor x₀ de D13), con la grilla de D5 (hex, s = 2r + 0,1 mm, sitio en el origen). Medido el 20/10 con el comando `grid-nmax`. Con N = N máx se usan todos los sitios, así que no depende de la semilla; 5 semillas verifican que no haya solapamientos. Sin topes teóricos (Q5, Q14: llegar al N más alto posible) | CERRADO 20/10 (medición) | — |
| D7 | N por estudio | 2.1.a: 300 · 2.1.b: hasta el N máx medido (D6), solo con obstáculos en x₀=r (Q1); los valores intermedios se fijan con la medición · 2.2: 100 y 20 · 2.3: 100 · 2.4: los de 2.1.b · TP3 se vuelve a correr con la misma grilla hasta su N máx de cancha vacía. Las curvas de TP3 y TP4 se tienen que cruzar (cuanto antes, mejor); si no se cruzan, se extienden las dos (Q5, Q14) | PROPUESTA | pendiente (con D6) |
| D8 | Realizaciones | 2.1.b: **10** · 2.2: **8** por x₀ (mínimo pedido 5) · 2.3: **30** · 2.1.a: 1 (determinista con la semilla) | DECIDIDO por defecto 19/10 | — |
| D9 | Tiempos | 2.1.a: tf=30 s · 2.1.b: tf=30 s (enunciado) · 2.2: tmax=100 s (enunciado) · 2.3: tmax=30 s, a confirmar con piloto | DECIDIDO por defecto 19/10 (tmax de 2.3 se ajusta con el piloto) | — |
| D10 | Desvío / barras | Desvío estándar muestral (n−1) entre realizaciones independientes, barra = ±1σ, dicho **una vez** en Simulaciones. Para f(v): σ entre realizaciones por bin. Releer `references/metodologia-estadistica.md` antes de graficar | DECIDIDO por defecto 19/10 | — |
| D11 | Tiempo de ejecución (2.1.b) | Convención de TP3: `System.nanoTime` alrededor de `run`, JVM nueva por realización, `--jobs 1`, misma máquina, **en serie y sin otras cargas**. TP3 se re-corre en esa misma sesión. Mide con `observables.txt` escrito, sin estados | DECIDIDO por defecto 19/10 | — |
| D12 | Máquina de medición | TP3 y TP4 corridos en la misma computadora (la de Fede) | DECIDIDO 19/10 | — |
| D13 | Grilla de x₀ (2.2) | 9 valores: r=0,0175 · 0,06 · 0,12 · 0,18 · 0,24 · 0,30 · 0,36 · 0,43 · R−r=0,4925. Fu(t) para 3: x₀=r, 0,24, R−r. Si el mínimo de t90 cae entre dos puntos, se agregan 2–3 más cerca | DECIDIDO por defecto 19/10 | — |
| D14 | Si no llega al umbral | t90: reportar Fu(tmax) como pide el enunciado. t100: el punto se omite y se explica en la diapositiva | DECIDIDO por defecto 19/10 | — |
| D15 | Distribución de velocidades (2.3) | Bins Δv=0,1 m/s. Instantes t ∈ {0; 0,5; 1; 2; 5; estacionario}. Estacionario = f(v) promediada en [t_est, 30 s] (t_est por piloto, T8). Ajuste MB 2D con **k_BT único**, mínimos cuadrados (método de Teórica 0, se declara). Comparar k_BT_ajuste con m v₀²/2. Fórmula `f(v)=(m v/k_BT)exp(−m v²/2k_BT)` del enunciado, con k_BT como único parámetro libre (Q10: "solo la temp"). t_est se define a ojo sobre el gráfico de f(v) de la corrida (Q13) | CERRADO 16/10 (Q10, Q13) | — |
| D16 | Animaciones | 3 casos típicos: 2.2 (N=100, x₀ intermedio, fresca/usada coloreada) · 2.3 (N=100 sin obstáculos, sin coloración fresca/usada) · 2.4 (N=600, x₀=r, fresca/usada coloreada; sirve también para 2.1.b porque 2.4 usa sus outputs). **2.1.a ninguna** (Nash). 2.1.b sin animación propia: usa la de 2.4 (Q11). 25 cuadros/s, ≤60 s, YouTube no listado, link visible + fotograma en el PDF. El código de animación **no va al ZIP** | CERRADO 16/10 (Q11) | — |
| D17 | Velocidad en fuerzas que dependen de v (oscilador) | Beeman: variante predictor-corrector explícita (diapo 20). Velocity Verlet: a(t+Δt) con velocidad predicha por Euler. Verlet: v(t) ≈ [r(t)−r(t−Δt)]/Δt (hacia atrás) para evaluar f. Se declara en Implementación. Paso inicial de Euler (Q6): si un punto del ECM sale fuera de la tendencia por ese primer paso, se descarta y se aclara en la presentación | CERRADO 19/10 (Q6) | — |
| D18 | Barrido de dt del Sistema 1 | ~13 valores log-espaciados entre 1e-6 y 5e-3 (dt<1e-2), tf=5 s, ECM = Σ_pasos (x_num−x_an)² / n_pasos | DECIDIDO por defecto 19/10 | — |
| D19 | Velocity Verlet: término de r | Δt²/(2m): la versión anterior de la diapo 17 imprimía Δt²/m y era errata (Q8); la versión subida el 16/10 ya trae Δt²/(2m) | CERRADO 16/10 (Q8) | — |
| D20 | Densidad en el eje | ρ = N/(πR²) en m⁻² (A=0,817 m²), con la fracción de área φ entre paréntesis. Se define una vez. Q4 sigue abierta y se consulta por mail a la cátedra (paso 09). TP3 usó φ = Σ πR_k²/(L·W) en % como fracción de área de los **obstáculos** (`TP3/scripts/plot_t90_density.py:142`), así que no es referencia directa | PROPUESTA | pendiente (Q4) |
| D21 | Energía total | E = Σ½m v² + Σ½k ξ² (pares + obstáculos + pared). v por diferencia central. La elástica de la pared se suma **una vez** (la de la partícula real); la partícula imagen es fantasma y no suma ni cinética ni elástica (Q12). El test de conservación decide: si la energía no se conserva al pegar en la pared, se revisa esto. Se grafica también E_cin sola (apéndice o figura aparte), como marcó el profesor | CERRADO 19/10 (Q12) | — |
| D22 | Mapa de calor 2.4.b | Se decide el mar 20 con el estado real; solo si todo lo obligatorio está revisado | PENDIENTE | Mar 20 |
| D23 | Reparto con nombres | Todos pares. **Fede** (git: fspivak, fespivak@itba.edu.ar): colocación por grilla, CIM, medición del N máx, tiempos de 2.1.b con la re-corrida de TP3 (incluye adaptar `StageGeneration` a la grilla) + rol E (cumplimiento de formato, `ESTADO.md`, README del motor, script del ZIP). **Federico Ruckauf** (git: fedir03 / Federico Ignacio Ruckauf): Sistema 2 (Verlet, contactos, pared imagen, obstáculos, fresca→usada, energía, salida cada dt2). **Lolo** (git: Lorenzo, lchiossone@itba.edu.ar; handle de GitHub "Lchiossone2004" sin verificar): estudio ECM vs dt del Sistema 1 con calentamiento de JVM, F1, plantilla de presentación (latexmk, E1–E3), figuras y animaciones + rol C (runner, observables, ajuste MB, `analysis/`). **Auditoría cruzada rotativa (D30):** Ruckauf audita a Fede, Fede audita a Lolo, Lolo audita a Ruckauf (S1 y S2, que no escribió). La oral la ensayan los tres con preguntas cruzadas; cada uno responde por cualquier parte (D32). **Si Fede se atrasa:** lo primero que se reasigna es el rol E (README del motor y ZIP), que se hace al final y no depende de nada más. Lo toma Lolo o Ruckauf; quien lo arma no puede ser quien lo audita (hoy lo audita Ruckauf: si lo toma él, el auditor pasa a ser otro; se actualiza `auditoria-codigo.md`) | DECIDIDO 19/10 | — |
| D24 | Sincronización | Todos los días 20:00, 5 min: cada rol dice "hecho / bloqueado en X". **Solo E** edita `ESTADO.md` y lo sube | DECIDIDO por defecto 19/10 | — |
| D25 | Búsqueda de vecinos | CIM de TP1 con la grilla rearmada en cada paso; obstáculos y pared fuera de la grilla; fuerza bruta solo en los tests (Q3: "CIM ayuda en las cuentas → usar"). Al ZIP van solo `CellIndexMethod`, `NeighborFinder` y `Particle`. **Ojo:** el CIM de TP1 trabaja en [0,L]² y recorta los índices de celda sin error, así que las coordenadas negativas del billar caerían en la celda 0: se pasan desplazadas en +R (L = 2R) y el test CIM = fuerza bruta incluye x<0 e y<0. Revisión del CIM de TP1: **parcial**, hecha contra el enunciado de TP1 y `TP1/CLAUDE.md` porque no hay correcciones de TP1 escritas | CERRADO 16/10 (Q3) | — |
| D26 | README del motor | TP4/README.md **chico**: requisitos (Java 21, Maven), cómo compilar y un comando de ejemplo que corra de verdad desde el ZIP descomprimido (o el ZIP lleva un config de ejemplo mínimo, o el comando lleva todos los argumentos). Sin formato de salidas ni esquema; sin mención del plan, del grupo, de resultados ni de figuras. Va en el ZIP. Main sin argumentos puede imprimir el uso, pero no reemplaza al README. De TP1 el ZIP lleva solo las clases que el motor necesita (D25) (Q9) | DECIDIDO 19/10 (Q9) | Mar 20 |
| D27 | Herramienta de la presentación | La misma plantilla de TP3 (estructura y disposición iguales desde TP2). El texto de cada diapositiva lo escribe una persona a partir de la figura; se automatiza solo colocar figuras y los parámetros del pie | DECIDIDO 15/10 | Vie 16 |
| D28 | Pipeline de figuras y animaciones | analysis/make_figures.py lee outputs/ y escribe F1–F10 en presentacion/figuras/ con nombre fijo y estilo único; un script aparte arma el fotograma y el video de cada animación desde dynamic.txt. Ninguno va al ZIP | DECIDIDO por defecto 19/10 | — |
| D29 | Auditoría de integradores | Cada esquema se contrasta con su diapositiva de Teórica 4: fórmula, archivo:línea, adaptación y justificación, en `auditoria-integradores.md`. Toda adaptación se explicita en la presentación (S03b) y se consulta con la cátedra antes de presentar, por mail (paso 09), porque la clase del 19/10 ya pasó (criterios de la cátedra para TP4 y TP5) | PROPUESTA | pendiente |
| D30 | Auditoría cruzada del código | Motor (S1, S2, CIM, grilla) y scripts de `analysis/` auditados por otro integrante según los pares de D23; nadie audita su propio código. Registro en `auditoria-codigo.md`. Compuerta: auditoría completa antes del paso 10 | PROPUESTA | pendiente |
| D31 | Anexo de prompts | Anexo de la declaración de IA con los prompts enviados al agente para construir el motor (S1, S2, CIM, grilla, formatos), con fecha y autor, en `TP4/docs/ia/prompts-motor.md`. Cada entrada se marca **"textual"** o **"reconstruido"** (reconstruido a partir del plan); no hace falta cargar todos los prompts usados. **Ubicación (decisión del grupo 19/10):** apéndice **después de "Muchas gracias"**, para que la declaración de IA sea la última diapositiva de la exposición. Si va dentro del PDF o aparte: consulta del paso 09 | PROPUESTA | pendiente |
| D32 | Preparación de la oral | La oral pesa más y la exposición puede cortarse: ordenar la presentación de lo más importante a lo secundario. Lista de preguntas probables por sección y ensayo con preguntas cruzadas entre los tres; cada uno tiene que poder responder por cualquier parte. **Preguntas probables:** (1) *¿Por qué corren las coordenadas +R en el CIM?* — responde cualquiera de los tres. El CIM de TP1 asume [0, L]² y recorta los índices de celda a [0, M−1]. Sin el corrimiento, todas las coordenadas negativas caen en la fila y la columna 0: los pares salen igual de bien (verificado contra fuerza bruta), pero esa franja junta más de la mitad de las partículas y la búsqueda se vuelve casi fuerza bruta. Medido: **2,0–4,4 veces más lento sin +R** (5 corridas, N=714, M=29, máquina con ruido; ver COMPLICACIONES). Además, se valida \|r\| ≤ R porque el recorte escondería sin error una partícula que se salió del dominio | PROPUESTA | pendiente |

## 2. Catálogo de figuras

| Fig | Estudio | Eje x | Eje y | Series (líneas) | Escala | Barras | Diap. |
|---|---|---|---|---|---|---|---|
| F1 | Sistema 1 | dt | ECM | 4 (Beeman, Verlet, Velocity Verlet, Euler PC) | log-log | no (determinista) | S06 |
| F2 | 2.1.a | t | E(t)/E(0) | 4: dt = 1e-3, 3e-4, 1e-4, 1e-5 (1e-2 y 3e-3 divergen: se dicen en el texto) | lineal | no | S07 |
| F3 | 2.1.a | dt | ε_E | 1 + línea del umbral + dt elegido | log-log | no | S08 |
| F4 | 2.1.b | N | tiempo de ejecución [s] | 2: TP4 (con obstáculos, x₀=r), TP3 (misma grilla, hasta su N máx; las curvas se cruzan) | log-log; ajuste de ley de potencia declarado | ±σ (10 realiz.) | S09 |
| F5 | 2.2 | t | Fu(t) | 3: x₀ = r, 0,24, R−r (N=100) | lineal | no (media de 8) | S11 |
| F6 | 2.2 | x₀ | ⟨t90⟩ | 2: N=100, N=20 | lineal | ±σ | S12 |
| F7 | 2.3 | v | f(v) | 5: t = 0; 0,5; 1; 2; 5 (+ estacionario en F8) | lineal | no | S13 |
| F8 | 2.3 | v | f(v) estacionaria | datos + ajuste MB 2D | lineal | ±σ por bin | S14 |
| F9 | 2.4.a | ρ | ⟨t90⟩, ⟨t100⟩ | 2 | lineal | ±σ | S15 |
| F10 | 2.4.b (opc.) | x₀ | N | mapa de calor ⟨t90⟩ | — | — | extra |

Figuras esquemáticas (sin datos):

| Fig | Tema | Contenido | Diap. | Responsable |
|---|---|---|---|---|
| E1 | Esquema del sistema | dominio circular, obstáculos en ±x₀ con cota, R y r con cota, partículas fresca y usada en dos colores | S05 | rol D |
| E2 | Contacto | dos círculos superpuestos con ξ marcada | S02 | rol D |
| E3 | Línea de tiempo | pasos de integración Δt y salidas Δt₂ marcadas | S03 | rol D |

Reglas para todas: sin título embebido; leyenda adentro; con qué parámetros y semilla se generó en el caption; etiquetas de eje cortas escritas a mano; mismos criterios de barras entre figuras del mismo tipo.

## 3. Diapositivas (13 min = 780 s)

| S | Sección | Contenido (figura primero, texto mínimo) | Fig | s |
|---|---|---|---|---|
| S01 | Introducción | Fenómeno y método general. **Nada** del billar ni de obstáculos | — | 30 |
| S02 | Modelo | Solo ecuaciones: Newton, fuerza normal de contacto (resorte), energía. Sin números ni geometría | — | 40 |
| S03 | Implementación | Los 4 esquemas del S1 y Verlet del S2 (fórmulas citadas), cómo se estima la velocidad (D17), pared imagen, CIM mencionado sin re-explicar | — | 70 |
| S03b | Implementación | Adaptaciones de los integradores respecto de la teórica, con su justificación (D29, `auditoria-integradores.md`) | — | a definir |
| S04 | Simulaciones S1 | Parámetros del oscilador (diapo 37), observable ECM definido | — | 25 |
| S05 | Simulaciones S2 | Esquema geométrico con parámetros marcados, tabla fijo/variable por estudio, observables definidos (E, Fu, t90, t100, f(v), tiempo), nº de realizaciones y σ dichos una vez | — | 60 |
| S06 | Resultados S1 | **UNA diapositiva**: ECM vs dt y respuesta a "¿cuál es el mejor esquema?". El tiempo por integrador va en la respuesta oral o en Conclusiones | F1 | 50 |
| S07 | 2.1.a | Energía en el tiempo para varios dt | F2 | 35 |
| S08 | 2.1.a | ε_E vs dt y dt elegido (esta es la conclusión sobre Δt; no se repite en otras) | F3 | 40 |
| S09 | 2.1.b | Tiempo vs N con TP3 superpuesto; descripción de la tendencia | F4 | 55 |
| S10 | 2.2 | Esquema de x₀ + fotograma de la animación + link | — | 25 |
| S11 | 2.2 | Fu(t) para 3 valores de x₀ | F5 | 40 |
| S12 | 2.2 | ⟨t90⟩ vs x₀ con N=100 y N=20 | F6 | 55 |
| S13 | 2.3 | f(v) en el tiempo + fotograma y link de la animación | F7 | 45 |
| S14 | 2.3 | Ajuste MB 2D y k_BT vs m v₀²/2 | F8 | 40 |
| S15 | 2.4 | ⟨t90⟩, ⟨t100⟩ vs densidad + fotograma y link de la animación | F9 | 45 |
| S16 | Conclusiones | Una afirmación por estudio, aclarando a qué caso se refiere. Sin conclusiones de Δt | — | 60 |
| S17 | Uso de IA | Agente/modelo usado y de qué manera | — | 10 |
| S17b | Anexo de prompts | Prompts del motor (D31). Apéndice, después del cierre ("Muchas gracias"); no se expone y no cuenta en el tiempo | — | — |

Total 725 s (12 min 05 s) sin S03b; **a recalcular** con S03b. Si el mapa de calor entra, va como extra y se saca otra cosa.

## 4. Cómputo estimado (a medir en la primera corrida)
- Pasos: tf=30 s con dt=1e-4 son 3·10⁵ pasos; tmax=100 s son 10⁶.
- 2.1.a con dt=1e-6: ≈3·10⁷ pasos con N=300, del orden de horas; va en segundo plano (D2).
- 2.1.b: ~8–10 N (hasta el N máx medido) × 10 realizaciones, cada una de segundos a decenas de segundos ⇒ del orden de 1 h en serie. Más la re-corrida de TP3 con la grilla hasta su N máx.
- 2.2: 9 x₀ × 8 realizaciones × 2 valores de N ≈ 144 corridas de ~10–30 s.
- 2.3: 30 corridas de 30 s con `dynamic.txt`.
- Tamaño de `dynamic.txt` (2.3 y animaciones): 2500 cuadros × 100 partículas × ~40 B ≈ 10 MB por corrida.
- Estos números son estimaciones: se reemplazan por los medidos en la primera corrida.

## 5. Glosario de símbolos (texto + marca visual)

Regla: todo símbolo o término nuevo se define **una vez**, en la primera diapositiva donde aparece, con una explicación en texto y una marca visual (cota o flecha en el esquema, línea o etiqueta en la figura). Si aparece en una figura antes de definirse, la definición se mueve a esa diapositiva.

| Símbolo | Significado | Se define en | Marca visual |
|---|---|---|---|
| R | radio del dominio circular | S05 | cota en el esquema |
| r | radio de partícula y de obstáculo | S05 | cota en el esquema |
| x₀ | posición de los obstáculos (±x₀, 0) | S05 | cota del origen al centro de un obstáculo |
| N, m, k, v₀ | partículas, masa, constante del resorte, rapidez inicial | S05 | tabla fijo / variable |
| ξ | superposición en el contacto | S02 | dibujo de dos círculos superpuestos |
| E | energía total (cinética + elástica) | S02 | — |
| Δt, Δt₂ | paso de integración / intervalo de salida | S03 | línea de tiempo con marcas |
| ECM | error cuadrático medio | S04 | — |
| ε_E | máx_t \|E(t)−E(0)\|/E(0) | S05 | línea horizontal del umbral en F3 |
| Nu, Fu | partículas usadas / fracción usada | S05 | colores fresca y usada en el esquema |
| t₉₀, t₁₀₀ | tiempos con Fu = 0,9 y Fu = 1 | S05 | marca horizontal en una curva de ejemplo |
| ρ | densidad N/(πR²) | S05 | — |
| f(v) | distribución de rapidez | S05 | — |
| t_est | inicio del estacionario | S13 | línea vertical en F7 |
| k_BT | parámetro efectivo del ajuste de Maxwell-Boltzmann | S14 | etiqueta en F8 |
