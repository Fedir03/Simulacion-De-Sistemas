#!/usr/bin/env python3
"""Barras agrupadas de ECM1/ECM2; incertidumbre = error estándar entre eventos.

Uso: .venv/bin/python scripts/graph_gen/summary_abe.py
Lee los óptimos ya calculados; no vuelve a ejecutar las simulaciones.
"""
import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
COLORS = {"A": "#0072B2", "B": "#E69F00", "E": "#D55E00"}
CALIBS = ("pob2", "pob4", "ind2", "ind4")
LABELS = ("pob. 2p", "pob. 4p", "ind. 2p", "ind. 4p")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "outputs/ped_abe_20261115_111241/optimos.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "presentacion/figuras/resumen-ABE")
    args = parser.parse_args()
    with args.source.open(encoding="utf-8", newline="") as source:
        records = list(csv.DictReader(source))

    plt.rcParams.update({"font.size": 16, "axes.labelsize": 18, "legend.fontsize": 15,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#777777", "xtick.color": "#555555",
                         "ytick.color": "#555555", "pdf.fonttype": 42})
    fig, axes = plt.subplots(1, 2, figsize=(17, 6.2), layout="constrained")
    comma = FuncFormatter(lambda value, _: f"{value:g}".replace(".", ","))
    for ax, metric, name in zip(axes, ("ecm1", "ecm2"), ("ECM 1", "ECM 2")):
        top = 0
        for index, (layer, color) in enumerate(COLORS.items()):
            means, errors = [], []
            for calibration in CALIBS:
                group = [r for r in records if (r["capa"], r["metrica"], r["calibracion"])
                         == (layer, metric, calibration)]
                if sorted(int(r["evento"]) for r in group) != list(range(1, 20)):
                    raise ValueError(f"Eventos incompletos o duplicados: {layer}/{metric}/{calibration}")
                values = np.array([float(r["ecm"]) for r in group])
                if not np.isfinite(values).all() or np.any(values < 0):
                    raise ValueError("ECM inválidos")
                means.append(values.mean())
                errors.append(values.std(ddof=1) / np.sqrt(len(values)))
            means, errors = np.array(means), np.array(errors)
            positions = np.arange(4) + (index - 1) * .25
            ax.bar(positions, means, width=.235, color=color, label=f"Capa {layer}", zorder=2)
            ax.errorbar(positions, means, yerr=errors, fmt="none", ecolor="#454545",
                        capsize=3, linewidth=1.3, zorder=3)
            top = max(top, float(np.max(means + errors)))
        ax.set(xticks=np.arange(4), xticklabels=LABELS, ylabel=f"⟨{name}⟩ (m²)",
               ylim=(0, top * 1.3))
        ax.yaxis.set_major_formatter(comma)
        ax.grid(axis="y", color="#e6e5e0", linewidth=.8)
        ax.set_axisbelow(True)
    axes[0].legend(loc="upper right", frameon=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf"):
        path = args.output.with_suffix(f".{extension}")
        fig.savefig(path, dpi=180, bbox_inches="tight", pad_inches=.1)
        print(path)
    plt.close(fig)


if __name__ == "__main__":
    main()
