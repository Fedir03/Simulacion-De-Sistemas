# Guía de lectura de las figuras — TP2

Qué mirar en cada gráfico, qué se observa y con qué se justifica. Un apartado por punto
del enunciado. Los números son los de las corridas que están en el repo.

**Parámetros comunes**: `rc = 1`, `v₀ = 0.03`, `Δt = 1`, contorno periódico, `M = 5`
corridas por punto. Densidades del enunciado con `L = 10` (`N = ρL² = 200, 400, 800`);
densidades del anuncio de la cátedra con `N = 400` y `L = √(N/ρ)`.

---

## (b) Evolución temporal y criterio de estado estacionario

**Figuras**: `evolucion-temporal.pdf` (estándar), `evolucion-variante.pdf` (votante)

Cada figura tiene **las tres densidades en el mismo gráfico**, todas arrancando con θ₀
aleatorio y con η=1. La línea vertical punteada marca el inicio del estado estacionario.

### Qué mirar

Dónde **deja de subir la curva y empieza a oscilar alrededor de un valor fijo**. Ese punto es
el inicio del estacionario, y de ahí en adelante es válido promediar. La cátedra confirmó que
determinarlo visualmente es suficiente; no hace falta un criterio automático.

Además, comparar el **ancho de la banda de fluctuación** entre las tres densidades, y comparar
los dos gráficos entre sí (comparten el eje y de 0 a 1, así que son directamente comparables).

### Qué se observa — estándar

Las tres curvas suben de golpe desde v_a ≈ 0 y se estabilizan antes de t = 200, que es donde
pusimos la línea:

| ρ | ⟨v_a⟩ estacionario (t ≥ 200) |
|---|---|
| 2 | 0.9252 ± 0.0164 |
| 4 | 0.9439 ± 0.0071 |
| 8 | 0.9529 ± 0.0027 |

Dos cosas para señalar:

- **El valor estacionario crece con la densidad** (0.925 → 0.944 → 0.953). Más vecinos, mejor
  cancelación del ruido individual.
- **La banda de fluctuación se angosta al subir la densidad**: σ pasa de 0.0164 a 0.0027, un
  factor 6. En el gráfico se ve como que la curva verde (ρ=2) es visiblemente más "peluda" que
  la azul (ρ=8). Es un efecto de tamaño finito: promediar sobre más partículas fluctúa menos.

### Qué se observa — votante

| ρ | ⟨v_a⟩ estacionario (t ≥ 100) |
|---|---|
| 2 | 0.1876 ± 0.0968 |
| 4 | 0.1483 ± 0.0766 |
| 8 | 0.1040 ± 0.0503 |

**El sistema nunca se ordena.** Las curvas oscilan entre 0 y 0.5 durante los 3000 pasos, se
cruzan permanentemente entre sí, y el valor medio queda en 0.1–0.2 contra 0.92–0.95 del
estándar en las mismas condiciones.

Acá el corte en t=100 es holgado por una razón distinta: como no hay un transitorio de subida
que esperar, las curvas ya arrancan oscilando en su valor típico. La línea sólo descarta el
arranque desde v_a ≈ 0 de la condición inicial.

### La inversión con la densidad

Vale la pena señalarlo porque es contraintuitivo: en el estándar v_a **crece** con la densidad
(0.925 → 0.953), pero en el votante **decrece** (0.188 → 0.104).

La explicación está en la regla de interacción. El estándar promedia sobre todos los vecinos,
así que más vecinos significa mejor cancelación del ruido. El votante copia a **uno solo**
elegido al azar: tener más vecinos no ayuda a cancelar nada —se copia a uno igual— pero sí
aumenta la frecuencia con que llegan direcciones ajenas. La densidad, que en el estándar
ordena, en el votante desordena.

> ⚠️ **El corte no se hereda entre observables ni entre modelos.** Para `S` el transitorio es
> mucho más largo (ver punto d), y en el votante en η bajo las corridas de 3000 pasos siguen
> evolucionando al final de la ventana. Cada caso necesita su propia inspección.

---

## (c) Curva input–observable: `v_a` vs. `η`

**Figura**: `relacion-parametro-observable.pdf` (tres densidades con barras de error)

