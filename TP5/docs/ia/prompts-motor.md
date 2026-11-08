# Prompts enviados al agente para construir el motor

Anexo de la declaración de uso de IA (anuncio de la cátedra "Criterios de Evaluación TP4 y TP5").

**Reglas:**
- Solo prompts usados para construir el **motor**: parser, SFM, capa, ECM y formatos de entrada y salida. No van los de análisis, figuras, presentación ni plan.
- Cada entrada lleva fecha, autor y una marca: **"textual"** (copiado tal cual, sin corregir ni resumir) o **"reconstruido"** (reconstruido a partir del plan, cuando no se guardó el original).
- No hace falta cargar todos los prompts usados: alcanza con los que muestran cómo se construyó cada parte del motor.
- Cada integrante completa su sección.

Plantilla por entrada:

```
### AAAA-MM-DD · <autor> · <parte del motor> · <agente/modelo> · textual | reconstruido
<prompt (textual o reconstruido)>
```

## Fede

### 2026-11-03 · Fede · Estructura, parser, SFM, ECM y línea base · Claude Code (Opus 5.5) · textual
Creá la estructura del repo del TP5 como la del TP4: src/ (paquete ar.edu.itba.sds.tp5, Java 21 y Maven, con tests JUnit), scripts/, docs/plan/, docs/ia/, presentacion/, tools/, data/ y outputs/ (ignorado por git). Copiá tools/build_zip.sh del TP4 y adaptalo al nombre SdS_TP5_2026Q2G02CS_Codigo, con los mismos controles (pesa menos de 100 KB, compila en carpeta aislada y reproduce una corrida). Poné DEFINICIONES.md y ESTADO.md en docs/plan/. Después, siguiendo DEFINICIONES.md y sin hacer commit, implementá: (1) un parser de los 19 eventos desde elusion_1_contra_1.txt y LEEME_elusion1contra1.txt, con la ventana común y el target y v_d de la trayectoria completa; (2) el SFM sin fuerza social para 2 agentes con Δt = Δt_exp/32 y salida cada 8 pasos; (3) ECM 1 y ECM 2; (4) la línea base sin capa para los 19 eventos. Cada etapa con sus tests. No uses la capa de elusión todavía.

Integrador: que compare Verlet y Beeman contra la solución analítica del peatón libre, y que use el que cumpla mejor. Es la prueba de D11.
Commits: en el prompt está explícito que no haga commit. Eso lo hacen ustedes después de revisarlo.

### 2026-11-03 · Fede · Llegada al target (D13) y velocidad inicial (D12) · Claude Code (Opus 5.5) · textual
Pregunta 1: llegada al target antes del último instante

El peatón real no se detiene en su target: el target es solo la última posición observada y el peatón sigue caminando fuera de la ventana de medición. Por eso no se frena ni se detiene a nadie. El peatón simulado sigue a su rapidez deseada v_d hasta llegar al target final, y al llegar se retira de la simulación, igual que en el Problema 2 del enunciado, donde los agentes se retiran al cruzar la puerta. Se considera que llegó cuando queda a distancia δ_a ≤ 0,1 m del target (constante declarada; se verifica en las pruebas que todos los peatones llegan y no dan vueltas alrededor del target). Esta regla no es parte de la capa de elusión, que solo reemplaza el target por uno temporal; es una condición de la simulación.

Consecuencias que hay que implementar y reportar: (1) el ECM 1 se calcula solo con los t_k en los que existe la posición simulada, así que N_m depende de cuándo llega cada peatón; hay que reportar N_m por evento y cuántos peatones llegan antes del último instante y con cuánta anticipación. (2) El ECM 2 usa toda la trayectoria simulada, que es geométrica, y no se ve afectado por el retiro. (3) Agregar una prueba que verifique, en los 19 eventos, que la llegada ocurre después del instante de máximo acercamiento entre los dos peatones, para que el retiro no cambie la interacción. Si en algún evento no se cumple, avisar antes de seguir.

Pregunta 2: velocidad experimental inicial

Se estima con la pendiente de un ajuste lineal por mínimos cuadrados sobre los primeros 5 frames de la ventana de simulación, empezando en t_0, con el mismo método para los dos peatones. No se usa la diferencia central porque con la ventana común (D3) el peatón que entra más tarde empieza en su primer frame y no tiene frame anterior; en 12 de los 19 eventos los dos peatones arrancan desfasados, y quedarían con estimadores distintos. Con ruido de seguimiento de ~1 cm a 15 fps, el error de la velocidad es de ~0,21 m/s con diferencia hacia adelante, ~0,11 m/s con diferencia central y ~0,05 m/s con el ajuste de 5 frames. El "5" es una constante de procesamiento de datos y no un parámetro del modelo: se declara y se justifica con ese análisis de ruido. Verificar primero el ruido de ~1 cm con los datos (por ejemplo con segundas diferencias), y agregar una prueba de sensibilidad que repita la corrida con 3 y con 7 frames y reporte cuánto cambia el ECM.

