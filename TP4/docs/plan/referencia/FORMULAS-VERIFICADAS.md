# Fórmulas verificadas (Teórica 4)

Transcriptas el 14/10 mirando imagen por imagen las 47 diapositivas de `Teorica_4.pdf` y las fotos de la carpeta "Teorica_4 - Formulas". Fuente editable: Notion, entrada "Teorica 4 - Dinámica Molecular por Paso Temporal". Lo dudoso está marcado con ⚠️.
**Estado:** Segunda lectura completa (15/10): diapos 9, 10, 13–15, 17, 19, 20, 23, 37 y 42–46 contrastadas por otra persona del grupo. No implementar de memoria: ante duda, leer la diapositiva.
**Verificación contra el PDF nuevo (19/10, hecha por el grupo):** las fórmulas de las diapos 9–23, 31–37 y 42–46 se verificaron contra la versión de `Teorica_4.pdf` subida el 16/10 (commit 90ffd06; metadatos de exportación 2/10). La versión anterior del repo (eef35f4) tiene metadatos de exportación 1/10. **Pendiente:** auditar el código contra estas fórmulas (D29), a cargo del revisor asignado en D30.

Notación: a_i = f_i / m_i. Vectores en negrita en la presentación; acá se escriben sin negrita.

## Euler (diapo 9) y Euler modificado (diapo 10)
Euler:
```
r(t+Δt) = r(t) + Δt·v(t) + (Δt²/(2m))·f(t) + O(Δt³)
v(t+Δt) = v(t) + (Δt/m)·f(t) + O(Δt²)
```
Euler modificado (usa la velocidad ya actualizada):
```
v(t+Δt) = v(t) + (Δt/m)·f(t)
r(t+Δt) = r(t) + Δt·v(t+Δt) + (Δt²/(2m))·f(t)
```

## Verlet original (diapos 13, 14, 15)
```
r(t+Δt) = 2·r(t) − r(t−Δt) + (Δt²/m)·f(t) + O(Δt⁴)
v(t)    = [r(t+Δt) − r(t−Δt)] / (2Δt)
```
- Primer paso: estimar posición y velocidad anteriores con Euler evaluado en −Δt.
- Las velocidades solo hacen falta para la energía cinética.
- ⚠️ La diapo 15 escribe O(Δt³) para v(t). Por Taylor sale O(Δt²) (el O(Δt³) es del numerador). No afirmar ningún orden para v (consulta 7: la cátedra dijo OK, 16/10).

## Velocity Verlet (diapo 17)
```
r(t+Δt) = r(t) + Δt·v(t) + (Δt²/(2m))·f(t) + O(Δt³)
v(t+Δt) = v(t) + (Δt/(2m))·(f(t) + f(t+Δt)) + O(Δt²)
```
Pasos intermedios de la diapo:
```
v(t+Δt/2) = v(t) + a(t)·Δt/2
v(t+Δt)   = v(t+Δt/2) + a(t+Δt)·Δt/2
```
La versión anterior del PDF (eef35f4, exportada 1/10) imprimía el término de posición como Δt²·f/m (sin el 2); la versión subida el 16/10 (90ffd06, exportada 2/10) ya trae Δt²/(2m) en la diapo 17, según la verificación visual del grupo. La cátedra confirmó que era errata (consulta 8, 16/10). **Se usa Δt²/(2m)**, que es lo coherente con Taylor (diapos 9, 10, 13) y con los pasos intermedios.

## Beeman (diapo 19)
```
r(t+Δt) = r(t) + v(t)·Δt + (2/3)·a(t)·Δt² − (1/6)·a(t−Δt)·Δt²
v(t+Δt) = v(t) + (1/3)·a(t+Δt)·Δt + (5/6)·a(t)·Δt − (1/6)·a(t−Δt)·Δt
```
Variante predictor-corrector para fuerzas que dependen de la velocidad (diapo 20):
```
r(t+Δt)        = r(t) + v(t)·Δt + (2/3)·a(t)·Δt² − (1/6)·a(t−Δt)·Δt² + O(Δt⁴)
v_pred(t+Δt)   = v(t) + (3/2)·a(t)·Δt − (1/2)·a(t−Δt)·Δt + O(Δt³)
a(t+Δt)        = f(r(t+Δt), v_pred(t+Δt)) / m
v_corr(t+Δt)   = v(t) + (1/3)·a(t+Δt)·Δt + (5/6)·a(t)·Δt − (1/6)·a(t−Δt)·Δt + O(Δt³)
```
Necesita a(t−Δt) en el primer paso (se estima, ej. Euler en −Δt como en Verlet).

