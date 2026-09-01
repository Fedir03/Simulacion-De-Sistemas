#!/usr/bin/env python3
"""Parametro de orden (polarizacion) v_a de una corrida de Vicsek.

    v_a = (1 / (N v0)) |sum_i v_i| = (1 / N) |sum_i (cos θ_i, sin θ_i)|

Como todas las particulas se mueven con el mismo modulo de velocidad v0, ese factor se
cancela y v_a queda entre 0 (direcciones desordenadas) y 1 (todas alineadas).

Uso:
    python3 TP2/scripts/order_parameter.py corrida.txt             # imprime t,va
    python3 TP2/scripts/order_parameter.py corrida.txt --out=va.csv
"""

from __future__ import annotations

import argparse
import math
import statistics
import sys
from pathlib import Path
from typing import Iterable, Sequence

from simulation_io import (
    Frame,
    SimulationFormatError,
    SimulationHeader,
    parse_header,
    stream_simulation,
)


CSV_COMMENT = "#"


def va(frame: Frame) -> float:
    """Parametro de orden de un unico cuadro."""
    sum_x = math.fsum(math.cos(p.theta) for p in frame.particles)
    sum_y = math.fsum(math.sin(p.theta) for p in frame.particles)
    return math.hypot(sum_x, sum_y) / len(frame.particles)


def va_series(path: str | Path) -> tuple[SimulationHeader, list[int], list[float]]:
    """Calcula v_a(t) leyendo la corrida de a un cuadro por vez (no la carga entera)."""
    header, frames = stream_simulation(path)
    steps: list[int] = []
    values: list[float] = []
    for frame in frames:
        steps.append(frame.step)
        values.append(va(frame))
    return header, steps, values


