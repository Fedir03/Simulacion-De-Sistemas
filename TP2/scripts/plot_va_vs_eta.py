#!/usr/bin/env python3
"""Grafica el parametro de orden estacionario <v_a> en funcion del ruido eta.

Lee el indice runs.csv que escribe sweep.py, promedia v_a sobre la cola estacionaria de
cada corrida y, para cada eta, informa el promedio sobre las M corridas con su desvio:

    v_a_barra = (1/M) sum_j v_a^(j)
    sigma     = sqrt( (1/(M-1)) sum_j (v_a^(j) - v_a_barra)^2 )

El transitorio NO se detecta solo: se elige a ojo mirando v_a(t) con plot_va.py y se pasa
con --transient.

Uso:
    python3 TP2/scripts/plot_va_vs_eta.py generated/sweep_eta/runs.csv --transient=1500 \
        --out=TP2/presentacion/figuras/relacion-parametro-observable.pdf
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from order_parameter import (
    load_named_series,
    mean_and_stdev,
    resolve_transient,
    tail_values,
)
from simulation_io import SimulationFormatError, SimulationHeader


PALETTE = ["#2a9d8f", "#e63946", "#457b9d", "#f4a261", "#8e7dbe", "#264653"]
MARKERS = ["o", "s", "^", "D", "v", "P"]
GROUP_FIELDS = ("density", "n", "model", "l", "theta0")


def group_key(header: SimulationHeader, field: str) -> tuple[float, str]:
    """Devuelve (orden, etiqueta) del grupo al que pertenece una corrida."""
    if field == "density":
        return header.density, f"ρ = {header.density:g} (N = {header.n}, L = {header.l:g})"
    if field == "n":
        return float(header.n), f"N = {header.n} (L = {header.l:g}, ρ = {header.density:g})"
    if field == "l":
        return header.l, f"L = {header.l:g} (N = {header.n})"
    if field == "model":
        return 0.0, f"modelo {header.model}"
    return 0.0, header.theta0_label


def differing_field(headers: Sequence[SimulationHeader]) -> str:
    """Elige solo el campo que distingue las corridas, para no repetir lo que es comun."""
    for field, getter in (("model", lambda h: h.model),
                          ("density", lambda h: h.density),
                          ("n", lambda h: h.n),
                          ("l", lambda h: h.l)):
        if len({getter(h) for h in headers}) > 1:
            return field
    return "density"


@dataclass(frozen=True)
class Curve:
    label: str
    etas: list[float]
    means: list[float]
    stdevs: list[float]
    counts: list[int]


def read_index(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise SimulationFormatError(f"{path}: el indice no tiene corridas")
    missing = {"eta", "va_csv"} - set(rows[0].keys())
    if missing:
        raise SimulationFormatError(
            f"{path}: al indice le faltan columnas: {', '.join(sorted(missing))}"
        )
    return rows


def collect(indexes: Sequence[Path], transient: str | int, group_by: str,
            column: str = "va_csv") -> tuple[list[Curve], str, str]:
    """Lee todos los indices y arma una curva <v_a> vs eta por cada grupo."""
    per_run: list[tuple[SimulationHeader, float, list[float]]] = []
    observables: set[str] = set()
    for index_path in indexes:
        for row in read_index(index_path):
            if column not in row or not row[column]:
                raise SimulationFormatError(
                    f"{index_path}: la corrida no tiene la columna '{column}' "
                    f"(¿falta correr 'sweep.py clusters' sobre este indice?)")
            series_path = Path(row[column])
            if not series_path.is_absolute():
                series_path = index_path.parent / series_path
            header, steps, values, observable = load_named_series(series_path)
            tail = tail_values(steps, values, resolve_transient(transient, steps[-1]))
            per_run.append((header, float(row["eta"]), tail))
            observables.add(observable)

    field = differing_field([header for header, _, _ in per_run]) if group_by == "auto" else group_by

    pooled: dict[tuple[float, str], dict[float, list[float]]] = defaultdict(
        lambda: defaultdict(list))
    run_counts: dict[tuple[float, str], dict[float, int]] = defaultdict(
        lambda: defaultdict(int))
    for header, eta, tail in per_run:
        key = group_key(header, field)
        pooled[key][eta].extend(tail)
        run_counts[key][eta] += 1

    curves: list[Curve] = []
    for (order, label) in sorted(pooled, key=lambda key: (key[0], key[1])):
        per_eta = pooled[(order, label)]
        etas = sorted(per_eta)
        means, stdevs, counts = [], [], []
        for eta in etas:
            mean, stdev = mean_and_stdev(per_eta[eta])
            means.append(mean)
            stdevs.append(stdev)
            counts.append(run_counts[(order, label)][eta])
        curves.append(Curve(label=label, etas=etas, means=means, stdevs=stdevs, counts=counts))
    return curves, field, observables.pop() if len(observables) == 1 else "va"


OBSERVABLE_LABELS = {
    "va": "Parámetro de orden estacionario $\\overline{v}_a$",
    "S": "Fracción en la componente gigante $\\overline{S}$",
}


def plot(curves: Sequence[Curve], title: str | None, transient: int, observable: str = "va"):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 6))
    for index, curve in enumerate(curves):
        ax.errorbar(curve.etas, curve.means, yerr=curve.stdevs,
                    fmt=MARKERS[index % len(MARKERS)] + "-",
                    color=PALETTE[index % len(PALETTE)], capsize=3, linewidth=1.4,
                    markersize=5, label=curve.label)
    ax.set_xlabel("Ruido $\\eta$")
    ylabel = OBSERVABLE_LABELS.get(observable, observable)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0.0, 1.02)
    if title is not None:
        ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    return fig


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Grafica <v_a> estacionario vs. eta con barras de error."
    )
    parser.add_argument("indexes", nargs="+", type=Path,
                        help="uno o mas runs.csv generados por sweep.py")
    parser.add_argument("--transient", default=None,
                        help="primer paso del estado estacionario, en pasos (500) o como "
                             "porcentaje del largo de cada corrida (40%%). El porcentaje "
                             "permite mezclar corridas de distinto largo")
    parser.add_argument("--out", type=Path, default=None,
                        help="archivo de salida (.pdf/.png); sin este flag abre una ventana")
    parser.add_argument("--group-by", choices=GROUP_FIELDS + ("auto",), default="auto",
                        help="una curva por cada valor de este campo (default: auto)")
    parser.add_argument("--observable", default="va_csv",
                        help="columna del indice con la serie a promediar: va_csv (default) o s_csv")
    parser.add_argument("--title", default=None, help="titulo del grafico")
    parser.add_argument("--dpi", type=int, default=150, help="resolucion de salida (default: 150)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    transient = args.transient
    if transient is None:
        transient = 0
        print("Aviso: sin --transient se promedia la corrida entera, transitorio incluido.",
              file=sys.stderr)

    try:
        curves, field, observable = collect(args.indexes, transient, args.group_by,
                                            args.observable)
        print(f"Curvas agrupadas por: {field}   (transitorio: t >= {transient})")
        for curve in curves:
            print(f"\n{curve.label}")
            for eta, mean, stdev, count in zip(curve.etas, curve.means,
                                               curve.stdevs, curve.counts):
                print(f"  eta={eta:<6g} <{observable}>={mean:.4f} +/- {stdev:.4f}  (M={count})")
        if args.out is not None:
            import matplotlib
            matplotlib.use("Agg")
        fig = plot(curves, args.title, transient, observable)
    except (OSError, SimulationFormatError, ValueError) as exc:
        print(f"Error: {exc}")
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
        print(f"Grafico guardado en {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
