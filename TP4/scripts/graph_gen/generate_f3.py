#!/usr/bin/env python3
"""Genera F3: error energético máximo frente a dt y selecciona el dt candidato."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from observables import configure_matplotlib, load_study


TP4_DIR = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=TP4_DIR / "outputs" / "2.1a")
    parser.add_argument(
        "--output",
        type=Path,
        default=TP4_DIR / "presentacion" / "figuras" / "F3-epsE-vs-dt.pdf",
    )
    parser.add_argument("--threshold", type=float, default=1e-3, help="umbral de epsilon_E")
    parser.add_argument(
        "--summary",
        type=Path,
        help="CSV de resumen (predeterminado: <input>/epsilon_energy.csv)",
    )
    args = parser.parse_args()
    if args.threshold <= 0:
        parser.error("--threshold debe ser positivo")

    try:
        runs = load_study(args.input.resolve())
    except ValueError as error:
        parser.error(str(error))

    # Si una corrida diverge antes de la primera salida dt2, solo existe t=0 y
    # epsilon=0 sería un artefacto: no hubo una segunda muestra con la cual
    # medir el error. Se registra como NaN y no se dibuja como dato numérico.
    points = sorted(
        (
            run.dt,
            run.epsilon if len(run.times) > 1 else math.nan,
            run,
        )
        for run in runs
    )
    eligible = [
        item
        for item in points
        if math.isfinite(item[1]) and item[1] <= args.threshold and item[2].status == "completa"
    ]
    chosen = max(eligible, key=lambda item: item[0]) if eligible else None

    summary = (args.summary or args.input / "epsilon_energy.csv").resolve()
    summary.parent.mkdir(parents=True, exist_ok=True)
    with summary.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(("dt", "epsilon_E", "status", "selected"))
        for dt, epsilon, run in points:
            writer.writerow((dt, "" if math.isnan(epsilon) else epsilon, run.status,
                             chosen is not None and run is chosen[2]))

    plt = configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.0, 4.4), layout="constrained")
    completed = [item for item in points if item[2].status == "completa" and math.isfinite(item[1]) and item[1] > 0]
    divergent = [item for item in points if item[2].status != "completa" and math.isfinite(item[1]) and item[1] > 0]
    ax.loglog(
        [item[0] for item in completed],
        [item[1] for item in completed],
        "o-",
        color="#3939B5",
        linewidth=2,
        markersize=7,
        label=r"$\varepsilon_E$ (corrida completa)",
    )
    if divergent:
        ax.scatter(
            [item[0] for item in divergent],
            [item[1] for item in divergent],
            marker="x",
            s=75,
            linewidths=2,
            color="#C43C39",
            label="divergió (error hasta la última salida)",
        )
    ax.axhline(args.threshold, color="#C43C39", linestyle="--", linewidth=1.8,
               label=rf"umbral $={args.threshold:g}$")
    if chosen is not None:
        ax.scatter([chosen[0]], [chosen[1]], marker="*", s=180, color="#15803D", zorder=4,
                   label=rf"candidato $\Delta t={chosen[0]:g}\,\mathrm{{s}}$")
    without_measurement = [item for item in points if not math.isfinite(item[1])]
    if without_measurement:
        dt_text = ", ".join(f"{item[0]:g}" for item in without_measurement)
        ax.text(
            0.98,
            0.03,
            rf"$\Delta t={dt_text}$ s: divergió antes de $\Delta t_2$",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=9,
            color="#C43C39",
        )
    ax.set_xlabel(r"$\Delta t$ (s)")
    ax.set_ylabel(r"$\varepsilon_E$")
    ax.grid(alpha=0.25, which="both")
    ax.legend(loc="best", fontsize=10)

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"CreationDate": None})
    plt.close(fig)

    print(f"F3 generada: {output}")
    print(f"Resumen: {summary}")
    if chosen is None:
        print(f"Ningún dt completo cumple epsilon_E <= {args.threshold:g}.")
    else:
        print(f"dt candidato: {chosen[0]:g} s (epsilon_E={chosen[1]:.6g})")
        print("Falta validarlo con N=714, x0=0.0175 y tf=10 s antes de cerrarlo.")


if __name__ == "__main__":
    main()
