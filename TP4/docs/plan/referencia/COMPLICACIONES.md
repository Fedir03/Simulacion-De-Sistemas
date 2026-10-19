# Complicaciones, riesgos y preguntas abiertas

## Trampas técnicas
- **Fuerza del oscilador dependiente de la velocidad** (−kr − γv): Verlet original no tiene v(t) hasta r(t+Δt); Velocity Verlet necesita f(t+Δt) que depende de v(t+Δt). Solo Beeman tiene variante explícita (diapo 20). La elección cambia el ECM y el "mejor esquema".
- **Diapo 17 (Velocity Verlet):** la versión anterior del PDF imprimía Δt²/m. Errata confirmada (consulta 8); la versión subida el 16/10 trae Δt²/(2m), que es lo que se usa.
- **Diapo 15 (Verlet)** escribe O(Δt³) para v(t); por Taylor sale O(Δt²). No afirmar orden para la velocidad.
- **Parámetros del oscilador:** están en la diapo 37 de la Teórica 4, no en la 36 que cita el enunciado: m=70 kg, k=1e4 N/m, γ=100 kg/s, tf=5 s, r(0)=1 m, v(0)=−Aγ/(2m).
- Euler predictor-corrector (diapo 23) ≠ Euler modificado (diapo 10).
- dt de 1e-2 (tope del enunciado) hace explotar a Verlet en el billar; la zona útil es mucho menor.
- La colocación al azar sin solapar se traba en N≈440; por eso la colocación es por grilla única para todo N (D5). El N máx se mide con código (paso 04), sin topes teóricos.
- **CIM de TP1 en el billar:** TP1 trabaja en [0,L]² y `cellIndex` recorta los índices a [0, M−1]. Las coordenadas negativas del billar (centrado en el origen) caerían todas en la celda 0 **sin ningún error**: hay que desplazarlas en +R (L = 2R). El mismo recorte tapa partículas fuera del dominio: validar |r| ≤ R antes de armar la grilla. Además, `findNeighbors` arma un `HashMap`/`HashSet` nuevo en cada llamada, lo que cuesta en el tiempo de 2.1.b. Revisión **parcial**, hecha contra el enunciado de TP1 y `TP1/CLAUDE.md`, porque no hay correcciones de TP1 escritas.

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
