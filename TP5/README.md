# TP5 — Dinámica peatonal (Problema 1)

Valores y decisiones: `docs/plan/DEFINICIONES.md`.

## Requisitos
- JDK 21 o más nuevo y Maven 3.6.3 o más nuevo.
- Para los scripts: Bash (Linux, macOS o Git Bash en Windows) y Python 3 con numpy.

## Compilar
```bash
mvn package
```
Genera `target/tp5.jar` y corre los tests, que usan los datos de `data/`.

## Ejemplo
```bash
java -jar target/tp5.jar baseline --data data --out outputs/baseline
java -jar target/tp5.jar run --event 3 --data data --out outputs/run
```
El motor (lo que va al ZIP) escribe `evento_XX.txt` (`t x1 y1 vx1 vy1 x2 y2 vx2 vy2`, cada Δt_exp/4; `NaN` si el peatón ya se retiró). Con `--layer a|b|f|e --p1 X --p2 Y` corre con capa de elusión. Con `--model cpm` corre el CPM en lugar del SFM (r_min = 0,10 m, r_max = 0,25 m, β = 0,9, τ = 0,5 s, Δt = r_min/(2 v_max)), con las mismas capas; la salida agrega `r1 r2`. `java -jar target/tp5.jar --help` lista comandos y opciones.

El análisis (fuera del ZIP) corre el mismo motor y además escribe `ecm.txt` (ECM 1 en sus dos variantes, ECM 2, N_m, llegadas, distancia mínima, contacto y poblacional), las grillas y el recorte exportado:
```bash
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain baseline --data data --out outputs/baseline
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer a --p1-values 3 --p2-values 0.5 --out outputs/grid_A.txt
```

