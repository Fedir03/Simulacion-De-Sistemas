# Metodología de desvío estándar entre repeticiones — hallazgo crítico confirmado por la cátedra

## El error común (que la cátedra marcó explícitamente como incorrecto en una clase real)

Calcular el desvío estándar de un punto (ej. un valor de η en una curva observable-vs-parámetro) como el desvío ENTRE los promedios de cada realización/repetición — es decir: M repeticiones, cada una promediada por separado en su propio estado estacionario, y el desvío calculado sobre esos M números.

**Por qué está mal:** esto es el desvío de una cantidad ya promediada sobre miles de pasos temporales (por el teorema central del límite, mucho más chico que la dispersión real del sistema). Dos realizaciones pueden tener muchísima variabilidad interna cada una, pero si por casualidad sus promedios coinciden, este método reporta un desvío casi cero — ocultando la variabilidad real del fenómeno.

## El método correcto

Juntar TODOS los valores instantáneos del observable en estado estacionario de TODAS las realizaciones en una sola "bolsa" de datos (ej. M=5 realizaciones × 2500 pasos en estacionario = 12500 puntos), y calcular UN SOLO promedio y UN SOLO desvío estándar muestral sobre esa bolsa completa.

```
B = { x_a^(k)(t) : k = 1,...,M ; t = t0,...,tf }
σ = sqrt( (1/(|B|-1)) * Σ_{x∈B} (x - <x>)² )
```

## Consecuencias prácticas al aplicar esto

- El **promedio** (posición del punto en la curva) no cambia, siempre que todas las corridas de un mismo punto tengan la misma cantidad de pasos en su cola estacionaria — el promedio de la bolsa completa es algebraicamente igual al promedio simple de los M promedios por corrida en ese caso.
- La **barra de error SÍ cambia**, y típicamente crece — a veces bastante. El método incorrecto subestima la incertidumbre real reportada.
- Si ya se generaron figuras con el método incorrecto y todavía existen los datos crudos (no se borraron), no hace falta volver a simular — es un recálculo barato sobre los datos que ya están.

## Cantidad de repeticiones (M)

No hay un número "correcto" universal, pero tené en cuenta el orden de magnitud: grupos de referencia de esta materia han usado desde M=5 hasta M=5000 según el tiempo de cómputo disponible. M bajo (ej. 5) no invalida el análisis si el método de bolsa de datos está bien aplicado, pero si sobra tiempo antes de la entrega, vale la pena correr una campaña con M más alto (ej. M=30) en paralelo para ver si angosta notoriamente las barras de error en las zonas de mayor variabilidad (típicamente cerca de una transición de fase/orden-desorden), sin descartar los resultados ya válidos si no da tiempo a terminarla.

## Criterio de estado estacionario (t0)

Se elige "a ojo" mirando la evolución temporal del observable — NO con un test estadístico automático, la cátedra confirmó explícitamente que no hace falta. Puede expresarse como un paso absoluto (si todas las corridas comparadas tienen el mismo largo total) o como un porcentaje del largo de la corrida (si se comparan corridas de distinto largo total, donde un valor absoluto no sería comparable proporcionalmente entre ellas).
