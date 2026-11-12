# Registro de correcciones de IA

Base del apéndice de la presentación que pide la cátedra: libertades que tomó la IA y que el grupo tuvo que corregir.

**Reglas:**
- Solo entradas que ocurrieron de verdad.
- Si el error era de la especificación y no de la IA, se anota igual y se aclara de quién era.
- Las correcciones anteriores a este registro las carga el grupo desde Notion.

Estructura de cada entrada: fecha, qué se hizo, cómo se detectó (lo corrigió el usuario, lo detectó la IA, lo detectó un test), qué se corrigió y qué efecto tuvo.

---

## 2026-11-03 · Desempate de F: "no influye salvo en choque exacto"
- **De quién era:** de la especificación (página de Notion). El umbral de |sin θ_j| ≤ 5° fue una interpretación de la IA: la página usaba ε en la fórmula y daba "rotación de 5°" en la tabla.
- **Qué se hizo:** se implementó el desempate con esa banda angular.
- **Cómo se detectó:** lo detectó un test (la simetría especular falló en F). La IA analizó la causa: la banda abarca 0,87 m de desvío lateral a 10 m. El grupo decidió cambiar el criterio.
- **Qué se corrigió:** el desempate pasó al criterio métrico |s_c| ≤ 0,05 m, el mismo de A y B. El grupo corrigió la página el 4/11.
- **Efecto (F, mejor par de cada criterio, ECM 1 excl. / ECM 2):**
  - Grilla oficial: métrico 2,355 / 0,567; banda de 5° 2,329 / 0,540; banda de 1° 2,466 / 0,607.
  - Zona exploratoria, elegida post-hoc: métrico 1,946 / 0,465; banda de 5° 1,911 / 0,421; banda de 1° 1,953 / 0,487.

## 2026-11-03 · Sentido de la rotación del desempate de F
- **De quién era:** de la especificación, que lo planteaba al revés o de forma ambigua ("rotar e_ij hacia la derecha").
- **Qué se hizo:** al implementar se vio que e_ij apunta hacia atrás del peatón, así que rotarlo a la derecha de su dirección lo manda a su izquierda.
- **Cómo se detectó:** lo detectó la IA al implementar. Lo informó al grupo en vez de aplicar la frase literal.
- **Qué se corrigió:** e_ij se rota de modo que el desvío resultante vaya a la derecha del peatón. El grupo corrigió la página el 4/11 y pidió un test, que lo verifica con seis rumbos.
- **Efecto:** con la frase literal, el desempate habría desviado al peatón al lado contrario del que justifican los datos (25 de 38 peatones se desvían a su derecha).

## 2026-11-03 · Exploración fuera de la grilla de F en la tabla comparativa
- **De quién era:** de la IA.
- **Qué se hizo:** sin que se pidiera, se exploró F con B_p hasta 1000 porque su óptimo quedaba en la esquina de la grilla, y se puso en la misma tabla comparativa. Una nota aclaraba que la zona se eligió después de ver los datos, pero la fila la rotulaba solo "fuera de la grilla".
- **Cómo se detectó:** lo corrigió el usuario, al definir cómo reportarlo.
- **Qué se corrigió:** la grilla de la página es la oficial. La zona ampliada se reporta aparte, rotulada como exploratoria y post-hoc, en archivos separados (`exploratoria/`, `mejores_exploratoria.txt`).
- **Efecto:** las conclusiones de la zona ampliada ya no se presentan al mismo nivel que las de la grilla oficial. Su validación cruzada queda marcada como no limpia.

## 2026-11-04 · Evento 2: el contacto extra no era de ese evento
- **De quién era:** de la IA.
- **Qué se hizo:** en el informe del piloto se planteó, como hipótesis sin verificar ("no comprobé que ese contacto sea el del evento 2"), que el cambio de 455% en el ECM 2 del evento 2 coincidía con un contacto extra que aparece con 3 frames. La hipótesis resultó errónea.
- **Cómo se detectó:** la verificación la pidió el prompt que el usuario pasó desde el chat. No fue una corrección directa suya.
- **Qué se corrigió:** se midió con la traza. El contacto extra es del evento 17 (peatones 2 y 45, t = 3,317 a 3,364 s, 0,37 cm). El evento 2 no tiene contacto con 3, 5 ni 7 frames: lo que cambia es el lado del cruce.
- **Efecto:** cambia la explicación de la sensibilidad a v_0 en ese evento: es la inversión de lado cuando s_c cruza el umbral de 0,05 m, no el contacto.