### Qué mirar

La forma de S de cada curva —plateau, caída, plateau— y **el corrimiento horizontal entre
densidades**. Y el tamaño de las barras de error según la zona.

### Qué se observa

| η | ρ=2 | ρ=4 | ρ=8 |
|---|---|---|---|
| 0 | 1.000 | 1.000 | 1.000 |
| 1 | 0.928 | 0.944 | 0.953 |
| 2 | 0.706 | 0.784 | 0.818 |
| 3 | 0.396 | 0.541 | 0.615 |
| 4 | 0.135 | 0.216 | 0.356 |
| 5 | 0.074 | 0.062 | 0.063 |

- **η → 0 da v_a = 1 exacto**, con σ = 0. El estado ordenado es un punto fijo perfecto.
- **Las curvas se corren a la derecha al subir ρ**: hace falta más ruido para desordenar un
  sistema más denso. La separación es máxima en η=4 (0.135 vs 0.356, casi 3×) y se anula en
  los extremos.
- **En η=5 las tres valen ~0.06–0.07 y se cruzan.** Esto **no** significa que ρ=8 se desordene
  más: es el piso estadístico 1/√N, que vale 0.071 / 0.050 / 0.035 para N=200/400/800. ρ=2
  ya está en su piso (0.074 ≈ 0.071) mientras ρ=8 sigue por encima del suyo (0.063 > 0.035),
  o sea que **conserva algo más de orden real**. Si preguntan por el cruce, la respuesta es ésa.

### Por qué pasa

Cada partícula promedia las direcciones de sus vecinos. A mayor densidad hay más vecinos, el
promedio cancela mejor el ruido individual, y por lo tanto hace falta más η para romper el
alineamiento. El número medio de vecinos es `π·rc²·ρ` = 6, 13 y 25 para ρ = 2, 4 y 8.

### Cómo se leen las barras de error

Son **dispersión entre las M=5 semillas**, no error de medición:

    v̄_a = (1/M)·Σ v_a⁽ʲ⁾        σ = √( (1/(M−1))·Σ (v_a⁽ʲ⁾ − v̄_a)² )

**El tamaño de la barra es información física.** En η bajo todas las corridas terminan en el
mismo estado ordenado y la barra es diminuta; en η alto todas terminan igual de desordenadas
y vuelve a ser chica. **Pican en la zona de transición**: σ máximo en η=3 para ρ=2 (0.0376),
η=3.5 para ρ=4 (0.0110) y η=4.5 para ρ=8 (0.0097) — o sea que **el pico de las barras es en
sí mismo un estimador de η_c**, y su corrimiento con ρ confirma el de las curvas.

> ⚠️ **No confundir con la fluctuación temporal.** Dentro de una corrida, σ es mucho mayor:
> en ρ=2 pasa de 0.0065 (η=0.5) a 0.1302 (η=2.5) y baja a 0.0370 (η=5). Las barras del
> gráfico son ~10× menores porque cada punto ya promedia 2500 pasos. Las dos dispersiones
> pican en la transición, pero **si se citan números hay que decir cuál de las dos es**.

### Barrido de densidad

**Figura**: `barrido-variable.pdf` — los mismos datos transpuestos, con ρ en el eje x y una
curva por η. Con L=10 fijo, variar ρ es variar N. Se observa que v_a crece con la densidad en
todos los η, pero **la pendiente depende del ruido**: en η=0.5 es plana (0.98 → 0.99, ya está
ordenado y densificar no aporta) mientras que en η=3.5 sube de 0.24 a 0.49, o sea que se
duplica el orden sólo por densificar.

---

## (d) Clusters: fracción en la componente gigante `S`

**Figuras**: `clusters-temporal.pdf` (densidades bajas), `clusters-temporal-enunciado.pdf`
(ρ=2,4,8), `clusters-vs-eta.pdf` (las seis densidades)

Un cluster es una **componente conexa del grafo de vecinos**: partículas unidas por cadenas
de saltos entre partículas a distancia menor que `rc`. `S` es la fracción de partículas en el
cluster más grande.

### Lo primero que hay que explicar: por qué hay seis densidades

