# DEFINICIONES — TP5 Dinámica Peatonal (Problema 1)

Fuente única de valores del TP5. Si algo cambia, se cambia acá primero y después en código y presentación.
Grupo 02, comisión S. Entrega: **lun 16/11/2026** (la cátedra corrigió el 13/11 del enunciado). Objetivo del grupo: **cerrar el lun 9/11**.

Estado de cada decisión: ✅ decidida · 🟡 default hasta que conteste la cátedra · ⏳ pendiente.

## 1. Decisiones

| # | Decisión | Valor | Estado |
|---|---|---|---|
| D1 | Modelo | SFM sin fuerza social | ✅ |
| D2 | Capa de elusión | Finalistas A, B y F. El piloto del mié 4/11 elige una sola | ⏳ |
| D3 | Ventana de simulación y medición | **Tramo frontal** (desde el 11/11, pedido oral de la cátedra del 6/11): criterio D(45°) con persistencia de 5 frames (sección 8b) **más la compuerta de tramo compartido** (sección 8c, aprobada por el grupo el 11/11): si el tramo de un peatón pasa la x inicial del otro en más de X = 1,5 m, la ventana termina en el último frame común antes de que la pase. Con X = 1,5 solo cambian los eventos 3 y 6, y el conjunto es el mismo con X entre 1 y 2 m. ⚠️ **X se eligió después de ver los 19 eventos (post-hoc)**. Ventana = primer a último frame común del tramo. **Target** de cada peatón = su última posición en esa ventana; **v_d** = su rapidez media en la ventana (opción 1). CLI: `--trim on|off --trim-deg 45 --trim-persist 5 --trim-half 2 --trim-target common|own --trim-shared on|off --trim-shared-x 1.5`. Con `--trim-shared off` se reproduce byte a byte el piloto D(45°) del 11/11 (`outputs/pilot_d45/`); con `--trim off`, el piloto sin recorte (`outputs/pilot_sin_recorte/`) | 🟡 consulta 1 |
| D4 | Paso de tiempo | Δt = Δt_exp/64 ≈ 1,04e-3 s (desde el 5/11; antes /32). Con capa, /32 no cumplía la prueba de D11: A(2,5; 2,5) cambiaba 2,1% en ECM 1 excl. poblacional entre /32 y /64 (evento 9: 35%). Entre /64 y /128, los mejores pares de A, B y F cambian a lo sumo 0,10% poblacional y ningún evento más de 5%; el peor es B(2,5; 4), con 2,6% de ECM 2 en el evento 10. Sin capa, el ECM 1 cambia hasta 0,04% por evento entre /32 y /64. Con el recorte (11/11), entre /64 y /128 los mejores pares cambian a lo sumo 0,004% poblacional y 0,053% por evento | 🟡 consulta 6 |
| D5 | Parámetros del SFM | Ver sección 3 | 🟡 consultas 4 y 5 |
| D6 | Salida | Ver sección 4 | ✅ |
| D7 | Huecos de frames (evento 1, ID 36: 32 frames; evento 4, ID 10: 16 frames) | Omitir los t_k faltantes en ambos ECM; N_m = frames disponibles. Con el recorte, el hueco del evento 1 sigue dentro de la ventana (68 frames comunes de 100); el del evento 4 queda antes del tramo, así que ese evento ya no tiene huecos. El rumbo usa los tiempos reales a través del hueco; un hueco no corta el tramo | 🟡 consulta 2 |
| D8 | Validación cruzada | 14 entrenamiento y 5 validación al azar, semilla fija (20261116), **5000** particiones reutilizando la grilla (desde el 11/11; con 1000, el control de convergencia no pasaba con el recorte: hasta 2,11%). Las primeras 1000 son las mismas que antes. ⚠️ Con la compuerta del 11/11, el control (1000 y 2500 contra 5000, menos de 1%) **no pasa** en las 6 filas de A y B: 1000 contra 5000 difiere entre 1,03% y 1,71%; 2500 contra 5000, a lo sumo 0,57%. F pasa | 🟡 |
| D9 | Estructura del repo | Como TP4 (sección 6) | ✅ |
| D10 | Constantes ocultas de la capa | Ver sección 5. Se fijan con estadísticos descriptivos o teoría, nunca ajustando el ECM; se verifica sensibilidad | ✅ |
| D11 | Integrador y prueba de Δt | **Beeman**: error de posición RMS de 1,4e-7 m a Δt_exp/64 contra el peatón libre (Verlet original: 4,0e-4 m; a /32, 5,5e-7 y 8,0e-4 m), orden 2 contra orden 1. La prueba de Δt se hace también con capa activa, en los mejores pares. Ver sección 7 | ✅ |
| D12 | Velocidad inicial experimental | Pendiente del ajuste lineal por mínimos cuadrados sobre los primeros 5 frames de la ventana (con recorte, del tramo frontal), desde t_0, igual para los dos peatones. Si hay un hueco, usa los frames disponibles con sus tiempos reales. El 5 es una constante de procesamiento de datos (`--v0-frames`), justificada por el ruido de seguimiento (medido con segundas diferencias: σ = 0,6 cm robusto, 1,2 cm RMS) | 🟡 consulta 9 |
| D13 | Llegada al target antes del último instante | El peatón se retira de la simulación al quedar a δ_a ≤ 0,1 m de su target (`--delta-a`); con recorte, el target es la última posición en la ventana recortada (D3). Es una condición de la simulación, no de la capa. El ECM 1 se informa excluyendo los t_k posteriores al retiro y, además, rellenando con la posición del target (solo como convención de la métrica) | 🟡 consulta 8 |

