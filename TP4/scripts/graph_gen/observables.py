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
    footer: dict[str, str] = {}

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
                footer = values
            continue
        if line.startswith("t "):
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f"{path}:{line_number}: se esperaban 5 columnas y hay {len(fields)}")
        try:
            time, total, kinetic, elastic, used = map(float, fields)
        except ValueError as error:
            raise ValueError(f"{path}:{line_number}: t o E_tot inválidos") from error
        if not all(math.isfinite(value) for value in (time, total, kinetic, elastic, used)):
            raise ValueError(f"{path}:{line_number}: valores no finitos")
        if kinetic < 0 or elastic < 0 or not math.isclose(total, kinetic + elastic, rel_tol=1e-12, abs_tol=1e-14):
            raise ValueError(f"{path}:{line_number}: energía inconsistente")
        if used < 0 or not used.is_integer() or used > int(metadata.get("N", 0)):
            raise ValueError(f"{path}:{line_number}: Nu inválido")
        if metadata.get("x0") == "none" and used != 0:
            raise ValueError(f"{path}:{line_number}: Nu debe ser cero sin obstáculos")
        times.append(time)
        energies.append(total)

    missing = {"N", "seed", "x0", "dt", "dt2", "tf"} - metadata.keys()
    if missing:
        raise ValueError(f"{path}: faltan metadatos: {', '.join(sorted(missing))}")
    if not times:
        raise ValueError(f"{path}: no contiene filas de datos")
    if any(right <= left for left, right in zip(times, times[1:])):
        raise ValueError(f"{path}: los tiempos no son estrictamente crecientes")
    if status not in {"completa", "divergio"}:
        raise ValueError(f"{path}: corrida sin terminar o estado no válido para 2.1.a: {status}")
    dt, dt2, tf = (float(metadata[key]) for key in ("dt", "dt2", "tf"))
    if not all(math.isfinite(value) and value > 0 for value in (dt, dt2, tf)):
        raise ValueError(f"{path}: pasos o duración inválidos")
    if any(not math.isclose(time, index * dt2, rel_tol=0, abs_tol=1e-9)
           for index, time in enumerate(times)):
        raise ValueError(f"{path}: faltan muestras o no respetan dt2 desde t=0")
    if energies[0] <= 0:
        raise ValueError(f"{path}: E(0) debe ser positiva")
    try:
        end, steps = float(footer["t"]), int(footer["pasos"])
    except (KeyError, ValueError) as error:
        raise ValueError(f"{path}: pie inválido") from error
    if not math.isfinite(end) or not math.isclose(end, steps * dt, abs_tol=1e-9):
        raise ValueError(f"{path}: tiempo final incompatible con los pasos")
    if status == "completa" and (not math.isclose(times[-1], tf, abs_tol=1e-9)
                                  or not math.isclose(end, tf, abs_tol=1e-9)):
        raise ValueError(f"{path}: corrida completa que no llega a tf")
    if status == "divergio" and not times[-1] < end <= tf:
        raise ValueError(f"{path}: instante de divergencia inconsistente")
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
        for key in ("N", "seed", "x0", "dt2", "tf", "R", "r", "m", "k", "v0"):
            if run.metadata.get(key) != reference.get(key):
                raise ValueError(
                    f"las corridas no son comparables: {key}={reference.get(key)} en "
                    f"{runs[0].path}, pero {key}={run.metadata.get(key)} en {run.path}"
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
