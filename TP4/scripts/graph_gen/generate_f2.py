#!/usr/bin/env python3
"""Genera F2: energía total en función del tiempo."""

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
    if not measured:
        parser.error("F2 necesita al menos una corrida con más de una muestra")

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    import numpy as np
    from matplotlib.ticker import FixedLocator, FuncFormatter

    # Transformación monótona de la escala, sin modificar los datos E(t).
    # Log(E) no separa variaciones de 1e-7 J alrededor de 3.75 J.
    reference = float(measured[0].metadata["N"]) * float(measured[0].metadata["m"]) * float(measured[0].metadata["v0"])**2 / 2
    width = 1e-8  # J: escala de transición suave alrededor de la energía inicial
    forward = lambda energy: np.arcsinh((np.asarray(energy) - reference) / width)
    inverse = lambda value: reference + width * np.sinh(np.asarray(value))
    fig, ax = plt.subplots(figsize=(7.0, 4.4), layout="constrained")
    colors = [plt.get_cmap("tab10")(i % 10) for i in range(len(measured))]
    for run, color in zip(measured, colors):
        status = " (divergió)" if run.status != "completa" else ""
        ax.plot(run.times, run.total_energy, color=color, linewidth=1.5,
                label=rf"$\Delta t={dt_label(run.dt)}$ s{status}")
    ax.set_yscale("function", functions=(forward, inverse))
    ticks = reference + np.array([-1e-2, -1e-4, -1e-6, -1e-7, 0,
                                  1e-7, 1e-6, 1e-4, 1e-2, 1, 10, 100])
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.7f}".rstrip("0").rstrip(".")))
    ax.axhline(reference, color="black", linewidth=0.7, alpha=0.5)
    ax.set_xlim(0, max(run.times[-1] for run in measured))
    ax.set_xlabel(r"$t$ (s)")
    ax.set_ylabel(r"$E(t)$ (J; escala asinh)")
    ax.tick_params(labelsize=11)
    ax.grid(alpha=0.22)
    ax.legend(loc="upper right", fontsize=11)
    fig.savefig(output, bbox_inches="tight", metadata={"CreationDate": None})
    fig.savefig(output.with_suffix(".png"), bbox_inches="tight", dpi=180)
    plt.close(fig)
    print(f"F2 energía total: {output}")



if __name__ == "__main__":
    main()