Con `rc = 1` el número medio de vecinos es `π·rc²·ρ`. El umbral de percolación continua en 2D
está en ~4.5 vecinos, o sea **ρ_c ≈ 1.44**. Las densidades del enunciado dan 6, 13 y 25
vecinos: **todas muy por encima del umbral**, así que el grafo está percolado y S ≈ 1 para
todo η. Por eso el anuncio de la cátedra extiende el estudio a ρ = 1/π, 1/2π, 1/3π, que dan
exactamente **1, ½ y ⅓ vecinos promedio** — el régimen fragmentado, donde S varía de verdad.

Verificación de que el código detecta la fragmentación: bajando la densidad, S da 0.15 / 0.16
/ 0.86 / 0.98 para ρ = 0.2 / 0.5 / 1 / 2. El salto cae justo donde predice la teoría.

### `clusters-vs-eta.pdf` — qué se observa

| ρ | η=0 | η=1 | η=2 | η=5 |
|---|---|---|---|---|
| 1/π | 0.927 | 0.429 | 0.132 | 0.022 |
| 1/2π | 0.658 | 0.236 | 0.053 | 0.015 |
| 1/3π | 0.464 | 0.116 | 0.032 | 0.011 |
| 2 | 1.000 | 0.988 | 0.978 | 0.988 |
| 4 | 1.000 | 0.999 | 0.999 | 1.000 |
| 8 | 1.000 | 1.000 | 1.000 | 1.000 |

Las seis curvas cuentan **dos historias opuestas en el mismo eje**: las tres del enunciado
pegadas en 1.0 y las tres del anuncio cayendo de 0.93 a 0.01. Esa separación *es* el
resultado: muestra de un vistazo el efecto del umbral de percolación.

### `clusters-temporal-enunciado.pdf` — el eje y va con zoom

Con el rango completo [0,1] es una recta plana inútil. Acotado a [0.84, 1.005] aparece el
gradiente: **ρ=2 fluctúa permanentemente entre 0.87 y 1.0** (pierde y recupera partículas
sueltas), **ρ=4 casi siempre en 1.0 con caídas esporádicas a 0.97**, y **ρ=8 es una recta
perfecta en 1.0**, ninguna partícula se despega jamás.

### El transitorio de `S` es mucho más largo que el de `v_a`

Esto hay que decirlo explícitamente. En ρ=1/π con η=0, ⟨S⟩ da **0.78 cortando en t=500 y
0.99 cortando en t=2500**: el sistema se sigue agrupando. El agrupamiento ocurre por
*coarsening* —cúmulos que se van fusionando de a pares— que es un proceso mucho más lento que
el alineamiento de direcciones.

Por eso **las densidades bajas se corrieron a 10000 pasos** y se promedia descartando el 40%
inicial, contra los 3000 pasos y el corte mucho mas temprano de (b) y (c). Con 3000 pasos ⟨S⟩ salía
subestimado.

### `dispersion-semillas.pdf` — por qué las barras de error son tan grandes

Dos paneles, **dos causas distintas para la misma barra grande**:

**Panel η=0 — multiestabilidad.** Las curvas son escaleras: cada escalón es una fusión de dos
cúmulos. Cuatro semillas suben a 1.0 y se quedan perfectamente planas; la semilla 3 llega a
1.0, y en t≈5000 **cae de golpe a 0.60** y se congela ahí:

| Semilla | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| S final | 0.998 | 1.000 | **0.605** | 1.000 | 1.000 |

El cúmulo único se partió en dos que nunca se reencuentran. En η=0, una vez que un grupo se
alinea internamente **se mueve como un bloque rígido**, y dos bloques con direcciones
distintas no vuelven a cruzarse. La barra σ=0.145 mide **estados finales distintos**, no error.

**Panel η=0.5 — fluctuación.** Ninguna curva se aplana: las cinco suben y bajan entre 0.2 y
0.9 durante los 10000 pasos, cruzándose todo el tiempo. Acá la barra es grande porque
**ninguna corrida termina en ningún lado**, y correr más tiempo no la achica.

