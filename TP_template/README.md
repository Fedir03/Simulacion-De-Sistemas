# Plantilla de Trabajo Practico

Esta carpeta es el punto de partida para un nuevo trabajo practico de
Simulacion de Sistemas. Separa el enunciado, el codigo de simulacion, los
scripts de analisis y los dos entregables: informe y presentacion.

## Flujo de trabajo recomendado

1. Copiar `TP_template/` con el nombre del nuevo trabajo, por ejemplo `TP3/`.
2. Guardar el enunciado original en `enunciado/` y registrar requisitos y
   decisiones antes de programar.
3. Configurar `pom.xml`, crear el paquete Java dentro de `src/main/java/` y
   escribir en paralelo sus pruebas en `src/test/java/`.
4. Colocar en `scripts/` solamente automatizaciones reproducibles para correr
   experimentos, procesar resultados o generar figuras.
5. Generar una sola vez cada figura y reutilizarla desde `informe/figuras/` y
   `presentacion/figuras/`, evitando versiones divergentes.
6. Completar y compilar primero el informe; luego sintetizar sus resultados en
   la presentacion.

## Estructura

| Ruta | Uso |
|---|---|
| `enunciado/` | Consigna original y aclaraciones de la catedra. |
| `src/main/java/` | Implementacion Java del simulador. |
| `src/test/java/` | Pruebas automatizadas con la misma jerarquia de paquetes. |
| `scripts/` | Experimentos, analisis y visualizaciones reproducibles. |
| `informe/` | Fuente LaTeX del informe y figuras publicables. |
| `presentacion/` | Fuente Beamer, figuras y salidas de la exposicion. |

Cada area incluye un `README.md` con sus reglas particulares. Los directorios
`target/`, `generated/`, caches, corridas crudas y auxiliares de LaTeX son
salidas regenerables: no deben versionarse.

## Puesta en marcha

- Reemplazar `tp-template`, `ar.edu.itba.sds.template` y los campos marcados
  `COMPLETAR` por los valores del nuevo TP.
- Declarar dependencias Java en `pom.xml` y dependencias Python en
  `requirements.txt`.
- Ejecutar `mvn test` desde esta carpeta.
- Compilar los entregables con los scripts incluidos en `informe/` y
  `presentacion/`.
- Documentar comandos, semillas, parametros y versiones necesarias para
  reproducir cada resultado.