def write_va_csv(path: str | Path, header: SimulationHeader, steps: Sequence[int],
                 values: Sequence[float]) -> None:
    """Guarda la serie con la cabecera de la corrida como comentario, para poder releerla."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(f"{CSV_COMMENT} {format_header(header)}\n")
        stream.write("t,va\n")
        for step, value in zip(steps, values):
            stream.write(f"{step},{value!r}\n")


def read_series_csv(path: str | Path) -> tuple[SimulationHeader, list[int], list[float], str]:
    """Lee un CSV de serie temporal de cualquier observable.

    El formato es el que escriben write_va_csv y el comando `clusters` del motor: la
    cabecera de la corrida como comentario, una linea `t,<observable>` y despues los datos.
    Devuelve tambien el nombre de la columna, para que los graficos se etiqueten solos.
    """
    input_path = Path(path)
    header: SimulationHeader | None = None
    column: str | None = None
    steps: list[int] = []
    values: list[float] = []
    with input_path.open("r", encoding="utf-8-sig") as stream:
        for line_number, raw in enumerate(stream, start=1):
            line = raw.strip()
            if not line:
                continue
            if line.startswith(CSV_COMMENT):
                if header is None:
                    header = parse_header(line.lstrip(CSV_COMMENT).strip())
                continue
            parts = line.split(",")
            if len(parts) != 2:
                raise SimulationFormatError(
                    f"{input_path}:{line_number}: se esperaban dos columnas 't,<observable>'"
                )
            if column is None and parts[0] == "t":
                column = parts[1]
                continue
            steps.append(int(parts[0]))
            values.append(float(parts[1]))
    if header is None:
        raise SimulationFormatError(
            f"{input_path}: falta la linea de cabecera '{CSV_COMMENT} model=... '"
        )
    if not steps:
        raise SimulationFormatError(f"{input_path}: no hay datos")
    return header, steps, values, column or "va"


def read_va_csv(path: str | Path) -> tuple[SimulationHeader, list[int], list[float]]:
    header, steps, values, _ = read_series_csv(path)
    return header, steps, values


def format_header(header: SimulationHeader) -> str:
    """Reconstruye la linea de cabecera del motor a partir de la cabecera parseada."""
    return " ".join([
        f"model={header.model}",
        f"N={header.n}",
        f"L={header.l}",
        f"rc={header.rc}",
        f"dt={header.dt}",
        f"v0={header.v0}",
        f"eta={header.eta}",
        f"periodic={str(header.periodic).lower()}",
        f"seedIC={header.seed_ic}",
        f"seedLoop={header.seed_loop}",
        f"theta0={header.theta0}",
    ])


def load_series(path: str | Path) -> tuple[SimulationHeader, list[int], list[float]]:
    """Acepta indistintamente una trayectoria .txt del motor o un .csv ya calculado."""
    return load_named_series(path)[:3]


def load_named_series(path: str | Path) -> tuple[SimulationHeader, list[int], list[float], str]:
    """Igual que load_series pero informando ademas que observable trae el archivo."""
    input_path = Path(path)
    if input_path.suffix.lower() == ".csv":
        return read_series_csv(input_path)
    header, steps, values = va_series(input_path)
    return header, steps, values, "va"


def resolve_transient(spec: str | int, last_step: int) -> int:
    """Convierte un transitorio en pasos.

    Acepta un entero (pasos absolutos) o un porcentaje del largo del run ('40%'). El
    porcentaje sirve para comparar corridas de distinto largo con el mismo criterio
    relativo: 40% son 1200 pasos en un run de 3000 y 4000 en uno de 10000.
    """
    if isinstance(spec, int):
        return spec
    text = str(spec).strip()
    if text.endswith("%"):
        fraction = float(text[:-1]) / 100.0
        if not 0.0 <= fraction < 1.0:
            raise ValueError(f"el porcentaje de transitorio debe estar en [0, 100): {spec}")
        return int(fraction * last_step)
    return int(text)


def tail_stats(steps: Sequence[int], values: Sequence[float],
               transient: int = 0) -> tuple[float, float]:
    """Media y desvio de v_a sobre la cola estacionaria (pasos con t >= transient).

    El transitorio se elige a ojo mirando v_a(t): ver la seccion correspondiente del
    README de TP2.
    """
    tail = [value for step, value in zip(steps, values) if step >= transient]
    if not tail:
        raise ValueError(
            f"no quedan pasos con t >= {transient} (la corrida llega hasta t={steps[-1]})"
        )
    if len(tail) == 1:
        return tail[0], 0.0
    return statistics.fmean(tail), statistics.stdev(tail)


def mean_and_stdev(values: Iterable[float]) -> tuple[float, float]:
    """Media y desvio muestral (M-1) entre corridas; con una sola corrida el desvio es 0."""
    data = list(values)
    if not data:
        raise ValueError("no hay valores para promediar")
    if len(data) == 1:
        return data[0], 0.0
    return statistics.fmean(data), statistics.stdev(data)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calcula el parametro de orden v_a(t) de una corrida de TP2."
    )
    parser.add_argument("input", type=Path, help="archivo .txt producido por el motor")
    parser.add_argument(
        "--out", type=Path, default=None,
        help="archivo CSV de salida; sin este flag imprime por pantalla",
    )
    parser.add_argument(
        "--transient", type=int, default=None,
        help="si se indica, ademas reporta media y desvio de v_a para t >= TRANSIENT",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        header, steps, values = load_series(args.input)
        if args.out is not None:
            write_va_csv(args.out, header, steps, values)
        else:
            print("t,va")
            for step, value in zip(steps, values):
                print(f"{step},{value:.6f}")
        if args.transient is not None:
            mean, stdev = tail_stats(steps, values, args.transient)
            print(
                f"v_a promedio (t >= {args.transient}): {mean:.6f} +/- {stdev:.6f}",
                file=sys.stderr,
            )
    except (OSError, SimulationFormatError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.out is not None:
        print(f"Serie de v_a guardada en {args.out.resolve()} ({len(steps)} pasos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