Roles (intercambiables): **Motor** (parser, SFM, capa, tests) · **Datos y calibración** (ECM 1 y 2, grillas b, c, d, figuras) · **Presentación y visual** (animación, slides, uso de IA, ZIP).
Asignación: Fede ___ · Rucka ___ · Lolo ___

## 2. Datos del enunciado (resumen)

- 19 eventos, 2 peatones. Inicio con posición y velocidad experimentales; target final = última posición de su trayectoria; v_d = rapidez media de esa trayectoria; se simula hasta el último instante experimental.
- r = 0,25 m (SFM). Δt_exp = 1/15,0192 s ≈ 0,0666 s.
- ECM 1 (mismo instante) y ECM 2 (punto más cercano de la trayectoria simulada), por peatón; evento = promedio de los 2; poblacional = promedio de eventos.
- Puntos: (a) modelo + capa + animaciones con superposición; (b) calibración poblacional por métrica; (c) individual por evento; (d) validación cruzada.
- Entregables: presentación oral de 13 min, PDF sin animaciones embebidas (links a YouTube o Vimeo) y ZIP solo con el motor.
- Nombres: `SdS_TP5_2026Q2G02CS_Presentación` y `SdS_TP5_2026Q2G02CS_Codigo`.
- Datos (Drive, carpeta U5): `elusion_1_contra_1.txt` (id, frame, x, y, markerID) y `LEEME_elusion1contra1.txt`. Evento 2, peatón izquierdo = ID 1000.

## 3. SFM sin fuerza social (Teórica 6, diapos 28–33)

m r̈_i = F_G,i + F_D,i

- Contacto: F_G,i = Σ_{j≠i} [ (−ε_ij k_n) e^n_ij + (v^t_ij ε_ij k_t) e^t_ij ] g(ε_ij), con ε_ij = r_ij − (R_i + R_j).
- ⚠️ ε_ij es **negativo** en el solapamiento (la Teórica 5 usa ξ positivo). g(ε) no está definida en la diapo: se toma g = 1 si ε < 0 y 0 si no. e^n_ij apunta de j a i (por consistencia de signo); v^t_ij = (v_i − v_j)·e^t_ij.
- Driving force: F_D,i = m (v_d e_target − v_i) / τ.
- Valores (diapo 33): k_n = 1,2e5 N/m, k_t = 2,4e5 kg/m/s, τ = 0,5 s. m = 80 kg (del paper, ⚠️ consulta 5). r = 0,25 m para todos. Sin fuerza social, así que A y B no se usan.

## 4. Salida

- Un `.txt` por corrida (evento y parámetros de la capa).
- Una fila cada 16 pasos (dt2 = Δt_exp/4, el mismo espaciado que con /32): `t x1 y1 vx1 vy1 x2 y2 vx2 vy2`. El ECM 1 usa cada 4ª fila (los t_k); el ECM 2, todas.
- Las columnas de un peatón retirado (D13) valen `NaN`.
- Prueba del piloto: en un evento, cuánto cambia el ECM 2 entre imprimir cada 32 y cada 8 pasos.
- La animación corre aparte, leyendo el archivo.

