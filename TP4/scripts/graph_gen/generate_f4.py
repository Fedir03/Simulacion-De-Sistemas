#!/usr/bin/env python3
"""Genera F4 comparando las medianas de tiempo de TP3 y TP4 frente a N."""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path

from observables import configure_matplotlib


TP4_DIR = Path(__file__).resolve().parents[2]


def read_summary(path: Path, expected_runs: int, allow_incomplete: bool):
    try:
        with path.open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
    except OSError as error:
        raise ValueError(f"no se pudo leer {path}: {error}") from error
    by_n: dict[int, list[float]] = {}
    seen: set[tuple[int, int]] = set()
    for line, row in enumerate(rows, start=2):
        try:
            n, seed, runtime = int(row["n"]), int(row["seed"]), float(row["runtime_s"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{path}:{line}: fila inválida") from error
        if (n, seed) in seen:
            raise ValueError(f"{path}: N={n}, semilla={seed} repetidos")
        seen.add((n, seed)); by_n.setdefault(n, []).append(runtime)

    result = []
    for n, values in sorted(by_n.items()):
        if not allow_incomplete and len(values) != expected_runs:
            raise ValueError(f"{path}: N={n} tiene {len(values)} corridas; se esperaban {expected_runs}")
        if len(values) < 2:
            raise ValueError(f"{path}: N={n} necesita al menos dos corridas")
        p25, median, p75 = statistics.quantiles(values, n=4, method="inclusive")
        result.append((n, median, p25, p75, len(values)))
    if not result:
        raise ValueError(f"{path}: no contiene mediciones")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tp3", type=Path, default=TP4_DIR / "outputs" / "runtime_tp3" / "runs.csv")
    parser.add_argument("--tp4", type=Path, default=TP4_DIR / "outputs" / "runtime_tp4" / "runs.csv")
    parser.add_argument("--output", type=Path,
                        default=TP4_DIR / "presentacion" / "figuras" / "F4-tiempo-vs-n.pdf")
    parser.add_argument("--dt", default="10^{-5}", help="dt de TP4 mostrado en la leyenda (LaTeX sin $)")
    parser.add_argument("--runs", type=int, default=10, help="corridas esperadas por N")
    parser.add_argument("--allow-incomplete", action="store_true", help="graficar tandas parciales con >=2 corridas por N")
    args = parser.parse_args()
    try:
        tp3 = read_summary(args.tp3.resolve(), args.runs, args.allow_incomplete)
        tp4 = read_summary(args.tp4.resolve(), args.runs, args.allow_incomplete)
    except ValueError as error:
        parser.error(str(error))

    plt = configure_matplotlib()
    fig, ax = plt.subplots(figsize=(10.5, 4.8), layout="constrained")
    for data, label, color, marker in (
        (tp3, "TP3 — dirigido por eventos", "#D55E00", "s"),
        (tp4, rf"TP4 — paso temporal ($\Delta t={args.dt}\,\mathrm{{s}}$)", "#0072B2", "o"),
    ):
        ns = [row[0] for row in data]; med = [row[1] for row in data]
        low = [row[1] - row[2] for row in data]; high = [row[3] - row[1] for row in data]
        ax.errorbar(ns, med, yerr=[low, high], fmt=marker + "-", color=color, ecolor=color,
                    linewidth=2.2, markersize=8, capsize=4, label=label)
    ax.set_xscale("log"); ax.set_yscale("log")
    all_ns = sorted({row[0] for row in tp3 + tp4})
    ax.set_xticks(all_ns, [str(n) for n in all_ns])
    ax.minorticks_off()
    ax.set_xlabel(r"$N$")
    ax.set_ylabel("tiempo de ejecución (s)")
    ax.grid(alpha=0.25, which="major")
    ax.legend(loc="best", fontsize=12)
    output = args.output.resolve(); output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"CreationDate": None})
    plt.close(fig)
    print(f"F4 generada: {output}")


if __name__ == "__main__":
    main()
