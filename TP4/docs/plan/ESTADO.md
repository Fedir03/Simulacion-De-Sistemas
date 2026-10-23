# Estado del TP4 (actualizar a diario)

> Solo la persona de rol E edita este archivo (DEFINICIONES.md, D24).

**Última actualización: 22/10/2026**

## Dónde estamos
- **dt = 1e-5 elegido y validado** (D1): ε_E = 1,99e-5 con N=300 y 1,87e-5 con N=714, x₀=r, 30 s (umbral 1e-3).
- **2.1.a hecho** (F2 y F3).
- **2.1.b: benchmark corriendo en la máquina de TP3** (commit cf581d5; `scripts/sim_gen/runtime_tp4.sh`, calentamiento 300:1,600:0.52, `order_seed` 20261025, 10 rondas), con **re-medición de TP3 (tanda limpia, `outputs/runtime_tp3_limpia`) en la misma sesión** (D12: la tanda A se midió con la máquina cargada; queda como referencia histórica).
- **F5–F8 hechas** (2.2 y 2.3).
- **Pendientes de los datos de 2.1.b:** F4 combinada (TP4 contra la tanda limpia de TP3; media ± σ en la figura y mediana en tabla, D7) y 2.4 (F9 y F10).
- Respuestas de la cátedra a las consultas por mail del 22/10 (M1–M6) pasadas a `DEFINICIONES.md` (D7, D12, D17, D18, D20, D29, D31). ZIP: lleva todo el código que genera datos y figuras (D16, D26, D28).
- **Pendientes:** anexo de prompts (D31), auditorías (`auditoria-integradores.md` D29, `auditoria-codigo.md` D30), ZIP (`tools/build_zip`, README del motor).

## Paso actual
Pasos 06 (tiempos, en curso en la máquina de TP3) y 07 (2.2 y 2.3 con figuras hechas; falta 2.4). **Entrega: vie 23/10, 13:00** (subida prevista ~11:00).

## Bitácora
- 14/10: se verificaron fórmulas contra Teórica 4; se resolvió Euler predictor-corrector (diapo 23); se detectó que la fuerza del oscilador depende de la velocidad; se agregó la regla "llenar el dominio lo más posible" (corrección de TP3).
- 16/10: la cátedra respondió las consultas 1, 3, 5–15 (task de Notion "TP4: llevar preguntas a la cátedra"); la 4 (densidad) sigue abierta. Resumen en `pasos/03-clase-presencial-consultas.md`.
- 19/10: decisiones del grupo pasadas a `DEFINICIONES.md`: grilla única para todo N y N máx medido con código (D5, D6, D7); barrido de dt hasta 1e-6 (D2); D15, D16, D17, D19, D21, D25 cerradas; README chico del motor (D26). Revisión parcial del CIM de TP1: hay que desplazar las coordenadas en +R (D25).
- 19/10: pull de 3 commits del 16/10 (214678c módulo Maven, 38e890b Sistema 1, 90ffd06 Teórica 4 nueva). La Teórica 4 nueva es una re-exportación del 2/10: misma cantidad de páginas; cambia el título de la diapo 12 ("Algoritmos Euler" → "Algoritmo de Verlet") y tiene una imagen más, en una página sin identificar. Hay que revisar a ojo las diapos con fórmulas (13–23, 37) contra `referencia/FORMULAS-VERIFICADAS.md`. PROPUESTA restantes adoptadas por defecto. Pasos 05–08 no empezados.
- 19/10: respuestas del grupo: D12 y D23 cerradas (Fede: grilla, CIM, N máx, tiempos 2.1.b + TP3, rol E; Ruckauf: Sistema 2; Lolo: Sistema 1, presentación, figuras, animaciones, rol C). Anuncio de la cátedra "Criterios de Evaluación TP4 y TP5": la oral pesa más, cuenta la participación, auditar integradores y código, anexo de prompts. Se crearon `auditoria-integradores.md`, `auditoria-codigo.md` y `../ia/prompts-motor.md`; se agregaron D29–D32 y las diapositivas S03b y S17b a la plantilla (sin compilar).
- 19/10: cambios de alcance: D12 solo exige TP3 y TP4 en la misma computadora (la de Fede), sin anotar CPU/RAM/SO/Java; consultas del paso 09 y Q4 por mail; prompts del motor marcados "textual" o "reconstruido", sin cargar todos (D31); anexo de prompts como apéndice después de "Muchas gracias" (plantilla ajustada, sin compilar); tiempo por integrador: primera corrida descartada, 5 repeticiones, mediana (paso 05); tarea de ordenar la presentación de lo más importante a lo secundario (paso 08, D32).
- 22/10: dt = 1e-5 verificado (D1). Benchmark de 2.1.b (cf581d5) lanzado en la máquina de TP3; el control de TP3 dio 26,4–27,0 s con la PC libre contra 40,84 s de la tanda A, así que TP3 se re-mide en la misma sesión (tanda limpia, D12). Respuestas de la cátedra a las consultas por mail del 22/10 (M1–M6) en DEFINICIONES. Nueva regla del ZIP: todo el código que genera datos y figuras (D26, D28).
