# Paso 03 — Clase presencial consultas

**Cuándo:** Vie 16/10, clase presencial
**Antes:** paso `02` · **Después:** paso `04`
**Todos los valores (dt, N, realizaciones, figuras, diapositivas):** `../DEFINICIONES.md`

## Estado al entrar
Módulo en marcha; consultas prioritarias listas. Todo lo demás de DEFINICIONES sigue como propuesta.

## Objetivo
Volver con respuestas para decidir D5, D6, D11, D15, D16, D17, D19.

## Tareas (en paralelo)
| Rol | Tarea | Entrega | Está hecho si |
|---|---|---|---|
| E | Hacer las consultas en este orden (la propuesta propia va después de cada una) | Respuestas anotadas textualmente | Cada consulta con respuesta o 'sin respuesta' |
| A | Probar en el momento la colocación con grilla (D5); la medición formal del N máx es una tarea del paso 04 | N máximo de la prueba | Número anotado |
| Todos | Escuchar y anotar lo que la cátedra dice de otros grupos (cambios de enunciado, advertencias) | RECORDAR [Sims]: ⚠️ … | Cada advertencia clasificada |

## Consultas (la numeración y el texto completo de cada respuesta están en la task de Notion "TP4: llevar preguntas a la cátedra", que es la fuente)
Respuestas de la cátedra del 16/10; decisiones del grupo del 19/10.
- [x] Q1 · Comparación de tiempos TP3 vs TP4 en 2.1.b → TP4 con obstáculos, porque es la única forma de que haya partículas usadas. No se corre TP4 sin obstáculos en 2.1.b (D7).
- [x] Q15 · Hasta cuándo se simula cada dt en 2.1.a → 30 s para todos los dt; después, hasta el estacionario (se aplana o se dispara), cortando al 1–2 % del último punto. Grupo 19/10: barrido hasta 1e-6 (D1, D2).
- [x] Q6 · Velocidad en Verlet y Velocity Verlet (oscilador) → se aceptan las estimaciones; ojo con el paso inicial de Euler. Grupo 19/10: un punto del ECM fuera de tendencia por ese paso se descarta y se aclara en la presentación (D17).
- [x] Q5 · Colocación inicial con N grande → grilla definida de antemano y partículas agregadas al azar en ella; las curvas de 2.1.b se tienen que cruzar. Grupo 19/10: N máx y tamaño de grilla se miden con código, sin topes teóricos (D5, D6, paso 04).
- [x] Q14 · N por estudio y N máximo → ver Q5; llegar a los N más altos posibles con la grilla (D6, D7).
- [x] Q11 · Animaciones → de acuerdo: 2.2, 2.3 y 2.4; 2.1.a ninguna; 2.1.b usa la de 2.4 (D16).
- [x] Q13 · Criterio de estado estacionario en 2.3 → se corre, se grafica y se define a ojo (D15).
- [x] Q10 · Fórmula de Maxwell-Boltzmann 2D → k_BT como único parámetro (D15).
- [x] Q8 · Velocity Verlet: Δt²/m vs Δt²/(2m) → errata; se usa Δt²/(2m) (D19).
- [x] Q3 · Estructura espacial (CIM) → usar CIM (D25).
- [x] Q9 · Contenido del ZIP → lo necesario de TP1 para que el motor funcione, sin archivos de más. Grupo 19/10: README chico (compilar y correr) y solo las clases del CIM (D25, D26).
- [x] Q12 · Energía total con la pared y los obstáculos → cinética + elástica de todos los choques; la partícula imagen no suma. Grupo 19/10: la elástica de la pared se suma una vez y decide el test de conservación (D21).
- [x] Q7 · Orden del error de v en Verlet → OK: no se afirma ningún orden.
- [ ] Q4 · Densidad: N/área o fracción de empaquetamiento → **abierta**. La cátedra pidió que le mostremos dónde se usó en TP3 (D20).

## Compuerta de salida
- [ ] Q1, Q5 y Q6 con respuesta, o con decisión propia escrita y su motivo
- [ ] Respuestas pegadas en la task de Notion "TP4: llevar preguntas a la cátedra" y en `../DEFINICIONES.md` (D5, D6, D11, D15, D16, D17, D19 pasan a CERRADO)
- [ ] N máximo de la prueba con grilla anotado (la medición formal está en el paso 04)

## Si se traba
Q1, Q5 y Q6 cambian lo que se corre; son las que no pueden quedar sin respuesta. Si no responden, se sigue con la propuesta y se deja escrito el motivo.
