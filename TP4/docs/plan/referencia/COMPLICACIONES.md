# Complicaciones, riesgos y preguntas abiertas

## Trampas técnicas
- **Fuerza del oscilador dependiente de la velocidad** (−kr − γv): Verlet original no tiene v(t) hasta r(t+Δt); Velocity Verlet necesita f(t+Δt) que depende de v(t+Δt). Solo Beeman tiene variante explícita (diapo 20). La elección cambia el ECM y el "mejor esquema".
- **Diapo 17 (Velocity Verlet):** la versión anterior del PDF imprimía Δt²/m. Errata confirmada (consulta 8); la versión subida el 16/10 trae Δt²/(2m), que es lo que se usa.
- **Diapo 15 (Verlet)** escribe O(Δt³) para v(t); por Taylor sale O(Δt²). No afirmar orden para la velocidad.
- **Parámetros del oscilador:** están en la diapo 37 de la Teórica 4, no en la 36 que cita el enunciado: m=70 kg, k=1e4 N/m, γ=100 kg/s, tf=5 s, r(0)=1 m, v(0)=−Aγ/(2m).
- Euler predictor-corrector (diapo 23) ≠ Euler modificado (diapo 10).
- dt de 1e-2 (tope del enunciado) hace explotar a Verlet en el billar; la zona útil es mucho menor.
- La colocación al azar sin solapar se traba en N≈440; por eso la colocación es por grilla única para todo N (D5). El N máx se mide con código (paso 04), sin topes teóricos.
- **CIM de TP1 en el billar:** TP1 trabaja en [0,L]² y `cellIndex` recorta los índices a [0, M−1]. Las coordenadas negativas del billar (centrado en el origen) caerían todas en la celda 0 **sin ningún error**: hay que desplazarlas en +R (L = 2R). **Medido 20/10:** sin el +R los pares salen **igual de bien**, porque un vecino en contacto de una coordenada negativa tiene coordenada < 2r < tamaño de celda y también cae en el índice 0. El problema es el **costo**: con N=714, 390 partículas caen en la columna 0 y 395 en la fila 0, y cada llamada tarda **2,0–4,4 veces más** (mediana 2,1×): sin +R, 920–2149 µs por llamada; con +R, 431–553 µs. Condiciones: N=714 (hex, x₀=r), 958 pares, M=29, 5 corridas en JVM nuevas, 2000 llamadas tras 300 de calentamiento. **Máquina con ruido:** el mismo test varió entre 2 y 4 s, y la corrida de 4,4× es un valor atípico. Hecho en `engine/cim/CellIndexMethod.forCircle`. El mismo recorte tapa partículas fuera del dominio: validar |r| ≤ R antes de armar la grilla. Además, `findNeighbors` arma un `HashMap`/`HashSet` nuevo en cada llamada: medido y resuelto el 21/10 (subítem siguiente). Revisión **parcial**, hecha contra el enunciado de TP1 y `TP1/CLAUDE.md`, porque no hay correcciones de TP1 escritas.
  - **Asignaciones por paso del CIM (medido y resuelto 21/10).**
    - **Problema:** piloto con N=714, x₀=r, tf=30 s, dt=1e-4, semilla 1, `-Xms2g -Xmx2g`, con JFR y `-Xlog:gc`: la corrida tardó **143,5 s**. La búsqueda de vecinos con el CIM tomaba ~69 % del tiempo y recorrer el `Map`/`HashSet` que devolvía, otro ~16 % (≈ 85 % en total). El recolector casi no pesaba (81 pausas, 0,30 s, 0,2 %), pero el programa asignaba ~99 GB (~330 KB por paso): `HashMap` y N `HashSet` nuevos en cada paso, boxing y recorrido del mapa.
    - **Solución:** `CellIndexMethod.forEachContact`, con listas `head[M·M]`/`next[N]` reutilizadas, sin `HashMap`/`HashSet` ni boxing, y con la misma media vecindad, el mismo corrimiento +R, el mismo recorte de celda y las mismas validaciones. `ContactForces` usa `forEachContact` y recorre los pares una sola vez. `findNeighbors` (interfaz de TP1) queda intacto. Rama `cim-sin-asignaciones`, commit 1733b42.
    - **Resultado de tiempo:** N=714, 5 semillas por versión, alternando main y rama en serie, mismas banderas. Main tardó 132,7 s [127, 145] y la rama **33,1 s [31,9, 34,0]** (−75 %, rangos sin solapamiento). La rama tuvo 0 pausas del GC: el total asignado no llenó el espacio joven de ~1,2 GB (< 4 KB por paso). El piloto de una semilla había dado 143,5 s contra 38,1 s.
    - **Tests: 48/48.** Al cambiar el orden de suma de las fuerzas, el caso (b) de `CimVsBruteForceSimulationTest` dejó de pasar con su criterio original (pares idénticos entre las dos corridas durante 2001 pasos). La diferencia de redondeo (~1e-16) crece unas 10 veces cada 200 pasos en un sistema denso y caótico (|Δr| ≈ 5e-12 en el paso 1000 y ≈ 2e-8 en el 1808), y un par con |ξ| ≈ 1e-8 se cuenta en una corrida y en la otra no. Antes pasaba por suerte, porque los dos caminos sumaban casi en el mismo orden. **Criterio nuevo:** los pares entre corridas se comparan solo en los primeros 1000 pasos (junto con r y v). En todos los pasos se verifica que CIM = `findNeighbors` = fuerza bruta sobre las mismas posiciones, lo que prueba que la búsqueda es correcta sin depender del caos.
    - **Equivalencia estadística** (n = 5 semillas por versión, N=714, x₀=r, tf=30 s, dt=1e-4): **no se detectó diferencia**, lo que no quiere decir que sean iguales.
      - Nu final: main 9,2 [8, 12] (σ 1,8) y rama 9,8 [8, 14] (σ 2,5); prueba t de Welch t ≈ 0,44 (p ≈ 0,7).
      - ΔE/E0 final: main 2,6e-3 y rama 3,1e-3 (σ ≈ 1,5e-3); t ≈ 0,5 (p ≈ 0,6).
      - Máximo |ΔE|/E0: 3,5e-3 en las dos.
      - Con n = 5 solo se detectarían diferencias de 2 desvíos o más, y esto no es una prueba de equivalencia.
      - Se descartó el criterio de "cada rango contiene al otro". Con valores continuos es imposible de cumplir, y con 5 contra 5 es muy probable que algún valor caiga fuera del rango de la otra versión por azar: aun si las dos versiones fueran idénticas, la rama caería entera dentro del rango de main solo con probabilidad ≈ 22 %.
      - No se comparó semilla por semilla porque, con la misma semilla, las trayectorias se separan por el orden de suma.
      - **Argumento principal (no estadístico):** los tests muestran los mismos pares sobre las mismas posiciones en todos los pasos, la misma fórmula de fuerza y |Δr| ≈ 5e-12 en los primeros 1000 pasos. El cambio solo altera el orden de suma, y el caos hace que cada versión sea otra realización igual de válida, equivalente a cambiar la semilla.
    - **Consecuencia:** los resultados de la rama no coinciden bit a bit con los de main anteriores. Cuando se hizo el cambio no había corridas de producción del Sistema 2; todo lo que va al informe (2.1.a, 2.1.b, 2.2, 2.3, 2.4) tiene que correrse con el código ya congelado.
    - **Pendientes (no resueltos):**
      - (a) En las 10 corridas la energía crece entre +0,04 % y +0,43 % en 30 s con dt=1e-4, igual en las dos versiones. No viene de la optimización: hay que revisar en 2.1.a cómo escala ε_E con dt antes de fijar el dt.
      - (b) `BilliardSimulator.outside` (`hypot` por partícula y por paso) pesa ~11 % del tiempo restante y se deja como está.
    - **Para la oral:** "Comparamos 5 semillas por versión en N = 714 y no detectamos diferencia en Nu ni en la deriva de energía más allá de la dispersión entre semillas; el tiempo bajó un 75 %; el cambio solo altera el orden de suma de las fuerzas."

