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
