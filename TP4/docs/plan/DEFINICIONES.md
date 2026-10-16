# Definiciones del TP4 — qué se corre, qué se grafica, qué va en cada diapositiva

**Estado: PROPUESTA del 15/10 (noche).** Un valor pasa a CERRADO cuando en la columna Estado figura una fecha. Si algo cambia, se cambia acá y en ningún otro lado: todos los pasos (`pasos/NN`) apuntan a este archivo.
Roles: **A** motor Sistema 2 · **B** Sistema 1 · **C** experimentos y análisis · **D** figuras y presentación · **E** cumplimiento y estado (ver `referencia/PLAN.md` §5).

## 1. Decisiones

| # | Tema | Propuesta | Estado | Se cierra |
|---|---|---|---|---|
| D1 | Criterio para elegir dt (2.1.a) | Observable ε_E = máx_t \|E(t)−E(0)\|/E(0). Umbral **1e-3** escrito y commiteado **antes** de ver curvas. dt elegido = el mayor del barrido que cumple, verificado también en N=700 con x₀=r. Valor esperado: ~1e-4 | PROPUESTA | Sáb 17 (2.1.a) |
| D2 | Barrido de dt en 2.1.a | N=300, sin obstáculos, tf=30 s, **misma condición inicial para todos los dt**. dt ∈ {1e-2, 3e-3, 1e-3, 3e-4, 1e-4, 3e-5, 1e-5}. Se espera inestable en 1e-2 y 3e-3 (límite teórico 2,2e-3) | PROPUESTA | Jue 15 |
| D3 | dt2 | **0,04 s** (25 cuadros/s), n = dt2/dt entero con el dt elegido (n=400 si dt=1e-4). Resolución de t90/t100 = 0,04 s. Ningún estado fuera de múltiplos de dt2 | PROPUESTA | Sáb 17 (con D1) |
| D4 | Qué escribe el motor | Siempre `observables.txt` (t, E_tot, E_cin, Nu) cada dt2. `dynamic.txt` (id, x, y, vx, vy, estado) solo si la config lo pide (animaciones y 2.3). 2.4 sale de los `observables.txt` de 2.1.b | PROPUESTA | Jue 15 |
| D5 | Condición inicial | RSA (sin solapar con nada) para **N ≤ 400**; red hexagonal con sitios sorteados y direcciones aleatorias para **N > 400**. Se declara en Simulaciones. Consulta Q5 | PROPUESTA | Vie 16 |
| D6 | N máximo | **700** (hex ideal ≈714–719 con x₀=r). Se confirma con una prueba real de colocación el viernes; si no entra, 650 | PROPUESTA | Vie 16 |
| D7 | N por estudio | 2.1.a: 300 · 2.1.b: {50,100,200,300,400,500,600,700} · 2.2: 100 y 20 · 2.3: 100 · 2.4: los de 2.1.b · TP3 se corre en los N en común (≤400) | PROPUESTA | Jue 15 |
| D8 | Realizaciones | 2.1.b: **10** · 2.2: **8** por x₀ (mínimo pedido 5) · 2.3: **30** · 2.1.a: 1 (determinista con la semilla) | PROPUESTA | Jue 15 |
| D9 | Tiempos | 2.1.a: tf=30 s · 2.1.b: tf=30 s (enunciado) · 2.2: tmax=100 s (enunciado) · 2.3: tmax=30 s, a confirmar con piloto | PROPUESTA | Jue 15 / piloto |
| D10 | Desvío / barras | Desvío estándar muestral (n−1) entre realizaciones independientes, barra = ±1σ, dicho **una vez** en Simulaciones. Para f(v): σ entre realizaciones por bin. Releer `references/metodologia-estadistica.md` antes de graficar | PROPUESTA | Jue 15 |
| D11 | Tiempo de ejecución (2.1.b) | Convención de TP3: `System.nanoTime` alrededor de `run`, JVM nueva por realización, `--jobs 1`, misma máquina, **en serie y sin otras cargas**. TP3 se re-corre en esa misma sesión. Mide con `observables.txt` escrito, sin estados | PROPUESTA | Vie 16 |
| D12 | Máquina de medición | Una sola, la de ____ . Mientras corre 2.1.b + TP3 nadie usa esa máquina (se lanza de noche, sin supervisión) | ABIERTA | Jue 15 |
| D13 | Grilla de x₀ (2.2) | 9 valores: r=0,0175 · 0,06 · 0,12 · 0,18 · 0,24 · 0,30 · 0,36 · 0,43 · R−r=0,4925. Fu(t) para 3: x₀=r, 0,24, R−r. Si el mínimo de t90 cae entre dos puntos, se agregan 2–3 más cerca | PROPUESTA | Jue 15 |
| D14 | Si no llega al umbral | t90: reportar Fu(tmax) como pide el enunciado. t100: el punto se omite y se explica en la diapositiva | PROPUESTA | Jue 15 |
| D15 | Distribución de velocidades (2.3) | Bins Δv=0,1 m/s. Instantes t ∈ {0; 0,5; 1; 2; 5; estacionario}. Estacionario = f(v) promediada en [t_est, 30 s] (t_est por piloto, T8). Ajuste MB 2D con **k_BT único**, mínimos cuadrados (método de Teórica 0, se declara). Comparar k_BT_ajuste con m v₀²/2. Fórmula `f(v)=(m v/k_BT)exp(−m v²/2k_BT)` **a verificar** (Q10) | PROPUESTA | Vie 16 |
| D16 | Animaciones | 3 casos típicos: 2.2 (N=100, x₀ intermedio, fresca/usada coloreada) · 2.3 (N=100 sin obstáculos, sin coloración fresca/usada) · 2.4 (N=600, x₀=r, fresca/usada coloreada; sirve también para 2.1.b porque 2.4 usa sus outputs). **2.1.a ninguna** (Nash). 2.1.b sin animación propia: usa la de 2.4 (Q11). 25 cuadros/s, ≤60 s, YouTube no listado, link visible + fotograma en el PDF. El código de animación **no va al ZIP** | PROPUESTA | Vie 16 |
| D17 | Velocidad en fuerzas que dependen de v (oscilador) | Beeman: variante predictor-corrector explícita (diapo 20). Velocity Verlet: a(t+Δt) con velocidad predicha por Euler. Verlet: v(t) ≈ [r(t)−r(t−Δt)]/Δt (hacia atrás) para evaluar f. Se declara en Implementación. Q6 | PROPUESTA | Vie 16 |
| D18 | Barrido de dt del Sistema 1 | ~13 valores log-espaciados entre 1e-6 y 5e-3 (dt<1e-2), tf=5 s, ECM = Σ_pasos (x_num−x_an)² / n_pasos | PROPUESTA | Jue 15 |
| D19 | Velocity Verlet: término de r | Δt²/(2m) (la diapo 17 imprime Δt²/m). Q8 | DECIDIDO por el grupo; confirmar | Vie 16 |
| D20 | Densidad en el eje | ρ = N/(πR²) en m⁻² (A=0,817 m²). Se define una vez | PROPUESTA | Jue 15 |
| D21 | Energía total | E = Σ½m v² + Σ½k ξ² (pares + obstáculos + pared imagen). v por diferencia central. Se grafica también E_cin sola (apéndice o figura aparte), como marcó el profesor | PROPUESTA | Jue 15 |
| D22 | Mapa de calor 2.4.b | Se decide el mar 20 con el estado real; solo si todo lo obligatorio está revisado | PENDIENTE | Mar 20 |
| D23 | Reparto con nombres | A ____ · B ____ · C ____ · D ____ · E ____ (con 3 personas: A / B+C / D+E) | ABIERTA | Jue 15 |
| D24 | Sincronización | Todos los días 20:00, 5 min: cada rol dice "hecho / bloqueado en X". **Solo E** edita `ESTADO.md` y lo sube | PROPUESTA | Jue 15 |
| D25 | Búsqueda de vecinos | CIM de TP1 con la grilla rearmada en cada paso; obstáculos y pared fuera de la grilla; fuerza bruta solo en los tests | PROPUESTA | Vie 16 |
| D26 | README del motor | TP4/README.md, una página: requisitos (Java 21, Maven), compilar, ejecutar (el comando exacto de la demo), formato de la config (N, x₀, dt, dt2, tf, semilla, guardar estados) y de las salidas (observables.txt, dynamic.txt), qué esquema implementa. Sin mención del plan, del grupo, de resultados ni de figuras. Va en el ZIP. Si la cátedra dice que cuenta como documentación extra (Q9), el mismo texto lo imprime Main sin argumentos | DECIDIDO por el grupo 15/10 | Mar 20 |
| D27 | Herramienta de la presentación | La misma plantilla de TP3 (estructura y disposición iguales desde TP2). El texto de cada diapositiva lo escribe una persona a partir de la figura; se automatiza solo colocar figuras y los parámetros del pie | DECIDIDO 15/10 | Vie 16 |
| D28 | Pipeline de figuras y animaciones | analysis/make_figures.py lee outputs/ y escribe F1–F10 en presentacion/figuras/ con nombre fijo y estilo único; un script aparte arma el fotograma y el video de cada animación desde dynamic.txt. Ninguno va al ZIP | PROPUESTA | Vie 16 |

