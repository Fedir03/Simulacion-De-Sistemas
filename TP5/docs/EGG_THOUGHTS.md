# Capa E (huevo): exploración, resultados y lo que sugiere

Exploración del 13/11/2026, fuera del piloto de D2. La cátedra fomenta probar enfoques novedosos y ver cómo resultan: este documento junta qué se probó, qué dio y qué pistas deja. La capa E no reemplaza a A, B ni F. Los números son con la configuración vigente: tramo frontal (D3), Δt = Δt_exp/64, Beeman y los 19 eventos.

Lo que la IA agregó sin pedirse y se deshizo está en `docs/ia/correcciones.md` (entrada del 13/11).

## 1. La capa

Cada peatón lleva un espacio personal con forma de huevo, con la punta hacia su velocidad. En su marco (u hacia el rumbo, w lateral):

- atrás (u ≤ 0): medio círculo de radio b;
- adelante (0 ≤ u ≤ a): |w| ≤ b (1 − (u/a)²)^q, con la punta a una distancia a del centro.

Con a ≥ b y q ∈ [1/2, 1] el huevo es convexo.

**Reacción, solo con los huevos en contacto** (`engine/layer/EggLayer.java`):

| Estado | e_target |
|---|---|
| Huevos separados | e_t: el SFM sin capa, sin cambios |
| En contacto | Se quita la componente de e_t que entra en el huevo del otro: se desliza por la tangente, como contra un borde sólido. En el choque frontal exacto, a la derecha |
| Solapados (por Δt o porque la velocidad tarda τ en seguir a e_target) | Además gira en sentido contrario al solape: componente normal hacia afuera proporcional a la profundidad |

Cuando los huevos dejan de tocarse vuelve e_t, así que retoma solo el camino al target final.

**Geometría:** la distancia con signo entre los huevos es max_n [n·(x_i − x_j) − h_j(n) − h_i(−n)], con h la función soporte de cada huevo. Es negativa si se solapan, y el n que la maximiza es la normal del contacto. Se evalúa en 180 direcciones.

**Forma del enunciado:** mientras los huevos se tocan, el target final se reemplaza por el target temporal x_T = x_i + a·e_target, en la punta del huevo. Solo cambia la dirección de la velocidad deseada (su módulo sigue siendo v_d), no se agrega ninguna fuerza y el SFM no se toca.

**Parámetros calibrables:** p1 = a (largo de la punta) y p2 = b (semiancho, igual al radio de atrás). Constantes declaradas: q = 0,75 (qué tan aguzada es la punta), escala de profundidad 0,05 m (cuánto gira por cm de solape), desempate a la derecha y 0,05 m/s (por debajo, el huevo apunta a e_t). Uso: `--layer e --p1 a --p2 b`.

## 2. Cómo evolucionó

| Versión | Qué hacía | ECM 1 / ECM 2 (m²) | Dónde empezaba a girar |
|---|---|---|---|
| Predictiva (a = 1, b = 0,35, T = 2 s), descartada | Menor giro desde e_t sin contacto de huevos en el horizonte T | 0,420 / 0,038 | Centros a unos 6,1 m |
| Solo contacto (a = 1, b = 0,35) | La de la sección 1 | 0,589 / 0,078 | Centros a unos 1,96 m (contacto de las puntas) |
| Solo contacto, huevo largo (a = 3, b = 0,35) | Igual, con la punta tres veces más larga | 0,448 / 0,050 | Centros a unos 6 m |

- **Versión solo contacto con a = 1:** solape máximo 1,4 cm, sin contacto de cuerpos y giro máximo de 45° a 60°. Entre Δt_exp/64 y /128 el ECM 1 cambia 0,13%; con Δt_exp/4 el solape llega a 3,6 cm.
- **Huevo largo (a = 3):** solape máximo 2 mm (72 de 7759 filas) y giro más suave (velocidad angular máxima mediana de 58 °/s, contra 79 °/s con a = 1). Con Δt_exp/4 el solape llega a 7 mm.
- **Animación:** `bash scripts/sim_gen/egg.sh` corre todo y escribe `outputs/egg/egg_animation.mp4`, con tres simulaciones: eventos 2 y 14, y el 19 con paso grueso.

## 3. Comparación con A, B y F

