# Lecciones reales de TP3 — Billar/Metegol, dinámica molecular por eventos (entregado 28/09/2026)

Lecciones de proceso previas a la entrega, confirmadas durante la auditoría y en discusión directa con la cátedra. La devolución oficial (nota 6,5, recibida 03/10/2026) está en `correcciones-reales-tp3-nota.md`. Máxima prioridad junto con correcciones-reales-tp2.md.

## 1) El algoritmo se verifica contra la letra EXACTA de la teórica, no solo del enunciado

La lección de TP2 ("verificar el orden contra la letra del enunciado, no contra lo que parece físicamente razonable") se extiende: en TP3 la fuente autoritativa del orden del ciclo del motor (predicción → avance → guardado de estado → resolución → repredicción) fue la **Teórica 3**, no el enunciado del TP. Antes de fijar o validar un algoritmo, identificar CUÁL es la fuente autoritativa (enunciado, teórica específica, o ambas) y compararlo palabra por palabra / paso por paso contra esa fuente — nunca reconstruirlo de memoria ni aprobar un reorden solo porque "tiene sentido físicamente".

Esto aplica también a fórmulas físicas puntuales (ej. impulso en colisión partícula-partícula, con signos de J, Jx, Jy): verificar contra fotos reales de la teórica antes de escribirlas en el informe/presentación, nunca reconstruirlas de memoria — alto riesgo de error de signo.

## 2) Títulos y nomenclatura: el contenido sigue a la fuente, el título sigue a la claridad

Al alinear el contenido de un diagrama/bloque con la nomenclatura literal de la fuente (ej. pasos "A1, A2, A3..." de la teórica), no dejar que esa nomenclatura técnica se filtre automáticamente al TÍTULO del bloque si ya había un título más claro y descriptivo de lo que se muestra. Ejemplo real: el contenido del bloque se reescribió correctamente con los pasos A1-A6 de la teórica, pero el título pasó de "Ciclo del motor" (claro, describe lo que se ve: un loop) a "Algoritmo" (genérico, no aporta nada) — se revirtió solo el título, manteniendo el contenido alineado a la fuente.
**Regla general:** contenido técnico = fidelidad a la fuente citada; títulos/etiquetas visibles = la opción más clara y natural, aunque la fuente use otra palabra.

## 3) σ vs σ/√N — NO es una regla fija, depende del caso (corregido 01/10)

Una versión anterior de esta lección decía "siempre σ, nunca σ/√N" para todo. Es incorrecto — el usuario lo corrigió explícitamente: a veces corresponde el desvío (σ) y otras el error estándar (σ/√N), **depende de la situación puntual** (qué se está reportando y sobre qué fuente de variabilidad), no es un criterio universal para todo el TP. Lo que sigue valiendo de la lección original de TP2 es el punto técnico específico de la "bolsa de datos" (ver `metodologia-estadistica.md`): si se combinan valores instantáneos de varias realizaciones, el desvío se calcula sobre la bolsa completa, no sobre los M promedios ya reducidos por CLT — pero eso no decide por sí solo si el número final a mostrar es σ o σ/√N. **Verificar caso a caso, no copiar un criterio fijo de un TP anterior.**

## 4) Demo en vivo: un fix verificado en el componente no implica que el wrapper lo use

Bug real encontrado en auditoría: un fix (print en vivo de goles/t90) se había propuesto y mostrado en una sesión anterior, pero nunca se había aplicado de verdad al código — no quedó en ningún commit ni stash. Por separado, el script de demo de competencia (`demo_mejor.sh`) corría las N realizaciones en paralelo con la salida de `simulate` redirigida a `/dev/null`, así que aunque el print en vivo hubiera estado implementado, la demo real no lo iba a mostrar.
**Regla reforzada (ya existía, ahora con caso real):** después de aplicar cualquier fix, (a) confirmar con un diff real que quedó aplicado al archivo — no solo que "se mostró" en una sesión — y (b) probar el comando EXACTO que se va a correr el día de la demo, no solo el componente aislado. Se resolvió con un flag `--live` que fuerza ejecución secuencial con salida visible.

## 5) Reproducibilidad del archivo de configuración de entrega

Antes de dar por bueno el `Config.txt` final que se entrega: re-simular esa configuración con la semilla elegida y confirmar que el resultado (ej. t90, cantidad de eventos) coincide EXACTAMENTE — al último dígito — con el dato ya registrado en el barrido (`runs.csv`/`summary.csv`). No alcanza con copiar el archivo y asumir que es el mismo; confirmar también byte a byte contra el archivo de configuración fuente (`cmp`).

## 6) Tamaño de letra efectivo en figuras — fórmula práctica

Para que una figura se lea con un tamaño de letra razonable una vez insertada en una diapositiva (no solo "grande en el PDF del gráfico suelto"), calcular el tamaño efectivo:

```
pt_efectivo = pt_en_script × ancho_mostrado_en_diapo / (figsize_pulgadas × 25.4)
```

Objetivo: 10–11 pt efectivos en la diapositiva. Ejemplo real: columna de 77 mm con figsize ≈ 3.4×2.25 in necesitó fuente de 11–12 pt en el script para llegar a ese rango. Para figuras más grandes en pantalla completa (ej. 117 mm de ancho), el mismo pt efectivo exige subir la fuente del script proporcionalmente. No hay que adivinar a ojo — conviene calcularlo antes de regenerar todas las figuras de una tanda.

## 7) Windows/Git Bash — scripts de demo y animación

Si el equipo tiene compañeros corriendo scripts en Windows (Git Bash), varios problemas recurrentes a anticipar en vez de descubrir el día de la demo:
- `multiprocessing`/`--jobs>1` puede fallar (`cannot find context for 'fork'`) — usar 1 proceso por video en Windows, o detectar el SO (`MINGW*|MSYS*|CYGWIN*`) y ajustar automáticamente.
- Consola cp1252 puede romper con símbolos no ASCII (ej. σ) — forzar `PYTHONUTF8=1`.
- Abrir archivos de video sin asumir que existe una app por default asociada — usar `cmd.exe //c start` en vez de un comando que solo funciona en Mac/Linux.
- Verificar siempre con una corrida real en Windows (no asumir que "corre en Linux, va a correr igual"), sobre todo para el script que se usa el día de la demo en vivo.

## 8) Verificación de build antes de cerrar una tanda de cambios al .tex

Antes de dar una tanda de cambios por terminada: compilar y revisar el log de build por `Overfull \vbox` nuevos (no preexistentes), y renderizar a 150 dpi las diapositivas tocadas para revisión visual real — no asumir que "compiló sin error" es lo mismo que "se ve bien".