## 2026-11-04 · Conmutaciones: se mezclaron pares donde la capa no tiene efecto
- **De quién era:** de la IA.
- **Qué se hizo:** el informe del piloto dio "percentil 99 de 6 y hasta 22 conmutaciones en A y B" sin separar los pares con ℓ = 0 o k = 0, donde la capa se prende y apaga sin cambiar la trayectoria.
- **Cómo se detectó:** lo detectó la IA, al listar las filas con más de 6 conmutaciones que pidió el usuario.
- **Qué se corrigió:** el resumen ahora separa pares inertes de activos.
- **Efecto:** sin los inertes, el percentil 99 baja de 6 a 4 y el máximo de B baja de 22 a 10. El máximo de A sigue en 22, porque hay un par activo que llega a ese valor.

## 2026-11-04 · "El criterio de regreso evita oscilar"
- **De quién era:** de la especificación. El informe anterior de la IA decía que se cumplía "casi siempre", sin analizar la causa de los casos altos.
- **Qué se hizo:** se implementó el criterio tal como lo define la página. La detección depende de la posición actual, que cambia con el desvío.
- **Cómo se detectó:** lo detectó la IA con la traza de conmutaciones que pidió el usuario.
- **Qué se corrigió:** todavía nada en el modelo; queda anotado en `DEFINICIONES.md` para que decida el grupo.
- **Efecto:** en A, con ℓ de 1,25 a 1,75 m, hay hasta 22 conmutaciones por agente, y de 83 a 95% son d_min cruzando ρ. No aparece en los mejores pares (hasta 4 por agente). En B no se da ese caso.

## 2026-11-04 · Redacción de la entrada del evento 2
- **De quién era:** de la IA.
- **Qué se hizo:** el plan redactó la entrada como "atribuí el 455% a un contacto extra" y "lo pidió verificar el usuario". Eso exageraba el error, que se había planteado como hipótesis, y le atribuía al usuario una corrección directa que no hubo.
- **Cómo se detectó:** lo corrigió el usuario, al revisar el plan.
- **Qué se corrigió:** la entrada se reescribió con lo que realmente pasó.
- **Efecto:** ninguno en resultados. Es precisión del propio registro.

## 2026-11-04 · Lado de esquive invertido en un script de análisis
- **De quién era:** de la IA.
- **Qué se hizo:** `trace_report.py` traducía s_c < 0 como "esquiva a su izquierda", cuando esquiva hacia el lado opuesto al otro y es a su derecha.
- **Cómo se detectó:** lo detectó la IA al revisar el script antes de correrlo.
- **Qué se corrigió:** se invirtió la condición.
- **Efecto:** ninguno en resultados; no llegó a usarse.

## 2026-11-04 · Control de la validación cruzada que no controlaba nada
- **De quién era:** de la IA.
- **Qué se hizo:** el primer `cross_validation.py` comprobaba "entrenamiento = validación da el error de (b)" comparando la matriz consigo misma, siempre verdadero. Su test tenía además una línea inservible (`if False`).
- **Cómo se detectó:** lo detectó la IA al revisar el script antes de correrlo.
- **Qué se corrigió:** se agregó `evaluate_on_all`, y el control lo compara contra el error calculado por otro camino (`surface` de `pilot_analysis.py`). Se reescribió el test.
- **Efecto:** ninguno en resultados; el control da verdadero también con la versión correcta.

