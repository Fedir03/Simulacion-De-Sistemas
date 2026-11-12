# ESTADO — TP5 Dinámica Peatonal

Última actualización: 12/11/2026 (bitácora; el resto del archivo es del 3/11). Solo lo edita el rol E (Presentación y visual) para no pisar versiones.
Entrega: lun 16/11. Objetivo: cerrar el lun 9/11.

## Dónde estamos
- Decididas: D1 (SFM sin fuerza social), D6, D8, D9, D10. Defaults en D3, D4, D5, D7.
- Pendiente: D2 (elige el piloto del mié 4/11), D11 (integrador y prueba de Δt).

## Paso actual
Repo armado y roles asignados.

## Plan
- [ ] Mar 3/11: parser de eventos, SFM sin capa, línea base de ECM 1 y 2
- [ ] Mié 4/11: capas A, B y F como módulo intercambiable; prueba piloto; elegir una
- [ ] Jue 5/11: calibración (b), (c) y (d)
- [ ] Vie 6/11: consultas a la cátedra; presentación completa
- [ ] Sáb 7/11 a lun 9/11: ZIP en carpeta limpia, uso de IA, ensayo cronometrado
- [ ] 10 a 16/11: margen

## Bitácora
- 2/11: se eligió SFM; finalistas F, B y A; D3 a D11 definidos en DEFINICIONES.md.
- 12/11: motor y análisis separados para que el ZIP tenga solo el motor (DEFINICIONES.md, sección 6). ECM, contactos, distancia mínima, longitud recorrida, conmutaciones de la capa, grilla, recorte exportado y series de direcciones pasan a `analysis/` (`AnalysisMain`), fuera del ZIP; los scripts de `scripts/` usan `AnalysisMain` para `grid`, `baseline` y `trim-export`. Verificado: 101 tests, 258 archivos de `outputs/` idénticos byte a byte, ZIP de 35 KB y 32 entradas que compila aislado y reproduce `evento_03.txt`.
