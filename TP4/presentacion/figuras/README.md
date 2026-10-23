# Figuras de la presentación

Las figuras con datos (F1–F10) las escribe `analysis/make_figures.py` desde
`outputs/`, con nombre fijo y estilo único; los fotogramas de las animaciones
salen del script de animación a partir de `dynamic.txt` (D28 en
`../../docs/plan/DEFINICIONES.md`). Ninguno de esos scripts va al ZIP.

Mientras un archivo no exista, la diapositiva muestra una caja gris con la
ruta esperada: no hace falta editar el `.tex`, solo generar el archivo con el
nombre correcto.

## Reglas (correcciones reales de TP2–TP3, ver skill `sims-tp-format`)

- Letra de la figura comparable a la de la diapositiva: la figura vive en una
  columna de `0.66\textwidth`, así que se genera ya con `font.size = 14`.
  Verificar proyectando a pantalla completa.
- Nunca título embebido dentro del área graficada.
- Labels de eje cortos (convención al principio del `.tex`).
- Leyenda solo con lo que varía; los parámetros fijos van en el `\parambox`.
- Barras de error según `DEFINICIONES.md` §2.
- Cada símbolo se define una vez, con texto y marca visual (`DEFINICIONES.md` §5).

## Nombres esperados por el `.tex`

| Archivo | Diapositiva | Contenido |
|---|---|---|
| `E2-contacto.png` | S02 | dos círculos superpuestos con ξ marcada |
| `E3-linea-de-tiempo.png` | S03 | pasos Δt y salidas Δt₂ marcadas |
| `E1-esquema-sistema.png` | S05 | dominio, obstáculos en ±x₀, R y r con cota, fresca/usada |
| `F1-ecm-vs-dt.pdf` | S06 | ECM vs. Δt, 4 esquemas |
| `F2-energia-vs-t.pdf` | S07 principal | energía total E(t) en joules vs. tiempo, curvas juntas y escala asinh centrada |
| `F3-epsE-vs-dt.pdf` | S08 | ε_E vs. Δt, umbral y Δt elegido |
| `F4-tiempo-vs-n.pdf` | S09 | tiempo de ejecución vs. N, TP4 y TP3 |
| `anim-2-2.png` | S10 | fotograma de la animación de 2.2 |
| `F5-fu-vs-t.pdf` | S11 | Fu(t) para 3 valores de x₀ |
| `F6-t90-vs-x0.pdf` | S12 | ⟨t₉₀⟩ vs. x₀, N=100 y N=20 |
| `F7-fv-temporal.pdf` | S13 | f(v) a varios tiempos |
| `anim-2-3.png` | S13 | fotograma de la animación de 2.3 |
| `F8-fv-mb.pdf` | S14 | f(v) estacionaria y ajuste MB 2D |
| `F9-t-vs-rho.pdf` | S15 | ⟨t₉₀⟩ y ⟨t₁₀₀⟩ vs. ρ |
| `anim-2-4.png` | S15 | fotograma de la animación de 2.4 |
| `F10-mapa-t90.pdf` | extra | mapa de calor 2.4.b (opcional, D22) |
| `muchas_gracias.jpeg` | cierre | imagen de cierre (heredada de TP3) |
