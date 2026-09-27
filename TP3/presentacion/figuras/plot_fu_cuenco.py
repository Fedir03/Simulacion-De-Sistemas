"""F_u(t) de una realización de la configuración elegida (Cuenco --- Fracción de
Partículas Usadas, diapositiva 26).

Cuenco fino R_f = 0.34 (configs/cuenco_fino_R0.34.txt), semilla 140: la
realización con t90 más cercano a la media y la mediana del barrido
cuenco_fino_radio (t90 = 13.36 s frente a <t90> = 13.31 s). Se lee el registro
de eventos completo; F_u sube un escalón 1/N en cada choque con gol = 1.

Uso, desde la raíz del repositorio:
    java -jar TP3/target/tp3.jar generate --seed 140 --obstacles TP3/configs/cuenco_fino_R0.34.txt \\
        --out TP3/generated/elegida_s140/ic.txt
    java -jar TP3/target/tp3.jar simulate --input TP3/generated/elegida_s140/ic.txt --time 100 \\
        --every 1000000000 --out TP3/generated/elegida_s140/full.txt
    python3 TP3/presentacion/figuras/plot_fu_cuenco.py

Regenera figuras/fu-temporal-cuenco.pdf en este mismo directorio.
"""

import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams.update({"font.size": 14})

COLOR_CURVA = "#3939B5"  # TPBlue, igual que el resto de la deck
COLOR_REF = "#4D4D4D"
N = 100

here = Path(__file__).parent
events = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    here.parents[1] / "generated" / "elegida_s140" / "full_events.txt"

tiempos = [0.0]
with open(events, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#"):
            continue
        cols = line.split()
        if cols[5] == "1":
            tiempos.append(float(cols[0]))
fu = [k / N for k in range(len(tiempos))]
t90 = tiempos[next(k for k, v in enumerate(fu) if v >= 0.9)]

fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=200)
ax.step(tiempos, fu, where="post", color=COLOR_CURVA, linewidth=1.8, zorder=3)
ax.axhline(0.9, color=COLOR_REF, linestyle="--", linewidth=1.2, zorder=2)
ax.axvline(t90, color=COLOR_REF, linestyle=":", linewidth=1.2, zorder=2)
ax.annotate(rf"$t_{{90}} = {t90:.2f}$ s", xy=(t90, 0.9), xytext=(t90 + 2, 0.55),
            arrowprops=dict(arrowstyle="->", color=COLOR_REF))

ax.set_xlabel(r"$t$ [s]")
ax.set_ylabel(r"$F_u$")
ax.set_xlim(0, tiempos[-1] * 1.05)
ax.set_ylim(0, 1.02)
ax.grid(alpha=0.3)

fig.tight_layout(pad=0.3)
out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else here / "fu-temporal-cuenco.pdf"
fig.savefig(out_path)
print(f"t90 = {t90}, goles = {len(tiempos) - 1}. Guardado: {out_path}")
