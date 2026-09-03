#!/usr/bin/env python3
"""Punto (e): polarizacion v_a en funcion de la fraccion en la componente gigante S.

Cada punto es un valor de eta: se toma el promedio estacionario de v_a y el de S sobre las
mismas corridas, y se los grafica uno contra otro. Un color por densidad.

Uso:
    python3 TP2/scripts/plot_va_vs_s.py generated/*/runs.csv --transient=500 \
        --out=TP2/presentacion/figuras/va-vs-s.pdf
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from order_parameter import load_series, mean_and_stdev, resolve_transient, tail_values
from simulation_io import SimulationFormatError, SimulationHeader


PALETTE = ["#2a9d8f", "#e63946", "#457b9d", "#f4a261", "#8e7dbe", "#264653"]
MARKERS = ["o", "s", "^", "D", "v", "P"]
ERRORBAR_ALPHA = 0.35


@dataclass(frozen=True)
class Point:
    eta: float
    va: float
    va_error: float
    s: float
    s_error: float


def steady_values(index_dir: Path, relative: str, transient: str | int) -> list[float]:
    path = Path(relative)
    if not path.is_absolute():
        path = index_dir / path
    _, steps, values = load_series(path)
    return tail_values(steps, values, resolve_transient(transient, steps[-1]))


def collect(indexes: Sequence[Path], transient: str | int) -> dict[tuple[float, str], list[Point]]:
    """Agrupa por densidad y devuelve un punto (v_a, S) por cada eta."""
    grouped: dict[tuple[float, str], dict[float, tuple[list[float], list[float]]]] = defaultdict(
        lambda: defaultdict(lambda: ([], [])))

    for index_path in indexes:
        with index_path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            if not row.get("s_csv"):
                raise SimulationFormatError(
                    f"{index_path}: falta la columna s_csv "
                    f"(correr antes: sweep.py clusters --index={index_path})")
            va_tail = steady_values(index_path.parent, row["va_csv"], transient)
            s_tail = steady_values(index_path.parent, row["s_csv"], transient)
            density = int(row["n"]) / (float(row["l"]) ** 2)
            key = (density, f"ρ = {density:.4g} (N = {row['n']}, L = {float(row['l']):.4g})")
            va_list, s_list = grouped[key][float(row["eta"])]
            va_list.extend(va_tail)
            s_list.extend(s_tail)

    curves: dict[tuple[float, str], list[Point]] = {}
    for key, per_eta in grouped.items():
        points = []
        for eta in sorted(per_eta):
            va_list, s_list = per_eta[eta]
            va_mean, va_error = mean_and_stdev(va_list)
            s_mean, s_error = mean_and_stdev(s_list)
            points.append(Point(eta, va_mean, va_error, s_mean, s_error))
        curves[key] = points
    return curves


def plot(curves: dict[tuple[float, str], list[Point]], title: str | None, transient: str | int):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 6))
    for index, key in enumerate(sorted(curves)):
        points = curves[key]
        _, caplines, barlinecols = ax.errorbar(
            [p.s for p in points], [p.va for p in points],
            xerr=[p.s_error for p in points], yerr=[p.va_error for p in points],
            fmt=MARKERS[index % len(MARKERS)] + "-", color=PALETTE[index % len(PALETTE)],
            capsize=1.5, linewidth=1.2, markersize=5, label=key[1],
        )
        for cap in caplines:
            cap.set_alpha(ERRORBAR_ALPHA)
        for barlinecol in barlinecols:
            barlinecol.set_alpha(ERRORBAR_ALPHA)

    ax.set_xlabel("Fracción en la componente gigante $\\overline{S}$")
    ax.set_ylabel("Parámetro de orden $\\overline{v}_a$")
    ax.set_xlim(0.0, 1.02)
    ax.set_ylim(0.0, 1.02)
    if title is not None:
        ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    return fig


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Grafica v_a estacionario en funcion de S estacionario, por densidad.")
    parser.add_argument("indexes", nargs="+", type=Path,
                        help="uno o mas runs.csv que ya tengan la columna s_csv")
    parser.add_argument("--transient", default=0,
                        help="primer paso del estado estacionario, en pasos (500) o como "
                             "porcentaje del largo de cada corrida (40%%). El porcentaje "
                             "permite mezclar corridas de distinto largo")
    parser.add_argument("--out", type=Path, default=None,
                        help="archivo de salida; sin este flag abre una ventana")
    parser.add_argument("--title", default=None)
    parser.add_argument("--dpi", type=int, default=150)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        curves = collect(args.indexes, args.transient)
        for key in sorted(curves):
            print(f"\n{key[1]}")
            for point in curves[key]:
                print(f"  eta={point.eta:<5g} S={point.s:.4f}+/-{point.s_error:.4f}  "
                      f"v_a={point.va:.4f}+/-{point.va_error:.4f}")
        if args.out is not None:
            import matplotlib
            matplotlib.use("Agg")
        fig = plot(curves, args.title, args.transient)
    except (OSError, SimulationFormatError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ImportError:
        print("Error: falta Matplotlib; instalar con: python3 -m pip install -r TP2/requirements.txt")
        return 1

    if args.out is None:
        import matplotlib.pyplot as plt
        plt.show()
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.out, dpi=args.dpi)
        print(f"\nGrafico guardado en {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
