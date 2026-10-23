#!/usr/bin/env python3
"""Genera F8 y F8b: f(v) estacionaria con el ajuste de Maxwell-Boltzmann 2D (2.3) y el error del ajuste E(k_BT).

- Estacionaria: salidas con t ≥ t_est (D15) de todas las realizaciones. Barra de error por bin con el método de la
  bolsa de datos (skill sims-tp-format, metodologia-estadistica.md): media y σ muestral sobre los f(v) instantáneos de
  todas esas salidas de todas las realizaciones, no entre promedios por realización.
- Ajuste (Teórica 0): mínimos cuadrados con k_BT como único parámetro libre, E(k_BT) = Σ_i [f_i − f_MB(v_i; k_BT)]²
  sobre los centros de bin v_i; se barre k_BT y se toma el mínimo.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from observables import configure_matplotlib
from speed_distribution import bin_edges, density, fit_kbt, load_runs, maxwell_boltzmann_2d


TP4_DIR = Path(__file__).resolve().parents[2]
V0, WIDTH, MASS = 1.0, 0.1, 0.025  # D15; m del enunciado
FIGS = TP4_DIR / "presentacion" / "figuras"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=TP4_DIR / "outputs" / "2.3")
    parser.add_argument("--output", type=Path, default=FIGS / "F8-fv-mb.pdf")
    parser.add_argument("--output-error", type=Path, default=FIGS / "F8b-error-ajuste.pdf")
    parser.add_argument("--t-est", type=float, default=0.75, help="inicio del estacionario (D15)")
    args = parser.parse_args()

    try:
        runs = load_runs(args.input)
    except ValueError as error:
        parser.error(str(error))
    frames = [speeds for run in runs for time, speeds in sorted(run.items()) if time >= args.t_est - 1e-9]
    all_speeds = [s for speeds in frames for s in speeds]
    edges = bin_edges(WIDTH, max(all_speeds) + 1e-9, center=V0)
    centers = [(a + b) / 2 for a, b in zip(edges, edges[1:])]

    # Bolsa de datos: f(v) instantáneo de cada salida; media y σ muestral por bin
    bins = len(centers)
    total, total_sq = [0.0] * bins, [0.0] * bins
    for speeds in frames:
        for i, value in enumerate(density(speeds, edges)):
            total[i] += value
            total_sq[i] += value * value
    n = len(frames)
    mean = [s / n for s in total]
    sigma = [math.sqrt(max(sq - n * m * m, 0.0) / (n - 1)) for sq, m in zip(total_sq, mean)]

    # Ajuste por barrido de k_BT (Teórica 0); el mismo que usa F7b
    reference = MASS * V0 ** 2 / 2  # m v0²/2
    try:
        kbt, grid, errors = fit_kbt(centers, mean, MASS, reference)
    except ValueError as error:
        parser.error(str(error))
    best = grid.index(kbt)
    v2 = sum(s * s for s in all_speeds) / len(all_speeds)

    plt = configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.0, 4.4), layout="constrained")
    ax.errorbar(centers, mean, yerr=sigma, fmt="o", color="#0072B2", markersize=5, capsize=3, elinewidth=1.2,
                label=r"simulación")
    smooth = [k * 3.0 / 400 for k in range(401)]
    ax.plot(smooth, [maxwell_boltzmann_2d(v, MASS, kbt) for v in smooth], color="#D55E00", linewidth=2,
            label=rf"Maxwell-Boltzmann 2D, $k_BT={kbt * 1e3:.2f}$ mJ".replace(".", "{,}", 1))
    ax.set_xlim(0, 3)
    ax.set_ylim(bottom=0)
    ax.set_xlabel(r"$v$ (m/s)")
    ax.set_ylabel(r"$f(v)$ (s/m)")
    ax.grid(alpha=0.22)
    ax.legend(loc="upper right", fontsize=11)
    for path, figure in ((args.output, fig),):
        path.resolve().parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path.resolve(), metadata={"CreationDate": None})
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.0, 4.4), layout="constrained")
    ax.plot([g * 1e3 for g in grid], errors, color="#0072B2", linewidth=2)
    ax.plot([kbt * 1e3], [errors[best]], "o", color="#0072B2", markersize=8)
    ax.axvline(reference * 1e3, color="#555555", linestyle="--", linewidth=1.2)
    ax.text(reference * 1e3, 0.98, r" $m v_0^2/2$", transform=ax.get_xaxis_transform(), ha="left", va="top",
            fontsize=13, color="#555555")
    ax.set_yscale("log")
    ax.set_xlabel(r"$k_BT$ (mJ)")
    ax.set_ylabel(r"$E(k_BT)$ (s²/m²)")
    ax.grid(alpha=0.22, which="both")
    args.output_error.resolve().parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output_error.resolve(), metadata={"CreationDate": None})
    plt.close(fig)

    summary = (args.input / "ajuste_mb.csv").resolve()
    with summary.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(("t_est", "realizaciones", "salidas", "kBT_ajuste_J", "E_min", "m_v0^2/2_J", "m_<v^2>/2_J"))
        writer.writerow((args.t_est, len(runs), n, kbt, errors[best], reference, MASS * v2 / 2))
    print(f"F8 generada: {args.output.resolve()}")
    print(f"F8b generada: {args.output_error.resolve()}")
    print(f"Estacionaria: {len(runs)} realizaciones × salidas con t ≥ {args.t_est:g} s = {n} salidas, {len(all_speeds)} rapideces")
    print(f"k_BT ajuste = {kbt * 1e3:.3f} mJ | m v0²/2 = {reference * 1e3:.3f} mJ | m<v²>/2 (estacionario) = "
          f"{MASS * v2 / 2 * 1e3:.3f} mJ | diferencia ajuste vs m v0²/2: {100 * (kbt / reference - 1):+.1f} %")


if __name__ == "__main__":
    main()
