# Paso 05 — Estudio de dt

**Cuándo:** Sáb 17 tarde
**Antes:** paso `04` · **Después:** paso `06`
**Todos los valores (dt, N, realizaciones, figuras, diapositivas):** `../DEFINICIONES.md`

## Estado al entrar
Motores con tests verdes. dt todavía no elegido (D1, D3 abiertas).

## Objetivo
Elegir dt y dt2 con el criterio escrito antes de mirar.

## Tareas (en paralelo)
| Rol | Tarea | Entrega | Está hecho si |
|---|---|---|---|
| C | Commitear el umbral de D1 **antes** de correr. Correr 2.1.a (D2). Producir ε_E por dt | Archivo con el umbral commiteado + outputs | El commit del umbral es anterior a los outputs |
| A | Probar el dt candidato en N=700 con x₀=r durante 10 s; corregir bugs | E acotada en el N más denso | ε_E del candidato cumple el umbral |
| D | F2 (E/E0 vs t) y F3 (ε_E vs dt con umbral y dt elegido); E_cin sola en figura aparte | F2, F3 | Sin título embebido; leyenda adentro |
| B | Tiempo por integrador medido; ayuda a C con el análisis | Frase 'el más rápido es …' | Medido en la máquina de D12 |
| E | Cerrar D1 y D3 en `../DEFINICIONES.md` con los números; definir n = dt2/dt | D1, D3 CERRADO | Todos hacen pull |

## Compuerta de salida
- [ ] dt elegido y justificado con el criterio D1
- [ ] dt2 y n enteros definidos
- [ ] F2 y F3 generadas con datos reales
- [ ] D1 y D3 en CERRADO

## Si se traba
Si ningún dt cumple el umbral, se revisa primero el motor (energía de la pared, primer paso) antes de tocar el umbral.
