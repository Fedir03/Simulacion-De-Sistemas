#!/usr/bin/env python3
"""Geometría del huevo de la capa E (EggLayer.java) y diagnóstico de solapes sobre las salidas del motor. Solo numpy.

Uso: python scripts/animation/egg_geometry.py <carpeta con evento_XX.txt> [a] [b]
"""
import re
import sys
from pathlib import Path

import numpy as np

Q = 0.75            # EggLayer.TIP_EXPONENT
MIN_SPEED = 0.05    # EggLayer.MIN_HEADING_SPEED
R = 0.25


def boundary(a, b, n=240):
    """Borde del huevo en su marco (punta hacia +x), en orden antihorario, como polígono cerrado."""
    back = np.linspace(np.pi / 2, 3 * np.pi / 2, n // 3)
    u = np.linspace(a, 0, n // 3)
    w = b * np.clip(1 - (u / a) ** 2, 0, None) ** Q
    top = np.column_stack([u, w])
    rear = np.column_stack([b * np.cos(back), b * np.sin(back)])
    bottom = np.column_stack([u[::-1], -w[::-1]])
    return np.vstack([top, rear[1:], bottom[1:]])


def placed(shape, x, y, heading):
    c, s = np.cos(heading), np.sin(heading)
    return np.column_stack([x + c * shape[:, 0] - s * shape[:, 1], y + s * shape[:, 0] + c * shape[:, 1]])


def signed_distance(pi, pj, k=720):
    """Distancia con signo entre dos convexos dados por sus bordes (negativa si se solapan)."""
    ang = np.linspace(0, 2 * np.pi, k, endpoint=False)
    n = np.column_stack([np.cos(ang), np.sin(ang)])
    # max_n [min_{q∈i} q·n − max_{q∈j} q·n]
    return float(np.max((pi @ n.T).min(axis=0) - (pj @ n.T).max(axis=0)))


def headings(run, ped, fallback):
    vx, vy = run[:, 3 + 4 * ped], run[:, 4 + 4 * ped]
    h = np.arctan2(vy, vx)
    return np.where(np.hypot(vx, vy) > MIN_SPEED, h, fallback)


def read_run(path):
    with open(path, encoding="utf-8") as f:
        header = dict(re.findall(r"(\w+)=(\S+)", f.readline()))
    return header, np.genfromtxt(path, comments="#")


def egg_gaps(run, a, b):
    """Distancia con signo entre huevos en cada fila (NaN si alguno se retiró)."""
    shape = boundary(a, b)
    h1, h2 = headings(run, 0, 0.0), headings(run, 1, np.pi)
    out = np.full(len(run), np.nan)
    for k, row in enumerate(run):
        if np.isnan(row[1]) or np.isnan(row[5]):
            continue
        out[k] = signed_distance(placed(shape, row[1], row[2], h1[k]), placed(shape, row[5], row[6], h2[k]))
    return out


def main():
    folder = Path(sys.argv[1])
    a = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
    b = float(sys.argv[3]) if len(sys.argv) > 3 else 0.35
    print("evento d_centros_min gap_huevo_min filas_con_solape contacto_cuerpos")
    total = overlapping = 0
    worst = []
    for path in sorted(folder.glob("evento_*.txt")):
        _, run = read_run(path)
        d = np.hypot(run[:, 1] - run[:, 5], run[:, 2] - run[:, 6])
        gaps = egg_gaps(run, a, b)
        valid = ~np.isnan(gaps)
        n_over = int(np.sum(gaps[valid] < -1e-3))
        total += int(valid.sum())
        overlapping += n_over
        worst.append(np.nanmin(gaps))
        print(f"{path.stem[-2:]} {np.nanmin(d):.3f} {np.nanmin(gaps):+.3f} {n_over} {bool(np.nanmin(d) < 2 * R)}")
    print(f"# filas con solape (> 1 mm): {overlapping} de {total}; peor solape {min(worst):+.3f} m")


if __name__ == "__main__":
    main()
