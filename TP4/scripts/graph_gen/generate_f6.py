#!/usr/bin/env python3
"""Genera F6: <t90> en función de x0 para N = 100 y N = 20 (2.2), con barras de ±σ entre semillas."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from observables import configure_matplotlib
from used_fraction import load_case, mean_std


TP4_DIR = Path(__file__).resolve().parents[2]
R, r = 0.51, 0.0175
# Dos series categóricas: azul y bermellón de Okabe-Ito (los de F2), con marcador distinto
SERIES = ((100, "#0072B2", "o"), (20, "#D55E00", "s"))
# Corrimiento horizontal de cada serie para que las barras no se tapen (se aclara en el pie de la figura)
DODGE = {100: -0.004, 20: 0.004}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=TP4_DIR / "outputs" / "2.2")
    parser.add_argument("--output", type=Path, default=TP4_DIR / "presentacion" / "figuras" / "F6-t90-vs-x0.pdf")
    parser.add_argument("--summary", type=Path, help="CSV de resumen (predeterminado: <input>/t90_vs_x0.csv)")
    args = parser.parse_args()

    rows = []
    data = {}
    for n, _, _ in SERIES:
        points = []
        for case in sorted((args.input / f"n-{n}").glob("x0-*"), key=lambda p: float(p.name[3:])):
            try:
                runs = load_case(case)
            except ValueError as error:
                parser.error(str(error))
            t90 = [run.first_time(0.9) for run in runs]
            reached = [t for t in t90 if t is not None]
            # D14: si alguna semilla no llega a Fu = 0,9 se informa Fu(tmax); no se promedia un t90 parcial
            fu_tmax = [run.used[-1] / run.n for run in runs if run.first_time(0.9) is None]
            mean, std = mean_std(reached) if len(reached) == len(runs) else (float("nan"), float("nan"))
            x0 = runs[0].x0
            points.append((x0, mean, std))
            rows.append((n, x0, len(runs), len(reached), mean, std, ";".join(f"{f:.3f}" for f in fu_tmax)))
        data[n] = points

    summary = (args.summary or args.input / "t90_vs_x0.csv").resolve()
    with summary.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(("N", "x0", "realizaciones", "llegan_a_0.9", "t90_media", "t90_sigma", "Fu_tmax_de_las_que_no_llegan"))
        writer.writerows(rows)

    plt = configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.0, 4.4), layout="constrained")
    for n, color, marker in SERIES:
        x, y, err = zip(*[p for p in data[n] if p[1] == p[1]])
        ax.errorbar([v + DODGE[n] for v in x], y, yerr=err, color=color, marker=marker, markersize=7, linewidth=2,
                    capsize=4, elinewidth=1.4, label=rf"$N={n}$")
    ax.set_xlim(0, R)
    ax.set_ylim(bottom=0)
    ax.set_xlabel(r"$x_0$ (m)")
    ax.set_ylabel(r"$\langle t_{90} \rangle$ (s)")
    ax.grid(alpha=0.22)
    ax.legend(loc="upper center", fontsize=12)

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"CreationDate": None})
    plt.close(fig)
    missing = [row for row in rows if row[3] < row[2]]
    print(f"F6 generada: {output}")
    print(f"Resumen: {summary}")
    print("Todas las semillas llegan a Fu = 0,9." if not missing else
          f"Casos con semillas que no llegan (D14, ver CSV): {[(row[0], row[1]) for row in missing]}")


if __name__ == "__main__":
    main()
