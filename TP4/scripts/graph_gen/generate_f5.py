#!/usr/bin/env python3
"""Genera F5: Fu(t) promediada entre semillas para 3 valores de x0 (2.2, N = 100)."""

from __future__ import annotations

import argparse
from pathlib import Path

from observables import configure_matplotlib
from used_fraction import load_case


TP4_DIR = Path(__file__).resolve().parents[2]
R, r = 0.51, 0.0175
# DEFINICIONES.md F5: x0 = r, 0,24 y R − r
CASES = (("0.0175", r"$x_0=r$"), ("0.24", r"$x_0=0{,}24$ m"), ("0.4925", r"$x_0=R-r$"))
# Valores ordenados de un mismo parámetro: tres pasos de viridis (oscuro → claro)
COLORS = ("#440154", "#21918C", "#5EC962")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=TP4_DIR / "outputs" / "2.2" / "n-100")
    parser.add_argument("--output", type=Path, default=TP4_DIR / "presentacion" / "figuras" / "F5-fu-vs-t.pdf")
    args = parser.parse_args()

    curves = []
    for x0, label in CASES:
        try:
            runs = load_case(args.input / f"x0-{x0}")
        except ValueError as error:
            parser.error(str(error))
        # Grilla común hasta la última salida de la corrida más larga del caso
        steps = max(len(run.used) for run in runs)
        fractions = [run.fraction_on_grid(steps) for run in runs]
        mean = [sum(column) / len(runs) for column in zip(*fractions)]
        times = [k * runs[0].dt2 for k in range(steps)]
        curves.append((times, mean, label, len(runs)))
    t_max = max(times[-1] for times, *_ in curves)

    plt = configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.0, 4.4), layout="constrained")
    ax.axhline(0.9, color="#888888", linewidth=1, linestyle="--", zorder=1)
    ax.text(t_max, 0.9, "0,9", ha="right", va="bottom", fontsize=11, color="#555555")
    for (times, mean, label, _), color in zip(curves, COLORS):
        # Después de t100 la curva queda en 1 hasta t_max (Nu ya es N y no decrece)
        if times[-1] < t_max:
            times = times + [t_max]
            mean = mean + [mean[-1]]
        ax.plot(times, mean, linewidth=2, color=color, label=label, zorder=2)
    ax.set_xlim(0, t_max)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel(r"$t$ (s)")
    ax.set_ylabel(r"$\langle F_u \rangle$")
    ax.grid(alpha=0.22)
    ax.legend(loc="lower right", fontsize=12)

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"CreationDate": None})
    plt.close(fig)
    print(f"F5 generada: {output} ({', '.join(f'{c[2]}: {c[3]} semillas' for c in curves)})")


if __name__ == "__main__":
    main()