Un número que distingue los dos mecanismos: en η=0 el desvío *dentro* de cada corrida es casi
cero (una semilla da 1.0000 ± 0.0000) mientras que *entre* corridas es 0.145. En η=0.5 se
invierte.

---

## (e) Polarización en función de la componente gigante

**Figuras**: `va-vs-s.pdf` (densidades bajas), `va-vs-s-enunciado.pdf` (ρ=2,4,8),
`va-vs-s-votante.pdf`

Van separadas a propósito: las escalas son incompatibles y juntas no se lee ninguna.

### `va-vs-s.pdf` — densidades bajas

**Relación creciente y bien definida**: más componente gigante, más polarización. Y lo más
interesante: **las tres curvas se superponen**, o sea que la relación entre conectividad y
orden **no depende de la densidad**, sólo de cuánta componente gigante haya. Es un resultado
más fuerte que el de cada densidad por separado.

La lectura física: para alinearse hay que estar conectado, así que el orden no puede aparecer
sin que antes exista un cúmulo que lo sostenga.

### `va-vs-s-enunciado.pdf` — la vertical

Las tres curvas son **líneas verticales en S ≈ 1**. No es un error del gráfico: como esas
densidades están percoladas, al barrer η el v_a recorre de 0.06 a 1 **mientras S no se mueve**.

El mensaje es el complemento del anterior: **S ≈ 1 es necesario pero no suficiente para el
orden.** Estando todos conectados, el sistema igual puede estar completamente desordenado si
el ruido es alto.

Detalle fino: ρ=2 no es del todo vertical, se curva hacia la izquierda en el medio (S baja a
0.96 cuando v_a ronda 0.2–0.4). Es la única de las tres que asoma por debajo de la
saturación, coherente con ser la más cercana al umbral.

---

## (f) Comparación con el modelo de votante

**Figuras**: `comparacion-modelos-rho{2,4,8}.pdf`, `clusters-modelos-*.pdf`,
`evolucion-temporal-votante-rho{2,4,8}.pdf`, `va-vs-s-votante.pdf`

### Qué mirar primero: la grilla de η

El votante hace toda su transición **por debajo de η = 0.5**, así que se barrió con una grilla
fina abajo (21 valores, con 10 entre 0 y 0.5). Con la grilla del estándar la curva era un
acantilado entre los dos primeros puntos y una recta en el piso: no se podía leer nada.

### Qué se observa

| ρ=4 | η=0 | η=0.5 | η=1 | η=3 |
|---|---|---|---|---|
| v_a estándar | 1.000 | 0.986 | 0.944 | 0.541 |
| v_a votante | 0.962 | 0.298 | 0.149 | 0.060 |

El votante está por debajo en todo el rango, con la diferencia máxima en la zona intermedia.

**Pero la diferencia cualitativa es más importante que la cuantitativa**: el estándar tiene la
forma de S típica de una transición de fase —plateau, caída abrupta, plateau—, mientras que el
votante **decae suave y monótonamente desde η=0**, sin plateau ordenado ni caída brusca. **No
tiene un η_c bien definido**: se desordena progresivamente apenas hay ruido.

### Por qué

En el estándar cada partícula promedia sobre todos sus vecinos, y ese promedio cancela buena
parte del ruido de cada uno. En el votante copia la dirección de **un solo** vecino elegido al
azar, así que arrastra el ruido de ese vecino entero y le suma el propio. El ruido se acumula
en vez de cancelarse.

### Clusters (`clusters-modelos-rho1pi.pdf`)

| ρ=1/π | η=0 | η=0.5 | η=1 |
|---|---|---|---|
| S estándar | 0.927 | 0.557 | 0.429 |
| S votante | 0.538 | 0.131 | 0.069 |

**El caso extremo vale la pena señalarlo**: en η=0, *sin nada de ruido*, el estándar llega a
S=0.93 y el votante se queda en 0.54. El votante **no logra armar un cúmulo único ni siquiera
sin ruido**, algo que el estándar sí hace. Copiar a un vecino al azar mantiene una dispersión
de direcciones que impide que los grupos se terminen de fusionar.