## Datos faltantes del repo (reporte de Claude Code)
- No existe módulo Maven TP4 (sin pom.xml ni src/, y no figura en `<modules>` del pom raíz); TP_template existe. Maven multimódulo, Java 21, paquete `ar.edu.itba.sds.tpN`.
- Actualizado 15/10: la carpeta `TP4/` ya existe con `docs/enunciado/` (enunciado + Teórica 4) y `docs/plan/` (staged, sin commit). Resto de esta sección re-verificado contra `cbd07ff`: sin cambios.
- CIM en TP1 (`CellIndexMethod.java`), dominio cuadrado, TP2 lo reusa; TP3 no usa CIM.
- Generador al azar de TP3 en `StageGeneration.java:16` (rectángulo, 100k intentos); hay que adaptarlo a la grilla única para volver a correr TP3 (paso 04, D7).
- Datos crudos del benchmark de TP3 no existen (gitignored) y la máquina no se registró.
- Nunca se hizo un ajuste de distribución de velocidades.
- Un borrador del script de ZIP no compilaría con solo `engine/`.
- Ruta real del código: src/main/java/ar/edu/itba/sds/tpN/..., no engine/ en la raíz del módulo.

## Bloqueos
- Segunda lectura de fórmulas completa (15/10); Paso 0 cerrado.
- Re-correr el benchmark de TP3 en la misma máquina que TP4 (bloquea 2.1.b).
- Qué cuenta como contacto con obstáculo y radio del obstáculo: releer el enunciado antes de codificar.
- Windows/Git Bash: probar el flujo completo en la máquina de la presentación.
- ZIP: TP2 reutilizaba el CIM de TP1 como dependencia Maven; en el ZIP de TP4 se copian **solo** `CellIndexMethod`, `NeighborFinder` y `Particle` dentro del módulo (Q9: nada de más), porque el ZIP debe compilar solo. Verificar en carpeta aislada.

