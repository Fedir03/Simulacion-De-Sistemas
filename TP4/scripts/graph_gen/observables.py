"""Lectura y validación compartida de los observables del estudio 2.1.a."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math


@dataclass(frozen=True)
class Run:
    path: Path
    metadata: dict[str, str]
    times: list[float]
    total_energy: list[float]
    status: str

    @property
    def dt(self) -> float:
        return float(self.metadata["dt"])

    @property
    def relative_error(self) -> list[float]:
        e0 = self.total_energy[0]
        if e0 == 0:
            raise ValueError(f"{self.path}: E(0) es cero")
        return [(energy - e0) / e0 for energy in self.total_energy]

    @property
    def epsilon(self) -> float:
        return max(abs(value) for value in self.relative_error)


def _key_values(line: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for token in line.removeprefix("#").strip().split():
        if "=" in token:
            key, value = token.split("=", 1)
            result[key] = value
    return result


def read_run(path: Path) -> Run:
    metadata: dict[str, str] = {}
    times: list[float] = []
    energies: list[float] = []
    status = "sin-pie"

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ValueError(f"no se pudo leer {path}: {error}") from error

    for line_number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            values = _key_values(line)
            if "format" in values:
                metadata.update(values)
            if line.startswith("# fin "):
                status = values.get("estado", "desconocido")
            continue
        if line.startswith("t "):
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f"{path}:{line_number}: se esperaban 5 columnas y hay {len(fields)}")
        try:
            time, total = float(fields[0]), float(fields[1])
        except ValueError as error:
            raise ValueError(f"{path}:{line_number}: t o E_tot inválidos") from error
        if not math.isfinite(time) or not math.isfinite(total):
            raise ValueError(f"{path}:{line_number}: t o E_tot no finitos")
        times.append(time)
        energies.append(total)

    missing = {"N", "seed", "x0", "dt", "dt2", "tf"} - metadata.keys()
    if missing:
        raise ValueError(f"{path}: faltan metadatos: {', '.join(sorted(missing))}")
    if not times:
        raise ValueError(f"{path}: no contiene filas de datos")
    if any(right <= left for left, right in zip(times, times[1:])):
        raise ValueError(f"{path}: los tiempos no son estrictamente crecientes")
    return Run(path, metadata, times, energies, status)


def load_study(directory: Path) -> list[Run]:
    paths = sorted(directory.glob("dt-*/observables.txt"))
    if not paths:
        raise ValueError(f"no se encontraron archivos dt-*/observables.txt en {directory}")
    runs = sorted((read_run(path) for path in paths), key=lambda run: run.dt, reverse=True)
    if len({run.dt for run in runs}) != len(runs):
        raise ValueError("hay valores de dt repetidos")

    reference = runs[0].metadata
    for run in runs[1:]:
        for key in ("N", "seed", "x0", "dt2", "tf"):
            if run.metadata[key] != reference[key]:
                raise ValueError(
                    f"las corridas no son comparables: {key}={reference[key]} en "
                    f"{runs[0].path}, pero {key}={run.metadata[key]} en {run.path}"
                )
    return runs


def configure_matplotlib():
    try:
        import matplotlib
    except ModuleNotFoundError as error:
        raise SystemExit(
            "Falta matplotlib. Activá el entorno virtual e instalalo con "
            "'python -m pip install matplotlib'."
        ) from error
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.size": 14,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
        }
    )
    return plt
