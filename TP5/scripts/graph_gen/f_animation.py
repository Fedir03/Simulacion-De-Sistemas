#!/usr/bin/env python3
"""Animación de un evento con cuatro paneles (experimental, A, B y F con sus mejores pares de ECM 1 excl.).

Lee los archivos de salida del motor (scripts/sim_gen/figures.sh); la animación corre aparte de la simulación.
Un cuadro por Δt_exp, en tiempo real. Necesita matplotlib (y Pillow para el GIF).
Uso: python scripts/graph_gen/f_animation.py [evento] [carpeta del piloto] [carpeta de datos]
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402

from figure_data import R, best_pairs, experimental, read_run  # noqa: E402

COLORS = {"exp.": "#0b0b0b", "A": "#2a78d6", "B": "#eb6834", "F": "#1baf7a"}
PED_FILL = ("#cde2fb", "#fbe1d5")


def position(track, t):
    """Posición del peatón experimental en t, o None si no hay frame (hueco o fuera de la ventana)."""
    k = int(np.argmin(np.abs(track[:, 0] - t)))
    return track[k, 1:] if abs(track[k, 0] - t) < 1e-6 else None


def main():
    event = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    pilot = Path(sys.argv[2] if len(sys.argv) > 2 else "outputs/pilot")
    data_dir = Path(sys.argv[3] if len(sys.argv) > 3 else "data")
    pairs = best_pairs(pilot, "ecm1_excl")
    runs = {}
    for name in "ABF":
        header, run = read_run(pilot / "figs" / "datos" / f"{name.lower()}_{pairs[name][0]}_{pairs[name][1]}" / f"evento_{event:02d}.txt")
        runs[name] = run
    exp = experimental(data_dir, header)
    dt = float(header["dt_exp"])
    frames = int(header["frame_final"]) - int(header["frame_inicial"]) + 1
    every = int(round(dt / (runs["A"][1, 0] - runs["A"][0, 0])))     # filas del motor por Δt_exp

    xs = np.concatenate([np.concatenate([e[:, 1] for e in exp])] + [np.concatenate([r[:, 1], r[:, 5]]) for r in runs.values()])
    ys = np.concatenate([np.concatenate([e[:, 2] for e in exp])] + [np.concatenate([r[:, 2], r[:, 6]]) for r in runs.values()])
    lim_x = (np.nanmin(xs) - 0.6, np.nanmax(xs) + 0.6)
    lim_y = (np.nanmin(ys) - 0.6, np.nanmax(ys) + 0.6)

    panels = ["exp."] + list("ABF")
    fig, axes = plt.subplots(len(panels), 1, figsize=(11, 2.6 * len(panels)), constrained_layout=True, sharex=True)
    artists = {}
    for ax, name in zip(axes, panels):
        ax.set_xlim(*lim_x)
        ax.set_ylim(*lim_y)
        ax.set_aspect("equal")
        ax.set_ylabel("y (m)", fontsize=13)
        ax.grid(color="#e6e5e0", lw=0.8)
        label = "experimental" if name == "exp." else f"{name}({pairs[name][0]}; {pairs[name][1]})".replace(".", ",")
        ax.text(0.01, 0.92, label, transform=ax.transAxes, fontsize=14, color=COLORS[name], va="top")
        trails = [ax.plot([], [], color=COLORS[name], lw=1.5, ls=ls)[0] for ls in ("-", "--")]
        circles = [plt.Circle((np.nan, np.nan), R, facecolor=PED_FILL[i], edgecolor=COLORS[name], lw=2) for i in range(2)]
        for c in circles:
            ax.add_patch(c)
        artists[name] = (trails, circles)
    axes[-1].set_xlabel("x (m)", fontsize=13)
    clock = axes[0].text(0.99, 0.92, "", transform=axes[0].transAxes, fontsize=14, ha="right", va="top")

    def update(k):
        t = k * dt
        clock.set_text(f"t = {t:.2f} s".replace(".", ","))
        for ped, track in enumerate(exp):
            past = track[track[:, 0] <= t + 1e-9]
            trails, circles = artists["exp."]
            trails[ped].set_data(past[:, 1], past[:, 2])
            p = position(track, t)
            circles[ped].set_center(p if p is not None else (np.nan, np.nan))
        for name, run in runs.items():
            trails, circles = artists[name]
            row = min(k * every, len(run) - 1)
            for ped in (0, 1):
                cx, cy = 1 + 4 * ped, 2 + 4 * ped
                trails[ped].set_data(run[: row + 1, cx], run[: row + 1, cy])
                circles[ped].set_center((run[row, cx], run[row, cy]))
        return [clock]

    animation = FuncAnimation(fig, update, frames=frames, interval=1000 * dt)
    out = pilot / "figs" / f"evento_{event:02d}_animacion.gif"
    animation.save(out, writer=PillowWriter(fps=round(1 / dt)), dpi=80)
    print(out)


if __name__ == "__main__":
    main()