## 2026-11-04 · Script de sensibilidad a v_0 sin la zona exploratoria
- **De quién era:** de la IA.
- **Qué se hizo:** una sustitución con `sed` para que `sensitivity_v0_layers.sh` leyera también `mejores_exploratoria.txt` no coincidió con la línea, y la falla pasó sin error.
- **Cómo se detectó:** lo detectó la IA al ver la salida del comando.
- **Qué se corrigió:** se editó la línea directamente antes de correr el script.
- **Efecto:** ninguno en resultados.

## 2026-11-05 · Porcentajes de "pasar de la banda de 5° al criterio métrico"
- **De quién era:** de la IA.
- **Qué se hizo:** el informe del 4/11 dijo que pasar de la banda de 5° al criterio métrico empeora F en 1,1% y 4,6% en la grilla oficial, y en 1,8% y 9,5% en la zona exploratoria. Calculó esos porcentajes sobre el valor métrico, cuando la base de un empeoramiento es el valor de partida (5°).
- **Cómo se detectó:** lo detectó la IA, al repasar sus cuentas mientras armaba el plan de auditoría de F.
- **Qué se corrigió:** con base en el valor de 5° son 1,1% y 4,9% en la grilla oficial, y 1,8% y 10,5% en la zona exploratoria. Las diferencias pareadas por celda y los archivos en `outputs/pilot/` no usaban esa cuenta.
- **Efecto:** cambian solo esas dos cifras del informe (4,6% → 4,9% y 9,5% → 10,5%). El grupo tiene que usar las corregidas si las citó.

## 2026-11-05 · Columnas corridas en el resumen de la auditoría
- **De quién era:** de la IA.
- **Qué se hizo:** la primera versión de `audit_f.py` leía las columnas de la traza corridas en una posición. Daba, por ejemplo, pasos totales como si fueran pasos con capa.
- **Cómo se detectó:** lo detectó la IA, al ver valores imposibles en la primera salida (0 pasos de solape con capa junto a 171 "a la izquierda" en A).
- **Qué se corrigió:** las columnas pasaron a tener nombres, y se volvió a generar `auditoria.txt`.
- **Efecto:** ninguno en resultados; la salida errónea no se informó.

## 2026-11-05 · Desempate de F: el desvío no siempre va a la derecha
- **De quién era:** de la IA. La especificación pide que el desvío resultante vaya a la derecha del peatón. La implementación solo rota e_ij 5°, y eso no alcanza si el otro está a más de 5° del eje. El test que se agregó el 4/11 solo cubría el choque frontal exacto y un caso de 1,9°, pero el informe lo presentó como verificación del sentido.
- **Qué se hizo:** en F(0,9; 2,5), 741 de 9049 pasos de desempate terminan a la izquierda (946 de 8405 en F(0,8; 3)), en los eventos 6, 9, 12, 13 y 19, con |sen θ_j| hasta 0,26 y d_ij de 4,8 m o más.
- **Cómo se detectó:** lo detectó la IA al auditar F con la especificación, en un pedido de auditoría del usuario. Se confirmó midiendo el lado aplicado.
- **Qué se corrigió:** el grupo decidió corregirlo el 5/11, en un paso separado del cambio de Δt. Si después de rotar e_ij el desvío sigue a la izquierda, se usa −e_t rotado 5°. Lo cubre un test con el otro a 11° del eje, y otro verifica que en los 19 eventos ningún desempate termina a la izquierda. La versión del motor coincide fila por fila con la estimación previa.
- **Efecto (tabla 2×2 en `outputs/pilot/desempate/`):** con Δt_exp/64, F(0,9; 2,5) pasa de 2,3546 a 2,3563 en ECM 1 excl. El mejor par de ECM 2 pasa de (0,8; 3) 0,5666 a (0,9; 2,5) 0,5722. El desempate cambia en más de 1% el ECM 2 de 17 de los 72 pares; Δt no cambia en más de 1% ningún par de F.

