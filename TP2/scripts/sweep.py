#!/usr/bin/env python3
"""Corre varias simulaciones de TP2 y deja listas las series de v_a para graficar.

Dos modos:

    # barrido en eta, con M corridas (semillas distintas) por valor
    python3 TP2/scripts/sweep.py eta --model=standard --n=400 --steps=5000 \
        --etas=0.1,0.5,1.0,2.0,3.0,5.0 --runs=3 --outdir=generated/sweep_eta

    # par de comparacion: misma condicion inicial, theta0 aleatorio vs. alineado
    python3 TP2/scripts/sweep.py theta0 --model=standard --n=400 --eta=1.0 --steps=5000 \
        --seedIC=1 --seedLoop=1 --outdir=generated/theta0_cmp

Cada corrida deja una trayectoria .txt (la del motor) y un .csv con la serie v_a(t).
Ademas se escribe un indice runs.csv que consume plot_va_vs_eta.py.

Las trayectorias .txt son grandes; con --no-keep-traj se borra cada una despues de
extraerle la serie de v_a (util para barridos largos, pero entonces no quedan archivos
para animar con animate.py).
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from order_parameter import va_series, write_va_csv
from simulation_io import SimulationFormatError


DEFAULT_JAR = Path(__file__).resolve().parents[1] / "target" / "tp2.jar"
BYTES_PER_PARTICLE_LINE = 65  # estimacion: "id x y theta" con doubles en precision completa
INDEX_COLUMNS = ["model", "n", "l", "eta", "theta0", "seedIC", "seedLoop", "steps",
                 "traj", "va_csv", "s_csv"]


@dataclass(frozen=True)
class Run:
    name: str
    eta: float
    theta0: str
    seed_ic: int
    seed_loop: int


def simulate(args, run: Run, outdir: Path) -> tuple[Path, Path]:
    """Corre el jar para una configuracion y devuelve (trayectoria, csv de v_a)."""
    # con --tmpdir la trayectoria se escribe en disco local: en WSL, escribir los ~70 MB de
    # cada corrida en /mnt/c cuesta 2.6x mas que en /tmp, y despues se borra igual
    traj_dir = args.tmpdir if (args.tmpdir is not None and not args.keep_traj) else outdir
    traj = traj_dir / f"{run.name}.txt"
    series_csv = outdir / f"{run.name}.csv"

    if args.skip_existing and series_csv.is_file():
        print(f"  {run.name}: ya existe, se saltea", flush=True)
        return traj, series_csv

    command = [
        args.java, "-jar", str(args.jar), "simulate",
        f"--model={args.model}",
        f"--n={args.n}",
        f"--eta={run.eta}",
        f"--steps={args.steps}",
        f"--seedIC={run.seed_ic}",
        f"--seedLoop={run.seed_loop}",
        f"--theta0={run.theta0}",
        f"--l={args.l}",
        f"--rc={args.rc}",
        f"--dt={args.dt}",
        f"--v0={args.v0}",
        f"--periodic={str(args.periodic).lower()}",
        f"--out={traj}",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"la simulacion {run.name} fallo (codigo {result.returncode}):\n"
            f"{result.stdout}{result.stderr}"
        )

    header, steps, values = va_series(traj)
    write_va_csv(series_csv, header, steps, values)
    print(f"  {run.name}: v_a(t=0)={values[0]:.4f} -> v_a(final)={values[-1]:.4f}",
          flush=True)

    if not args.keep_traj:
        traj.unlink()
    return traj, series_csv


def plan_runs(args) -> list[Run]:
    if args.mode == "eta":
        runs = []
        for eta in args.etas:
            for repetition in range(args.runs):
                seed = args.seed + repetition
                runs.append(Run(
                    name=f"eta{eta:g}_seed{seed}",
                    eta=eta,
                    theta0=args.theta0,
                    seed_ic=seed,
                    seed_loop=seed,
                ))
        return runs

    # modo theta0: las dos corridas comparten seedIC (misma condicion inicial de posiciones)
    # y seedLoop (mismo ruido), asi lo unico que cambia es el angulo inicial.
    return [
        Run(name="theta0_random", eta=args.eta, theta0="random",
            seed_ic=args.seedIC, seed_loop=args.seedLoop),
        Run(name="theta0_alineado", eta=args.eta, theta0=f"{args.aligned:g}",
            seed_ic=args.seedIC, seed_loop=args.seedLoop),
    ]


def estimated_megabytes(args, run_count: int) -> float:
    lines = run_count * (args.steps + 1) * args.n
    return lines * BYTES_PER_PARTICLE_LINE / (1024 * 1024)


def write_index(path: Path, rows: Sequence[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=INDEX_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in INDEX_COLUMNS})


def run_sweep(args) -> int:
    if not args.jar.is_file():
        print(f"Error: no existe el jar {args.jar}; compilar con 'mvn clean package' "
              f"desde la raiz del repo")
        return 1

    runs = plan_runs(args)
    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    if args.tmpdir is not None:
        args.tmpdir.mkdir(parents=True, exist_ok=True)

    size = estimated_megabytes(args, len(runs))
    print(f"{len(runs)} corridas de {args.steps} pasos con N={args.n} "
          f"(modelo {args.model}) -> {outdir}")
    if args.keep_traj:
        print(f"Espacio estimado en trayectorias: ~{size:.0f} MB "
              f"(usar --no-keep-traj para borrarlas al vuelo)")

    rows = []
    for index, run in enumerate(runs, start=1):
        print(f"[{index}/{len(runs)}] eta={run.eta:g} theta0={run.theta0} seed={run.seed_ic}",
              flush=True)
        traj, series_csv = simulate(args, run, outdir)
        rows.append({
            "model": args.model,
            "n": args.n,
            "l": args.l,
            "eta": run.eta,
            "theta0": run.theta0,
            "seedIC": run.seed_ic,
            "seedLoop": run.seed_loop,
            "steps": args.steps,
            "traj": traj.name if args.keep_traj else "",
            "va_csv": series_csv.name,
            "s_csv": "",
        })

    index_path = outdir / "runs.csv"
    write_index(index_path, rows)
    print(f"Indice escrito en {index_path.resolve()}")
    return 0


def run_clusters(args) -> int:
    """Re-simula las corridas de un indice y les calcula S con el comando `clusters` del jar.

    Hay que volver a simular porque S se calcula desde las posiciones y las trayectorias se
    borran despues de extraer v_a. Es reproducible al bit: las semillas estan en el indice.
    """
    if not args.jar.is_file():
        print(f"Error: no existe el jar {args.jar}; compilar con 'mvn clean package'")
        return 1

    index_path = args.index
    outdir = index_path.parent
    if args.tmpdir is not None:
        args.tmpdir.mkdir(parents=True, exist_ok=True)
    with index_path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        print(f"Error: {index_path} no tiene corridas")
        return 1

    print(f"{len(rows)} corridas de {index_path} -> S cada {args.stride} pasos")
    for index, row in enumerate(rows, start=1):
        name = Path(row["va_csv"]).stem
        s_csv = outdir / f"{name}_S.csv"
        row["s_csv"] = s_csv.name

        if args.skip_existing and s_csv.is_file():
            print(f"[{index}/{len(rows)}] {name}: ya existe, se saltea", flush=True)
            continue

        traj = (args.tmpdir or outdir) / f"{name}__tmp.txt"
        simulate_command = [
            args.java, "-jar", str(args.jar), "simulate",
            f"--model={row['model']}",
            f"--n={row['n']}",
            f"--eta={row['eta']}",
            f"--steps={row['steps']}",
            f"--seedIC={row['seedIC']}",
            f"--seedLoop={row['seedLoop']}",
            f"--theta0={row['theta0']}",
            f"--l={row['l']}",
            f"--rc={args.rc}",
            f"--dt={args.dt}",
            f"--v0={args.v0}",
            f"--periodic={str(args.periodic).lower()}",
            f"--out={traj}",
        ]
        clusters_command = [
            args.java, "-jar", str(args.jar), "clusters",
            f"--in={traj}", f"--out={s_csv}", f"--stride={args.stride}",
        ]
        try:
            for command in (simulate_command, clusters_command):
                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode != 0:
                    raise RuntimeError(f"{name} fallo (codigo {result.returncode}):\n"
                                       f"{result.stdout}{result.stderr}")
        finally:
            traj.unlink(missing_ok=True)

        _, _, values = read_s_csv(s_csv)
        print(f"[{index}/{len(rows)}] {name}: S(t=0)={values[0]:.4f} -> S(final)={values[-1]:.4f}",
              flush=True)

    write_index(index_path, rows)
    print(f"Indice actualizado con la columna s_csv: {index_path.resolve()}")
    return 0


def read_s_csv(path: Path) -> tuple[object, list[int], list[float]]:
    from order_parameter import read_series_csv
    header, steps, values, _ = read_series_csv(path)
    return header, steps, values


def comma_separated_floats(value: str) -> list[float]:
    try:
        values = [float(item) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"lista de numeros invalida: {value!r}") from exc
    if not values:
        raise argparse.ArgumentTypeError("la lista no puede estar vacia")
    return values


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", default="standard", choices=("standard", "voter"))
    parser.add_argument("--n", type=int, required=True, help="cantidad de particulas")
    parser.add_argument("--steps", type=int, required=True, help="pasos de tiempo")
    parser.add_argument("--outdir", type=Path, required=True, help="carpeta de salida")
    parser.add_argument("--l", type=float, default=10.0)
    parser.add_argument("--rc", type=float, default=1.0)
    parser.add_argument("--dt", type=float, default=1.0)
    parser.add_argument("--v0", type=float, default=0.03)
    parser.add_argument("--periodic", type=lambda v: v.lower() == "true", default=True)
    parser.add_argument("--jar", type=Path, default=DEFAULT_JAR)
    parser.add_argument("--java", default="java", help="ejecutable de Java (default: java)")
    parser.add_argument("--tmpdir", type=Path, default=None,
                        help="carpeta para las trayectorias temporales; conviene un disco "
                             "local (ej: /tmp) porque escribir en /mnt/c es ~2.6x mas lento. "
                             "Se ignora si se conservan las trayectorias")
    parser.add_argument("--no-keep-traj", dest="keep_traj", action="store_false",
                        help="borrar cada trayectoria .txt despues de calcular v_a")
    parser.add_argument("--skip-existing", action="store_true",
                        help="saltear las corridas que ya tengan su .csv (retomar un barrido)")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Corre simulaciones de TP2 y extrae las series de v_a."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    eta_parser = subparsers.add_parser("eta", help="barrido en el ruido eta")
    add_common_arguments(eta_parser)
    eta_parser.add_argument("--etas", type=comma_separated_floats, required=True,
                            help="valores de eta separados por coma, ej: 0.1,0.5,1.0")
    eta_parser.add_argument("--runs", type=int, default=3,
                            help="corridas (semillas) por cada eta (default: 3)")
    eta_parser.add_argument("--seed", type=int, default=1,
                            help="primera semilla; las repeticiones usan seed, seed+1, ...")
    eta_parser.add_argument("--theta0", default="random",
                            help="condicion inicial de angulos: 'random' o un angulo en radianes")

    theta_parser = subparsers.add_parser(
        "theta0", help="par de corridas con la misma condicion inicial y distinto theta0")
    add_common_arguments(theta_parser)
    theta_parser.add_argument("--eta", type=float, required=True)
    theta_parser.add_argument("--seedIC", type=int, default=1)
    theta_parser.add_argument("--seedLoop", type=int, default=1)
    theta_parser.add_argument("--aligned", type=float, default=0.0,
                              help="angulo comun de la corrida alineada, en radianes (default: 0)")

    clusters_parser = subparsers.add_parser(
        "clusters", help="re-simula las corridas de un indice y les calcula S")
    clusters_parser.add_argument("--index", type=Path, required=True,
                                 help="runs.csv de un barrido ya hecho")
    clusters_parser.add_argument("--stride", type=int, default=5,
                                 help="calcular S cada STRIDE pasos (default: 5)")
    clusters_parser.add_argument("--rc", type=float, default=1.0)
    clusters_parser.add_argument("--dt", type=float, default=1.0)
    clusters_parser.add_argument("--v0", type=float, default=0.03)
    clusters_parser.add_argument("--periodic", type=lambda v: v.lower() == "true", default=True)
    clusters_parser.add_argument("--jar", type=Path, default=DEFAULT_JAR)
    clusters_parser.add_argument("--java", default="java")
    clusters_parser.add_argument("--tmpdir", type=Path, default=None,
                                 help="carpeta para la trayectoria temporal (ej: /tmp)")
    clusters_parser.add_argument("--skip-existing", action="store_true",
                                 help="saltear las corridas que ya tengan su CSV de S")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        if args.mode == "clusters":
            return run_clusters(args)
        return run_sweep(args)
    except (OSError, RuntimeError, SimulationFormatError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
