#!/usr/bin/env python3
"""Genera F4: tiempo de ejecución de TP3 y TP4 frente a N, con media ± desvío estándar (D7, M6), y su tabla con la mediana."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path

from observables import configure_matplotlib


TP4_DIR = Path(__file__).resolve().parents[2]
OUTPUTS = TP4_DIR / "outputs"
HEADER = ("motor", "N", "corridas", "media_s", "desvio_s", "mediana_s", "p25_s", "p75_s")
HEADER_MD = ("Motor", "N", "Corridas", "Media (s)", "Desvío (s)", "Mediana (s)", "p25 (s)", "p75 (s)")


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
        # Desvío muestral (n − 1); percentiles con interpolación lineal (D7)
        p25, median, p75 = statistics.quantiles(values, n=4, method="inclusive")
        result.append((n, statistics.mean(values), statistics.stdev(values), median, p25, p75, len(values)))
    if not result:
        raise ValueError(f"{path}: no contiene mediciones")
    return result


def crossing(tp3, tp4) -> float | None:
    """N en que las medias de TP4 y TP3 se cruzan, interpolando en log-log (rectas como en la figura) entre los dos N medidos que lo encierran."""
    tp3_means = {row[0]: row[1] for row in tp3}
    diffs = [(math.log(row[0]), math.log(row[1] / tp3_means[row[0]])) for row in tp4 if row[0] in tp3_means]
    for (n1, d1), (n2, d2) in zip(diffs, diffs[1:]):
        if d1 * d2 <= 0 and d1 != d2:
            return math.exp(n1 + (n2 - n1) * d1 / (d1 - d2))
    return None


def write_tables(directory: Path, series) -> None:
    rows = [(name, n, count, mean, std, median, p25, p75)
            for name, data in series for n, mean, std, median, p25, p75, count in data]
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "F4-tiempos.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(HEADER); writer.writerows(rows)
    lines = ["| " + " | ".join(HEADER_MD) + " |", "|" + "---|" * len(HEADER_MD)]
    for name, n, count, *values in rows:
        lines.append("| " + " | ".join([name, str(n), str(count)] + [f"{v:.4g}".replace(".", ",") for v in values]) + " |")
    (directory / "F4-tiempos.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tp3", type=Path, default=OUTPUTS / "runtime_tp3_limpia" / "runs.csv",
                        help="tanda de TP3 (D7: la limpia; la tanda A solo como fallback, con advertencia)")
    parser.add_argument("--tp4", type=Path, default=OUTPUTS / "runtime_tp4_obs" / "runs.csv")
    parser.add_argument("--output", type=Path,
                        default=TP4_DIR / "presentacion" / "figuras" / "F4-tiempo-vs-n.pdf")
    parser.add_argument("--table-dir", type=Path, default=OUTPUTS / "runtime_tp4_analisis",
                        help="carpeta de F4-tiempos.csv y F4-tiempos.md")
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
    for data, label, color, marker in ((tp3, "TP3", "#D55E00", "s"), (tp4, "TP4", "#0072B2", "o")):
        ns = [row[0] for row in data]; means = [row[1] for row in data]; stds = [row[2] for row in data]
        ax.errorbar(ns, means, yerr=stds, fmt=marker + "-", color=color, ecolor=color,
                    linewidth=2.2, markersize=8, capsize=4, label=label)
    ax.set_xscale("log"); ax.set_yscale("log")
    all_ns = sorted({row[0] for row in tp3 + tp4})
    ax.set_xticks(all_ns, [str(n) for n in all_ns])
    ax.minorticks_off()
    ax.set_xlabel("N")
    ax.set_ylabel("tiempo (s)")
    ax.grid(alpha=0.25, which="major")
    cross = crossing(tp3, tp4)
    if cross is not None:
        ax.axvline(cross, color="#555555", linestyle=":", linewidth=1.4)
        ax.text(cross, 0.03, f" ≈ {round(cross, -1):.0f}", transform=ax.get_xaxis_transform(),
                ha="left", va="bottom", fontsize=12, color="#555555")
    ax.legend(loc="upper left", fontsize=12)
    output = args.output.resolve(); output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"CreationDate": None})
    plt.close(fig)

    table_dir = args.table_dir.resolve()
    write_tables(table_dir, (("TP3", tp3), ("TP4", tp4)))
    print(f"F4 generada: {output}")
    print(f"Tablas: {table_dir / 'F4-tiempos.csv'} y {table_dir / 'F4-tiempos.md'}")
    print("Las medias no se cruzan en los N medidos (D7: extender las dos curvas)." if cross is None else
          f"Cruce de las medias (interpolación log-log entre N medidos): N ≈ {cross:.0f}")


if __name__ == "__main__":
    main()