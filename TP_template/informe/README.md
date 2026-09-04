# Informe

Esta carpeta contiene la fuente del informe final. Partir de
`informe_template.tex`, reemplazar todos los campos `COMPLETAR` y renombrar el
archivo si se desea. Las figuras definitivas pertenecen a `figuras/`.

## Contenido recomendado

1. Resumen: problema, metodo y resultado principal.
2. Introduccion y modelo: contexto, hipotesis y ecuaciones.
3. Implementacion: decisiones relevantes sin narrar el codigo clase por clase.
4. Simulaciones: parametros, semillas, cantidad de corridas y criterio de
   estacionariedad.
5. Resultados: evidencia cuantitativa antes de la interpretacion.
6. Conclusiones: respuesta directa a los objetivos y limitaciones.

Cada figura debe tener ejes, unidades, leyenda y caption autocontenido. Citarla
desde el texto y conservar el comando o script que la genera. No editar
manualmente resultados para que se vean mejor.

## Compilacion

- Linux/macOS: `./build_informe.sh`
- Windows PowerShell: `./build_informe_windows.ps1`

El PDF se genera en `generated/`, que no se versiona.

