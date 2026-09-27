# Figuras de la presentación

Guardar acá las figuras finales que consume `template_presentacion_tp3.tex`
vía `\maybeimage`/`\videooimagen`. Mientras no existan, las diapositivas
muestran una caja gris "figura pendiente" con la ruta esperada — no hace
falta editar el `.tex` para eso, solo agregar el archivo con el nombre
correcto.

## Regla de tamaño de fuente (corrección real recibida en TP2)

> "Los tamaños de fuente de las figuras son ilegibles, deben ser de un
> tamaño comparable con el resto de la información en la diapositiva."

Generar las figuras ya con ese tamaño de fuente (ticks, labels, leyenda)
antes de exportarlas — no depender de que Beamer las achique bien al
insertarlas. Verificar contraste y legibilidad proyectando a pantalla
completa, no solo mirando el archivo en el editor.

**Ojo con las diapositivas de Resultados (15–31):** ahí la figura vive en
una columna de `0.66	extwidth`, no en el ancho completo del frame (el
costado de `0.31	extwidth` es la caja de parámetros fijos y, si hay, el mapa
de ejemplo). Por eso todos los scripts de figuras usan `font.size = 14`
(`plot_sweep.py`, `plot_fu.py`, `plot_arquetipos.py`): no es algo que se
arregle después en el `.tex` de la presentación.

## Otras reglas de figura que aplican acá (ver skill `sims-tp-format`)

- Nunca título embebido dentro del área graficada — el `\frametitle` o el
  `\parambox` ya lo dicen.
- Labels de eje cortos: `t [s]`, `N`, `⟨t₉₀⟩ [s]`, `F_u`, `DCM [m²]`,
  `x_k [m]`. Nada de paréntesis explicando "unidades del modelo".
- Leyenda solo con lo que varía entre curvas; los parámetros fijos van en
  el `\parambox` de la diapositiva, no repetidos en cada entrada.
- Barras de error en un solo eje por figura.
- Con varias configuraciones/curvas relacionadas, paleta perceptualmente
  uniforme (Viridis/Parula), apiladas verticalmente si no entran legibles
  en una fila.

## Nombres esperados por el `.tex` actual

| Archivo | Diapositiva | Contenido |
|---|---|---|
| `sistema_real.jpg` | 3 | Foto de una mesa de metegol/billar real |
| `geometria-sistema.png` | 11 | ✅ Esquema con L, W, d, r y R_k. `plot_geometria_sistema.py` |
| `tiempo-ejecucion-vs-n.png` | 15 | ✅ ⟨t_ejec⟩ vs. N, mesa vacía (`generated/runtime.png`) |
| `vacia_frame.png` | 16 | ✅ Fotograma de la mesa vacía, semilla 141, t = 11.27 s (`generated/vacia_s141/vacia_s141.mp4`, cuadro 96, con flechas, sin la franja de texto superior) |
| `fu-temporal-vacia.pdf` | 17 | ✅ F_u(t) de esa corrida. `plot_fu.py` |
| `t90-vs-xk.png` | 18 | ✅ ⟨t₉₀⟩ vs. x_k, un disco R = 0.30 (barrido `xk`) |
| `t90-vs-r-central.png`, `mapa-central.png` | 19 | ✅ ⟨t₉₀⟩ vs. R del disco central (barrido `centro_R`) |
| `t90-vs-largo-embudo.png`, `mapa-embudo.png` | 20 | ✅ ⟨t₉₀⟩ vs. largo del embudo, dos fronteras (barridos `embudo_min`, `embudo_libre`) |
| `t90-vs-separacion-galton.png`, `mapa-galton.png` | 21 | ✅ ⟨t₉₀⟩ vs. separación de la red (barrido `galton`) |
| `t90-vs-rf-central-cuenco.png`, `mapa-central-cuenco.png` | 22 | ✅ ⟨t₉₀⟩ vs. R_f, disco central + cuenco (barrido `central_cuenco`; referencia `arq_central_R0.32`) |
| `t90-vs-desplazamiento-cuenco.png`, `mapa-cuenco-desplazado.png` | 23 | ✅ ⟨t₉₀⟩ vs. desplazamiento del centro del cuenco R_f = 0.35 (barrido `cuenco_desplazado`) |
| `elegida_frame.png` | 24, 28 | ✅ Fotograma del cuenco R_f = 0.34, semilla 140, t = 6.67 s (`generated/elegida_s140/elegida_s140.mp4`, cuadro 204, con flechas, sin la franja superior). En 24 con link; en 28 solo el fotograma |
| `fu-temporal-cuenco.pdf` | 25 | ✅ F_u(t) de esa corrida. `plot_fu.py` |
| `t90-vs-rf-cuenco.png` | 26 | ✅ ⟨t₉₀⟩ vs. R_f del cuenco (barrido `cuenco_fino_radio`) |
| `t90-vs-arquetipo.pdf` | 27 | ✅ ⟨t₉₀⟩ por arquetipo: disco solo, +embudo, +palos y el cuenco R_f = 0.34 (sin disco), vs. mesa vacía. `plot_arquetipos.py` con los datos de `TP3/GUIA.md` |
| `fu-temporal-elegida.pdf` | 29 | ✅ F_u(t): cuenco (semilla 140) y mesa vacía (semilla 141). `plot_fu.py` |
| `dcm-ajuste.pdf` | 30 | ✅ DCM z(t) con el ajuste lineal superpuesto |
| `d-vs-t90.pdf` | 31 | ✅ D por configuración, y D vs. ⟨t₉₀⟩ |

Los mapas de ejemplo (`mapa-*.png`) son solo obstáculos, sin ejes: `plot_mapas.py`
(comandos en su docstring). Las curvas ⟨t₉₀⟩ vs. parámetro salen de
`TP3/scripts/plot_sweep.py` sobre `TP3/generated/sweeps/<barrido>/summary.csv`
(semillas 101–150, 50 realizaciones, referencia `arq_vacia` salvo que se indique otra).

Las URLs de YouTube de las diapositivas 16 y 24 se completan en
`\animacionVaciaURL` / `\animacionElegidaURL`, al principio del `.tex`.
