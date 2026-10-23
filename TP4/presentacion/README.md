# Presentación

Esta carpeta contiene la presentación Beamer de TP4 (Dinámica Molecular Regida
por el Paso Temporal), con la misma plantilla que TP3 y TP2 (D27 en
`../docs/plan/DEFINICIONES.md`).

- `template_presentacion_tp4.tex`: el documento real, una diapositiva por fila
  S01–S17 de `DEFINICIONES.md` §3. Los títulos son provisorios y los recuadros
  grises "Sxx — ..." marcan qué va en cada una; el texto lo escribe una persona
  a partir de la figura.
- `presentacion_imagen.tex`: wrapper de entrega — mismo contenido, versión
  donde el fotograma de cada animación NO es un enlace clickeable (la URL de
  YouTube igual queda visible como texto debajo). Es el archivo que compila
  el `build_presentacion*`.

El logo institucional (`logo_itba.png`) se comparte con TP2 y TP3.

La presentación son 13 minutos: una idea por diapositiva, texto breve,
tipografía legible a distancia. Toda conclusión debe estar respaldada por una
figura ya mostrada. Cada símbolo nuevo se define una vez, en texto y con una
marca visual (`DEFINICIONES.md` §5).

## Compilación

- Linux/macOS: `./build_presentacion.sh`
- Windows PowerShell: `./build_presentacion_windows.ps1`

Requiere `latexmk`. El PDF se genera en `generated/`, que no se versiona.

Si se agregan o quitan diapositivas, renumerar a mano los rangos de
`\TPnavrow` (barra de secciones) en el `.tex`.

Después del resultado del Sistema 1 se muestran dos animaciones del Sistema 2:
sin obstáculos y con obstáculos en ±0.25 m. N=100 y Δt=1e-5 s se indican
en un recuadro al costado del fotograma; el video muestra el tiempo y
`Usadas: Nu/100`. Los fotogramas son de t=5 s,
extraídos de los MP4 de `TP4/generated/animaciones/`. Los enlaces bajo estas
imágenes muestran y abren los videos de YouTube: sin obstáculos,
https://youtu.be/82lP3rStJBo; con obstáculos, https://youtu.be/uctSdF2HWXg.
Las URL se definen en `\animacionSinObstaculosURL` y `\animacionConObstaculosURL`.

## Versión para Google Slides

Después de compilar el PDF, ejecutar `python3 create_google_slides_sources.py`
desde esta carpeta. Requiere LibreOffice, el módulo Python `uno` y las herramientas
`pdftoppm` y `pdftotext` (Poppler). Genera
`generated/google-slides/TP4_Dinamica_Molecular_imagenes.pptx`, una imagen por
diapositiva; las que tienen URL de YouTube abren el video al hacer clic.

## Figuras

Ver `figuras/README.md`.
