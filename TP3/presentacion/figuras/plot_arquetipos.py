"""Comparación de arquetipos de obstáculos (Comparación de Arquetipos, diapositiva 27).

Datos leídos de los summary.csv de los barridos arq_* (TP3/generated/sweeps/):
50 realizaciones por arquetipo, disco central R=0.32 fijo,
variando qué se agrega en los arcos, más 50 realizaciones de la mesa vacía como
referencia (semillas 101-150). Se agrega el cuenco R_f=0.34 (sin disco central,
el mapa elegido, el de demo_mejor.sh) con las mismas semillas, en otro color.
El disco central + cuenco R_f=0.30 (13.5 ± 1.5 s) no se muestra: la presentación
usa un solo cuenco, el de mejor <t90>.
Barras: desvío estándar muestral de los t90 de las realizaciones que alcanzaron el 90 %.

Uso:
    python3 plot_arquetipos.py

Regenera figuras/t90-vs-arquetipo.pdf en este mismo directorio.
"""

import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams.update({"font.size": 14})
SWEEPS = Path(__file__).resolve().parents[2] / "generated" / "sweeps"

COLOR_BARRA = "#3939B5"  # TPBlue, igual que el resto de la deck
COLOR_SIN_DISCO = "#9A9AD8"  # misma familia, más claro: no comparte la base
COLOR_REF = "#4D4D4D"

# Las 3 primeras: disco central R=0.32 fijo, solo cambia qué se agrega en los
# arcos. La última: cuenco R_f=0.34 sin disco central.
categorias = ["Disco solo", "Embudo", "Palos", "Cuenco"]
barridos = ["arq_central_R0.32", "arq_central_embudo_a0.05", "arq_central_palos_Rp0.02", "arq_cuenco_fino_R0.34"]
colores = [COLOR_BARRA] * 3 + [COLOR_SIN_DISCO]


def media_desvio(barrido):
    with open(SWEEPS / barrido / "summary.csv", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    return float(row["t90_mean"]), float(row["t90_std"])


medias, desvios = zip(*map(media_desvio, barridos))
# Mesa vacía, 50 realizaciones (semillas 101-150).
ref_media, ref_desvio = media_desvio("arq_vacia")

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
# Margen arriba de la banda de la mesa vacía para que la leyenda no la tape.
ax.set_ylim(0, 1.25 * ref_media)
ax.legend(loc="upper right")
ax.grid(axis="y", alpha=0.3)

fig.tight_layout(pad=0.3)
out_path = Path(__file__).parent / "t90-vs-arquetipo.pdf"
fig.savefig(out_path)
print(f"Guardado: {out_path}")