Grillas oficiales de A, B y F (`scripts/sim_gen/pilot.sh`) y grilla de E con a de 0,5 a 6 m y b de 0,25 a 0,5 m. La validación cruzada usa 5000 particiones de 14 eventos de entrenamiento y 5 de validación, con semilla fija.

| | A | B | F | E | E sin contacto (b ≥ 0,30) |
|---|---|---|---|---|---|
| Mejor par (ECM 1) | (3; 0,5) | (3,5; 1) | (0,9; 3), borde | (3; 0,25), borde | (3; 0,30) |
| ⟨ECM 1⟩ ± error estándar | 0,428 ± 0,062 | **0,413** ± 0,062 | 1,396 ± 0,143 | 0,418 ± 0,060 | 0,430 ± 0,061 |
| ⟨ECM 2⟩ | 0,046 | **0,041** | 0,240 | **0,041** | 0,045 |
| Validación ECM 1 / ECM 2 | 0,451 / 0,058 | **0,422 / 0,050** | 1,422 / 0,242 | 0,432 / 0,053 | 0,446 / 0,060 |
| Ganancia individual (2 parámetros), ECM 2 | 32% | 28% | 9% | 43% | 44% |
| Eventos con contacto de cuerpos | 0 | 0 | 17 | 8 | 0 |
| Distancia mínima simulada (real: 0,49 a 0,92 m) | 0,51 a 0,85 | 0,50 a 0,64 | 0,45 a 0,62 | 0,50 en todos | 0,60 en todos |
| Llegada al mínimo respecto del real (mediana) | +0,40 s | +0,41 s | +0,24 s | +0,39 s | +0,39 s |
| Conmutaciones máximas por peatón | 2 | 2 | 2 | 150 | 142 |

Sin capa: ECM 1 = 3,18 y ECM 2 = 1,94, con contacto en los 19 eventos.

**Lectura:**
- **Empate con A y B:** las diferencias de error (0,41 a 0,43) son una fracción del error estándar (±0,06). B queda apenas adelante en todas las métricas.
- **Debilidades propias de E:**
  - su óptimo en b queda en el borde de la grilla, donde los cuerpos se tocan;
  - la distancia mínima es exactamente 2b en todos los eventos;
  - conmuta muchas veces: e_target alterna entre e_t y la tangente mientras desliza. Las trayectorias quedan suaves porque la velocidad tarda τ en seguir.
- **Ventajas de E:**
  - parámetros con lectura física directa (alcance y distancia de paso), sin ρ ni predicción de choque;
  - la mayor ganancia en la calibración individual de ECM 2.
- **⚠️ Post-hoc:** la grilla de E se eligió después de ver sus resultados. Su validación no es tan limpia como la de A y B, igual que la zona exploratoria de F.

**Sensibilidad a las constantes** (a = 3, b = 0,35; después, la grilla a × b):

| Variante | ECM 1 | ECM 2 | Mejor par de la grilla |
|---|---|---|---|
| Vigente (q = 0,75; escala 0,05 m) | 0,448 | 0,0499 | (3; 0,30) |
| q = 0,5 (punta redondeada) | 0,445 | 0,0487 | (3; 0,30) |
| q = 1 (punta con ángulo) | 0,451 | 0,0507 | (3; 0,30) |
| Escala 0,02 m | 0,452 | 0,0499 | (3; 0,30) |
| Escala 0,2 m | 0,446 | 0,0499 | (3; 0,30) |

Mueven el error menos de 1% y el óptimo no cambia. Tampoco servirían como tercer parámetro: la superficie es plana en esas direcciones.

## 4. Calibración individual por peatón (punto c opcional)

La cátedra: *"2 c) OPCIONAL: optimizar parametros por cada peatón (en lugar de 1 juego de parametros por cada par de peatones). Notar que el caso opcional, requiere hallar 4 parametros en lugar de solo 2."*

**Implementación:**
- `Layers.perPedestrian` en el motor: el peatón 2 usa `--p1-ped2` y `--p2-ped2`.
- En E, cada uno lleva su huevo y ve el del otro, así que los dos ven el mismo contacto.
- `AnalysisMain grid-ped` corre, por evento, todas las combinaciones (par del peatón 1) × (par del peatón 2). Los dos peatones interactúan, así que no se pueden calibrar por separado.