### 2026-11-03 · Fede · ECM 1 en dos variantes y constantes como parámetros · Claude Code (Opus 5.5) · textual
Aprobado con tres cambios. (1) En ecm.txt y en la línea base calculá el ECM 1 de dos formas: excluyendo los t_k posteriores al retiro (como está en el plan) y rellenando con la posición del target después del retiro (solo como convención de la métrica, sin simular nada); informá las dos y si cambia el orden de los eventos. (2) En DEFINICIONES.md corregí las referencias a consultas a la numeración de la sección 8 (D3 → 1, D7 → 2, D4 → 6, D5 → 4 y 5), cambiá la consulta 6 a 'imprimir cada 8 pasos, usando una de cada 4 filas para el ECM 1', y agregá las consultas 8 (qué hace un peatón al llegar al target antes del último instante) y 9 (método esperado para estimar la velocidad inicial desde posiciones con ruido). (3) Dejá las constantes δ_a y el número de frames de v_0 como parámetros con valor por defecto, no fijos en el código.

### 2026-11-03 · Fede · Capas de elusión A, B y F · Claude Code (Opus 5.5) · textual
Con la línea base lista, implementá las capas A, B y F como módulo intercambiable siguiendo la página 'Capas de elusión: especificación matemática (A, B, F)' de Notion, sin agregar fuerzas (solo cambia la dirección de e_target). Probá primero que con el parámetro nulo (ℓ = 0, k = 0, A_p = 0) dé exactamente la línea base, y que sin choque predicho la trayectoria sea idéntica. Después corré el piloto con las grillas gruesas de la página sobre los 19 eventos y reportá, para cada capa, el mejor par para ECM 1 y ECM 2, el error de entrenamiento y la forma de la superficie (en particular si F tiene un valle por la compensación entre A_p y B_p). Repetí la sensibilidad a v₀ con 3, 5 y 7 frames sobre el mejor par de cada capa. No elijas la capa: dame la tabla comparativa.

### 2026-11-04 · Fede · Desempate métrico de F y sentido de la rotación · Claude Code (Opus 5.5) · textual
1. Desempate de F: reemplazá la banda angular por el criterio métrico |s_c| ≤ 0,05 m, donde s_c es el desvío lateral al punto de máximo acercamiento previsto. Es el mismo criterio que usan A y B. Reportá F con ese criterio en la grilla oficial y en la zona ampliada, al lado de los resultados con 5° y con 1°. Así se ve cuánto de F viene de "esquivar a la derecha" y cuánto de A_p y B_p.
2. Sentido de la rotación: agregá un test que confirme que el peatón se desvía hacia su derecha, en su propio sistema de referencia. Anotá en DEFINICIONES.md que la página de especificación lo planteaba al revés o de forma ambigua (e_ij apunta hacia atrás).

### 2026-11-05 · Fede · Δt_exp/64 y corrección del desempate de F · Claude Code (Opus 5.5) · textual
Decisiones:
1. Sí a Δt_exp/64 (D4 y D11). Mantené el mismo espaciado de salida (Δt_exp/4, o sea una fila cada 16 pasos) y el mismo criterio de t_k para el ECM 1, para no reintroducir el sesgo del ECM 2. Copiá una línea base nueva a /64 para la regresión y regenerá todo el piloto: grid_A, grid_B, grid_F, por evento, validación, ρ, v_0 y oscilación.
2. Sí a corregir el desempate de F con la candidata medida, como paso separado del cambio de Δt. Tabla 2×2 de F (Δt /32 y /64; desempate viejo y nuevo) con mejor par, ECM 1, ECM 2 y contactos, para atribuir cada efecto.
3. Contacto: solo documentarlo en DEFINICIONES.md. No hacer F4.

Después de los resultados a /64:
- Repetí la convergencia con los mejores pares de las tres capas entre /64 y /128 (criterio: menos de 1%). Informá cualquiera que no cumpla.
- Informá cuántos eventos cambian más de 5% entre /64 y /128 y por qué el evento 9 es tan sensible al paso (contacto).
- Seguí con las Fases 3 a 5 usando los nuevos mejores pares.
- Actualizá DEFINICIONES.md (D4 y D11), correcciones.md y prompts-motor.md. Sin commit, sin elegir capa.

## Rucka

## Lolo
