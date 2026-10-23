#!/usr/bin/env python3
"""Genera F10 (2.4.b): mapas x0 × N de ⟨t90⟩ y ⟨Fu(tf)⟩ (D22) y su tabla, con una fila por (x0, N).

- Columnas: x0 de la grilla de D13 (categórico). Filas: N = 100…600 y N máx (714 en x0 = r y R−r, 713 en los
  interiores, rotulado arriba de cada columna). A la derecha, ρ y φ de cada fila (D20; la fila de N máx usa 714).
- Panel 1: ⟨t90⟩ solo si llegan las 3 semillas; si no, gris con "k/3" en las parciales y "—" si no llega ninguna
  (D14). Panel 2: ⟨Fu(tf)⟩ en todas las celdas, curva de nivel Fu = 0,9 (interpolada entre centros de celda) y un
  punto en el x0 de máximo Fu de cada fila.
- x0 = r sale de runtime_tp4_obs (semillas 1–3, según "reused" de meta.json del barrido); el resto, del barrido.
Se niega a graficar si falta alguna corrida. Los tiempos de ejecución no se usan.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

from observables import configure_matplotlib
from used_fraction import UsedRun, mean_std, read_used_run


TP4_DIR = Path(__file__).resolve().parents[2]
OUTPUTS = TP4_DIR / "outputs"
R, r = 0.51, 0.0175
X0S = (0.0175, 0.06, 0.12, 0.18, 0.24, 0.30, 0.36, 0.43, 0.4925)  # D13
NS = (100, 200, 300, 400, 500, 600)  # más el N máx de cada columna (D22)
SEEDS = (1, 2, 3)
X0_LABELS = ("0.0175", "0.06", "0.12", "0.18", "0.24", "0.30", "0.36", "0.43", "0.4925")  # como en D13, con el 0 final
GRAY = "#BDBDBD"
HEADER = ("x0", "N", "fuente", "rho_1/m2", "phi", "realizaciones", "Fu_tf_media", "Fu_tf_desvio",
          "llegan_a_0.9", "t90_media_s", "t90_desvio_s", "llegan_a_1")


def n_max(col: int) -> int:
    """N máx de la grilla de D5 con el obstáculo en X0S[col] (D6, D22): 714 en r y R−r, 713 en los x0 interiores."""
    return 714 if col in (0, len(X0S) - 1) else 713


def column(x0: float) -> int:
    """Índice de x0 en la grilla de D13."""
    for index, value in enumerate(X0S):
        if math.isclose(x0, value, rel_tol=0, abs_tol=1e-9):
            return index
    raise ValueError(f"x0={x0} no está en la grilla de D13")


def expected_keys() -> set[tuple[int, int, int]]:
    """(columna de x0, N, semilla) de las 189 corridas de D22."""
    return {(col, n, seed) for col in range(len(X0S)) for n in NS + (n_max(col),) for seed in SEEDS}


def read_final_nu(path: Path, nu_column: str, x0: float | None = None) -> dict[tuple[int, int, int], int]:
    """Nu final por (columna de x0, N, semilla) desde runs.csv de obs (x0 fijo) o progress.csv del barrido.
    Solo se leen x0, n, seed, status y la columna de Nu; una corrida repetida tiene que repetir el valor."""
    result: dict[tuple[int, int, int], int] = {}
    with path.open(newline="", encoding="utf-8") as source:
        for line, row in enumerate(csv.DictReader(source), start=2):
            if row["status"] not in ("completa", "completed"):
                raise ValueError(f"{path}:{line}: estado {row['status']!r}")
            key = (column(x0 if x0 is not None else float(row["x0"])), int(row["n"]), int(row["seed"]))
            if result.setdefault(key, int(row[nu_column])) != int(row[nu_column]):
                raise ValueError(f"{path}:{line}: Nu final distinto para la misma corrida")
    return result


def load_runs(barrido: Path, obs: Path) -> dict[tuple[int, int, int], UsedRun]:
    """Las 189 corridas por (columna de x0, N, semilla), validadas; falla si el barrido no terminó."""
    reused = json.loads((barrido / "meta.json").read_text(encoding="utf-8"))["reused"]
    if column(reused["x0"]) != 0 or sorted(reused["ns"]) != list(NS) + [n_max(0)]:
        raise ValueError(f"{barrido / 'meta.json'}: 'reused' no coincide con D22")
    pending = sorted(barrido.glob("runs/x0-*/*.err"))
    if pending:
        raise ValueError(f"el barrido no terminó o tuvo errores: {len(pending)} archivos .err (p. ej. {pending[0]})")

    paths = {(0, n, seed): obs / "runs" / f"n{n}_s{seed}" / "observables.txt" for n in reused["ns"] for seed in SEEDS}
    for path in sorted(barrido.glob("runs/x0-*/n*_s*/observables.txt")):
        col = column(float(path.parent.parent.name.removeprefix("x0-")))
        n, seed = (int(part) for part in path.parent.name.removeprefix("n").split("_s"))
        if col == 0 or (col, n, seed) in paths:
            raise ValueError(f"{path}: corrida de más o repetida")
        paths[(col, n, seed)] = path
    missing, extra = sorted(expected_keys() - paths.keys()), sorted(paths.keys() - expected_keys())
    if missing or extra:
        raise ValueError(f"faltan {len(missing)} corridas (p. ej. {missing[:3]}) y sobran {len(extra)} {extra[:3]}")

    runs: dict[tuple[int, int, int], UsedRun] = {}
    for key, path in paths.items():
        run = read_used_run(path)
        if (column(run.x0), run.n, run.seed) != key:
            raise ValueError(f"{path}: el encabezado no coincide con la carpeta")
        if run.status != "completa":
            raise ValueError(f"{path}: estado {run.status}, se esperaba completa")
        runs[key] = run
    first = runs[(0, NS[0], SEEDS[0])]
    for run in runs.values():
        if (run.dt2, run.times[-1]) != (first.dt2, first.times[-1]):
            raise ValueError(f"{run.path}: dt2 o tf distintos de {first.path}")

    # Control cruzado del último Nu: barrido contra progress.csv, x0 = r contra runs.csv de obs (semillas 1–3)
    found = {key: run.used[-1] for key, run in runs.items()}
    expected = read_final_nu(barrido / "progress.csv", "nu_final")
    expected.update({key: value for key, value in read_final_nu(obs / "runs.csv", "used_final", x0=X0S[0]).items()
                     if key in found})
    if expected != found:
        bad = sorted(key for key in found.keys() | expected.keys() if found.get(key) != expected.get(key))
        raise ValueError(f"el último Nu no coincide con progress.csv/runs.csv en {len(bad)} corridas (p. ej. {bad[:3]})")
    return runs


def summarize(runs: dict[tuple[int, int, int], UsedRun]) -> list[tuple]:
    rows = []
    for col, x0 in enumerate(X0S):
        for n in NS + (n_max(col),):
            group = [runs[(col, n, seed)] for seed in SEEDS]
            fu_mean, fu_std = mean_std([run.used[-1] / n for run in group])
            reached = [t for t in (run.first_time(0.9) for run in group) if t is not None]
            # D14: ⟨t90⟩ solo si llegan las 3 semillas
            t90_mean, t90_std = mean_std(reached) if len(reached) == len(group) else (math.nan, math.nan)
            full = sum(run.first_time(1.0) is not None for run in group)
            rows.append((x0, n, "obs" if col == 0 else "barrido", n / (math.pi * R * R), n * r * r / (R * R),
                         len(group), fu_mean, fu_std, len(reached), t90_mean, t90_std, full))
    return rows


def write_tables(directory: Path, rows, tf: float) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "F10-2.4b.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(HEADER); writer.writerows(rows)

    def number(value: float, digits: int) -> str:
        return "—" if math.isnan(value) else f"{value:.{digits}f}".replace(".", ",")

    lines = [f"| x0 (m) | N | Fuente | ρ (1/m²) | φ | Realizaciones | Fu({tf:g} s) | Llegan a 0,9 | t90 (s) | Llegan a 1 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for x0, n, source, rho, phi, count, fu, fu_std, reached, t90, t90_std, full in rows:
        t90_text = "—" if math.isnan(t90) else f"{number(t90, 2)} ± {number(t90_std, 2)}"
        lines.append(f"| {number(x0, 4)} | {n} | {source} | {number(rho, 1)} | {number(phi, 3)} | {count} "
                     f"| {number(fu, 3)} ± {number(fu_std, 3)} | {reached}/{count} | {t90_text} | {full} |")
    (directory / "F10-2.4b.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def draw(ax, plt, grid, labels: dict[tuple[int, int], str]):
    """Mapa de una magnitud por celda; NaN en gris, con el texto de cada celda en blanco o negro según el fondo.
    El texto lleva un recuadro del color de su celda, así la curva de nivel pasa por detrás de los números."""
    cmap = plt.get_cmap("viridis").copy()
    cmap.set_bad(GRAY)
    image = ax.imshow(np.ma.masked_invalid(grid), cmap=cmap, origin="lower", aspect="auto")
    for (i, j), text in labels.items():
        background = GRAY if math.isnan(grid[i, j]) else image.cmap(image.norm(grid[i, j]))
        dark = not math.isnan(grid[i, j]) and sum(background[:3]) < 1.5
        ax.text(j, i, text, ha="center", va="center", fontsize=9, color="white" if dark else "black", zorder=4,
                bbox=dict(boxstyle="square,pad=0.1", facecolor=background, edgecolor="none"))
    return image


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--barrido", type=Path, default=OUTPUTS / "runtime_tp4_barrido")
    parser.add_argument("--obs", type=Path, default=OUTPUTS / "runtime_tp4_obs", help="fuente de x0 = r (D22)")
    parser.add_argument("--output", type=Path, default=TP4_DIR / "presentacion" / "figuras" / "F10-mapa-x0-n.pdf")
    parser.add_argument("--table-dir", type=Path, default=OUTPUTS / "runtime_tp4_analisis",
                        help="carpeta de F10-2.4b.csv y F10-2.4b.md")
    args = parser.parse_args()
    try:
        runs = load_runs(args.barrido.resolve(), args.obs.resolve())
    except (OSError, KeyError, ValueError) as error:
        parser.error(str(error))
    rows = summarize(runs)
    tf = next(iter(runs.values())).times[-1]

    shape = (len(NS) + 1, len(X0S))
    t90, fu = np.full(shape, np.nan), np.full(shape, np.nan)
    t90_text, fu_text = {}, {}
    for x0, n, _, _, _, count, fu_mean, _, reached, t90_mean, _, _ in rows:
        cell = (NS.index(n) if n in NS else len(NS), column(x0))
        fu[cell], t90[cell] = fu_mean, t90_mean
        fu_text[cell] = f"{fu_mean:.2f}"
        # D14: valor si llegan 3/3, "k/3" en las parciales, "—" si no llega ninguna
        t90_text[cell] = f"{t90_mean:.1f}" if reached == count else f"{reached}/{count}" if reached else "—"

    plt = configure_matplotlib()
    fig, (left, right) = plt.subplots(1, 2, figsize=(14.0, 5.8), sharey=True, layout="constrained")
    for ax, grid, labels, label in ((left, t90, t90_text, "t90 (s)"), (right, fu, fu_text, f"Fu({tf:g} s)")):
        image = draw(ax, plt, grid, labels)
        if not np.isnan(grid).all():
            fig.colorbar(image, ax=ax, location="bottom", shrink=0.8, label=label)
        ax.set_xticks(range(len(X0S)), X0_LABELS)
        ax.set_xlabel("x₀ (m)")
        top = ax.secondary_xaxis("top")
        top.set_xticks(range(len(X0S)), [str(n_max(col)) for col in range(len(X0S))])
        top.set_xlabel("N máx")
    right.contour(range(shape[1]), range(shape[0]), fu, levels=[0.9], colors="black", linestyles="--", linewidths=1.6,
                  zorder=3)
    for i in range(shape[0]):
        j = int(np.argmax(fu[i]))  # primer x0 de máximo Fu de la fila
        # a la izquierda del número, para no tocar el borde en la fila de N máx
        right.plot(j - 0.36, i, "o", markersize=5, markerfacecolor="white", markeredgecolor="black", zorder=5)
    left.set_yticks(range(shape[0]), [str(n) for n in NS] + ["N máx"])
    left.set_ylabel("N")
    row_ns = NS + (n_max(0),)  # la fila de N máx usa 714 (D22: 0,14 % con 713, va en el caption)
    rho = right.secondary_yaxis("right")
    rho.set_yticks(range(shape[0]), [f"{n / (math.pi * R * R):.0f}" for n in row_ns])
    rho.set_ylabel("ρ (1/m²)")
    phi = right.secondary_yaxis(1.22)
    phi.set_yticks(range(shape[0]), [f"{n * r * r / (R * R):.2f}" for n in row_ns])
    phi.set_ylabel("φ")
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"CreationDate": None})
    plt.close(fig)

    table_dir = args.table_dir.resolve()
    write_tables(table_dir, rows, tf)
    ties = [NS[i] if i < len(NS) else "N máx" for i in range(shape[0]) if (fu[i] == fu[i].max()).sum() > 1]
    print(f"F10 generada: {output}")
    print(f"Tablas: {table_dir / 'F10-2.4b.csv'} y {table_dir / 'F10-2.4b.md'}")
    print(f"Celdas con ⟨t90⟩ (3/3): {sum(row[8] == row[5] for row in rows)} de {len(rows)}")
    print("Curva Fu = 0,9: " + ("ninguna celda llega" if np.nanmax(fu) < 0.9 else "dibujada"))
    if ties:
        print(f"Empate en el máximo de Fu (se marca el primer x0): filas {ties}")


if __name__ == "__main__":
    main()