## 5. Capa de elusión (especificación completa en Notion: "Capas de elusión: especificación matemática (A, B, F)")

Detección: sea r = x_j − x_i, w = v_j − v_d e_t, t* = −(r·w)/|w|², d_min = |r + w t*|. Hay choque predicho si 0 < t* ≤ t_a y d_min < ρ. La capa se apaga cuando deja de predecirse. Solo cambia la **dirección** de v_d (no agrega fuerzas).

- **A (t_a, ℓ):** x_T = x_i + v_d t_a e_t + ℓ n.
- **B (t_a, k):** ℓ = k (ρ − d_min); mismo x_T.
- **F (A_p, B_p):** n_c = e_ij A_p exp(−d_ij/B_p) cosθ_j (cosθ_j > 0), e_a = (n_c + e_t)/|n_c + e_t|. A_p ∈ (0, 1).
- Lado n: opuesto al otro en el punto de máximo acercamiento; desempate a la derecha.

Constantes fijas: ρ = 0,9 m (sensibilidad 0,7 a 1,1; distancias mínimas experimentales 0,49 a 0,92 m, mediana 0,68), ε = 0,05 m, visión de F = semiplano, d_ij entre centros (⚠️ por confirmar).

Alineado con la especificación corregida el 4/11:
- **Desempate de F (vigente):** |s_c| ≤ 0,05 m, con s_c = e_t^⊥·(r + w t*), el mismo criterio métrico de A y B. Al activarse, e_ij se rota 5° hacia la derecha del peatón; la especificación no da el ángulo, así que se mantienen los de la versión anterior. **Corregido el 5/11:** si después de rotar el desvío sigue a la izquierda (el otro a más de 5° del eje), se usa −e_t rotado 5°, como en el choque frontal exacto. Antes, 741 de 9049 pasos de desempate de F(0,9; 2,5) terminaban a la izquierda (eventos 6, 9, 12, 13 y 19). Efecto: ECM 1 excl. de 2,3546 a 2,3562; el mejor par de ECM 2 pasa de (0,8; 3) 0,5666 a (0,9; 2,5) 0,5722. Lo verifica `layerFMetricTieGoesRightEvenWithTheOtherFarFromTheAxis`.
- **Contacto:** con solape, las tres capas siguen actuando y además actúa F_G del SFM. La diapo 29 de la Teórica 7 aplica e_a solo "si la partícula NO está en contacto"; la especificación no lo dice. Se deja así por decisión del grupo (5/11). En los mejores pares, la capa está prendida en el 100% de los pasos con solape.
- **Orden del algoritmo con Beeman:** la capa se evalúa una vez por paso, dentro de la aceleración a(t+Δt), con las posiciones nuevas r(t+Δt) y las velocidades predichas. No queda congelada del paso anterior. El enunciado no fija ese orden. El conteo de conmutaciones usa en cambio las velocidades corregidas; puede diferir en pocos agentes (B(2,5; 4): 80 contra 76 en los 19 eventos) sin cambiar el máximo por agente.
- **Horizonte de F:** infinito. Con t_a = 5 el error cambia hasta 0,16%; con 2,5, hasta 0,77% en el par fijo, y el mejor par de la grilla pasa a (0,8; 3). Un t_a sería un tercer parámetro (`--f-horizon` queda solo para medirlo).
- **Variantes declaradas de F (5/11; no reemplazan a F):** F1 sin compuerta de choque predicho (actúa con el otro en el semiplano; el desempate pide t* > 0); F2 con max(0, d_ij − 2R) en la exponencial y e_ij y cos θ_j entre centros (la figura de la diapo 28 dibuja d_ij entre bordes); F3 = F1 + F2. Se corren con `--f-gate off` y `--f-distance edges`, y salen del motor al cerrar D2.
- **Por qué cambió:** la versión original rotaba e_ij 5° cuando |sin θ_j| ≤ ε y decía que no influía salvo en choque exacto. Era falso: la banda abarca 0,87 m de desvío lateral a 10 m. Para regenerar la comparación queda `--f-tie angular --frontal-deg X`, que sale del motor al cerrar D2.
- **Sentido de la rotación:** la versión original lo planteaba al revés o de forma ambigua. e_ij apunta de j hacia i, o sea hacia atrás del peatón: rotarlo "a la derecha" de su dirección lo manda a su izquierda. Lo que vale es el desvío resultante, hacia la derecha del peatón en su propio sistema de referencia. Lo verifica un test (`frontalTieDodgesToTheWalkersOwnRightForAnyHeading`).
- **F, sin horizonte:** el choque predicho pide t* > 0 y d_min < ρ.
- **Grilla oficial del piloto (la de la especificación):** A: t_a ∈ {0,5; ...; 5} s y ℓ ∈ {0; ...; 2,5} m. B: t_a igual y k ∈ {0; ...; 4}. F: A_p ∈ {0,1; ...; 0,9} y B_p ∈ {0,25; 0,5; 0,75; 1; 1,5; 2; 2,5; 3} m (la versión original daba 8 valores sin el paso).
- **Zona exploratoria de F (elegida post-hoc, después de ver los datos):** B_p hasta 1000 m. Se reporta aparte y rotulada; no es parte de la grilla oficial.
- **Resultado a reportar:** con B_p grande la exponencial vale ≈ 1 y **F colapsa de hecho a un solo parámetro**. Fijando B_p = 3 en la grilla oficial y barriendo solo A_p, F empeora 0,5% en ECM 1 excl. y 0% en ECM 2; fijando B_p = 1, 14% y 32% (números a Δt_exp/32 y con el desempate anterior; ver `comparacion_f.txt` para los vigentes).
- ⚠️ La especificación dice que el criterio de regreso "evita oscilar". En A no siempre: a Δt_exp/64, A(3; 1,75) llega a 38 conmutaciones por agente en el evento 15, y 97% son d_min cruzando ρ (a /32 eran hasta 22). El conteo crece al achicar Δt.

