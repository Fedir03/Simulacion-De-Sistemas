#!/usr/bin/env python3
"""Genera F9: Fu(tf) en función de la densidad (2.4) a partir de los observables de 2.1.b, con barras de ±σ entre semillas.

Con tf = 30 s no todos los N llegan a Fu = 0,9 y ninguno a 1, así que se grafica Fu(tf) (D14). ⟨t90⟩ va en la tabla
solo para los N en que llegan todas las semillas (misma regla que F6); t100 se omite.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from observables import configure_matplotlib
from used_fraction import UsedRun, mean_std, read_used_run


TP4_DIR = Path(__file__).resolve().parents[2]
R, r = 0.51, 0.0175
HEADER = ("N", "rho_1/m2", "phi", "realizaciones", "Fu_tf_media", "Fu_tf_desvio",
          "llegan_a_0.9", "t90_media_s", "t90_desvio_s", "llegan_a_1")


def density(n: float) -> float:
    """ρ = N/(πR²) en 1/m² (D20)."""
    return n / (math.pi * R * R)


def load_runs(directory: Path) -> dict[int, list[UsedRun]]:
    """Corridas por N desde runs/n{N}_s{semilla}/observables.txt, validando que sean comparables."""
    by_n: dict[int, list[UsedRun]] = {}
    for path in sorted(directory.glob("n*_s*/observables.txt")):
        run = read_used_run(path)
        if path.parent.name != f"n{run.n}_s{run.seed}":
            raise ValueError(f"{path}: la carpeta no coincide con N={run.n}, semilla={run.seed}")
        if run.status != "completa":
            raise ValueError(f"{path}: estado {run.status}, se esperaba completa")
        by_n.setdefault(run.n, []).append(run)
    if not by_n:
        raise ValueError(f"no hay n*_s*/observables.txt en {directory}")
    first = next(iter(by_n.values()))[0]
    for runs in by_n.values():
        for run in runs:
            if (run.x0, run.dt2, run.times[-1]) != (first.x0, first.dt2, first.times[-1]):
                raise ValueError(f"{run.path} no es comparable con {first.path}")
    return dict(sorted(by_n.items()))


def check_runs_csv(path: Path, by_n: dict[int, list[UsedRun]]) -> None:
    """Control cruzado: el último Nu de cada observables.txt es el used_final de runs.csv, sin corridas de más ni de menos."""
    with path.open(newline="", encoding="utf-8") as source:
        expected = {(int(row["n"]), int(row["seed"])): int(row["used_final"]) for row in csv.DictReader(source)}
    found = {(run.n, run.seed): run.used[-1] for runs in by_n.values() for run in runs}
    if found != expected:
        raise ValueError(f"los observables no coinciden con {path} (corridas o used_final distintos)")


def write_tables(directory: Path, rows, tf: float) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "F9-2.4.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(HEADER); writer.writerows(rows)

    def number(value: float, digits: int) -> str:
        return "—" if math.isnan(value) else f"{value:.{digits}f}".replace(".", ",")

    lines = [f"| N | ρ (1/m²) | φ | Realizaciones | Fu({tf:g} s) | Llegan a 0,9 | t90 (s) | Llegan a 1 |",
             "|---|---|---|---|---|---|---|---|"]
    for n, rho, phi, count, fu, fu_std, reached, t90, t90_std, full in rows:
        t90_text = "—" if math.isnan(t90) else f"{number(t90, 2)} ± {number(t90_std, 2)}"
        lines.append(f"| {n} | {number(rho, 1)} | {number(phi, 3)} | {count} | {number(fu, 3)} ± {number(fu_std, 3)} "
                     f"| {reached} | {t90_text} | {full} |")
    (directory / "F9-2.4.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=TP4_DIR / "outputs" / "runtime_tp4_obs",
                        help="carpeta de la tanda de 2.1.b (runs.csv y runs/n{N}_s{semilla}/)")
    parser.add_argument("--output", type=Path, default=TP4_DIR / "presentacion" / "figuras" / "F9-fu-vs-densidad.pdf")
    parser.add_argument("--table-dir", type=Path, default=TP4_DIR / "outputs" / "runtime_tp4_analisis",
                        help="carpeta de F9-2.4.csv y F9-2.4.md")
    args = parser.parse_args()
    try:
        by_n = load_runs(args.input / "runs")
        check_runs_csv(args.input / "runs.csv", by_n)
    except (OSError, KeyError, ValueError) as error:
        parser.error(str(error))

    rows = []
    for n, runs in by_n.items():
        if len({run.seed for run in runs}) != len(runs):
            parser.error(f"semillas repetidas en N={n}")
        fu_mean, fu_std = mean_std([run.used[-1] / n for run in runs])
        reached = [t for t in (run.first_time(0.9) for run in runs) if t is not None]
        # D14: si alguna semilla no llega a 0,9 no se promedia un t90 parcial
        t90_mean, t90_std = mean_std(reached) if len(reached) == len(runs) else (math.nan, math.nan)
        full = sum(run.first_time(1.0) is not None for run in runs)
        rows.append((n, density(n), n * r * r / (R * R), len(runs), fu_mean, fu_std,
                     len(reached), t90_mean, t90_std, full))
    tf = next(iter(by_n.values()))[0].times[-1]

    plt = configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.0, 4.4), layout="constrained")
    ax.errorbar([row[1] for row in rows], [row[4] for row in rows], yerr=[row[5] for row in rows], fmt="o-",
                color="#0072B2", markersize=7, linewidth=2, capsize=4, elinewidth=1.4)
    ax.axhline(0.9, color="#555555", linestyle="--", linewidth=1.2)
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0])
    ax.set_xlabel("ρ (1/m²)")
    ax.set_ylabel(f"Fu({tf:g} s)")
    # φ = N r²/R² = ρ π r² (D20), como escala secundaria
    top = ax.secondary_xaxis("top", functions=(lambda rho: rho * math.pi * r * r, lambda phi: phi / (math.pi * r * r)))
    top.set_xlabel("φ")
    ax.grid(alpha=0.22)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"CreationDate": None})
    plt.close(fig)

    table_dir = args.table_dir.resolve()
    write_tables(table_dir, rows, tf)
    print(f"F9 generada: {output}")
    print(f"Tablas: {table_dir / 'F9-2.4.csv'} y {table_dir / 'F9-2.4.md'}")
    print(f"Llegan todas a Fu = 0,9 (t90 en la tabla): N = {[row[0] for row in rows if row[6] == row[3]]}")
    print(f"Corridas que llegan a Fu = 1: {sum(row[9] for row in rows)} (D14: t100 se omite)")


if __name__ == "__main__":
    main()
