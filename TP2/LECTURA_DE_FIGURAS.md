# Guía de lectura de las figuras — TP2

Qué mirar en cada gráfico, qué se observa y con qué se justifica.

**Las secciones están en el mismo orden en el que las figuras aparecen en la
presentación** (`presentacion/generated/TP2_Vicsek_entrega.pdf`, 32 diapositivas). Cada
título indica el número de diapositiva y el archivo de la figura. Al final hay dos
apartados de cierre: las figuras del repo que no entraron en la presentación y el
checklist para la defensa.

**Parámetros comunes**: `rc = 1`, `v₀ = 0.03`, `Δt = 1`, contorno periódico, `M = 5`
corridas por punto. Densidades del enunciado con `L = 10` (`N = ρL² = 200, 400, 800`).

| Diapositiva | Figura | Sección |
|---|---|---|
| 14–16 | `standard_rho{2,4,8}_eta{0.5,2}_mid.png` | [Modelo estándar en movimiento](#diapositivas-1416--modelo-estándar-en-movimiento) |
| 17 | `evolucion-temporal.pdf` | [v_a(t) del estándar](#diapositiva-17--evolucion-temporalpdf) |
| 18 | `relacion-parametro-observable-estandar.pdf` | [v_a vs. η](#diapositiva-18--relacion-parametro-observable-estandarpdf) |
| 19 | `barrido-variable.pdf` | [v_a vs. densidad](#diapositiva-19--barrido-variablepdf) |
| 20–22 | `voter_rho{2,4,8}_eta{0.5,2}_mid.png` | [Modelo votante en movimiento](#diapositivas-2022--modelo-votante-en-movimiento) |
| 23 | `clusters-temporal.pdf` | [S(t)](#diapositiva-23--clusters-temporalpdf) |
| 24 | `clusters-vs-eta.pdf` | [S vs. η](#diapositiva-24--clusters-vs-etapdf) |
| 25 | `va-vs-s.pdf` | [v_a vs. S](#diapositiva-25--va-vs-spdf) |
| 26 | `evolucion-variante.pdf` | [v_a(t) del votante](#diapositiva-26--evolucion-variantepdf) |
| 27 | `clusters-modelos-rho1pi.pdf` | [S: estándar vs. votante](#diapositiva-27--clusters-modelos-rho1pipdf) |
| 28 | `va-vs-s-votante.pdf` | [v_a vs. S del votante](#diapositiva-28--va-vs-s-votantepdf) |
| 29 | `tiempos-cim.pdf` | [Tiempos del CIM](#diapositiva-29--tiempos-cimpdf) |

> ⚠️ Las diapositivas 23–25 y la 27 **no usan la misma convención para las densidades
> bajas**. Está explicado en [Las dos convenciones de densidades bajas](#las-dos-convenciones-de-densidades-bajas);
> conviene leerlo antes de la defensa porque es lo primero que se nota si comparan las
> figuras entre sí.

---

## Diapositivas 14–16 — Modelo estándar en movimiento

**Figuras**: `standard_rho{2,4,8}_eta{0.5,2}_mid.png`, cada una enlazada al video completo
en YouTube. Tres diapositivas, una por densidad (`ρ = 2, 4, 8` con `L = 10`), y en cada una
dos cuadros: **izquierda `η = 0.5`, derecha `η = 2`**.

### Qué mirar

El **color de las flechas codifica la dirección** de cada partícula, así que la lectura es
inmediata sin mirar los ángulos uno por uno:

- **`η = 0.5`**: el cuadro es casi monocromático. Todas las partículas apuntan para el mismo
  lado; es el estado ordenado que en la diapositiva 17 se lee como `v_a ≈ 0.93–0.95`.
- **`η = 2`**: conviven varios colores. Todavía se distinguen parches de un mismo color
  —grupos localmente alineados— pero ya no hay una dirección global.

Al subir la densidad, la misma caja `L = 10` tiene 200 → 400 → 800 partículas: el cuadro se
llena y los parches se ven más definidos.

---

## Diapositiva 17 — `evolucion-temporal.pdf`

`v_a(t)` del **modelo estándar**, con las tres densidades del enunciado superpuestas, todas
con θ₀ aleatorio y `η = 1`. La vertical punteada marca el inicio del estado estacionario
(`t = 200`).

### Qué mirar

Dónde **deja de subir la curva y empieza a oscilar alrededor de un valor fijo**. Ese punto es
el inicio del estacionario, y de ahí en adelante es válido promediar. La cátedra confirmó que
determinarlo visualmente es suficiente; no hace falta un criterio automático.

Además, el **ancho de la banda de fluctuación** de cada densidad.

### Qué se observa

Las tres curvas suben de golpe desde `v_a ≈ 0` y se estabilizan antes de `t = 200`:

| ρ | ⟨v_a⟩ estacionario (t ≥ 200) |
|---|---|
| 2 | 0.9252 ± 0.0164 |
| 4 | 0.9439 ± 0.0071 |
| 8 | 0.9529 ± 0.0027 |

- **El valor estacionario crece con la densidad** (0.925 → 0.944 → 0.953). Más vecinos, mejor
  cancelación del ruido individual.
- **La banda de fluctuación se angosta al subir la densidad**: σ pasa de 0.0164 a 0.0027, un
  factor 6. En el gráfico se ve como que la curva de ρ=2 es visiblemente más "peluda" que la
  de ρ=8. Es un efecto de tamaño finito: promediar sobre más partículas fluctúa menos.

> ⚠️ **El corte no se hereda entre observables ni entre modelos.** Para `S` el transitorio es
> mucho más largo (diapositiva 23) y en el votante el criterio es otro (diapositiva 26).

---

## Diapositiva 18 — `relacion-parametro-observable-estandar.pdf`

`v_a` estacionario vs. `η`, una curva por densidad, con barras de error. Promedios sobre
`t ≥ 500` y `M = 5` semillas.

### Qué mirar

La forma de S de cada curva —plateau, caída, plateau— y **el corrimiento horizontal entre
densidades**. Y el tamaño de las barras según la zona.

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

Cada punto junta **los puntos crudos de la cola estacionaria de las 5 semillas en una sola
bolsa** y calcula un único promedio y desvío sobre esa bolsa. No es el promedio de los
promedios ni el desvío entre esos promedios: la cátedra marcó ese método como incorrecto
porque subestima la dispersión real. Como consecuencia, **la barra mezcla las dos fuentes de
dispersión** —la fluctuación temporal dentro de cada corrida y la diferencia entre semillas—
y por eso es grande.

**El tamaño de la barra es información física.** En η bajo todas las corridas están en el
mismo estado ordenado y la barra es diminuta; en η alto todas están igual de desordenadas y
vuelve a ser chica. **Pican en la zona de transición**, y el pico se corre a la derecha con la
densidad igual que las curvas:

| ρ | η del σ máximo | σ |
|---|---|---|
| 2 | 3.0 | 0.131 |
| 4 | 4.0 | 0.081 |
| 8 | 4.5 | 0.064 |

O sea que **el pico de las barras es en sí mismo un estimador de η_c**, y su corrimiento
confirma el de las curvas.

---

## Diapositiva 19 — `barrido-variable.pdf`

Los mismos datos de la diapositiva 18 transpuestos: `ρ` en el eje x y una curva por `η`
(0.5, 1.5, 2.5, 3.5, 4.5). Con `L = 10` fijo, variar ρ es variar N.

### Qué se observa

`v_a` crece con la densidad en todos los η, pero **la pendiente depende del ruido**:

| η | ρ=2 | ρ=4 | ρ=8 |
|---|---|---|---|
| 0.5 | 0.982 | 0.986 | 0.988 |
| 1.5 | 0.832 | 0.876 | 0.895 |
| 2.5 | 0.559 | 0.673 | 0.723 |
| 3.5 | 0.238 | 0.393 | 0.493 |
| 4.5 | 0.093 | 0.100 | 0.175 |

En η=0.5 la curva es plana (0.98 → 0.99: ya está ordenado y densificar no aporta), mientras
que en η=3.5 sube de 0.24 a 0.49, o sea que **se duplica el orden sólo por densificar**. Es la
misma física del corrimiento de la diapositiva 18, vista de canto.

---

## Diapositivas 20–22 — Modelo votante en movimiento

**Figuras**: `voter_rho{2,4,8}_eta{0.5,2}_mid.png`, con el mismo formato que las 14–16
(izquierda `η = 0.5`, derecha `η = 2`) y enlazadas a los videos.

### Qué mirar

**Comparar contra la diapositiva de la misma densidad del estándar** (14–16). Con `η = 0.5`,
donde el estándar es casi monocromático, el votante ya muestra todos los colores mezclados:
copiar la dirección de **un solo** vecino no alcanza para alinear el sistema ni con ruido
bajo. Es la lectura visual del `⟨v_a⟩ ≈ 0.10–0.19` de la diapositiva 26.

---

## Diapositiva 23 — `clusters-temporal.pdf`

`S(t)` en las **densidades bajas con `L = 10`**: tres paneles apilados, `ρ = 0.11, 0.16, 0.32`
(`N = 11, 16, 32`), cuatro curvas por panel (`η = 0, 0.5, 1, 3`) y corte del estacionario en
`t = 4000` sobre corridas de 10000 pasos.

Un cluster es una **componente conexa del grafo de vecinos**: partículas unidas por cadenas de
saltos entre partículas a distancia menor que `rc`. `S` es la fracción de partículas en el
cluster más grande.

### Qué mirar

1. **`η = 0` se pega a S = 1 y se queda ahí** en las tres densidades: sin ruido el sistema
   termina armando un único cúmulo y no lo vuelve a romper.
2. **`η = 0.5` y `η = 1` no se estabilizan nunca**: barren todo el rango entre ~0.2 y 1.0
   durante los 10000 pasos. Acá el corte en `t = 4000` no separa un transitorio de un
   estacionario —no hay un valor al que la curva converja— sino que descarta el arranque para
   que el promedio no quede sesgado por él.
3. **`η = 3` oscila abajo**, entre ~0.1 y 0.4, sin subir nunca.
4. **Las curvas son escaleras, no líneas suaves.** Con N entre 11 y 32, una sola partícula que
   entra o sale del cúmulo mueve S en 1/N ≈ 3–9%. Es la razón de que el gráfico se vea tan
   dentado, y también de que las barras de error de la diapositiva 24 sean tan grandes.

> ⚠️ Este panel usa `N = 11, 16, 32` con `L = 10`, no las corridas de `N = 400` de la
> diapositiva 27. Ver [Las dos convenciones de densidades bajas](#las-dos-convenciones-de-densidades-bajas).

---

## Diapositiva 24 — `clusters-vs-eta.pdf`

`S` estacionario vs. `η`, una curva por densidad baja (`ρ = 0.11, 0.16, 0.32` con `L = 10`),
con barras de error.

### Lo primero que hay que explicar: por qué estas densidades y no las del enunciado

Con `rc = 1` el número medio de vecinos es `π·rc²·ρ`. El umbral de percolación continua en 2D
está en ~4.5 vecinos, o sea **ρ_c ≈ 1.44**. Las densidades del enunciado (2, 4, 8) dan 6, 13 y
25 vecinos: **todas muy por encima del umbral**, así que el grafo está percolado y S ≈ 1 para
todo η — la curva no tendría nada que mostrar. Por eso el anuncio de la cátedra extiende el
estudio a `ρ = 1/π, 1/2π, 1/3π`, que dan exactamente **1, ½ y ⅓ vecinos promedio**: el régimen
fragmentado, donde S varía de verdad.

Verificación de que el código detecta la fragmentación: bajando la densidad, S da 0.15 / 0.16
/ 0.86 / 0.98 para ρ = 0.2 / 0.5 / 1 / 2. El salto cae justo donde predice la teoría.

### Qué se observa

- **Las tres curvas caen juntas**, de `S ≈ 0.99` en η=0 a `S ≈ 0.18–0.19` en η=5, y son
  prácticamente indistinguibles entre sí dentro de las barras. En este rango de densidades el
  ruido manda mucho más que la densidad.
- **El piso no es cero.** Con N tan chico, el cúmulo más grande siempre tiene unas pocas
  partículas y eso ya representa una fracción apreciable del total (1/N vale 0.09 en N=11).
  El piso de la curva es una cota de tamaño finito, no una medida de agrupamiento.
- **Las barras son enormes en toda la caída** (η entre 0.5 y 2.5). Son reales: la diapositiva
  23 muestra que en ese rango las corridas nunca se estabilizan, así que la bolsa de puntos
  crudos que se promedia está repartida entre 0.2 y 1.0.

### El transitorio de `S` es mucho más largo que el de `v_a`

Esto hay que decirlo explícitamente. El agrupamiento ocurre por *coarsening* —cúmulos que se
van fusionando de a pares— que es un proceso mucho más lento que el alineamiento de
direcciones. Por eso **las densidades bajas se corrieron a 10000 pasos** y se promedia
descartando el arranque, contra los 3000 pasos y el corte mucho más temprano de las
diapositivas 17–19.

---

## Diapositiva 25 — `va-vs-s.pdf`

`v_a` estacionario en función de `S` estacionario, un punto por η y una curva por densidad.
Están **las seis densidades**: las tres bajas (`N = 11, 16, 32` con `L = 10`) y las tres del
enunciado (`ρ = 2, 4, 8`).

### Qué mirar

- **Las tres densidades bajas trazan una relación creciente y bien definida**: más componente
  gigante, más polarización. Y lo más interesante: **las tres curvas se superponen**, o sea que
  la relación entre conectividad y orden **no depende de la densidad**, sólo de cuánta
  componente gigante haya. Es un resultado más fuerte que el de cada densidad por separado.
- **Las tres del enunciado son líneas verticales pegadas a S = 1.** Están percoladas: S no se
  mueve y sólo cambia `v_a`. No aportan información sobre la relación, y sirven justamente
  para mostrar eso: **el eje S se agota apenas se pasa el umbral de percolación**.

La lectura física: para alinearse hay que estar conectado, así que el orden no puede aparecer
sin que antes exista un cúmulo que lo sostenga.

---

## Diapositiva 26 — `evolucion-variante.pdf`

`v_a(t)` del **modelo votante**, con las tres densidades superpuestas, θ₀ aleatorio y `η = 1`.
La vertical marca `t = 100`.

### Qué se observa

| ρ | ⟨v_a⟩ estacionario (t ≥ 100) |
|---|---|
| 2 | 0.1876 ± 0.0968 |
| 4 | 0.1483 ± 0.0766 |
| 8 | 0.1040 ± 0.0503 |

**El sistema nunca se ordena.** Las curvas oscilan entre 0 y 0.5 durante los 3000 pasos, se
cruzan permanentemente entre sí, y el valor medio queda en 0.1–0.2 contra 0.92–0.95 del
estándar en las mismas condiciones (diapositiva 17, que comparte el eje y: son directamente
comparables).

El corte en t=100 es holgado por una razón distinta a la del estándar: como no hay un
transitorio de subida que esperar, las curvas ya arrancan oscilando en su valor típico. La
línea sólo descarta el arranque desde `v_a ≈ 0` de la condición inicial.

### La inversión con la densidad

Vale la pena señalarlo porque es contraintuitivo: en el estándar `v_a` **crece** con la
densidad (0.925 → 0.953), pero en el votante **decrece** (0.188 → 0.104).

La explicación está en la regla de interacción. El estándar promedia sobre todos los vecinos,
así que más vecinos significa mejor cancelación del ruido. El votante copia a **uno solo**
elegido al azar: tener más vecinos no ayuda a cancelar nada —se copia a uno igual— pero sí
aumenta la frecuencia con que llegan direcciones ajenas. La densidad, que en el estándar
ordena, en el votante desordena.

---

## Diapositiva 27 — `clusters-modelos-rho1pi.pdf`

`S` estacionario vs. `η` en `ρ = 1/π`, una curva por modelo. Corridas de 10000 pasos con
`N = 400` y `L = 35.45`, promediando el último 60%.

### Qué mirar primero: la grilla de η

El votante hace toda su transición **por debajo de η = 0.5**, así que se barrió con una grilla
fina abajo. Con la grilla del estándar la curva era un acantilado entre los dos primeros
puntos y una recta en el piso: no se podía leer nada.

### Qué se observa

| ρ=1/π | η=0 | η=0.5 | η=1 |
|---|---|---|---|
| S estándar | 0.927 | 0.557 | 0.429 |
| S votante | 0.538 | 0.131 | 0.069 |

**El caso extremo vale la pena señalarlo**: en η=0, *sin nada de ruido*, el estándar llega a
S=0.93 y el votante se queda en 0.54. El votante **no logra armar un cúmulo único ni siquiera
sin ruido**, algo que el estándar sí hace. Copiar a un vecino al azar mantiene una dispersión
de direcciones que impide que los grupos se terminen de fusionar.

> ⚠️ Esta figura usa `N = 400` con `L = √(N/ρ)`, no el `L = 10` de las diapositivas 23–25.

---

## Diapositiva 28 — `va-vs-s-votante.pdf`

El equivalente de la diapositiva 25 para el votante, con las tres densidades bajas a `N = 400`
(`L = 61.4 / 50.13 / 35.45`).

### Qué se observa

| ρ = 1/π | η=0 | η=0.5 | η=1 |
|---|---|---|---|
| S | 0.538 | 0.131 | 0.069 |
| v_a | 0.863 | 0.155 | 0.087 |

- **La relación creciente se mantiene** y las tres densidades vuelven a superponerse: es el
  mismo resultado de la diapositiva 25, y que se repita en un modelo con otra regla de
  interacción lo refuerza.
- **Pero el votante recorre sólo el tramo de abajo.** Todos los puntos con η ≥ 0.5 se amontonan
  en `S < 0.14` y `v_a < 0.16`; el único punto que llega arriba es η=0. El votante **no
  alcanza los estados de S alto** que el estándar visita, así que la curva queda truncada.
- Las barras cruzadas (en S y en v_a) son grandes en η=0 porque, igual que en el estándar, en
  esa zona cada semilla termina en un estado distinto.

---

## Diapositiva 29 — `tiempos-cim.pdf`

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

Es el punto que conecta este slide con la física del TP: **el mismo agrupamiento que se mide
con S es el que degrada la performance del CIM.**

La tercera curva separa las causas: densificar de L=20 a L=10 con el mismo N ya duplica el
tiempo (1.26 → 2.32 ms en N=1000) sólo por tener más vecinos por partícula; el resto —de 2.32
a 6.19— es efecto del agrupamiento.

### Advertencia metodológica

Ambas mediciones descartan las primeras llamadas por el **JIT de la JVM**. Sin ese descarte,
la primera N de la lista sale anómalamente lenta (N=100 daba 0.305 ms contra 0.197 de N=200,
con desvío enorme) y **la curva deja de ser monótona**. En TP1 se resolvió anteponiendo un
N=50 descartable; en TP2 con `--warmup=100` cuadros.

---

## Las dos convenciones de densidades bajas

Las densidades del anuncio de la cátedra (`ρ = 1/π, 1/2π, 1/3π`) **no dan un N entero con
L = 10**: saldrían N = 31.8, 15.9 y 10.6. La presentación resuelve eso de dos maneras
distintas según la diapositiva, y hay que tenerlo claro porque los números no son
comparables entre sí:

| Diapositivas | Convención | Densidades | Corridas |
|---|---|---|---|
| 23, 24, 25 | `L = 10` fijo, N redondeado | ρ = 0.11 / 0.16 / 0.32 | N = 11 / 16 / 32 |
| 27, 28 | N = 400 fijo, `L = √(N/ρ)` | ρ = 1/(3π) / 1/(2π) / 1/π | L = 61.4 / 50.13 / 35.45 |

- Con **L = 10 y N chico** se respeta la caja del enunciado, pero el sistema tiene entre 11 y
  32 partículas: S se mueve de a 1/N y las barras son enormes por tamaño finito, no por
  física.
- Con **N = 400 y L despejado** las estadísticas son mucho más limpias, pero es un
  **apartamiento del enunciado y hay que declararlo**.

Si en la defensa preguntan por qué la diapositiva 24 y la 27 dan valores distintos para "la
misma" densidad, la respuesta es ésta. Unificar el deck a una sola convención implica
regenerar las figuras de las diapositivas 23–25 (con los datos de `generated/d10k_rho*`) o
las de la 27–28 (con corridas nuevas a L = 10).

---

## Figuras del repo que no están en la presentación

Están generadas y sirven como respaldo para preguntas, pero no ocupan diapositiva:

| Figura | Qué muestra |
|---|---|
| `relacion-parametro-observable-votante.pdf` | El equivalente de la diapositiva 18 para el votante: la caída no tiene plateau ni η_c definido, decae desde η=0. |
| `comparacion-modelos.pdf`, `comparacion-modelos-rho{2,4,8}.pdf` | `v_a` vs. η del estándar contra el votante, una figura por densidad (`comparacion-modelos.pdf` es la pareada con la **misma condición inicial**, `--shared-ic-dir`). En ρ=4 los dos arrancan en 1.00 con η=0, pero el votante se derrumba a 0.26 en η=0.5 y a 0.15 en η=1, donde el estándar todavía está en 0.99 y 0.94. **La diferencia cualitativa importa más que la cuantitativa**: el estándar tiene la forma de S de una transición de fase —plateau, caída abrupta, plateau— y el votante decae suave y monótonamente desde η=0, sin η_c definido. |
| `evolucion-temporal-rho{2,4,8}.pdf` y `evolucion-temporal-votante-rho{2,4,8}.pdf` | El criterio de estacionario por convergencia desde condiciones iniciales opuestas: θ₀ aleatorio contra θ₀ alineado con la misma semilla. Cuando las dos curvas se juntan, el sistema se olvidó de la condición inicial. |
| `clusters-modelos-rho{2pi,3pi}.pdf` | Lo mismo que la diapositiva 27 en las otras dos densidades bajas. |
| `clusters-modelos-enunciado-rho{2,4,8}.pdf` | S estándar vs. votante en las densidades del enunciado: las dos pegadas a 1, que es lo que se espera arriba del umbral de percolación. |
| `dispersion-semillas.pdf` | Las 5 semillas de `ρ = 1/π` por separado (N=400), en `η = 0` y `η = 0.5`. **Es la mejor respuesta a "¿por qué las barras de S son tan grandes?"**: en η=0 cuatro semillas terminan en S≈1.0 y una cae a 0.605 y se congela (multiestabilidad: dos bloques rígidos que no se reencuentran); en η=0.5 ninguna curva se aplana nunca (fluctuación). Misma barra grande, dos causas distintas. |

---

## Checklist para la defensa

| Si preguntan | Respuesta corta |
|---|---|
| ¿Cómo eligieron el transitorio? | A ojo sobre las curvas v_a(t), como confirmó la cátedra: donde dejan de subir y pasan a oscilar. t=200 en el estándar, t=100 en el votante, y para S se descarta el arranque de corridas de 10000 pasos. |
| ¿Por qué las barras crecen en el medio? | Fluctuación crítica: el sistema finito cerca de η_c queda ordenado o desordenado según el detalle del ruido. El pico estima η_c (η = 3 / 4 / 4.5 para ρ = 2 / 4 / 8). |
| ¿Qué mide exactamente la barra? | El desvío sobre la bolsa de puntos crudos de la cola de las 5 semillas juntas: mezcla fluctuación temporal y dispersión entre semillas. No es el desvío de los promedios por corrida. |
| ¿Por qué las tres curvas de v_a se cruzan en η=5? | Están en el piso estadístico 1/√N, no es orden residual. |
| ¿Por qué S ≈ 1 en las densidades del enunciado? | Están sobre el umbral de percolación (ρ_c ≈ 1.44 con rc=1). Por eso la cátedra extendió a 1/π, 1/2π, 1/3π. |
| ¿Por qué la diapositiva 24 y la 27 no dan lo mismo? | Usan convenciones distintas para las densidades bajas (L=10 con N chico vs. N=400 con L despejado). Ver el apartado correspondiente. |
| ¿Por qué las barras de S no bajan corriendo más? | En η=0 sí bajaron (era relajación); en η ≥ 0.5 no, son fluctuaciones lentas de gran amplitud. |
| ¿Por qué el CIM es más lento en TP2? | El flocking concentra partículas en pocas celdas y rompe la hipótesis de ocupación uniforme. |
