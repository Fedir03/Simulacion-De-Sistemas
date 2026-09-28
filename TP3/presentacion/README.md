# Presentación

Esta carpeta contiene la presentación Beamer de TP3 (Billar-Metegol), con el
mismo estilo visual (colores, comandos, barra de navegación) que
`TP2/presentacion/template_presentacion_tp2.tex`.

- `template_presentacion_tp3.tex`: el documento real, con las diapositivas
  numeradas y los `\maybeimage`/`\parambox` con placeholders hasta que existan
  las figuras finales. Estructura y correcciones aplicadas documentadas en
  `TP3/README.md` y en el plan de sesión que generó este esqueleto.
- `presentacion_imagen.tex`: wrapper de entrega — mismo contenido, versión
  donde el fotograma de cada animación NO es un enlace clickeable (la URL de
  YouTube igual queda visible como texto debajo). Es el archivo que compila
  el `build_presentacion*`.

El logo institucional (`logo_itba.png`) se comparte con TP2.

La presentación son 13 minutos: una idea por diapositiva, texto breve,
tipografía legible a distancia. Toda conclusión debe estar respaldada por una
figura, tabla o medición ya mostrada. Ensayar con el PDF final y comprobar
enlaces, animaciones y tiempo antes de la entrega del 28/09/2026.

## Compilación

- Linux/macOS: `./build_presentacion.sh`
- Windows PowerShell: `./build_presentacion_windows.ps1`

El PDF se genera en `generated/`, que no se versiona.

## Versión para Google Slides

Después de compilar el PDF, ejecutar `python3 create_google_slides_sources.py`
desde esta carpeta. Requiere LibreOffice, el módulo Python `uno` y las herramientas
`pdftoppm` y `pdftotext` (Poppler).

Genera `generated/google-slides/TP3_Billar_Metegol_imagenes.pptx`, listo para
importar en Google Slides. Cada diapositiva es una imagen de 2400 × 1800 píxeles,
con el diseño original y sin texto editable. Las diapositivas que contienen URLs
de YouTube abren el video al hacer clic en la imagen. Los enlaces se extraen del
PDF, por lo que siguen las URLs y el orden de la presentación actual.

## Figuras

Ver `figuras/README.md` para la lista de archivos que espera el `.tex` y las
reglas de formato (tamaño de fuente legible, labels cortos, sin título
embebido).
