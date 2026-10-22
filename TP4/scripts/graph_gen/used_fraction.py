"""Lectura de Nu(t) de las corridas del Sistema 2 (2.2 y 2.4): Fu(t), t90 y t100."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import statistics


@dataclass(frozen=True)
class UsedRun:
    path: Path
    n: int
    seed: int
    x0: float
    dt2: float
    times: list[float]
    used: list[int]
    status: str  # completa | t100 | divergio

    def fraction_on_grid(self, steps: int) -> list[float]:
        """Fu en t = k·dt2, k = 0..steps-1. Después de cortar en t100 Fu vale 1 (Nu no decrece y ya es N)."""
        if steps > len(self.used) and self.status != "t100":
            raise ValueError(f"{self.path}: termina en t={self.times[-1]} sin llegar a t100")
        return [self.used[k] / self.n if k < len(self.used) else 1.0 for k in range(steps)]

    def first_time(self, fraction: float) -> float | None:
        """Primer t de salida con Nu/N ≥ fraction; None si no se alcanza."""
        target = math.ceil(fraction * self.n - 1e-9)
        for time, used in zip(self.times, self.used):
            if used >= target:
                return time
        return None


def read_used_run(path: Path) -> UsedRun:
    metadata: dict[str, str] = {}
    times: list[float] = []
    used: list[int] = []
    status = "sin-pie"
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            values = dict(token.split("=", 1) for token in line[1:].split() if "=" in token)
            if "format" in values:
                metadata.update(values)
            if line.startswith("# fin "):
                status = values.get("estado", "desconocido")
            continue
        if line.startswith("t "):
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f"{path}: se esperaban 5 columnas y hay {len(fields)}")
        times.append(float(fields[0]))
        used.append(int(fields[4]))
    if status == "sin-pie":
        raise ValueError(f"{path}: la corrida no terminó (falta el pie '# fin')")
    if not times:
        raise ValueError(f"{path}: no contiene filas de datos")
    x0 = metadata.get("x0", "none")
    return UsedRun(path, int(metadata["N"]), int(metadata["seed"]), math.nan if x0 == "none" else float(x0),
                   float(metadata["dt2"]), times, used, status)


def load_case(directory: Path) -> list[UsedRun]:
    """Todas las semillas de un caso (carpeta con seed-*/observables.txt), validando que sean comparables."""
    runs = [read_used_run(p) for p in sorted(directory.glob("seed-*/observables.txt"))]
    if not runs:
        raise ValueError(f"no hay seed-*/observables.txt en {directory}")
    first = runs[0]
    for run in runs[1:]:
        if (run.n, run.x0, run.dt2) != (first.n, first.x0, first.dt2) and not (
                math.isnan(run.x0) and math.isnan(first.x0)):
            raise ValueError(f"{run.path} no es comparable con {first.path}")
    if len({run.seed for run in runs}) != len(runs):
        raise ValueError(f"semillas repetidas en {directory}")
    if any(run.status == "divergio" for run in runs):
        raise ValueError(f"hay corridas divergentes en {directory}")
    return runs


def mean_std(values: list[float]) -> tuple[float, float]:
    """Media y desvío estándar muestral (n − 1) entre realizaciones independientes (D10)."""
    if len(values) < 2:
        raise ValueError("se necesitan al menos 2 realizaciones para el desvío")
    return statistics.mean(values), statistics.stdev(values)
