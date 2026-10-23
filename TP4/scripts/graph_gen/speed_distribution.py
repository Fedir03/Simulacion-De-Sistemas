"""Rapideces |v| de dynamic.txt (2.3) y su distribución de probabilidad f(v) (Teórica 0: y_i = N_i / (Δv·N))."""

from __future__ import annotations

from pathlib import Path
import bisect
import math


def read_speeds(path: Path, times: set[float] | None = None, tol: float = 1e-6) -> dict[float, list[float]]:
    """{t: [|v| de cada partícula]} para los cuadros de dynamic.txt (todos, o solo los de `times`)."""
    frames: dict[float, list[float]] = {}
    current: list[float] | None = None
    wanted = sorted(times) if times is not None else None
    with path.open(encoding="utf-8") as source:
        for raw in source:
            if raw.startswith("#"):
                continue
            if raw.startswith("t="):
                t = float(raw.split()[0][2:])
                keep = wanted is None or any(abs(t - w) < tol for w in wanted)
                current = frames.setdefault(t, []) if keep else None
                continue
            if current is not None:
                fields = raw.split()
                current.append(math.hypot(float(fields[3]), float(fields[4])))
    if wanted is not None:
        missing = [w for w in wanted if not any(abs(t - w) < tol for t in frames)]
        if missing:
            raise ValueError(f"{path}: no hay cuadros en t = {missing} (las salidas son múltiplos de dt2)")
    return frames


def load_runs(directory: Path, times: set[float] | None = None) -> list[dict[float, list[float]]]:
    paths = sorted(directory.glob("seed-*/dynamic.txt"))
    if not paths:
        raise ValueError(f"no hay seed-*/dynamic.txt en {directory}")
    return [read_speeds(p, times) for p in paths]


def pooled(runs: list[dict[float, list[float]]], t: float, tol: float = 1e-6) -> list[float]:
    """Todas las rapideces de todas las realizaciones en el instante t."""
    out: list[float] = []
    for frames in runs:
        out.extend(next(v for time, v in frames.items() if abs(time - t) < tol))
    return out


def bin_edges(width: float, v_max: float, center: float | None = None) -> list[float]:
    """Bordes de ancho `width` que cubren [0, v_max).

    Con `center`, los bordes se corren para que ese valor quede en el centro de un bin (ej. v0: si cayera en un
    borde, el pico de t = 0 se partiría en dos bins por redondeo). El primer bin va de 0 al primer borde.
    """
    offset = 0.0 if center is None else (center - width / 2) % width
    if offset < 1e-9 or width - offset < 1e-9:
        offset = 0.0
    edges = [0.0] if offset > 0 else []
    k = 0
    while not edges or edges[-1] < v_max - 1e-9:
        edges.append(offset + k * width)
        k += 1
    return edges


def density(speeds: list[float], edges: list[float]) -> list[float]:
    """N_i/(Δv_i·N) en cada bin (cada bin con su propio ancho); integral = 1."""
    counts = [0] * (len(edges) - 1)
    for s in speeds:
        i = bisect.bisect_right(edges, s) - 1
        if not 0 <= i < len(counts):
            raise ValueError(f"rapidez {s} fuera del rango [0, {edges[-1]})")
        counts[i] += 1
    return [c / ((edges[i + 1] - edges[i]) * len(speeds)) for i, c in enumerate(counts)]


def pdf(speeds: list[float], width: float, v_max: float, center: float | None = None) -> tuple[list[float], list[float]]:
    """Bordes de bin y densidad N_i/(Δv_i·N) sobre [0, v_max)."""
    edges = bin_edges(width, v_max, center)
    return edges, density(speeds, edges)


def maxwell_boltzmann_2d(v: float, mass: float, kbt: float) -> float:
    """f(v) = (m v / k_BT) exp(−m v² / (2 k_BT)) (enunciado, 2.3)."""
    return mass * v / kbt * math.exp(-mass * v * v / (2 * kbt))


def fit_kbt(centers: list[float], values: list[float], mass: float, reference: float,
            low: float = 0.2, high: float = 3.0, steps: int = 20000) -> tuple[float, list[float], list[float]]:
    """Ajuste por mínimos cuadrados de la Teórica 0 con k_BT como único parámetro libre.

    E(k_BT) = Σ_i [f_i − f_MB(v_i; k_BT)]² sobre los centros de bin, barriendo k_BT en [low, high]·reference.
    Devuelve (k_BT del mínimo, barrido, E del barrido). Error si el mínimo cae en un borde del barrido.
    """
    grid = [reference * (low + (high - low) * k / steps) for k in range(steps + 1)]
    errors = [sum((f - maxwell_boltzmann_2d(v, mass, kbt)) ** 2 for v, f in zip(centers, values)) for kbt in grid]
    best = min(range(len(grid)), key=errors.__getitem__)
    if best in (0, len(grid) - 1):
        raise ValueError("el mínimo de E(k_BT) cae en el borde del barrido: ampliar el rango")
    return grid[best], grid, errors
