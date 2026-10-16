# Complicaciones, riesgos y preguntas abiertas

## Trampas técnicas
- **Fuerza del oscilador dependiente de la velocidad** (−kr − γv): Verlet original no tiene v(t) hasta r(t+Δt); Velocity Verlet necesita f(t+Δt) que depende de v(t+Δt). Solo Beeman tiene variante explícita (diapo 20). La elección cambia el ECM y el "mejor esquema".
- **Diapo 17 (Velocity Verlet)** imprime Δt²/m: probable errata, usar Δt²/(2m).
- **Diapo 15 (Verlet)** escribe O(Δt³) para v(t); por Taylor sale O(Δt²). No afirmar orden para la velocidad.
- **Parámetros del oscilador** están en la diapo 37 (el enunciado dice 36): m=70 kg, k=1e4 N/m, γ=100 kg/s, tf=5 s, r(0)=1 m, v(0)=−Aγ/(2m).
- Euler predictor-corrector (diapo 23) ≠ Euler modificado (diapo 10).
- dt de 1e-2 (tope del enunciado) hace explotar a Verlet en el billar; la zona útil es mucho menor.
- RSA se traba en N≈440; para N mayor hace falta la red hexagonal (no existe generador en el repo).

## Datos faltantes del repo (reporte de Claude Code)
- No existe módulo Maven TP4 (sin pom.xml ni src/, y no figura en `<modules>` del pom raíz); TP_template existe. Maven multimódulo, Java 21, paquete `ar.edu.itba.sds.tpN`.
- Actualizado 15/10: la carpeta `TP4/` ya existe con `docs/enunciado/` (enunciado + Teórica 4) y `docs/plan/` (staged, sin commit). Resto de esta sección re-verificado contra `cbd07ff`: sin cambios.
- CIM en TP1 (`CellIndexMethod.java`), dominio cuadrado, TP2 lo reusa; TP3 no usa CIM.
- RSA en TP3 `StageGeneration.java:16` (rectángulo, 100k intentos).
- Datos crudos del benchmark de TP3 no existen (gitignored) y la máquina no se registró.
- Nunca se hizo un ajuste de distribución de velocidades.
- Un borrador del script de ZIP no compilaría con solo `engine/`.
- Ruta real del código: src/main/java/ar/edu/itba/sds/tpN/..., no engine/ en la raíz del módulo.

## Bloqueos
- Segunda lectura de fórmulas completa (15/10); Paso 0 cerrado.
- Re-correr el benchmark de TP3 en la misma máquina que TP4 (bloquea 2.1.b).
- Qué cuenta como contacto con obstáculo y radio del obstáculo: releer el enunciado antes de codificar.
- Windows/Git Bash: probar el flujo completo en la máquina de la presentación.
- ZIP: TP2 reutilizaba el CIM de TP1 como dependencia Maven; en el ZIP de TP4 hay que copiar esas clases dentro del módulo (o dejar CIM como código propio de TP4), porque el ZIP debe compilar solo. Verificar en carpeta aislada.

## Preguntas a la cátedra (estado en Notion, task "TP4: llevar preguntas a la cátedra")
1. Comparación TP3 (sin obstáculos) vs TP4 2.1.b (con obstáculos): ¿válida? (alta)
6. Velocidad en Verlet/Velocity Verlet con fuerza dependiente de v (alta)
5. Red hexagonal para N grande (alta)
3. CIM vs fuerza bruta para N>600
4. Definición de densidad en 2.4.a
7. Orden del error de v en Verlet (baja)
8. Errata Δt²/m en Velocity Verlet (baja)
9. Contenido del ZIP (baja)
10. Fuente de f(v) de Maxwell-Boltzmann 2D (baja)
11. Animaciones: ¿la de 2.4 cubre 2.1.b? (media)
12. Energía total con la pared y los obstáculos (baja)
13. Criterio de estado estacionario en 2.3 (media)
Resuelta: 2 (Euler predictor-corrector).
Cuando el profesor responda, documentar la respuesta debajo de la pregunta en Notion y copiar aquí.