## 2026-11-05 · Δt_exp/32 se validó solo sin capa
- **De quién era:** de la IA. La prueba de D11 se corrió sin capa ("hasta 0,04% por evento"), y el piloto se informó con Δt_exp/32 sin repetirla con las capas activas.
- **Qué se hizo:** con capa, A(2,5; 2,5) cambia 2,12% en ECM 1 excl. poblacional entre /32 y /64 (evento 9: 2,3342 → 3,1535), y B(2,5; 4) tiene eventos que superan el criterio de 1%. A(4; 0,5), B(4,5; 1) y los pares de F lo cumplen.
- **Cómo se detectó:** se midió porque el usuario lo pidió en la auditoría (ítem 8).
- **Qué se corrigió:** el grupo pasó D4 y D11 a Δt_exp/64 el 5/11, con el mismo espaciado de salida (Δt_exp/4), y se regeneró todo el piloto. Entre /64 y /128, los mejores pares de las tres capas cambian a lo sumo 0,10% poblacional, y ningún evento cambia más de 5%.
- **Efecto:** el mejor par de A en ECM 1 excl. pasa de (2,5; 2,5) 2,0348 a (4; 0,5) 2,0606. A(2,5; 2,5) a /32 dependía de qué peatón dejaba de esquivar primero en el evento 9, que no tiene contacto. La comparación con /32 queda en `outputs/pilot/auditoria_dt32/`.

## 2026-11-05 · Controles corridos con un jar desactualizado
- **De quién era:** de la IA.
- **Qué se hizo:** al pasar D4 a Δt_exp/64, un test con el 8 fijo falló y Maven no regeneró el jar. El comando siguió igual y generó grillas, línea base y copias de regresión con el jar anterior, a /32.
- **Cómo se detectó:** lo detectó un test, y la IA lo confirmó al ver `dt_div=32` en el encabezado de la línea base.
- **Qué se corrigió:** se borraron esas copias, se ajustó el test y se repitió todo con el jar nuevo. Desde este paso, los comandos cortan si falla la compilación.
- **Efecto:** ninguno en resultados; nada de eso llegó a usarse.

## 2026-11-11 · Referencia del desvío lateral contaminada por el tramo vertical
- **De quién era:** de la IA. El plan de la Fase 1 del recorte medía el desvío lateral máximo contra la recta entre los extremos de |x − x_c| ≤ 4 m, y el pico de rumbo en esa misma zona.
- **Qué se hizo:** en esa zona entra la subida vertical inicial de varios peatones. Para los izquierdos de los eventos 6, 7, 8, 9, 11, 13, 14 y 19 dio "desvíos" de 1,3 a 1,8 m unos 3 s antes del mínimo, y el pico de rumbo quedaba "fuera del tramo" en casi todos los eventos con A(45°).
- **Cómo se detectó:** lo detectó la IA, al ver que la marca saltaba en eventos sin esquive visible y listar dónde caía el desvío máximo respecto del mínimo.
- **Qué se corrigió:** la referencia pasó a la zona de interacción (frames alrededor del mínimo con distancia ≤ 5 m, donde el rumbo máximo es ≤ 31° en los 38 peatones). Se agregó el inicio del esquive. Quedó anotado en `DEFINICIONES.md`, sección 8b.
- **Efecto:** ninguno en resultados del piloto. En la tabla de exploración, "esquive cortado" pasa de 5 peatones a 0 con A(45°), y de 7 a 2 con A(30°) (los dos del evento 14). La versión anterior no se informó.

## 2026-11-11 · Recorte no idempotente en la primera implementación
- **De quién era:** de la IA.
- **Qué se hizo:** la primera versión de `FrontalTrim` cortaba las trayectorias a la ventana recortada. Al recortar otra vez, el rumbo de los frames del borde se calculaba con una diferencia hacia un solo lado.
- **Cómo se detectó:** lo detectó un test (`trimmingIsIdempotent`): el evento 1 pasaba de empezar en el frame 20074 a empezar en el 20075.
- **Qué se corrigió:** el evento conserva las trayectorias completas y guarda la ventana, el frame del target y el frame inicial de v_d por peatón (`PedestrianEvent`). Sin recorte se usan el primer y el último frame de cada trayectoria, como en D3.
- **Efecto:** ninguno en resultados; ninguna corrida usó la primera versión. Con `--trim off`, la línea base y F(0,9; 2,5) coinciden byte a byte con el piloto anterior.

