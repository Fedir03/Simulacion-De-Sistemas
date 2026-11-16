# Animaciones de la presentación

Las cuatro animaciones vigentes se regeneran desde TP5/ con:

```bash
mvn package
MPLCONFIGDIR=/tmp/tp5-matplotlib .venv/bin/python scripts/animation/presentation_videos.py
```

El script vuelve a simular con los pares seleccionados en las tablas poblacionales, verifica los ECM contra las grillas y actualiza los MP4 de esta carpeta y sus fotogramas en `presentacion/figuras/`. Lee `outputs/calibracion_poblacional/resumen.json` y aplica el mismo criterio de selección de las filas amarillas: menor sacrificio relativo máximo entre las dos métricas; empate a favor de ECM1.

| Archivo | Evento | Comparación | Duración |
|---|---:|---|---:|
| `01_recorte_evento09.mp4` | 9 | Trayectoria experimental completa y recortada | 10,2 s |
| `02_sin_capa_vs_A_evento16.mp4` | 16 | Real, sin capa y A(2,18; 0,44) | 7,3 s |
| `03_A_y_B_evento16.mp4` | 16 | Real, A(2,18; 0,44) y B(3,2; 0,92) | 7,3 s |
| `05_E_evento16.mp4` | 16 | Real y E(3,4; 0,25) | 7,3 s |

Todos usan SFM, Beeman, paso experimental /64 y velocidad inicial ajustada con cinco cuadros. Los videos se reproducen a 15 cuadros/s, con un cuadro por cuadro experimental y sin interpolar. Real en negro con círculos grises rellenos; simulaciones con círculos huecos de color. El recorte usa la trayectoria completa en gris y los tramos recortados en color, con flechas hacia sus objetivos.

Los MP4 originales, corridas nuevas y metadatos están en `outputs/pilot/animaciones_presentacion/`; los parámetros y hashes de entrada quedan en `parametros_animaciones.json`. La versión PDF se recompila con `bash presentacion/build_presentacion.sh`. El exportador `presentacion/create_google_slides_sources.py` asocia estos archivos a las URL de las diapositivas para insertar los videos en el PPTX.

Se pueden regenerar animaciones por separado pasando las claves `recorte`, `sincapa`, `ab` o `e`. La clave opcional `lado` genera el evento 12.
