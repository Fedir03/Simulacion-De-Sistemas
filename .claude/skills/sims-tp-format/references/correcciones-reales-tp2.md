# Correcciones reales recibidas — TP2 propio (nota 5.5+1=6.5, 16/09)

A diferencia de correcciones-nash.md (otro grupo), esto es feedback directo sobre nuestro propio TP2 entregado. Máxima prioridad — es la fuente más confiable de qué evalúa esta cátedra en concreto.

## Hallazgo más grave — el orden del algoritmo se verifica contra la LETRA del enunciado, nunca contra "lo que parece físicamente razonable"

Corrección real de código: *"El orden del paso temporal no parece el adecuado... El enunciado define θ(t+dt) a partir del vecindario en r(t)"*. El código calculaba el vecindario sobre posiciones YA actualizadas, no las viejas — una decisión que se había tomado porque "tenía sentido", sin releer la frase exacta del enunciado.

**Regla:** cuando un algoritmo tiene un orden de pasos específico, releer la oración exacta del enunciado que lo define, palabra por palabra, antes de fijar el orden en el código. No alcanza con que el orden sea físicamente coherente — tiene que coincidir con lo que el enunciado dice literalmente.

## Texto que "suena generado por IA" — señalado activamente, no una preocupación teórica

Corrección real sobre una etiqueta de eje: *"la etiqueta del eje x tiene muchísima información... Suena a eje nombrado por la IA, mejor Uds. tomen decisiones humanas al respecto."*

**Regla:** cualquier texto/label/nombre que un agente de código proponga necesita revisión humana real antes de aceptarlo — no pegar la primera propuesta. Ver uso-de-agentes-ia.md para la pauta completa de la cátedra sobre esto.

## Correcciones de figuras y estructura (aplicables a cualquier TP)

- Definir explícitamente TODOS los observables usados, sin dejar ninguno sin definición formal (se marcó que faltaba definir el observable de clusters).
- Terminar el recorrido completo de un modelo/estudio antes de pasar al siguiente — no intercalar resultados de estudios distintos.
- Con varias configuraciones/densidades a mostrar, elegir 1-2 representativas para animación/evolución temporal — no todas.
- Elegir UNA sola representación de barras de error por figura (un eje, no ambos) salvo que ambos observables lo requieran genuinamente.
- Títulos de subsección/diapositiva específicos y descriptivos del contenido real — nunca genéricos ("Relación entre Parámetro y Observable" suena a resultado, no dice nada).
- En el informe: nunca figuras sueltas — cada una referenciada explícitamente en el texto (\ref{}), con análisis real, no solo el gráfico.
- Los tiempos de ejecución (si el TP los pide como resultado) van en Resultados/Conclusiones, NUNCA en Simulaciones ni Parámetros — son un resultado medido, no un parámetro de entrada.
- Diagramas de arquitectura (UML u otro) deben detallar el INTERIOR del motor de simulación específicamente — no un pipeline genérico de todo el proyecto (scripts de post-proceso, graficado, etc. no van ahí).