> ⚠️ **El transitorio del votante tampoco se hereda.** En η ≤ 0.5 las corridas de 3000 pasos
> siguen ordenándose al final de la ventana de promedio. Además, mover el corte de 500 a 1500
> **no mejora** la deriva: el votante tiene fluctuaciones lentas de gran amplitud que un run
> de 3000 pasos no alcanza a promediar. Las barras grandes en η bajo son reales.

---

## (g) Tiempos de ejecución del Cell Index Method

**Figura**: `tiempos-cim.pdf`

### Qué mirar

Tres curvas, todas medidas **en la misma máquina y la misma JVM** (comparar contra números
medidos en otro momento u otra máquina no sería válido):

1. **TP1 con sus parámetros originales** (L=20, radios 0.23–0.26, configuraciones uniformes).
2. **TP1 con la geometría de TP2** (L=10, radio ≈ 0, uniformes) — aísla el efecto de la geometría.
3. **TP2 midiendo dentro de la simulación** (L=10, configuraciones agrupadas).

### Qué se observa

| N | TP1 orig (L=20) | TP1 geom TP2 (L=10) | TP2 en simulación |
|---|---|---|---|
| 100 | 0.175 ms | 0.085 ms | 0.150 ms |
| 500 | 0.446 | 0.552 | 1.268 |
| 1000 | 1.257 | 2.318 | **6.189** |

**El CIM tarda hasta 2.7× más dentro de la simulación** que sobre configuraciones uniformes
con la misma geometría, y la brecha **crece con N**: 1.1× en N=200, 2.3× en N=500, 2.7× en
N=1000.

### Por qué

El CIM asume partículas repartidas parejo entre las celdas; bajo esa hipótesis su costo es
O(N). Pero en Vicsek **las partículas se agrupan**, así que unas pocas celdas concentran
muchas partículas y dentro de ellas la comparación vuelve a ser todos contra todos. Cuanto
más grande el sistema, más pesa ese desbalance.

Es el punto que conecta (g) con la física del TP: **el mismo agrupamiento que se mide con S es
el que degrada la performance del CIM.**

La tercera curva separa las causas: densificar de L=20 a L=10 con el mismo N ya duplica el
tiempo (1.26 → 2.32 ms en N=1000) sólo por tener más vecinos por partícula; el resto —de 2.32
a 6.19— es efecto del agrupamiento.

### Advertencia metodológica

Ambas mediciones descartan las primeras llamadas por el **JIT de la JVM**. Sin ese descarte,
la primera N de la lista sale anómalamente lenta (N=100 daba 0.305 ms contra 0.197 de N=200,
con desvío enorme) y **la curva deja de ser monótona**. En TP1 se resolvió anteponiendo un
N=50 descartable; en TP2 con `--warmup=100` cuadros.

---

## Checklist para la defensa

| Si preguntan | Respuesta corta |
|---|---|
| ¿Cómo eligieron el transitorio? | A ojo sobre las curvas v_a(t), como confirmó la cátedra: donde dejan de subir y pasan a oscilar. t=200 en el estándar, t=100 en el votante, 40% del run para S. |
| ¿Por qué las barras crecen en el medio? | Fluctuación crítica: el sistema finito cerca de η_c queda ordenado o desordenado según el detalle del ruido. El pico estima η_c. |
| ¿Por qué las tres curvas de v_a se cruzan en η=5? | Están en el piso estadístico 1/√N, no es orden residual. |
| ¿Por qué S ≈ 1 en las densidades del enunciado? | Están sobre el umbral de percolación (ρ_c ≈ 1.44 con rc=1). Por eso la cátedra extendió a 1/π, 1/2π, 1/3π. |
| ¿Por qué usaron L ≠ 10 en las densidades bajas? | Con L=10 darían N = 10.6, 15.9 y 31.8 — no enteros y sistemas inviables. Se fijó N=400 y se despejó L. **Es un apartamiento del enunciado y hay que declararlo.** |
| ¿Por qué las barras de S no bajan corriendo más? | En η=0 sí bajaron (era relajación); en η ≥ 0.5 no, son fluctuaciones lentas de gran amplitud. |
| ¿Por qué el CIM es más lento en TP2? | El flocking concentra partículas en pocas celdas y rompe la hipótesis de ocupación uniforme. |
