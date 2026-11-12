# Animaciones de la presentación

Copias de los MP4 que usa la presentación, con el nombre de la diapositiva donde van. Se regeneran con `py scripts/animation/presentation_videos.py` (desde TP5/), que también los copia acá.

- **PDF de entrega:** cada animación aparece como fotograma, con el link de YouTube debajo.
- **Exposición en vivo:** el PPTX (`presentacion/generated/SdS_TP5_presentacion_en_vivo.pptx`) trae estos mismos MP4 embebidos, así que no hace falta internet.
- **Si no hay PPTX ni internet:** se muestran estos archivos directamente.

| Archivo | Diapositiva | Macro del .tex | Placeholder actual | URL de YouTube | Duración |
|---|---|---|---|---|---|
| `01_recorte_evento11.mp4` | Datos: recorte al tramo frontal (evento 11) | `\animacionRecorteURL` | `https://youtu.be/PENDIENTE-recorte` | | 17,5 s |
| `02_sin_capa_vs_A_evento16.mp4` | Animaciones (Resultados), izquierda: sin capa y A | `\animacionSinCapaURL` | `https://youtu.be/PENDIENTE-sincapa` | | 7,3 s |
| `03_A_y_B_evento16.mp4` | Animaciones (Resultados), derecha: A y B | `\animacionURL` | `https://youtu.be/PENDIENTE-ab` | | 7,3 s |
| `04_lado_contrario_evento12.mp4` | Anexo: A elige el lado de cruce contrario al real (evento 12) | `\animacionLadoURL` | `https://youtu.be/PENDIENTE-lado` | | 7,2 s |

**Cuando se suban a YouTube:**
1. Completar la columna "URL de YouTube" de esta tabla.
2. Reemplazar cada placeholder en la macro correspondiente de `presentacion/presentacion_tp5.tex`.
3. Reemplazar la misma clave en el diccionario `VIDEOS` de `presentacion/create_google_slides_sources.py`.
4. Recompilar con `bash presentacion/build_presentacion.sh` y volver a armar el PPTX.

**Formato de los videos:** son a 15 cuadros/s, un cuadro de video por cuadro experimental (tiempo real) y sin interpolar.

**Qué muestra cada uno:**
- **Real:** en negro, con círculo gris relleno.
- **Simulados:** con círculo hueco de color: sin capa en púrpura, A en azul y B en naranja.
- **Evento 16:** es el representativo, porque su distancia mínima real y su ECM 1 con A están más cerca de las medianas de los 19 eventos.
- **Recorte, evento 11:** en el 16 el recorte casi no cambia la dirección al objetivo (2,7° → 1,3°). En el 11 pasa de 17,5° a 1,8° (máximo de los dos peatones en el primer segundo; fuente: `outputs/recorte/verificacion/resumen.md`). Trayectoria completa en gris, con su objetivo (cuadrado); tramo recortado en color, con su objetivo (cruz). En cada inicio, una flecha hacia el objetivo con su ángulo respecto del eje x. Durante el video, la flecha sigue a cada peatón y se oculta a menos de 2 m del objetivo, porque ahí gira sola.