| | Poblacional | 2 parámetros por evento | 4 parámetros por evento |
|---|---|---|---|
| B, ECM 1 | 0,413 | 0,402 (−3%) | **0,375 (−9%)** |
| B, ECM 2 | 0,041 | 0,029 (−28%) | **0,008 (−81%)** |
| E, ECM 1 | 0,418 | 0,397 (−5%) | **0,386 (−8%)** |
| E, ECM 2 | 0,041 | 0,023 (−43%) | **0,015 (−64%)** |

**Lectura:**
- **Pares distintos:** en 17 o 18 de los 19 eventos los dos peatones prefieren pares distintos.
- **Óptimos en el borde de la grilla:**
  - en E, en los 19 eventos algún parámetro queda en el borde: las medianas por peatón son a = 5,5 m (ECM 1) y 6 m (ECM 2), con 6 m como máximo de la grilla, y b = 0,25 m, el mínimo;
  - en B, en 7 de 19 (ECM 2) y 14 de 19 (ECM 1).
- **Cota superior:** 4 parámetros sobre un solo evento siempre bajan el error, y parte de eso es sobreajuste.

## 5. Lo que sugiere: el huevo tiende a la detección más lejana posible

La hipótesis: si el huevo óptimo tiende a alargarse, la capa "quiere" detectar el choque lo antes posible. Los datos la confirman, pero con un matiz: en este conjunto de datos "lo más lejos posible" quiere decir "desde el primer frame de la ventana".

**Evidencia:**
- **Distancia al inicio:** las ventanas (tramo frontal) arrancan con los centros a 6,8–7,6 m (mediana 7,4 m).
- **Población:** el ECM 1 baja hasta a ≈ 3–3,5 m y después queda casi plano:

  | a (m) | 0,5 | 1 | 1,5 | 2 | 2,5 | 3 | 3,5 | 4 | 5 | 6 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | ECM 1, b = 0,25 | 1,164 | 0,708 | 0,539 | 0,465 | 0,430 | **0,418** | 0,419 | 0,424 | 0,425 | 0,436 |
  | ECM 1, b = 0,30 | 0,953 | 0,533 | 0,479 | 0,456 | 0,439 | **0,430** | 0,432 | 0,437 | 0,438 | 0,450 |

  Con a = 3 m las puntas se tocan con los centros a a₁ + a₂ = 6 m, o sea apenas empieza la ventana. Más largo no adelanta la reacción: solo cambia la forma del deslizamiento.
- **Calibración por evento (2 parámetros):** el mejor a es 4,5 m o más en 14 de 19 eventos (ECM 1).
- **Calibración por peatón (4 parámetros):** el óptimo hace que los huevos se toquen desde t = 0 en 18 de 19 eventos (ECM 1) y en 15 de 19 (ECM 2). Además, los dos peatones difieren (|a₁ − a₂| mediano de 1,5 m en ECM 1): uno reacciona antes que el otro, como en los eventos reales donde uno hace la mayor parte del esquive.
- **A y B dicen lo mismo:** sus mejores horizontes (t_a = 3 y 3,5 s) superan los ~2,8 s que se tarda en cerrar 7,4 m a ~2,6 m/s de velocidad relativa. También actúan desde el principio de la ventana.

**Consecuencias:**
1. **El alcance de la detección casi no se puede calibrar con estos datos.** Más allá de la distancia de inicio de la ventana, la superficie de error es casi plana, así que el valor que sale es en buena parte arbitrario. Vale para a de E y para t_a de A y B, y conviene decirlo en la presentación.
2. **Lo que sí se puede calibrar es cómo reaccionan:** cuán separados pasan y cuán bruscamente giran. E captura lo primero con b, y lo segundo solo indirectamente, con la forma del huevo.
3. **La versión predictiva reaccionaba lejos, y los datos la favorecen.** La que el usuario pidió sacar (sección 2) giraba a ~6 m y daba ECM 1 = 0,420 sin calibrar. No es razón para volver a ella, pero coincide con la intuición de que el huevo "quiere" ver lejos.
4. **El ECM 1 está dominado por el tiempo, no por la forma:**
   - ECM 2 ≈ 0,04 m² (unos 20 cm RMS) contra ECM 1 ≈ 0,42 m² (unos 65 cm RMS);
   - todas las capas llegan al mínimo ~0,4 s tarde (atraso del modelo: relajación con τ = 0,5 s);
   - la calibración individual con 2 parámetros baja el ECM 1 solo entre 3 y 6% en A, B y E.

   Una capa que solo cambia la dirección no puede corregir ese atraso, y un rodeo más grande lo empeora. Mejorar la capa rinde en ECM 2, casi nada en ECM 1.

