# Scripts de experimentacion y analisis

Guardar aqui scripts reproducibles para lanzar barridos, leer salidas,
calcular observables, producir tablas y generar figuras. El codigo del motor
de simulacion pertenece a `src/`, no a esta carpeta.

Practicas esperadas:

- Recibir rutas, parametros y semillas por argumentos de linea de comandos.
- Incluir ayuda (`--help`) y fallar claramente ante datos invalidos.
- Separar lectura, calculo y visualizacion para facilitar pruebas.
- Escribir resultados regenerables fuera del codigo fuente, normalmente en
  un directorio `generated/` ignorado por Git.
- Registrar metadatos suficientes para repetir cada experimento.
- Agregar pruebas pequenas para parsers y calculos cientificos sensibles.