## 2026-11-11 · Caso sintético mal armado en un test del recorte
- **De quién era:** de la IA.
- **Qué se hizo:** el evento sintético con tramo vertical inicial le daba al peatón derecho una curva senoidal en y. Su pendiente al inicio del tramo es de 6%, y el test exigía menos de 5% de componente vertical en v_0.
- **Cómo se detectó:** lo detectó el mismo test, al fallar. La IA vio que la causa era el caso sintético y no el recorte.
- **Qué se corrigió:** el peatón derecho cruza en línea recta sobre y = 2,6.
- **Efecto:** ninguno en resultados.

## 2026-11-11 · Rumbo máximo del perfil de giro contaminado por la salida
- **De quién era:** de la IA. Es el mismo tipo de error que la entrada de la referencia lateral de esta misma fecha.
- **Qué se hizo:** `trim_phase4.py` buscaba el rumbo máximo de cada peatón real en toda la ventana recortada. Dio una mediana de 46° y un máximo de 148°, que corresponden al giro de salida que la persistencia deja dentro del tramo, no al esquive.
- **Cómo se detectó:** lo detectó la IA al ver valores imposibles para un esquive (148°, es decir, hacia atrás).
- **Qué se corrigió:** el rumbo máximo se busca solo con distancia al otro ≤ 5 m, como en la exploración. Con eso, la mediana es 17,6° y el rango va de 3,0 a 31,4°.
- **Efecto:** ninguno en el piloto; la versión anterior no se informó.

## 2026-11-11 · D(45°) deja una cola fuera de la zona compartida en los eventos 3 y 6
- **De quién era:** de la IA. D(45°) fue su recomendación al cerrar la Fase 1 de la exploración.
- **Qué se hizo:** en los eventos 3 y 6, el tramo del peatón izquierdo sigue 2,62 y 2,43 m más allá de la x donde empieza el tramo del derecho (hasta x ≈ 10,65 y 10,35 contra ≈ 8), con una subida final de pendiente menor que 45° que el criterio no corta. La exploración había informado el ángulo de e_target de 9,1° del evento 3 como "residual", sin ver que la causa era esa cola.
- **Cómo se detectó:** por la verificación visual de Fede (`outputs/recorte/verificacion/`). Los otros 17 eventos los aprobó.
- **Qué se corrigió:** todavía nada en el motor. Se midieron discriminadores sin simular (`outputs/recorte/discriminadores.md`) y se armó el ajuste manual de los dos eventos (`outputs/recorte/ajuste_manual/`). Decide el grupo.
- **Efecto:** el piloto con D(45°) incluye esas dos colas. Con el ajuste manual, el evento 3 pierde 46 frames y el 6 pierde 31.

## 2026-11-11 · Variante "tramo espacial compartido": se previsualizó antes de implementarla
- **De quién era:** de la especificación del chat. La variante pedía cortar el tramo de cada peatón en la x donde empieza el del otro, manteniendo la ventana común.
- **Qué se hizo:** antes de tocar código, la IA la previsualizó sobre los CSV del recorte vigente. Habría cambiado 8 eventos en lugar de 2: el 2, 3, 4, 5, 6, 10, 14 y 15 pierden más de 0,5 m (el 15, 1,90 m). En la mayoría el corte lo dispara el peatón derecho, que termina en x ≈ 0,1 a 0,2 m, antes de la x inicial del izquierdo (≈ 0,6 a 0,8 m). Cortando solo del lado del izquierdo, igual cambian 6 eventos.
- **Cómo se detectó:** lo detectó la IA con la previsualización y lo informó antes de implementar.
- **Qué se corrigió:** no se implementó. El usuario pidió buscar primero un discriminador que separe el 3 y el 6.
- **Efecto:** ninguno en resultados ni en código.

