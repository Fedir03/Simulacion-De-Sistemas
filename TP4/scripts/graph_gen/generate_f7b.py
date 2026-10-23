#!/usr/bin/env python3
"""Genera F7b: f(v) en instantes del transitorio y la estacionaria (2.3, N = 100, sin obstáculos).

Cada curva junta las rapideces de todas las partículas de todas las realizaciones (salidas en múltiplos de dt2, sin
interpolar). La estacionaria junta además todas las salidas con t ≥ t_est (D15).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from observables import configure_matplotlib
from speed_distribution import bin_edges, density, fit_kbt, load_runs, maxwell_boltzmann_2d


TP4_DIR = Path(__file__).resolve().parents[2]
V0, WIDTH, MASS = 1.0, 0.1, 0.025  # D15; m del enunciado
TIMES = (0.12, 0.24, 0.48)  # instantes del transitorio


def label_time(t: float) -> str:
    return rf"$t={t:g}$ s".replace(".", "{,}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=TP4_DIR / "outputs" / "2.3")
    parser.add_argument("--output", type=Path, default=TP4_DIR / "presentacion" / "figuras" / "F7b-fv-instantes.pdf")
    parser.add_argument("--t-est", type=float, default=0.75, help="inicio del estacionario (D15)")
    args = parser.parse_args()

    try:
        runs = load_runs(args.input)
    except ValueError as error:
        parser.error(str(error))

    def at(t: float) -> list[float]:
        out = []
        for frames in runs:
            out.extend(next(v for time, v in frames.items() if abs(time - t) < 1e-6))
        return out

    initial = at(0.0)
    # Tolerancia 1e-9: la velocidad central con dt = 1e-5 tiene redondeo ~5e-12
    if not all(abs(s - V0) < 1e-9 for s in initial):
        parser.error("en t = 0 todas las partículas deberían tener |v| = v0")
    stationary = [s for frames in runs for time, speeds in frames.items() if time >= args.t_est - 1e-9 for s in speeds]
    transient = {t: at(t) for t in TIMES}
    v_max = max(max(stationary), *(max(s) for s in transient.values())) + 1e-9
    edges = bin_edges(WIDTH, v_max, center=V0)
    centers = [(a + b) / 2 for a, b in zip(edges, edges[1:])]
    # Mismo ajuste que F8 (mismos bins: los de la estacionaria sola), para que k_BT sea idéntico
    fit_edges = bin_edges(WIDTH, max(stationary) + 1e-9, center=V0)
    fit_centers = [(a + b) / 2 for a, b in zip(fit_edges, fit_edges[1:])]
    try:
        kbt, _, _ = fit_kbt(fit_centers, density(stationary, fit_edges), MASS, MASS * V0 ** 2 / 2)
    except ValueError as error:
        parser.error(str(error))

    plt = configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.0, 4.4), layout="constrained")
    # Tiempos del transitorio: pasos de viridis (oscuro → claro); la estacionaria en negro.
    # t = 0 no se dibuja: f(v) = δ(v − v0) no es comparable con las otras curvas (se dice en el pie); solo se marca v0
    colors = ("#3B528B", "#21918C", "#5EC962")
    ax.plot([V0], [0], marker="v", color="#555555", markersize=9, clip_on=False, zorder=5,
            transform=ax.get_xaxis_transform())
    ax.text(V0, 0.04, r"$v_0$", transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=12,
            color="#555555")
    # Puntos en los centros de bin (v_i, f_i), unidos para seguir cada curva
    for t, color in zip(TIMES, colors):
        ax.plot(centers, density(transient[t], edges), color=color, marker="o", markersize=4, linewidth=1.6,
                label=label_time(t))
    t_est = f"{args.t_est:g}".replace(".", "{,}")
    # La curva ajustada de F8 (mismo color y mismo k_BT) debajo; la estacionaria solo con puntos, como en F8,
    # porque coincide con el ajuste y una línea encima la taparía
    smooth = [k * 3.0 / 400 for k in range(401)]
    ax.plot(smooth, [maxwell_boltzmann_2d(v, MASS, kbt) for v in smooth], color="#D55E00", linewidth=2.2,
            label="Maxwell-Boltzmann 2D (ajuste)", zorder=2)
    ax.plot(centers, density(stationary, edges), color="black", marker="o", markersize=5, linestyle="none",
            label=rf"estacionaria ($t \geq {t_est}$ s)", zorder=3)
    ax.set_xlim(0, 3)
    ax.set_ylim(bottom=0)
    ax.set_xlabel(r"$v$ (m/s)")
    ax.set_ylabel(r"$f(v)$ (s/m)")
    ax.grid(alpha=0.22)
    ax.legend(loc="upper right", fontsize=11)

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"CreationDate": None})
    plt.close(fig)
    above = sum(s >= 3 for s in stationary) / len(stationary)
    print(f"F7b generada: {output} ({len(runs)} realizaciones; estacionaria con {len(stationary)} rapideces; "
          f"fracción con v ≥ 3 m/s fuera del eje: {above:.1e}; k_BT del ajuste = {kbt * 1e3:.3f} mJ)")


if __name__ == "__main__":
    main()
