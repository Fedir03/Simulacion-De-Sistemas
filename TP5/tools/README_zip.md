# TP5 — Dinámica peatonal (72.25 Simulación de Sistemas)
Grupo 02: Federico Ignacio Ruckauf, Federico Spivak Fontaiña, Lorenzo Chiossone

Requisitos: Java 21 y Maven. Datos de la cátedra (`elusion_1_contra_1.txt` y `LEEME_elusion1contra1.txt`) en `data/`.

Compilar (desde la raíz de este zip; genera `target/tp5.jar`): `mvn package`

Ejemplo (evento 3, capa A con t_a = 3 s y ℓ = 0,5 m):
```
java -cp target/tp5.jar ar.edu.itba.sds.tp5.Main run --event 3 --layer a --p1 3 --p2 0.5 --data data --out outputs/run
```
Otros modos: `baseline` (los 19 eventos) e `integrator-check` (control del integrador); `--help` lista las opciones.

Salida: un `evento_XX.txt` por evento en la carpeta de `--out` (`t x1 y1 vx1 vy1 x2 y2 vx2 vy2`, cada Δt_exp/4).