## Preguntas a la cátedra (numeración y respuestas completas en Notion, task "TP4: llevar preguntas a la cátedra")
Respondidas el 16/10; decisiones del grupo del 19/10. Resumen por ítem en `../pasos/03-clase-presencial-consultas.md`.
1. TP3 vs TP4 en 2.1.b → TP4 con obstáculos (D7). Respondida.
15. Hasta cuándo simular cada dt en 2.1.a → 30 s y después hasta el estacionario; barrido hasta 1e-6 (D1, D2). Respondida.
6. Velocidad en Verlet/Velocity Verlet → se aceptan; ojo con el paso inicial de Euler (D17). Respondida.
5. Colocación para N grande → grilla única; N máx medido (D5, D6). Respondida.
14. N por estudio y N máx → el más alto posible con la grilla (D6, D7). Respondida.
11. Animaciones → 2.2, 2.3, 2.4 (D16). Respondida.
13. Estacionario en 2.3 → a ojo sobre el gráfico (D15). Respondida.
10. MB 2D → k_BT único (D15). Respondida.
8. Errata Δt²/m → sí, errata (D19). Respondida.
4. Densidad en 2.4.a → **abierta**: la cátedra pidió ver dónde se usó en TP3 (D20).
3. CIM → usar (D25). Respondida.
9. ZIP → solo lo necesario de TP1; README chico (D26). Respondida.
12. Energía total → cinética + elástica, sin la partícula imagen (D21). Respondida.
7. Orden de v en Verlet → OK, no se afirma. Respondida.
Resuelta antes: 2 (Euler predictor-corrector).