## 6. Estructura del repo

```
src/            paquete ar.edu.itba.sds.tp5 y tests JUnit:
                  motor (va al ZIP): Main, engine/, engine/layer/, data/ (parser y recorte FrontalTrim), io/OutputFiles
                  analysis/ (no va al ZIP): AnalysisMain, Ecm, ContactMonitor, MotionMonitor, EcmReport, GridSearch, DirectionSeries, TrimExport
                  diagnostics/ (no va al ZIP): RunTrace, LayerChecks, V0Probe
scripts/        sim_gen (corridas), graph_gen (figuras), animation
docs/plan/      DEFINICIONES.md, ESTADO.md
docs/ia/        prompts del motor (anexo de la presentación)
presentacion/   LaTeX y figuras
tools/          build_zip.sh (controles: menos de 100 KB, compila aislado, reproduce una corrida)
data/           datos de la cátedra (no van al ZIP)
outputs/        corridas (ignorado por git)
```
El dt elegido es el valor por defecto de la CLI.

**Motor y análisis separados (12/11).** El motor del ZIP solo simula y escribe `evento_XX.txt`: `java -jar target/tp5.jar baseline|run|integrator-check`. Los observables (ECM 1 y 2, distancia mínima, contactos), la grilla de calibración, el recorte exportado y la serie de direcciones son postproceso, en `analysis/`: `java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain baseline|run|grid|trim-export`, con los mismos archivos que antes (`ecm.txt`, `grid_*.txt`). El contacto, la distancia mínima, la longitud recorrida y las conmutaciones de la capa se siguen midiendo en cada paso Δt, con el `StepObserver` del motor (`ContactMonitor` y `MotionMonitor`), no con las filas de salida; el motor solo devuelve las filas y las llegadas. Verificado: 258 archivos de `outputs/` (línea base, grillas A, B, F y F angular, corridas de `figs/datos`) y las trazas de `RunTrace` idénticos byte a byte antes y después; 101 tests.

## 7. Pruebas y validación

- Paso de tiempo: correr Δt_exp/32, /64 y /128, sin capa y con los mejores pares de cada capa. Criterio, fijado antes de ver las curvas: el ECM cambia menos de 1% al duplicar la resolución, y la energía cinética no tiene saltos. El criterio de energía del TP4 no aplica (la driving force inyecta energía).
- Prueba analítica: peatón libre con v(t) = v_d + (v_0 − v_d) e^{−t/τ}.
- Capas: parámetro nulo (ℓ = 0, k = 0, A_p = 0) = línea base; sin choque predicho = línea base; simetría especular; vuelta al target final; ninguna fuerza nueva.
- Línea base: ECM 1 y 2 de los 19 eventos sin capa.
- Validación cruzada: la media del error de validación converge entre N/5, N/2 y N particiones (menos de 1%; con N = 5000, entre 1000, 2500 y 5000); con entrenamiento = validación da el error de (b); el error de entrenamiento no supera al de validación en promedio.

