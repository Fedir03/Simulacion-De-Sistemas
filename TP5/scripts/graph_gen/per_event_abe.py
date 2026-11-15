#!/usr/bin/env python3
"""Compara A, B y E en los 19 eventos, con el mejor par poblacional de cada métrica.

Uso: MPLCONFIGDIR=/tmp/tp5-matplotlib .venv/bin/python scripts/graph_gen/per_event_abe.py
Genera PDF, PNG, datos CSV y parámetros JSON en outputs/per_event_abe, sin modificar la presentación.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

from per_event import best_rows
from pilot_analysis import load_grid

COLORS = {"A": "#0072B2", "B": "#E69F00", "E": "#D55E00"}
METRICS = {"ecm1": (3, "ECM 1 [m²]"), "ecm2": (5, "ECM 2 [m²]")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path, default=Path("outputs/pilot"))
    parser.add_argument("--out", type=Path, default=Path("outputs/per_event_abe"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    grids = {layer: load_grid(args.pilot / f"grid_{layer}.txt") for layer in COLORS}
    events = np.arange(1, 20)
    records = []
    metadata = {"criterio": "Mejor par poblacional por métrica, compartido por ambos peatones y los 19 eventos",
                "velocidad_inicial": "Ajuste lineal de 5 cuadros", "fuentes_sha256": {}, "metricas": {}}
    for layer in COLORS:
        path = args.pilot / f"grid_{layer}.txt"
        metadata["fuentes_sha256"][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    plt.rcParams.update({"font.size": 16, "axes.labelsize": 19, "legend.fontsize": 17, "pdf.fonttype": 42})
    for metric, (column, label) in METRICS.items():
        metadata["metricas"][metric] = {}
        fig, ax = plt.subplots(figsize=(13.5, 5.4), constrained_layout=True)
        highest = 0
        for k, (layer, color) in enumerate(COLORS.items()):
            a, b, rows = best_rows(grids[layer], column)
            values = rows[:, column]
            if not np.array_equal(rows[:, 2], events) or not np.isfinite(values).all() or (values < 0).any():
                raise ValueError(f"Datos inválidos para {layer}/{metric}")
            ax.bar(events + (k - 1) * 0.25, values, width=0.235, color=color, label=f"Capa {layer}", zorder=3)
            highest = max(highest, float(values.max()))
            metadata["metricas"][metric][layer] = {"p1": float(a), "p2": float(b), "error_promedio": float(values.mean())}
            records.extend([metric, int(event), layer, float(a), float(b), float(value)] for event, value in zip(events, values))
        ax.set_xticks(events)
        ax.set_xlim(0.35, 19.65)
        ax.set_ylim(0, highest * 1.20)
        ax.set_xlabel("Evento")
        ax.set_ylabel(label)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}".replace(".", ",")))
        ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(loc="upper center", ncol=3, frameon=False)
        for suffix in ("pdf", "png"):
            file = args.out / f"errores_por_evento_ABE_{metric}.{suffix}"
            fig.savefig(file, bbox_inches="tight", dpi=160)
            print(file)
        plt.close(fig)
    with (args.out / "errores_por_evento.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metrica", "evento", "capa", "p1", "p2", "error_m2"])
        writer.writerows(records)
    (args.out / "parametros.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