## 6. Otro enfoque: "ver" al otro desde lejos

Si lo que manda es reaccionar en cuanto el otro está a la vista, una figura más natural que el huevo es un campo visual. Dos trabajos con ese enfoque:

- **Moussaïd, M., Helbing, D. & Theraulaz, G. (2011). How simple rules determine pedestrian behavior and crowd disasters. *PNAS*, 108(17), 6884–6888.**
  - **Cómo decide:** el peatón recorre las direcciones α dentro de su campo visual ±φ. Para cada una calcula f(α), la distancia que podría caminar antes de chocar (con los demás a velocidad constante, hasta un alcance d_max), y elige la que lo deja más cerca del objetivo: d(α)² = d_max² + f(α)² − 2 d_max f(α) cos(α₀ − α).
  - **Encaje con el enunciado:** solo cambia la dirección, usa el "ver" y es el más defendible de los dos.
  - **Parámetros:** por lo de la sección 5, d_max quedaría fijo, al menos tan grande como la distancia de inicio de la ventana y justificado con esos números. Se calibrarían el ángulo de visión φ y una distancia de paso (lo que los datos sí determinan).
- **Ondřej, J., Pettré, J., Olivier, A.-H. & Donikian, S. (2010). A synthetic-vision based steering approach for crowd simulation. *ACM Transactions on Graphics*, 29(4), 123 (SIGGRAPH 2010).**
  - **Cómo decide:** usa el ángulo con que se ve al otro (bearing angle) y su derivada. Si ese ángulo casi no cambia y el tiempo hasta el encuentro es corto, hay curso de colisión, y el peatón gira para que el ángulo cambie más rápido.
  - **Parámetros:** dos naturales (umbral de tiempo y ganancia del giro).
  - **Riesgo:** es más novedoso, pero más difícil de explicar y de calibrar.

## 7. Otras ideas que se discutieron

- **Combinarlo con CPM haciendo que el huevo sea la forma del radio:** no vale. En CPM el radio que crece y se achica entre r_min y r_max es una regla del modelo, y el enunciado dice que la capa *"no puede agregar fuerzas ni modificar las reglas propias del modelo"*.
  - **CPM con la capa E encima sí vale,** pero obliga a implementar y validar otro modelo (con su Δt como parte de las reglas) y a rehacer la línea base y la calibración.
  - **Paralelo útil para la presentación:** el "giro al revés" de E con los huevos solapados es la misma idea que la velocidad de escape de CPM en el contacto.
- **Contacto suave:** pasar de e_t a la tangente de forma gradual en los últimos centímetros de separación (por ejemplo 5 cm). Saca las conmutaciones, a costa de empezar a girar esos centímetros antes del contacto.
- **Largo proporcional a la velocidad:** a = t_a·|v|. El primer parámetro pasa a ser un tiempo, como t_a de A y B, y la comparación es más limpia. Pero por la sección 5, t_a tampoco sería identificable más allá del inicio de la ventana.
- **Huevo orientado según la velocidad relativa (v_i − v_j):** la punta apunta adonde ocurriría el choque. Es lo más cercano a "detectar colisiones" sin dejar de ser geométrico.
- **Ancho como margen sobre el cuerpo (b = r + m, m ≥ 0):** la falta de contacto queda en la definición y no es un borde de la grilla. Es cosmético: el óptimo quedaría en m = 0.
- **Reparametrizar el huevo:** si el largo satura, fijarlo largo y calibrar b y q.

## 8. Cómo reproducir

```bash
mvn package
bash scripts/sim_gen/egg.sh                                   # sin capa, E(3; 0,35), paso grueso, solapes y animación
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer e \
  --p1-values 0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6 --p2-values 0.25,0.3,0.35,0.4,0.45,0.5 --out outputs/egg/grid_E.txt
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid-ped --layer b \
  --p1-values 0.5,1,1.5,2,2.5,3,3.5,4,4.5,5 --p2-values 0,0.5,1,1.5,2,2.5,3,3.5,4 --out outputs/egg/ped_B.txt   # ~1 min; E tarda ~10 min
python3 scripts/animation/egg_geometry.py outputs/egg/e_3_0.35 3.0 0.35   # solapes de huevos en cualquier corrida
```