## Scripts (desde `TP5/`)
- `scripts/graph_gen/shared_vs_per_pedestrian.py`: anexo de ECM 1 que compara, por evento, un par compartido (2p) con un par por peatón (4p). Usa las grillas completas A/B/E de `outputs/ped_abe_20261115_111241`, verifica sus hashes y que las diagonales reproduzcan las grillas amplias actuales, y repite con el motor actual los 57 óptimos por peatón. Ambas opciones se optimizan sobre la **misma grilla amplia**, con ambos peatones interactuando; es una comparación de ajuste por evento, distinta de la calibración refinada de las diapositivas principales. Grafica la diferencia de errores medios con error estándar de las diferencias pareadas; guarda datos y verificación en `outputs/compartido_vs_por_peaton/`, figuras `compartido-vs-por-peaton-ecm1.{pdf,png}` y la diapositiva `presentacion/comparacion_por_peaton.tex`. Ejecutar `.venv/bin/python scripts/graph_gen/shared_vs_per_pedestrian.py`; `--plots-only` regenera la figura desde su resumen verificado.
- `scripts/graph_gen/refined_cross_validation.py`: validación cruzada de A/B/E y ambas métricas con 5000 particiones aleatorias de 14 eventos de entrenamiento y 5 de validación, semilla 20261116 y particiones comunes. Repite la grilla amplia y los dos refinamientos /5 **usando exclusivamente entrenamiento**, igual que (b); las ventanas de otra partición no se incorporan a sus candidatos. Reutiliza errores por par/evento y simula solo los pares faltantes, con `AnalysisMain grid --pairs-file` (dos columnas, sin producto cartesiano). Ejecutar `mvn package` y `.venv/bin/python scripts/graph_gen/refined_cross_validation.py --reuse`; `--plots-only` reconstruye el análisis con la caché existente. Guarda particiones, parámetros elegidos, errores, procedencia y resumen en `outputs/validacion_refinada/`; genera figuras `validacion-refinada-ecm*.{pdf,png}` y dos diapositivas de resultados en `presentacion/validacion_cruzada.tex`. Compara validación con el mínimo de (b) y reporta media ± desvío entre particiones, no error estándar. El control con los 19 eventos reproduce exactamente (b). Verificación: `.venv/bin/python -m unittest discover -s scripts/graph_gen -p 'test*cross_validation*.py'`.
- `scripts/graph_gen/refined_event_figures.py`: regenera los cuatro gráficos por evento de las diapositivas 25, 28, 29 y 30 con los óptimos refinados de `outputs/calibracion_poblacional/resumen.json`. ECM 1 usa su propio óptimo poblacional y ECM 2 el suyo; vuelve a simular y verifica los errores originales contra las grillas. Detecta los eventos que se espejan usando las corridas nuevas de ECM 2 y aplica ese mismo conjunto a ECM 1, como en la comparación anterior. Conserva una escala común entre cada gráfico original y su versión espejada, sin recortar barras. Ejecutar `.venv/bin/python scripts/graph_gen/refined_event_figures.py`; `--plots-only` reutiliza los resultados si la procedencia coincide. Guarda corridas, datos y metadatos en `outputs/eventos_optimos_refinados/` y actualiza los cuatro PDF/PNG `presentacion/figuras/errores-por-evento-ABE-ecm*.{pdf,png}`.
- `scripts/graph_gen/individual_calibration.py`: calibración individual del punto (c), con **un par por evento, compartido por sus dos peatones**, para ECM 1 y ECM 2 por separado. Después de `mvn package` y de la calibración poblacional, ejecutar `.venv/bin/python scripts/graph_gen/individual_calibration.py`. Parte de todos los pares evaluados en (b), refina dos veces cada mínimo por evento (paso /5, mismos límites) y selecciona cada mínimo en la unión de muestras de ambas métricas del propio evento. Usa `AnalysisMain grid --event N` para simular únicamente el evento que se refina. `--reuse` reutiliza corridas con los mismos ejes, opciones, JAR y datos; `--plots-only` regenera el análisis desde los archivos existentes. Guarda los parámetros y errores de los 19 eventos, las ganancias y la procedencia en `outputs/calibracion_individual/`; genera las distribuciones de parámetros y errores en `presentacion/figuras/individual-*.{pdf,png}` y tres diapositivas en `presentacion/calibracion_individual.tex`: una diapositiva por capa con parámetros óptimos a la izquierda y distribución de errores a la derecha (`individual-*-ecm1.pdf`). Los resultados de ambas métricas siguen disponibles en los datos y las figuras de consulta. En los gráficos de parámetros, el tamaño y la anotación ×N indican óptimos coincidentes; en los de errores, cada línea une el error poblacional e individual del mismo evento, y las cajas muestran la distribución. La ganancia global compara los promedios, no el promedio de los porcentajes de mejora. La referencia usa el óptimo poblacional de la misma métrica, y la ganancia corresponde al ajuste a esos mismos eventos.
- `scripts/graph_gen/population_calibration.py`: calibración poblacional SFM de A, B y E, con ECM 1 y ECM 2 por separado. Después de `mvn package`, ejecutar `.venv/bin/python scripts/graph_gen/population_calibration.py` (numpy y matplotlib). Corre las grillas amplias de la presentación y dos refinamientos por métrica: ventana de ± un paso anterior, paso dividido por 5, sin salir de los rangos definidos; selecciona cada mínimo sobre la unión de los pares evaluados. Guarda los errores por evento, `resumen.json` y `comparacion.csv` en `outputs/calibracion_poblacional/`; genera mapas y cortes en `presentacion/figuras/calibracion-*.{pdf,png}` y las tres diapositivas de resultados en `presentacion/calibracion_resultados.tex`. Los cortes fijan exactamente el otro parámetro en el óptimo; las barras son ± error estándar entre los 19 eventos, no incertidumbre del parámetro. `--reuse` reutiliza grillas cuyos ejes coinciden; `--plots-only` solo regenera figuras y diapositivas desde estas corridas. Compilar después con `bash presentacion/build_presentacion.sh`. Las diapositivas 17–20 muestran esta calibración refinada; los demás análisis mantienen los pares de la grilla amplia original.
- `scripts/sim_gen/generate_baseline.sh`: compila, prueba y genera la línea base.
- `scripts/sim_gen/validate_dt.sh`: prueba de Δt de D11 sin capa (Δt_exp/32, /64 y /128).
- `scripts/sim_gen/sensitivity_v0.sh`: sensibilidad de D12 (3, 5 y 7 frames).
- `scripts/graph_gen/noise.py`: ruido de seguimiento con segundas diferencias.
- `scripts/graph_gen/compare_runs.py`: compara corridas.
- `scripts/sim_gen/pilot.sh`: piloto de capas (grillas de la especificación y diagnóstico fuera de ellas).
- `scripts/graph_gen/pilot_analysis.py`: mejores pares, superficies y comparación pareada del piloto.
- `scripts/sim_gen/sensitivity_v0_layers.sh`: sensibilidad de D12 sobre los mejores pares: 3, 5 y 7 cuadros y módulo inicial igual a la rapidez deseada (`v_d = longitud experimental / duración`), conservando la dirección del ajuste de 5 cuadros. Usa `.venv/bin/python` (configurable con `PYTHON`). Después, `.venv/bin/python scripts/graph_gen/presentation_figures.py 11 V0` actualiza `presentacion/figuras/V0-sensibilidad.pdf` con las cuatro variantes. La configuración habitual del motor sigue siendo el ajuste de 5 cuadros.
- `scripts/sim_gen/sensitivity_rho.sh`: sensibilidad a ρ sobre los mejores pares.
- `scripts/graph_gen/pilot_compare.py`: F por criterio de desempate y con B_p fijo.
- `scripts/graph_gen/per_event.py`: comparación de capas evento por evento.
- `scripts/graph_gen/cross_validation.py`: validación de D8 sobre las grillas del piloto.
- `scripts/graph_gen/trace_report.py`: contactos y causa de las conmutaciones, con `diagnostics/RunTrace` (no va al ZIP).
- `scripts/sim_gen/regenerate_pilot.sh`: regenera el piloto completo y sus análisis, en orden.
- `scripts/sim_gen/audit_f.sh` y `scripts/graph_gen/audit_f.py`: auditoría de las capas (contacto, lado, conmutaciones, espejo, horizonte de F y Δt /64 contra /128).
- `scripts/graph_gen/tie_2x2.py`: F con Δt /32 y /64 y desempate viejo y nuevo.
- `scripts/sim_gen/variants.sh` y `scripts/graph_gen/f_variants.py`: variantes declaradas F1, F2 y F3.
- `scripts/graph_gen/layer_checks.py`: recuperación de parámetros, lado por moneda y piso de error (las dos primeras con `diagnostics/LayerChecks`, que no va al ZIP).
- `scripts/sim_gen/figures.sh`, `scripts/graph_gen/f_figures.py` y `f_animation.py`: figuras y animación comparativas. Necesitan matplotlib (por defecto usan `../TP4/.venv`; cambiar con `PYTHON=...`).
- `scripts/sim_gen/egg.sh`, `scripts/animation/egg_geometry.py` y `egg_animation.py`: capa E (huevo, `--layer e --p1 a --p2 b`; actúa solo con los huevos en contacto): corridas, diagnóstico de solapes y tres animaciones de tres simulaciones cada una: la original (a = 3, b = 0,35), huevo corto (a = 1, b = 0,35) y el óptimo poblacional (a = 3, b = 0,25). `egg_animation.py --a --b --panels sub:evento,... --out` arma otras.
- `scripts/sim_gen/cpm.sh` y `scripts/graph_gen/cpm_compare.py`: capas A, B y E sobre el CPM (`--model cpm`, en el motor y en `AnalysisMain`) con las mismas grillas que en el SFM, y comparación de errores con los mismos parámetros (`outputs/cpm/comparacion.md` y `outputs/cpm/figs/`). Tarda menos de un minuto.
- `diagnostics/CpmRacetrack` (no va al ZIP; también `CpmRacetrackTest`): valida el CPM contra el paper, con el diagrama fundamental de la pista circular (juegos de parámetros 1 y 2, y la sensibilidad a r_min, r_max y β; Fig. 3, 4, 7, 8 y 9). Uso: `java -cp target/tp5.jar ar.edu.itba.sds.tp5.diagnostics.CpmRacetrack [realizaciones] [N1,N2,...]`.
- `scripts/animation/cpm_videos.py`: animaciones del CPM con A, B y E en su óptimo poblacional de cada métrica (discos de radio r(t), en rojo en contacto), en `outputs/cpm/animaciones/`. Corre después de `cpm.sh`.
- `tools/build_zip.sh`: arma y verifica el ZIP de entrega.
