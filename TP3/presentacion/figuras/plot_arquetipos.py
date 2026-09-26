"""Comparación de arquetipos de obstáculos (Comparación de Arquetipos, diapositiva 26).

Datos tomados de la tabla "Configuraciones guardadas" de TP3/GUIA.md (no de una
corrida en vivo): 50 realizaciones por arquetipo, disco central R=0.32 fijo,
variando qué se agrega en los arcos, más 50 realizaciones de la mesa vacía como
referencia (semillas 101-150). Se agrega el cuenco fino R_f=0.34 (sin disco
central, mejor mapa de demo_mejor.sh) con las mismas semillas, en otro color.
Si se vuelve a correr el barrido y los números de GUIA.md cambian, actualizar
las listas de abajo.

Uso:
    python3 plot_arquetipos.py

Regenera figuras/t90-vs-arquetipo.pdf en este mismo directorio.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams.update({"font.size": 14})

COLOR_BARRA = "#3939B5"  # TPBlue, igual que el resto de la deck
COLOR_SIN_DISCO = "#9A9AD8"  # misma familia, más claro: no comparte la base
COLOR_REF = "#4D4D4D"

# Las 4 primeras: disco central R=0.32 fijo, solo cambia qué se agrega en los
# arcos. La última: cuenco fino R_f=0.34 sin disco central.
categorias = ["Disco solo", "+ Embudo", "+ Palos", "+ Cuenco", "Cuenco fino\n(sin disco)"]
medias = [16.4, 17.4, 22.4, 13.5, 13.3]
desvios = [1.9, 1.8, 2.6, 1.5, 1.6]
colores = [COLOR_BARRA] * 4 + [COLOR_SIN_DISCO]

# Mesa vacía, 50 realizaciones (semillas 101-150).
ref_media, ref_desvio = 22.6, 2.6

fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=200)

x = range(len(categorias))
ax.bar(x, medias, yerr=desvios, capsize=5, color=colores,
       edgecolor="black", linewidth=0.6, width=0.6, zorder=3)
ax.axhline(ref_media, color=COLOR_REF, linestyle="--", linewidth=1.3,
           label="Mesa vacía", zorder=2)
ax.axhspan(ref_media - ref_desvio, ref_media + ref_desvio, color=COLOR_REF,
           alpha=0.15, lw=0, zorder=1)

ax.set_xticks(list(x))
ax.set_xticklabels(categorias)
ax.set_ylabel(r"$\langle t_{90} \rangle$ [s]")
ax.set_ylim(0, None)
ax.legend(loc="upper right")
ax.grid(axis="y", alpha=0.3)

fig.tight_layout(pad=0.3)
out_path = Path(__file__).parent / "t90-vs-arquetipo.pdf"
fig.savefig(out_path)
print(f"Guardado: {out_path}")
