# Pruebas

Esta area contiene pruebas automatizadas. Reproducir bajo `java/` la misma
jerarquia de paquetes que se use en produccion. Los fixtures pequenos pueden
vivir en un futuro `resources/`; los resultados grandes o generados no deben
versionarse.

Priorizar pruebas deterministas, rapidas e independientes del orden de
ejecucion. Toda prueba que use azar debe fijar y mostrar su semilla.

