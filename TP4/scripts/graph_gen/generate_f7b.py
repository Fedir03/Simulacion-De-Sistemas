#!/usr/bin/env python3
"""Genera F7b: f(v) en instantes del transitorio y la estacionaria (2.3, N = 100, sin obstáculos).

Cada curva junta las rapideces de todas las partículas de todas las realizaciones (salidas en múltiplos de dt2, sin
interpolar). La estacionaria junta además todas las salidas con t ≥ t_est (D15).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from observables import configure_matplotlib
from speed_distribution import bin_edges, density, load_runs


TP4_DIR = Path(__file__).resolve().parents[2]
V0, WIDTH = 1.0, 0.1  # D15
TIMES = (0.12, 0.24, 0.48)  # instantes del transitorio (además de t = 0)


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

    plt = configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.0, 4.4), layout="constrained")
    # Tiempos del transitorio: pasos de viridis (oscuro → claro); la estacionaria en negro
    colors = ("#440154", "#3B528B", "#21918C", "#5EC962")
    ax.axvline(V0, color=colors[0], linewidth=2, linestyle="--", label=label_time(0) + r" (todas con $v_0$)")
    for t, color in zip(TIMES, colors[1:]):
        ax.stairs(density(transient[t], edges), edges, color=color, linewidth=2, label=label_time(t))
    t_est = f"{args.t_est:g}".replace(".", "{,}")
    ax.stairs(density(stationary, edges), edges, color="black", linewidth=2.2,
              label=rf"estacionaria ($t \geq {t_est}$ s)")
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
          f"fracción con v ≥ 3 m/s fuera del eje: {above:.1e})")


if __name__ == "__main__":
    main()