## 2026-11-11 · Umbral X de la compuerta de tramo compartido elegido post-hoc
- **De quién era:** de la definición del grupo, a partir del análisis de discriminadores de la IA. No es un error de implementación: se anota porque condiciona cómo se reporta.
- **Qué se hizo:** la compuerta corta la ventana cuando un peatón pasa la x inicial del otro en más de X = 1,5 m. X se eligió después de ver el discriminador (a) en los 19 eventos: 2,62 y 2,43 m en el 3 y el 6, contra 0,95 m como máximo del resto.
- **Cómo se detectó:** lo declaró el usuario al aprobar el corte.
- **Qué se corrigió:** queda documentado en D3 y en la sección 8c de `DEFINICIONES.md`. Los resultados con la compuerta se reportan como post-hoc. Con `--trim-shared off` se reproduce D(45°) byte a byte.
- **Efecto:** cambian solo los eventos 3 y 6 (46 y 31 frames menos). El conjunto es el mismo con X = 1,0 y X = 2,0. Lo verifican `gateChangesOnlyEventsThreeAndSixForXBetweenOneAndTwo` y `theOtherSeventeenEventsSimulateIdenticallyWithTheGate`.

## 2026-11-11 · Errores en los scripts de la tabla de tres columnas y de las figuras de la presentación
- **De quién era:** de la IA.
- **Qué se hizo:**
  - `trim_compare3.py` leía las grillas de ρ con `np.genfromtxt`, que convierte la columna de contacto (`true`/`false`) en NaN, y se cortó con un error.
  - En la primera versión de R3 (`presentation_figures.py`), el formato con coma decimal pisaba las etiquetas del eje x: mostraba 0, 1 y 2 en lugar de A, B y F.
  - En R1, la leyenda tapaba la trayectoria real del peatón derecho, y en R6 el eje de contactos tenía marcas decimales.
- **Cómo se detectó:** lo detectó la IA, por el error del script y al revisar las figuras rasterizadas antes de entregarlas.
- **Qué se corrigió:** el lector pasó a `load_grid`, se aplicó el formato antes de las etiquetas, se movió la leyenda de R1 y el eje de contactos de R6 quedó en enteros.
- **Efecto:** ninguno en resultados; las versiones con errores no se entregaron.

## 2026-11-11 · Errores del borrador de la presentación
- **De quién era:** de la IA que armó el borrador de `presentacion/presentacion_tp5.tex`.
- **Qué se hizo:** 1000 particiones en lugar de 5000; ECM 2 escrita al revés (mínimo sobre la trayectoria real en vez de la simulada, contra `Ecm.java` y la sección 2 de `DEFINICIONES.md`); fuerza de contacto `k_n ε n̂` sin decir el sentido de n̂ (con n̂ de j a i, como en `SfmField.java`, sería atractiva); desempate de F con solo el paso de respaldo (faltaba la rotación de e_ij); "más de 30 correcciones" sin contar; contacto "en algún cuadro" cuando el motor lo controla en cada paso; ρ = 0,9 m presentado como "el máximo" de las distancias mínimas reales (es 0,92 m); en el anexo, "atribuyó" en la fila del evento 2, que había sido una hipótesis declarada.
- **Cómo se detectó:** en la revisión de la presentación que pidió el usuario, comparando cada número y ecuación con `outputs/pilot/`, `DEFINICIONES.md`, el código y la página de Notion "Correcciones a la IA".
- **Qué se corrigió:** el texto de esas diapositivas. El detalle (antes, después y motivo) está en `presentacion/REVISION.md`. La cuenta del registro da 36 entradas distintas (23 previas del repo, esta y 12 que solo están en Notion).
- **Efecto:** ninguno en resultados; solo cambia el texto de la presentación.

