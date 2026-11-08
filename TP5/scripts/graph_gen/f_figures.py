#!/usr/bin/env python3
"""Figuras comparativas por evento: trayectorias, distancia entre centros y desvío de e_target, para A, B y F.

Usa los archivos de scripts/sim_gen/figures.sh (motor, con --direction-series). Necesita matplotlib.
Uso: python scripts/graph_gen/f_figures.py [carpeta del piloto] [carpeta de datos]
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from figure_data import R, best_pairs, closest_approach, common_times, deviation_degrees, experimental, marks, read_directions, read_run  # noqa: E402

COLORS = {"exp.": "#0b0b0b", "A": "#2a78d6", "B": "#eb6834", "F": "#1baf7a"}
GRID = "#e6e5e0"
STYLES = ("-", "--")
SETS = {"ecm1": ("ecm1_excl", (5, 12, 17, 8, 11, 13)), "ecm2": ("ecm2", (8, 11))}

plt.rcParams.update({"font.size": 15, "axes.labelsize": 16, "legend.fontsize": 13, "xtick.labelsize": 14, "ytick.labelsize": 14,
                     "axes.edgecolor": "#52514e", "axes.labelcolor": "#0b0b0b", "xtick.color": "#52514e", "ytick.color": "#52514e"})


COMMA = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))


def label(name, pair):
    return f"{name}({pair[0]}; {pair[1]})".replace(".", ",")


def series(folder, layer, pair, event):
    base = folder / f"{layer}_{pair[0]}_{pair[1]}"
    header, run = read_run(base / f"evento_{event:02d}.txt")
    return header, run, read_directions(base / f"direccion_{event:02d}.txt")


def figure(pilot, data_dir, folder, metric, event, out):
    pairs = best_pairs(pilot, metric)
    runs = {name: series(folder, name.lower(), pairs[name], event) for name in "ABF"}
    header = runs["A"][0]
    exp = experimental(data_dir, header)
    fig = plt.figure(figsize=(13, 10), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=(0.8, 1))
    ax_xy, ax_d, ax_dev = fig.add_subplot(grid[0, :]), fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])

    # Trayectorias: experimental y las tres capas, con marcas cada 0,5 s y círculos de radio R en el máximo acercamiento
    t_exp, e1, e2 = common_times(*exp)
    k_exp, d_exp = closest_approach(t_exp, e1, e2)
    for ped, track in enumerate(exp):
        ax_xy.plot(track[:, 1], track[:, 2], STYLES[ped], color=COLORS["exp."], lw=2, label="exp." if ped == 0 else None)
        m = marks(track[:, 0])
        ax_xy.plot(track[m, 1], track[m, 2], "o", color=COLORS["exp."], ms=5)
    for p in (e1[k_exp], e2[k_exp]):
        ax_xy.add_patch(plt.Circle(p, R, fill=False, color=COLORS["exp."], lw=1.5))
    for name, (_, run, _) in runs.items():
        t = run[:, 0]
        p1, p2 = run[:, 1:3], run[:, 5:7]
        for ped, p in enumerate((p1, p2)):
            ax_xy.plot(p[:, 0], p[:, 1], STYLES[ped], color=COLORS[name], lw=2, label=label(name, pairs[name]) if ped == 0 else None)
            m = marks(t[~np.isnan(p[:, 0])])
            ax_xy.plot(p[m, 0], p[m, 1], "o", color=COLORS[name], ms=5)
        k, _ = closest_approach(t, p1, p2)
        for p in (p1[k], p2[k]):
            ax_xy.add_patch(plt.Circle(p, R, fill=False, color=COLORS[name], lw=1.5))
    ys = np.concatenate([e[:, 2] for e in exp] + [r[1][:, [2, 6]].ravel() for r in runs.values()])
    ax_xy.set_ylim(np.nanmin(ys) - 0.4, np.nanmax(ys) + 0.7)
    ax_xy.set_aspect("equal", adjustable="box")
    ax_xy.set_xlabel("x (m)")
    ax_xy.set_ylabel("y (m)")
    ax_xy.grid(color=GRID, lw=0.8)
    ax_xy.legend(loc="best", ncol=4, frameon=False)

    # Distancia entre centros
    ax_d.plot(t_exp, d_exp, color=COLORS["exp."], lw=2, label="exp.")
    for name, (_, run, _) in runs.items():
        ax_d.plot(run[:, 0], np.hypot(run[:, 1] - run[:, 5], run[:, 2] - run[:, 6]), color=COLORS[name], lw=2, label=name)
    ax_d.axhline(2 * R, color="#52514e", ls=":", lw=1.5)
    ax_d.annotate("2R", (0.01, 2 * R), xycoords=("axes fraction", "data"), xytext=(0, 4), textcoords="offset points", color="#52514e")
    ax_d.set_xlabel("t (s)")
    ax_d.set_ylabel("distancia entre centros (m)")
    ax_d.set_ylim(bottom=0)
    ax_d.grid(color=GRID, lw=0.8)
    ax_d.legend(loc="upper center", frameon=False)

    # Desvío de e_target respecto de e_t, positivo hacia la derecha de cada peatón
    for name, (_, _, dirs) in runs.items():
        for ped in (0, 1):
            c = 1 + 5 * ped
            ax_dev.plot(dirs[:, 0], deviation_degrees(dirs[:, c + 1], dirs[:, c + 2], dirs[:, c + 3], dirs[:, c + 4]), STYLES[ped], color=COLORS[name], lw=2,
                        label=f"{name}, peatón {ped + 1}")
    ax_dev.axhline(0, color="#52514e", lw=0.8)
    ax_dev.set_xlabel("t (s)")
    ax_dev.set_ylabel("desvío de e_target (°)")
    ax_dev.grid(color=GRID, lw=0.8)
    ax_dev.legend(loc="best", frameon=False, ncol=2, fontsize=11)
    for ax in (ax_xy, ax_d, ax_dev):
        ax.xaxis.set_major_formatter(COMMA)
        ax.yaxis.set_major_formatter(COMMA)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main():
    pilot = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/pilot")
    data_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "data")
    folder = pilot / "figs" / "datos"
    for tag, (metric, events) in SETS.items():
        for event in events:
            out = pilot / "figs" / f"evento_{event:02d}_{tag}.png"
            figure(pilot, data_dir, folder, metric, event, out)
            print(out)


if __name__ == "__main__":
    main()
