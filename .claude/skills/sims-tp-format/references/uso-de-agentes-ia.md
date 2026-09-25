# Uso de Coding Agents — pauta oficial de la cátedra

Documento de la cátedra "TIPS PARA EL USO DE CODING AGENTS", publicado en la carpeta general de Drive de la materia. Aplica a todos los TPs.

1. **Mantener el control del código** — nunca incorporar código generado sin entenderlo y revisarlo.
2. **Delegar la complejidad que ya dominan** — pedirle al agente que implemente cosas que el equipo ya sabe resolver, no cosas nuevas para ellos. La delegación es de trabajo, no de conocimiento.
3. **No extralimitarse** — usar solo ideas/código que el equipo sea capaz de comprender y procesar por sí mismo.
4. **Pedir explicaciones, no ocultar complejidad** — que el agente justifique sus decisiones paso a paso.
5. **Pair programming** — trabajar de a dos para revisar y evaluar el código generado juntos.
6. **Exigir explicabilidad** — conectar cada implementación con la teoría/algoritmos de la materia: qué algoritmo usa, por qué es apropiado, qué complejidad tiene.
7. **Explicaciones cambio por cambio**, no solo el resultado final.
8. **Incluir unit tests** siempre que se pida código — pensar los casos a testear ayuda a entender el comportamiento esperado.
9. **Atención a los "unhappy paths"** — casos límite, entradas inesperadas, errores — identificados por el propio equipo antes de consultar al agente, no delegados por completo.
10. **Usar snippets propios como punto de partida** — para mantener el estilo/convenciones del resto del proyecto.

## Buenas prácticas ya aplicadas con éxito (TP2/TP3)

- **Verificar límites/derivaciones contra una implementación ya funcionando**, no solo contra el álgebra en abstracto. Ejemplo real: antes de aceptar que la fórmula general de colisión (masas i,j) se reducía correctamente al caso de obstáculo fijo, se derivó el límite m_j→∞ a mano y se comparó explícitamente contra la fórmula ya implementada y funcionando en el motor (v' = v - 2(v·n̂)n̂) — confirmando que son la misma física, no dos versiones que por casualidad coinciden.
- **No aceptar una fórmula de una fuente de origen incierto** (ej. un archivo intermedio tipo notas propias) sin verificarla contra la fuente autoritativa real (la teórica correspondiente) — pedir la diapositiva/imagen real en vez de asumir que el archivo intermedio ya la transcribió bien.
- **Pedir el diagnóstico completo antes de aplicar cualquier cambio** cuando hay ambigüedad real (ej. "mostrame primero de dónde salió cada dato, decidimos juntos después") — evita aplicar un fix basado en una interpretación equivocada.
