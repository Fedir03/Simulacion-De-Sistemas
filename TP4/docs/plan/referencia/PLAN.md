# Plan pre-código TP4

**Regla del grupo:** no se escribe código del motor hasta cerrar el paso 01 de ../pasos/ (definiciones); las fórmulas ya están verificadas en FORMULAS-VERIFICADAS.md. Cada corrección recibida en TP2/TP3 tiene un check (`CORRECCIONES-CHECKS.md`). Si un check falla, no se entrega.

## 1. Ya resuelto por el enunciado
- Sistema 2 conservativo: solo fuerza normal de contacto (resorte lineal k = 1e4 N/m); sin fricción, sin tangencial, sin disipación.
- Sistema 2: Verlet original, dt fijo; salida cada dt2 = n·dt.
- Sistema 1: Beeman, Verlet original, Velocity Verlet, Euler predictor-corrector; ECM(dt) log-log; **una sola diapositiva**.
- Pared por partícula imagen (recalculada en cada dt); obstáculos fijos; fresca→usada al primer contacto con un obstáculo.
- ZIP < 100 KB, solo el motor final. Nombres: `SdS_TP4_2026Q2G02CS_Presentación.pdf`, `SdS_TP4_2026Q2G02CS_Codigo.zip`. Última diapositiva: declaración de uso de IA. Links de animaciones explícitos (YouTube/Vimeo).
- Δt es parámetro del método, no variable de estudio del sistema (va en su propia sección, 2.1.a).

## 2. Números de diseño (a re-verificar en el repo)
| Dato | Valor | Consecuencia |
|---|---|---|
| Área del círculo (R=0,51 m) | 0,817 m²; φ por partícula 0,001177 | N=100→0,12; 300→0,35; 600→0,71; 700→0,82 |
| Colocación aleatoria secuencial (RSA) | se traba en N≈440–445 (φ≈0,52) | N grande: red hexagonal con sitios sorteados |
| Máximo en red hexagonal | ≈721–725 sin obstáculos; 714–719 con obstáculos en x0=r | barrido de N debe llegar a ~700 (llenar el dominio) |
| Contacto partícula–partícula | ω=√(2k/m)≈894 rad/s; contacto ≈3,5 ms | Verlet inestable para dt > 2,2e-3; práctico dt ≲ 3,5e-4, barrer hasta ~1e-5 |
| Contacto pared | contacto ≈4,97 ms | mismo criterio |
| CIM | M=29 celdas por lado | CIM obligatorio en N grande |
| Superposición máxima | ~1,1 mm (par), ~1,6 mm (pared) a v0=1 | no asumir v ≤ v0 en tests |

## 3. Pasos con compuertas
Ver `../pasos/` (01→12, cada uno con su compuerta de salida) y `../DEFINICIONES.md` para los valores.

## 4. Roadmap
Fechas y tareas por rol en `../pasos/` (el paso actual, en `../ESTADO.md`); valores en `../DEFINICIONES.md`.

## 5. División de tareas (sin nombres todavía)
- A. Motor Sistema 2 (Verlet, primer paso, CIM, pared imagen, obstáculos, fresca/usada, salida en múltiplos de dt2, colocación RSA y hexagonal, semillas).
- B. Sistema 1 (4 integradores, solución analítica, ECM(dt), diapositiva única, tests de orden).
- C. Observables y experimentos (energía, Fu, Nu, t90, t100, f(v) y ajuste MB 2D con método de Teórica 0, runner, densidad, barras de error con bolsa de datos).
- D. Figuras, animación, presentación.
- E. Cumplimiento de formato (transversal): revisa contra `CORRECCIONES-CHECKS.md`, verifica ZIP, nombres, links, declaración de IA.

Reglas: `git pull` antes de empezar; un worktree por paquete; cada persona entiende el algoritmo antes de pedirle código a un agente; todo texto o etiqueta de un agente lo revisa y reescribe una persona.

## 6. Estructura del repo
```
TP4/
  README.md
  pom.xml
  docs/plan/            # plan del grupo (README, ESTADO, DEFINICIONES, pasos/, referencia/)
  docs/formatos.md      # formato de archivos entre paquetes (versionado)
  src/main/java/ar/edu/itba/sds/tp4/
    Main.java
    engine/  models/  io/   # mismos subpaquetes que TP3
    command/                # opcional, si se crea (como en TP1/TP2)
  tools/build_zip.sh        # genera el ZIP de entrega (Linux/Mac/Git Bash)
  tools/build_zip.ps1       # idem para Windows PowerShell
  analysis/  tests/  outputs/  presentacion/
```
Va al ZIP todo lo necesario para que el motor compile y corra: pom.xml, Main, models, io y engine (y command si se crea), código fuente Java de TP4, el README del motor (`TP4/README.md`, D26) y la copia de las clases de TP1 que use (CIM), porque la cátedra no tiene el resto del repo. NO van: tests, scripts de Python, outputs, configs de corridas, presentación, docs, .git, target/.

Los paquetes se hablan solo por archivos de texto (`static.txt`, `dynamic.txt` con id, x, y, vx, vy, estado). Una config por corrida con la semilla adentro.

## 7. Tests antes de experimentar
**Sistema 1:** reproduce la solución analítica; pendientes de ECM(dt) = orden esperado (sacado de Teórica 4); primer paso de Verlet/Beeman correcto; errores claros ante dt ≤ 0 o parámetros faltantes.
**Sistema 2:** CIM = fuerza bruta (aceleraciones idénticas, incluyendo bordes de celda, pared y obstáculo); una partícula sola conserva momento angular y |v|; dos partículas de frente conservan momento y energía; pared imagen (contacto solo si |r| > R−r); fresca→usada irreversible y Nu no decrece; energía total acotada para el dt elegido, también en N máximo; salida solo en múltiplos de dt2, incluye t=0, ningún estado extra; N imposible ⇒ error explícito; misma semilla ⇒ salida byte a byte igual. No testear conservación de momento total (pared/obstáculos).
**Entrega:** comando exacto de la demo de punta a punta; ZIP < 100 KB extraído en carpeta vacía compila y corre; PDF a 150 dpi sin cortes, fuente efectiva 10–11 pt; Windows: `PYTHONUTF8=1`.
- El ZIP se genera con un solo comando: `tools/build_zip.sh` o `tools/build_zip.ps1`. Ambos copian pom.xml, src/main/java y el README del motor (`TP4/README.md`) del módulo TP4 más las clases de TP1 de las que depende (CIM), excluyen outputs, `.git`, `target/` y archivos del SO (.DS_Store, Thumbs.db, __MACOSX), nombran el archivo `SdS_TP4_2026Q2G02CS_Codigo.zip`, fallan con mensaje claro si pesa 100 KB o más y listan el contenido al terminar. Probar los dos en la máquina de entrega y comparar que el contenido sea el mismo.

## 8. Revisión por sección con la skill
Cada vez que una sección de la presentación o del informe queda en borrador (Simulaciones, Sistema 1, 2.1.a, 2.1.b, 2.2, 2.3, 2.4, Conclusiones), el paquete E la pasa por la skill `sims-tp-format` en una pasada aparte, con un agente revisor que no escribió ese texto, en paralelo al resto del trabajo. El revisor devuelve solo una lista de ítems incumplidos contra CORRECCIONES-CHECKS.md; no corrige. La persona del paquete E decide qué se arregla y marca la sección como revisada. Antes de la entrega se corre una pasada final sobre el PDF completo.