## 2026-11-11 · Medición de "hasta cuándo influye v_0" mal planteada en la primera versión del diagnóstico de A
- **De quién era:** de la IA, en el prototipo de `scripts/graph_gen/diag_a.py`.
- **Qué se hizo:** para medir hasta qué instante influye la velocidad inicial se tomó el último instante en que la rapidez de A(3; 0,5) con el ajuste de D12 y con v_0 = v_d·e_target difiere en más de 5% de v_d. Esa diferencia dura hasta el final de la ventana, porque la capa se activa en instantes distintos en las dos corridas, y el script devolvía 0 s cuando el último instante era la última fila.
- **Cómo se detectó:** lo detectó la IA, al ver una mediana de 0,00 s contra 1,25 s esperados para el peatón libre.
- **Qué se corrigió:** se mide el primer instante en que la diferencia vectorial de velocidad baja de 5% de v_d (mediana 1,43 s; peatón libre, τ·ln(|v_d e_t − v_0|/(0,05 v_d)), 1,26 s), y aparte el avance que queda en la posición en t_min real (mediana 0,36 m).
- **Efecto:** ninguno en resultados; la versión con el error no se entregó.

## 2026-11-11 · Controles mal armados al regenerar las figuras y probar el script de build
- **De quién era:** de la IA.
- **Qué se hizo:**
  - El control del signo menos en R4b y R4c leyó el PDF con `pdftotext` sin `-enc UTF-8` y contó 9 y 5 "guiones", que eran el signo menos real (U+2212) convertido por la codificación por defecto.
  - La prueba de `Overfull \vbox` de `build_presentacion.sh` armó el `.tex` de prueba con `printf`, que interpretó `\rule` y `\b` como caracteres de control. El script falló por un error de compilación y no por el `Overfull \vbox` que se quería probar.
- **Cómo se detectó:** lo detectó la IA. En el primer caso, al mirar los bytes de la salida (`342 210 222`); en el segundo, al leer el mensaje de error ("Unicode character U+0008").
- **Qué se corrigió:** se repitió la lectura con `-enc UTF-8` y se armó el `.tex` de prueba con un heredoc. Con eso, el script falla por el `Overfull \vbox`, como se esperaba.
- **Efecto:** ninguno en resultados ni en archivos entregados; los dos controles se repitieron antes de informar.

## 2026-11-12 · Rótulo "Postproceso (fuera del motor)" con el ECM todavía en el motor
- **De quién era:** de la IA.
- **Qué se hizo:** en la lámina 7 (Motor: paso temporal) la IA rotuló la caja punteada como "Postproceso (fuera del motor)", cuando el ECM, los contactos y la grilla de calibración todavía se calculaban dentro del motor (`metrics/Ecm.java`, `calibration/GridSearch.java` y el control de contacto en `engine/Simulation.java`) y entraban en el ZIP.
- **Cómo se detectó:** al pedir el grupo, en el mismo pedido, dónde estaba el código del ECM, los contactos y la calibración y qué entraba en el ZIP.
- **Qué se corrigió:** primero se volvió al rótulo "Después de la corrida: ECM, contactos, calibración". Después de la refactorización que separó `analysis/` del motor (fuera del ZIP), el rótulo "Postproceso (fuera del motor)" pasó a ser cierto y se volvió a poner.
- **Efecto:** ninguno en resultados; la lámina dijo algo falso solo entre dos compilaciones intermedias.

## 2026-11-12 · ECM y contactos dentro del motor de la entrega
- **De quién era:** de la IA.
- **Qué se hizo:** la IA propuso calcular y mostrar el ECM y los contactos dentro del motor de la entrega.
- **Cómo se detectó:** lo marcó el grupo: en TP4 se penalizaron los observables calculados en el motor.
- **Qué se corrigió:** se separaron del motor. ECM, contactos, distancia mínima, longitud recorrida, conmutaciones, grilla, recorte exportado y series de direcciones pasaron a `analysis/` (`AnalysisMain`), fuera del ZIP. El contacto y la distancia mínima se siguen midiendo en cada paso con el `StepObserver` del motor.
- **Efecto:** ninguno en resultados. Los 258 archivos de salida de `outputs/` (línea base, grillas de A, B y F, y corridas de `figs/datos`) salen idénticos byte a byte antes y después; pasan los 101 tests, y el motor del ZIP compila sin `analysis/` y reproduce `evento_03.txt`.
