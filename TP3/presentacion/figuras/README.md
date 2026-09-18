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

**Ojo con las 9 diapositivas de Resultados (15–23):** ahí la figura vive en
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
| `tiempo-ejecucion-vs-n.pdf` | 15 | ⟨t_ejec⟩ vs. N, mesa vacía, barras de error |
| `vacia_frame.png` | 16 | Fotograma representativo, mesa vacía |
| `fu-temporal-vacia.pdf` | 17 | F_u(t) de 1–2 corridas, mesa vacía |
| `t90-vs-xk.pdf` | 18 | ⟨t₉₀⟩ vs. posición del obstáculo único |
| `t90-vs-k.pdf` | 19 | ⟨t₉₀⟩ vs. K, área total fija |
| `elegida_frame.png` | 20 | Fotograma representativo, configuración elegida |
| `fu-temporal-elegida.pdf` | 21 | F_u(t): configuración elegida vs. mesa vacía |
| `dcm-ajuste.pdf` | 22 | DCM z(t) con el ajuste lineal superpuesto |
| `d-vs-t90.pdf` | 23 | D por configuración, y D vs. ⟨t₉₀⟩ |

Las URLs de YouTube de las diapositivas 17 y 21 se completan en
`\animacionVaciaURL` / `\animacionElegidaURL`, al principio del `.tex`.
