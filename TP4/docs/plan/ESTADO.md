# Estado del TP4 (actualizar a diario)

> Solo la persona de rol E edita este archivo (DEFINICIONES.md, D24).

**Última actualización: 19/10/2026**

## Dónde estamos
- Enunciado leído y resumido. Fórmulas de Teórica 4 verificadas por el grupo contra el PDF nuevo (19/10; diapos 9–23, 31–37, 42–46) y de Teórica 0 (diapos 60–72). Pendiente: auditar el código contra ellas (D29, `auditoria-integradores.md`).
- Consultas a la cátedra respondidas (16/10) salvo la Q4 (densidad). Decisiones del grupo del 19/10 en `DEFINICIONES.md`; las PROPUESTA restantes se adoptaron por defecto, menos D1, D6, D7 y D20, que esperan medición o respuesta. D12 (máquina: la de Fede) y D23 (roles y pares de auditoría) DECIDIDO 19/10. Nuevas D29–D32 (auditoría de integradores, auditoría cruzada, anexo de prompts, preparación de la oral) en PROPUESTA.
- En el repo: módulo Maven `TP4` (214678c) y Sistema 1 completo, con 4 esquemas, ECM(dt) y tests (38e890b). Los tests no se corrieron en esta revisión (sin verificar).
- No hay todavía: Sistema 2, CIM copiado, colocación por grilla, medición del N máx, `docs/formatos.md`, runner, `analysis/`, F1, README del motor, script del ZIP.
- Sin verificar (no está en los commits): plantilla de presentación de TP4 compilada sin Overfull vbox, figuras E1–E3, hoja de consultas.
- La clase virtual del lun 19/10 ya pasó: las consultas (a)–(e) del paso 09 y la Q4 van **por mail** a la cátedra (pendiente, antes del vie 23).

## Paso actual
Estamos en el paso 04 (`pasos/04-motores-con-tests.md`), con pendientes del paso 02 (`formatos.md`, E1–E3). Sistema 1 hecho; falta el Sistema 2 y sus tests, la simulación completa CIM vs fuerza bruta, la medición del N máx y el generador de TP3 con grilla.

## Bitácora
- 14/10: se verificaron fórmulas contra Teórica 4; se resolvió Euler predictor-corrector (diapo 23); se detectó que la fuerza del oscilador depende de la velocidad; se agregó la regla "llenar el dominio lo más posible" (corrección de TP3).
- 16/10: la cátedra respondió las consultas 1, 3, 5–15 (task de Notion "TP4: llevar preguntas a la cátedra"); la 4 (densidad) sigue abierta. Resumen en `pasos/03-clase-presencial-consultas.md`.
- 19/10: decisiones del grupo pasadas a `DEFINICIONES.md`: grilla única para todo N y N máx medido con código (D5, D6, D7); barrido de dt hasta 1e-6 (D2); D15, D16, D17, D19, D21, D25 cerradas; README chico del motor (D26). Revisión parcial del CIM de TP1: hay que desplazar las coordenadas en +R (D25).
- 19/10: pull de 3 commits del 16/10 (214678c módulo Maven, 38e890b Sistema 1, 90ffd06 Teórica 4 nueva). La Teórica 4 nueva es una re-exportación del 2/10: misma cantidad de páginas; cambia el título de la diapo 12 ("Algoritmos Euler" → "Algoritmo de Verlet") y tiene una imagen más, en una página sin identificar. Hay que revisar a ojo las diapos con fórmulas (13–23, 37) contra `referencia/FORMULAS-VERIFICADAS.md`. PROPUESTA restantes adoptadas por defecto. Pasos 05–08 no empezados.
- 19/10: respuestas del grupo: D12 y D23 cerradas (Fede: grilla, CIM, N máx, tiempos 2.1.b + TP3, rol E; Ruckauf: Sistema 2; Lolo: Sistema 1, presentación, figuras, animaciones, rol C). Anuncio de la cátedra "Criterios de Evaluación TP4 y TP5": la oral pesa más, cuenta la participación, auditar integradores y código, anexo de prompts. Se crearon `auditoria-integradores.md`, `auditoria-codigo.md` y `../ia/prompts-motor.md`; se agregaron D29–D32 y las diapositivas S03b y S17b a la plantilla (sin compilar).
- 19/10: cambios de alcance: D12 solo exige TP3 y TP4 en la misma computadora (la de Fede), sin anotar CPU/RAM/SO/Java; consultas del paso 09 y Q4 por mail; prompts del motor marcados "textual" o "reconstruido", sin cargar todos (D31); anexo de prompts como apéndice después de "Muchas gracias" (plantilla ajustada, sin compilar); tiempo por integrador: primera corrida descartada, 5 repeticiones, mediana (paso 05); tarea de ordenar la presentación de lo más importante a lo secundario (paso 08, D32).
