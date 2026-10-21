#!/usr/bin/env python3
"""Genera F2: error relativo de energía en función del tiempo para cada dt."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from observables import configure_matplotlib, load_study


TP4_DIR = Path(__file__).resolve().parents[2]


def dt_label(dt: float) -> str:
    exponent = round(math.log10(dt))
    if math.isclose(dt, 10.0**exponent, rel_tol=1e-12):
        return rf"10^{{{exponent}}}"
    return f"{dt:g}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=TP4_DIR / "outputs" / "2.1a")
    parser.add_argument(
        "--output",
        type=Path,
        default=TP4_DIR / "presentacion" / "figuras" / "F2-energia-vs-t.pdf",
    )
    args = parser.parse_args()

    try:
        runs = load_study(args.input.resolve())
    except ValueError as error:
        parser.error(str(error))

    plt = configure_matplotlib()
    measured = [run for run in runs if len(run.times) > 1]
    without_measurement = [run for run in runs if len(run.times) == 1]
    if len(measured) > 4:
        parser.error("F2 admite como máximo cuatro corridas con más de una muestra")

    # Los errores abarcan más de ocho órdenes de magnitud. Una sola escala
    # lineal aplasta las curvas estables contra cero; pequeños múltiplos
    # mantienen la escala lineal pedida y permiten ver la evolución de cada dt.
    # Relación ancha para aprovechar la diapositiva completa sin reducir la
    # figura a una columna angosta.
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 4.8), layout="constrained")
    axes = list(axes.flat)
    colors = ("#D55E00", "#0072B2", "#009E73", "#CC79A7")
    for ax, run, color in zip(axes, measured, colors):
        errors = run.relative_error
        ax.plot(run.times, errors, linewidth=1.6, color=color)
        ax.axhline(0, color="black", linewidth=0.7, alpha=0.4)
        status = " — divergió" if run.status != "completa" else ""
        ax.set_title(rf"$\Delta t={dt_label(run.dt)}\,\mathrm{{s}}${status}", fontsize=12, pad=3)
        ax.grid(alpha=0.22)
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useMathText=True)
        ax.tick_params(labelsize=10.5)

        low, high = min(errors), max(errors)
        span = high - low
        padding = 0.08 * span if span > 0 else max(abs(high) * 0.08, 1e-15)
        ax.set_ylim(min(low - padding, -padding), max(high + padding, padding))
        ax.set_xlim(0, max(run.times))

    for ax in axes[len(measured):]:
        ax.set_visible(False)

    if without_measurement:
        descriptions = []
        for run in without_measurement:
            status = "divergió" if run.status != "completa" else "sin segunda muestra"
            descriptions.append(rf"$\Delta t={dt_label(run.dt)}$ s: {status} antes de $\Delta t_2$")
        axes[0].text(
            0.97,
            0.06,
            "\n".join(descriptions),
            transform=axes[0].transAxes,
            ha="right",
            va="bottom",
            fontsize=9.5,
            color="#A61B1B",
            bbox={"facecolor": "white", "edgecolor": "#A61B1B", "alpha": 0.9, "pad": 3},
        )

    fig.supxlabel(r"$t$ (s)", fontsize=14)
    fig.supylabel(r"$(E(t)-E(0))/E(0)$", fontsize=14)

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"CreationDate": None})
    plt.close(fig)
    print(f"F2 generada: {output}")


if __name__ == "__main__":
    main()