## 8. Consultas para la cátedra (vie 6/11)

1. Instante inicial y final cuando los peatones no coinciden (12 de 19 eventos arrancan desfasados, hasta 62 frames; 15 terminan desfasados, hasta 92). Opciones: ventana común con target y v_d de la trayectoria completa; cada peatón con su ventana; ventana común también para target y v_d.
2. Huecos de frames (evento 1, ID 36): ¿interpolar o omitir?
3. Criterio de "conflicto resuelto".
4. Fuerza de contacto: ¿vale la del paper de Helbing 2000 con k_n y k_t de la diapo 33?
5. Parámetros: ¿m = 80 kg, τ = 0,5 s y r = 0,25 m fijo?
6. Paso de tiempo: ¿vale Δt_exp/64 imprimiendo cada 16 pasos, usando una de cada 4 filas para el ECM 1?
7. Capa: ¿puede usar velocidad y posición del otro agente si solo cambia la dirección de v_d?
8. ¿Qué hace un peatón al llegar al target antes del último instante? Default: se retira de la simulación (D13).
9. ¿Qué método se espera para estimar la velocidad inicial desde posiciones con ruido? Default: ajuste lineal de 5 frames (D12).

## 8b. Recorte al tramo frontal (✅ D(45°), persistencia 5, opción 1; decidido por el grupo el 11/11)

Pedido de la cátedra (vie 6/11, oral): analizar solo el tramo en que los peatones se mueven enfrentados. Exploración: `scripts/graph_gen/trim_explore.py`, salida en `outputs/recorte/`. Implementación en el motor: `data/FrontalTrim.java` (el evento conserva las trayectorias completas y guarda ventana, frame del target y frame inicial de v_d; así el rumbo de los bordes no cambia al recortar de nuevo y el recorte es idempotente). El tramo de Java coincide frame a frame con el del script en los 19 eventos.

- **Criterio vigente:** D(45°): frames comunes con los dos peatones a ≤ 45° del eje x, el izquierdo con vx > 0 y el derecho con vx < 0; interrupciones de menos de 5 frames cerradas; bloque que contiene el frame de distancia mínima real (si ese frame no cumpliera, el bloque más largo; no pasa en ningún evento).
- **Opción 2 (solo sensibilidad, `--trim-target own`):** misma ventana; target al final del tramo frontal propio de cada peatón (mismo criterio con su rumbo solo, bloque que contiene el mínimo), si termina después de la ventana; v_d desde el inicio de la ventana hasta ese target.

Decisiones de procesamiento tomadas por la IA para la exploración (no ajustan ningún ECM):
- **Rumbo:** ángulo entre la velocidad y el sentido de avance sobre x, con diferencia centrada de ±2 frames (≈ 0,27 s) y tiempos reales en los huecos; en los bordes, diferencia hacia un lado. ±2 frames supera el ruido de seguimiento (σ ≈ 1 cm, D12) sin borrar el esquive. Sensibilidad con ±1 y ±4 en `sensibilidad_suavizado.txt`.
- **Bloque de A y D:** bloque contiguo de frames comunes que cumplen y contienen el frame de distancia mínima real. Un hueco de frames no corta el bloque, porque no hay dato que lo contradiga.
- **D (persistencia):** A con las interrupciones de menos de 5 frames (0,33 s) cerradas, para que un frame ruidoso no parta el tramo.
- **C:** x_c = x media de los dos en el frame de distancia mínima.
- **Zona de interacción** (para el desvío lateral y el inicio del esquive): frames comunes alrededor del mínimo con distancia ≤ 5 m. Con 5 m, el rumbo máximo dentro de la zona es ≤ 31° en los 38 peatones, así que no incluye la subida vertical. Con |x − x_c| ≤ 4 m sí la incluía: detectaba "desvíos" de 1,3 a 1,8 m que eran el tramo vertical.
- **Inicio del esquive:** último frame antes del desvío máximo con |desvío| ≤ 20% del máximo.
- **Marcas:** "poco antes" si quedan menos de 4,5 s antes del mínimo (el t_a máximo útil de los mejores pares). "Poco después" si quedan menos de 2 s después (4τ; se informan también 1 y 3 s). Un evento con menos de 30 frames comunes se lista aparte.