## 2. Catálogo de figuras

| Fig | Estudio | Eje x | Eje y | Series (líneas) | Escala | Barras | Diap. |
|---|---|---|---|---|---|---|---|
| F1 | Sistema 1 | dt | ECM | 4 (Beeman, Verlet, Velocity Verlet, Euler PC) | log-log | no (determinista) | S06 |
| F2 | 2.1.a | t | E(t)/E(0) | 4: dt = 1e-3, 3e-4, 1e-4, 1e-5 (1e-2 y 3e-3 divergen: se dicen en el texto) | lineal | no | S07 |
| F3 | 2.1.a | dt | ε_E | 1 + línea del umbral + dt elegido | log-log | no | S08 |
| F4 | 2.1.b | N | tiempo de ejecución [s] | 2: TP4, TP3 (TP3 hasta N=400) | log-log; ajuste de ley de potencia declarado | ±σ (10 realiz.) | S09 |
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

Total 725 s (12 min 05 s); quedan ~55 s de margen. Si el mapa de calor entra, va como extra y se saca otra cosa.

## 4. Cómputo estimado (a medir en la primera corrida)
- Pasos: tf=30 s con dt=1e-4 son 3·10⁵ pasos; tmax=100 s son 10⁶.
- 2.1.b: 8 N × 10 realizaciones, cada una de segundos a decenas de segundos ⇒ del orden de 1 h en serie. Más la re-corrida de TP3.
- 2.2: 9 x₀ × 8 realizaciones × 2 valores de N ≈ 144 corridas de ~10–30 s.
- 2.3: 30 corridas de 30 s con `dynamic.txt`.
- Tamaño de `dynamic.txt` (2.3 y animaciones): 2500 cuadros × 100 partículas × ~40 B ≈ 10 MB por corrida.
- Estos números son estimaciones: se reemplazan por los medidos el sábado.

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
