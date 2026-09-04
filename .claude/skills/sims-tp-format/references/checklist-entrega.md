# Checklist de entrega

## Entregables típicos (confirmar contra el enunciado de cada TP puntual, esto es el patrón general)

a) Presentación oral (con duración fija, ej. 13 minutos) siguiendo el formato de "Formato_Presentaciones.pdf" de la cátedra.
b) El documento de la presentación en PDF — **sin animaciones embebidas, solo links explícitos** (ver reglas-figuras.md, sección "Animaciones — entrega vs presentación en vivo").
c) Código fuente en un .zip — **SOLO la versión final del motor de simulación**. Tamaño esperado del orden de los KB, no MB. NO incluir: historial de commits, documentación, scripts de post-procesamiento/graficado/animación, output de simulaciones, ni ningún archivo de trabajo intermedio.
d) Informe con las mismas secciones que la presentación, formato según "Formato_Informes.pdf" de la cátedra.

## Nombres de archivo

Confirmar el patrón exacto en el enunciado de cada TP (suele incluir número de TP, año/cuatrimestre, número de grupo, comisión, y tipo de entregable) — por ejemplo: `SdS_TPn_YYYYQnGXXCSS_Presentación`, `..._Codigo`, `..._Informe`, donde XX es el número de grupo y SS la comisión.

## Antes de armar el ZIP de código

Verificar explícitamente que NO se cuelan:
- Scripts de graficado/animación/post-procesamiento (van en el repo de desarrollo, no en la entrega).
- Datos generados (CSVs, archivos de trayectoria, figuras).
- Archivos de configuración de IDE, documentación de arquitectura, tests de otros TPs del mismo repo si el motor es multi-módulo.
- Historial de git (`.git/`).

## Al recibir un enunciado nuevo (TP3, TP4, etc.)

1. Releer completo el enunciado — no asumir que la estructura es idéntica a un TP anterior, aunque el formato general de entregables suele repetirse.
2. Confirmar fecha y hora exactas de entrega, y si hay clase de pre-entrega o consulta programada — esas clases suelen tener información crítica de formato que no está en ningún PDF (ver ejemplo real en metodologia-estadistica.md, encontrado en una clase así).
3. Revisar si hay carpetas de ex-alumnos (Drive) o links de Notion con material de referencia de cuatrimestres anteriores para ese TP puntual — pueden contener parametrizaciones reales, correcciones específicas, o errores comunes a evitar.