### 8c. Cola fuera de la zona compartida en los eventos 3 y 6 (✅ compuerta con X = 1,5 m, aprobada por el grupo el 11/11; umbral post-hoc)
- **Problema:** lo detectó la verificación visual del 11/11. En el 3 y el 6, el tramo D(45°) del peatón izquierdo sigue 2,62 y 2,43 m más allá de la x inicial del derecho.
- **"Tramo espacial compartido" sin compuerta:** no se implementó. Cambiaría 8 eventos (ver `docs/ia/correcciones.md`).
- **Discriminadores sin simular** (`scripts/graph_gen/trim_discriminators.py`, salida en `outputs/recorte/discriminadores.md`), por peatón sobre su tramo; a nivel evento, el máximo de los dos:
  - (a) sobrepaso en x;
  - (b) ángulo de la cuerda;
  - (c) e_target en el mínimo y en el primer segundo;
  - (d) excursión lateral de la cola.
- **Margen claro (decisión de la IA):** el 3 y el 6 son los dos primeros, y el hueco entre el menor de ellos y el mayor de los otros 17 es de al menos 25% de ese mayor. En (c) además tiene que superar el cambio que produce el suavizado (±1 contra ±2 frames). Es un criterio fijado para esta comparación; se informa el número exacto.
- **Resultado:** separan con margen claro
  - (a): 2,43 contra 0,95 m del evento 10, hueco de 157%;
  - (b): 6,68° contra 1,71° del evento 14, hueco de 291%;
  - (c) en el primer segundo: 6,68° contra 2,71°, hueco de 146%; ruido del suavizado, 1,06°;
  - (d): 0,89 contra 0,25 m del evento 4, hueco de 262%.
  - No separa (c) en el mínimo: el evento 13 tiene 12,69° y el 6, 7,21°.
- **Decisión (11/11):** opción 1 con X = 1,5 m, `--trim-shared on` por defecto. Implementada en `FrontalTrim.sharedEnd`. Reproduce el ajuste manual: 90 frames comunes en el 3 y 83 en el 6. X se fijó después de ver los 19 eventos, así que el resultado se reporta como post-hoc, igual que la zona exploratoria de F.
- **Opciones que se evaluaron:**
  1. Una regla con compuerta, por ejemplo "si el sobrepaso del izquierdo pasa X m, la ventana termina donde pasa la x inicial del derecho", con X en cualquier valor entre 1 y 2,4 m. Es post-hoc: el umbral se elige después de ver los 19 eventos.
  2. Dejar D(45°) y documentar el corte del 3 y el 6 como ajuste manual tras la verificación visual (`outputs/recorte/ajuste_manual/`).

## 9. Glosario

| Símbolo | Significado |
|---|---|
| x_i, v_i | posición y velocidad del peatón i |
| e_t | versor hacia el target final |
| v_d | rapidez media de la trayectoria experimental |
| t_a | horizonte de anticipación (s) |
| ℓ, k | desplazamiento lateral (m) y ganancia (adim.) |
| A_p, B_p | intensidad (adim.) y alcance (m) en F |
| ρ | espacio personal (m) |
| d_min, t* | distancia mínima predicha y su tiempo |
| δ_s | umbral de desempate de la regla de lado, \|s_c\| ≤ δ_s (m); es el ε = 0,05 m de la sección 5, renombrado en la presentación para no confundirlo con ε_ij del contacto |
| θ_d | ángulo de rotación del desempate de F (5°, sección 5) |
| D^exp, D^sim | distancia mínima entre los centros de los dos peatones en la ventana, real y simulada (m); no confundir con d_min, que es la predicha por la capa |
| c | corrimiento del mínimo, t(D^sim) − t(D^exp) (s), con t = 0 al inicio de la ventana; "llega tarde" si c > 0 |
| ECM 1, ECM 2 | errores a mismos instantes y al punto más cercano |
| ⟨E⟩ | error poblacional |
