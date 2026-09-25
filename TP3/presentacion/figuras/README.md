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

**Ojo con las diapositivas de Resultados (15–29):** ahí la figura vive en
una columna de `0.70\textwidth`, no en el ancho completo del frame (el
costado de `0.27\textwidth` es la caja de parámetros fijos). Eso reduce el
ancho disponible en pantalla a un factor ~0.68 del ancho anterior. Compensar
subiendo la fuente de ticks/labels/leyenda en el script que genera cada
figura (matplotlib/TikZ) en esa misma proporción — no es algo que se
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
| `geometria-sistema.png` | 11 | ✅ Ya incluida. Esquema con L, W, d, r y R_k marcados. Generada por `plot_geometria_sistema.py` (regenerar con `python3 figuras/plot_geometria_sistema.py` si cambia la paleta) |
| `tiempo-ejecucion-vs-n.png` | 15 | ✅ ⟨t_ejec⟩ vs. N, mesa vacía (`generated/runtime.png`) |
| `vacia_frame.png` | 16 | Fotograma representativo, mesa vacía |
| `fu-temporal-vacia.pdf` | 17 | F_u(t) de 1–2 corridas, mesa vacía |
| `t90-vs-xk.png` | 18 | ✅ ⟨t₉₀⟩ vs. x_k, un disco R = 0.30 (`generated/exp3_eje_R0.3.png`) |
| `t90-vs-r-central.png`, `mapa-central.png` | 19 | ✅ ⟨t₉₀⟩ vs. R del disco central (`generated/centro_R.png`) |
| `t90-vs-k.pdf` | 20 | ⟨t₉₀⟩ vs. K, área total fija (sin barrido todavía) |
| `t90-vs-largo-embudo.png`, `mapa-embudo.png` | 21 | ✅ ⟨t₉₀⟩ vs. largo del embudo, dos fronteras (`generated/exp1_embudo_min.png`) |
| `t90-vs-separacion-galton.png`, `mapa-galton.png` | 22 | ✅ ⟨t₉₀⟩ vs. separación de la red (`generated/galton.png`) |
| `t90-vs-rf-central-cuenco.png`, `mapa-central-cuenco.png` | 23 | ✅ ⟨t₉₀⟩ vs. R_f, disco central + cuenco (`generated/central32_cuenco.png`) |
| `t90-vs-desplazamiento-cuenco.png`, `mapa-cuenco-desplazado.png` | 24 | ✅ ⟨t₉₀⟩ vs. desplazamiento del centro del cuenco (`generated/cuenco_R0.35_offset.png`) |
| `t90-vs-rf-cuenco.png` | 25 | ⟨t₉₀⟩ vs. R_f, cuenco de frontera fina (barrido `cuenco_fino_radio`) |
| `elegida_frame.png` | 26 | Fotograma representativo, configuración elegida |
| `fu-temporal-elegida.pdf` | 27 | F_u(t): configuración elegida vs. mesa vacía |
| `dcm-ajuste.pdf` | 28 | DCM z(t) con el ajuste lineal superpuesto |
| `d-vs-t90.pdf` | 29 | D por configuración, y D vs. ⟨t₉₀⟩ |

Las URLs de YouTube de las diapositivas 16 y 26 se completan en
`\animacionVaciaURL` / `\animacionElegidaURL`, al principio del `.tex`.
