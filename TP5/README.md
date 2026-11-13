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
El motor (lo que va al ZIP) escribe `evento_XX.txt` (`t x1 y1 vx1 vy1 x2 y2 vx2 vy2`, cada Δt_exp/4; `NaN` si el peatón ya se retiró). Con `--layer a|b|f --p1 X --p2 Y` corre con capa de elusión. `java -jar target/tp5.jar --help` lista comandos y opciones.

El análisis (fuera del ZIP) corre el mismo motor y además escribe `ecm.txt` (ECM 1 en sus dos variantes, ECM 2, N_m, llegadas, distancia mínima, contacto y poblacional), las grillas y el recorte exportado:
```bash
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain baseline --data data --out outputs/baseline
java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain grid --layer a --p1-values 3 --p2-values 0.5 --out outputs/grid_A.txt
```

## Scripts (desde `TP5/`)
- `scripts/sim_gen/generate_baseline.sh`: compila, prueba y genera la línea base.
- `scripts/sim_gen/validate_dt.sh`: prueba de Δt de D11 sin capa (Δt_exp/32, /64 y /128).
- `scripts/sim_gen/sensitivity_v0.sh`: sensibilidad de D12 (3, 5 y 7 frames).
- `scripts/graph_gen/noise.py`: ruido de seguimiento con segundas diferencias.
- `scripts/graph_gen/compare_runs.py`: compara corridas.
- `scripts/sim_gen/pilot.sh`: piloto de capas (grillas de la especificación y diagnóstico fuera de ellas).
- `scripts/graph_gen/pilot_analysis.py`: mejores pares, superficies y comparación pareada del piloto.
- `scripts/sim_gen/sensitivity_v0_layers.sh`: sensibilidad de D12 sobre los mejores pares.
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
- `tools/build_zip.sh`: arma y verifica el ZIP de entrega.
