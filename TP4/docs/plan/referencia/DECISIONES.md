# Decisiones y tradeoffs

| # | Decisión | Recomendación y motivo |
|---|---|---|
| T1 | Criterio para elegir dt | Umbral de deriva de energía fijado **antes** de ver curvas; probarlo en el N más denso; dt más grande que cumpla. Mostrar por qué fallan los mayores (inestabilidad). |
| T2 | dt2 | Elegir dt2 ≪ escala de t90 (resolución de t90/t100 = dt2). Escribir solo en múltiplos de dt2 (error de TP3: estado final fuera de los tiempos del método). |
| T3 | Condición inicial N grande | RSA hasta ~300–400; red hexagonal con sitios sorteados y direcciones aleatorias para N grande; declararlo en Simulaciones. Falta escribir el generador hexagonal. |
| T4 | CIM vs fuerza bruta | CIM (reuso de TP1; TP3 no usa CIM: es event-driven y recalcula los próximos choques solo de las partículas involucradas) con test de equivalencia. No re-explicar CIM. |
| T5 | Medición de tiempo (2.1.b) | Misma convención que TP3, misma máquina, en serie, sin otras cargas. TP3 midió con `System.nanoTime` alrededor de `CollisionSimulator.run`, JVM nueva por realización, N=25–425, 10 realizaciones, tf=30, `--jobs 1`; sin datos crudos ni registro de máquina ⇒ re-correr TP3. |
| T6 | Comparación TP3 vs TP4 | Correr también TP4 sin obstáculos para una curva comparable limpia; mostrar la de obstáculos como pide el enunciado. |
| T7 | Realizaciones y barras de error | Más que el mínimo si alcanza el tiempo; σ vs σ/√N decidido por caso y escrito en una línea. |
| T8 | Estado estacionario (2.3) | Evolución temporal de un escalar que justifique el tiempo elegido. |
| T9 | Euler predictor-corrector | **Resuelto** (diapo 23): una sola pasada; no es el Euler modificado de la diapo 10. |
| T10 | Mapa de calor 2.4.b (opcional) | Decidir el mar 20/10; solo si todo lo obligatorio está revisado. |
| T11 | Animaciones | 3 animaciones de casos típicos: 2.2, 2.3 y 2.4; 2.2 y 2.4 con fresca/usada coloreada; 2.3 (sin obstáculos) sin esa coloración. La de 2.4 (N=600, x₀=r) sirve también para 2.1.b porque 2.4 usa los outputs de 2.1.b. 2.1.a no lleva (Nash). Confirmar con la cátedra en Q11. Link visible en el PDF. Corrección IMPORTANTE de Nash TP4: sin animaciones no se verifica la implementación. |
| T12 | Llenado del dominio | Corrección de TP3: otros grupos usaron N>1000 y fue bien visto. Barrido de N hasta ~700. |
| T13 | Velocidad en fuerza dependiente de v (oscilador) | A decidir el jue 15/10. Propuesta: Beeman PC (diapo 20); Velocity Verlet con velocidad predicha por Euler; Verlet con velocidad hacia atrás. Declarar en Implementación; afecta el ECM. |

## Registro (completar en la reunión)
- [ ] T1: 
- [ ] T2: 
- [ ] T3: 
- [ ] T5: 
- [ ] T13: 
- [ ] Reparto A–E: 
- [ ] Fecha/hora de congelado del motor: 
