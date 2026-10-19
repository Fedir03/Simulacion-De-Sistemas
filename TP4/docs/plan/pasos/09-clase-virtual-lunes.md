# Paso 09 — Consultas a la cátedra por mail

**Cuándo:** la clase virtual del lun 19/10 ya pasó. Las consultas se hacen **por mail** a la cátedra; pendiente, antes del vie 23.
**Antes:** paso `08` · **Después:** paso `10`
**Todos los valores (dt, N, realizaciones, figuras, diapositivas):** `../DEFINICIONES.md`

## Estado al entrar
Sin PDF v1 (paso 08 no empezado). Sistema 1 en el repo (38e890b).

## Objetivo
Tener respuesta escrita de la cátedra a las consultas de abajo antes de presentar. **La participación en las clases de TP se evalúa** (anuncio "Criterios de Evaluación TP4 y TP5"): aplica a las próximas clases de TP.

## Tareas (en paralelo)
| Rol | Tarea | Entrega | Está hecho si |
|---|---|---|---|
| E · Fede | Redactar y mandar el mail a la cátedra con las consultas (a)–(e) | Mail enviado | Fecha de envío anotada abajo |
| Lolo | Adjuntar al mail la figura del ECM vs dt del Sistema 1, si ya corre (consulta e) | Figura adjunta | Adjunta, o anotado "no corría" |
| E · Fede | Registrar cada respuesta con su fecha y pasarla a: hay que corregir / lo hacemos distinto / queda igual, con motivo | `../referencia/DECISIONES.md` + RECORDAR | Cada respuesta tiene destino |

## Consultas (por mail)
- [ ] (a) Anexo de prompts (D31): ¿va dentro del PDF o aparte?
- [ ] (b) Validar la lista de adaptaciones de los integradores (`../auditoria-integradores.md`, D29). Anotar la respuesta y su fecha en la columna "Consultado con la cátedra".
- [ ] (c) Q4: densidad como N/área (ρ = N/(πR²)) o fracción de empaquetamiento φ (D20).
- [ ] (d) Como la fuerza del oscilador es lineal en v, ¿prefieren que en Verlet y Velocity Verlet resolvamos la ecuación exacta en lugar de estimar v (D17)?
  - Velocity Verlet: v(t+Δt) = [v(t) + (Δt/(2m))(f(t) − k·r(t+Δt))] / (1 + γΔt/(2m))
  - Verlet con la v central: r(t+Δt)(1 + γΔt/(2m)) = 2r(t) − r(t−Δt)(1 − γΔt/(2m)) − (kΔt²/m)r(t)
- [ ] (e) Figura del ECM vs dt del Sistema 1 adjunta, si ya corre.

Mail enviado: ____ · Respuesta recibida: ____

## Compuerta de salida
- [ ] Consultas (a)–(e) con respuesta o "sin respuesta" (con fecha)
- [ ] Respuestas clasificadas
- [ ] Lista de cambios con dueño (nombres de D23)

## Si se traba
Si la cátedra no responde antes del jueves, se sigue con la decisión propia de cada D y se aclara en la presentación.
