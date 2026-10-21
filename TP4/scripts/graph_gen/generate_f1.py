#!/usr/bin/env python3
"""Genera F1: ECM frente a dt para los cuatro integradores del Sistema 1."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import math

from observables import configure_matplotlib


TP4_DIR = Path(__file__).resolve().parents[2]
SCHEMES = {
    "beeman": ("Beeman", "#0072B2", "o"),
    "verlet": ("Verlet original", "#D55E00", "s"),
    "velocity_verlet": ("Velocity Verlet", "#009E73", "D"),
    "euler_pc": ("Euler predictor-corrector", "#CC79A7", "^"),
}


def read_ecm(path: Path) -> dict[str, list[tuple[float, float]]]:
    series: dict[str, list[tuple[float, float]]] = defaultdict(list)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ValueError(f"no se pudo leer {path}: {error}") from error

    for line_number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("scheme "):
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f"{path}:{line_number}: se esperaban 5 columnas y hay {len(fields)}")
        scheme = fields[0]
        if scheme not in SCHEMES:
            raise ValueError(f"{path}:{line_number}: esquema desconocido: {scheme}")
        try:
            dt, steps, ecm = float(fields[1]), int(fields[2]), float(fields[3])
        except ValueError as error:
            raise ValueError(f"{path}:{line_number}: dt, steps o ecm inválidos") from error
        if not all(math.isfinite(value) and value > 0 for value in (dt, ecm)) or steps < 1:
            raise ValueError(f"{path}:{line_number}: dt, steps y ecm deben ser positivos y finitos")
        series[scheme].append((dt, ecm))

    missing = set(SCHEMES) - series.keys()
    if missing:
        raise ValueError(f"faltan esquemas: {', '.join(sorted(missing))}")
    extra = set(series) - set(SCHEMES)
    if extra:
        raise ValueError(f"sobran esquemas: {', '.join(sorted(extra))}")

    reference_dts: list[float] | None = None
    for scheme in SCHEMES:
        points = sorted(series[scheme])
        if len(points) != 13:
            raise ValueError(f"{scheme}: se esperaban 13 valores de dt y hay {len(points)}")
        dts = [point[0] for point in points]
        if len(set(dts)) != len(dts):
            raise ValueError(f"{scheme}: hay valores de dt repetidos")
        if reference_dts is not None and dts != reference_dts:
            raise ValueError("los cuatro esquemas no tienen exactamente los mismos valores de dt")
        reference_dts = dts
        series[scheme] = points
    return dict(series)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=TP4_DIR / "outputs" / "sistema1" / "ecm" / "ecm-dt-sweep.txt",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=TP4_DIR / "presentacion" / "figuras" / "F1-ecm-vs-dt.pdf",
    )
    args = parser.parse_args()

    try:
        series = read_ecm(args.input.resolve())
    except ValueError as error:
        parser.error(str(error))

    plt = configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.0, 4.4), layout="constrained")
    for scheme, (label, color, marker) in SCHEMES.items():
        points = series[scheme]
        ax.loglog(
            [point[0] for point in points],
            [point[1] for point in points],
            marker=marker,
            markersize=5,
            linewidth=1.8,
            color=color,
            label=label,
        )

    ax.set_xlabel(r"$\Delta t$ (s)")
    ax.set_ylabel(r"ECM (m$^2$)")
    ax.grid(alpha=0.25, which="both")
    ax.legend(loc="upper left", fontsize=10)

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"CreationDate": None})
    plt.close(fig)
    print(f"F1 generada: {output}")


if __name__ == "__main__":
    main()