## Euler predictor-corrector (diapos 22 y 23)
Una sola pasada, sin iterar:
```
1) Predecir:  v_p(t+Δt) = v(t) + a(t)·Δt ;  r_p(t+Δt) = r(t) + v(t)·Δt
2) Evaluar:   a(t+Δt) = f(r_p, v_p) / m
3) Corregir:  v(t+Δt) = v(t) + a(t+Δt)·Δt ;  r(t+Δt) = r(t) + v(t+Δt)·Δt
```
No es el Euler modificado de la diapo 10.

## Sistema 1: oscilador amortiguado (los parámetros están en la diapo 37 de la Teórica 4, no en la 36 que cita el enunciado)
```
f = m·a = −k·r − γ·v
m = 70 kg, k = 1e4 N/m, γ = 100 kg/s, tf = 5 s
r(0) = 1 m (= A), v(0) = −A·γ/(2m) ≈ −0,714 m/s
r(t) = A·exp(−γt/(2m))·cos( sqrt(k/m − γ²/(4m²))·t )
```
### 🚨 La fuerza depende de la velocidad
- **Verlet original:** f(t) necesita v(t), que Verlet solo conoce con r(t+Δt). Estimar v(t) (diferencia hacia atrás o velocidad predicha por Euler) y declararlo.
- **Velocity Verlet:** f(t+Δt) necesita v(t+Δt). Usar velocidad predicha.
- **Beeman:** usar la variante predictor-corrector (diapo 20).
- La elección cambia el ECM. Se escribe en Implementación. Cerrado (consulta 6, D17): diferencia hacia atrás en Verlet, velocidad predicha por Euler en Velocity Verlet, PC en Beeman. Si un punto del ECM sale fuera de la tendencia por el paso inicial de Euler, se descarta y se aclara en la presentación.

## Elección del paso temporal (diapos 31–35)
- Δt muy corto: lento. Muy largo: errores y "explosiones".
- Distinguir Δt de la simulación de Δt2 = n·Δt (n entero) para guardar: la diapo 33 guarda si t/Δt2 = round(t/Δt2).
- **Adaptación declarada (mínima):** se guarda con un contador entero, cuando `paso % n == 0`, en lugar de comparar t/Δt2 con round(t/Δt2), que es frágil con t flotante (t acumula redondeo). Es equivalente en aritmética exacta. Figura en `../auditoria-integradores.md`.
- Verificación del error: caso simple → comparar con la solución analítica; conservativo → E_cin + E_pot = cte; no conservativo → achicar Δt hasta que los resultados cambien menos que un error dado.

## Fuerza normal de contacto (diapos 42–46)
```
F_N = −k_n·ξ·e_n
e_n = (r_j − r_i) / |r_j − r_i|
ξ_ij = R_i + R_j − |r_j − r_i|     (contacto si ξ > 0)
E_pot = (1/2)·k_n·ξ²
```
La condición de contacto ξ > 0 tiene como fuente el **enunciado** (Sistema 2), no una diapositiva.
La fuerza total sobre i es la suma sobre los j en contacto. La parte tangencial (diapo 45) no se usa en TP4.

## Teórica 0: ajuste y estadística (diapos 60–72, verificadas por el grupo el 19/10)
- Ajuste: por mínimos cuadrados, E(c) = Σ_i [y_i − f(x_i, c)]²; el mejor c minimiza E. Solo con modelos teóricos, nunca polinomios ni splines. Para 2.3: barrer k_BT, graficar E(k_BT), mostrar el mínimo.
- Histograma: y_i = N_i (cuentas); probabilidad y_i = N_i/N; PDF y_i = N_i/(dx_i·N), integral = 1.
- Error muestral: promedio ± σ entre semillas; no informar más cifras que las que sostiene el error.
- Maxwell-Boltzmann 2D: no está en Teórica 0 ni 4. La fórmula está en el enunciado (2.3): f(v) = (m·v/(k_BT))·exp(−m·v²/(2·k_BT)). En el PDF es una imagen: la extracción de texto solo trae la frase que la introduce. Confirmada por la cátedra el 16/10: único parámetro k_BT (consulta 10).

## No usado en TP4
Gear predictor-corrector (diapos 24–30) y gravedad: no los pide el enunciado.
