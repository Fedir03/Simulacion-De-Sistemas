#!/usr/bin/env python3
"""Punto (g): tiempos de ejecucion del Cell Index Method, TP2 contra TP1.

Lee los CSV con el esquema de `benchmark-n` de TP1 (N,L,M,meanMs,stdDevMs) y los superpone.
Usa solo la biblioteca estandar mas Matplotlib: TP1/scripts/plot_benchmark.py hace algo
equivalente pero necesita pandas, que no es dependencia de TP2.

Uso:
    python3 TP2/scripts/plot_benchmark_cim.py generated/bench/*.csv --out=cim.pdf
    python3 TP2/scripts/plot_benchmark_cim.py a.csv:"etiqueta" b.csv:"otra" --out=cim.pdf --log
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Sequence


PALETTE = ["#2a9d8f", "#e63946", "#457b9d", "#f4a261", "#8e7dbe", "#264653"]
MARKERS = ["o", "s", "^", "D", "v", "P"]
REQUIRED = {"N", "meanMs", "stdDevMs"}


def read_benchmark(path: Path) -> tuple[list[int], list[float], list[float]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"{path}: el CSV no tiene filas")
    missing = REQUIRED - set(rows[0])
    if missing:
        raise ValueError(f"{path}: faltan columnas {sorted(missing)}; "
                         f"se espera el esquema de benchmark-n (N,L,M,meanMs,stdDevMs)")
    rows.sort(key=lambda row: int(row["N"]))
    return ([int(r["N"]) for r in rows],
            [float(r["meanMs"]) for r in rows],
            [float(r["stdDevMs"]) for r in rows])


def split_label(spec: str) -> tuple[Path, str | None]:
    """Acepta 'archivo.csv' o 'archivo.csv:Etiqueta para la leyenda'."""
    if ":" in spec and not Path(spec).exists():
        path, _, label = spec.rpartition(":")
        return Path(path), label
    return Path(spec), None


def plot(specs: Sequence[str], log: bool, title: str | None):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 6))
    for index, spec in enumerate(specs):
        path, label = split_label(spec)
        ns, means, stds = read_benchmark(path)
        ax.errorbar(ns, means, yerr=stds, fmt=MARKERS[index % len(MARKERS)] + "-",
                    color=PALETTE[index % len(PALETTE)], capsize=3, linewidth=1.4,
                    markersize=5, label=label or path.stem)

    ax.set_xlabel("Cantidad de partículas $N$")
    ax.set_ylabel("Tiempo por llamada al CIM [ms]")
    if log:
        ax.set_xscale("log")
        ax.set_yscale("log")
    else:
        ax.set_ylim(bottom=0.0)
    ax.set_title(title if title is not None
                 else "Tiempo de ejecución del Cell Index Method")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=9)
    fig.tight_layout()
    return fig


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compara tiempos del CIM entre TP1 y TP2.")
    parser.add_argument("inputs", nargs="+",
                        help="CSV de benchmark, opcionalmente como 'archivo.csv:Etiqueta'")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--log", action="store_true", help="escala logaritmica en ambos ejes")
    parser.add_argument("--title", default=None)
    parser.add_argument("--dpi", type=int, default=150)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        if args.out is not None:
            import matplotlib
            matplotlib.use("Agg")
        fig = plot(args.inputs, args.log, args.title)
    except (OSError, ValueError) as exc:
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
        print(f"Grafico guardado en {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
