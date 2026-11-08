#!/usr/bin/env python3
"""Atribuye el cambio de F a cada paso: Δt (/32 y /64) y desempate (rotar e_ij, viejo; siempre a la derecha, nuevo).

Uso: python scripts/graph_gen/tie_2x2.py [carpeta del piloto]
"""
import sys
from pathlib import Path

import numpy as np

from pilot_analysis import load_grid, surface

METRICS = {"ECM 1 excl.": 3, "ECM 1 rell.": 4, "ECM 2": 5}
CONTACT = 10
CASES = [("/32", "viejo", "grid_F_dt32_viejo.txt"), ("/64", "viejo", "grid_F_dt64_viejo.txt"),
         ("/32", "nuevo", "grid_F_dt32_nuevo.txt"), ("/64", "nuevo", "grid_F_dt64_nuevo.txt")]


def at(rows, a, b):
    out = rows[(rows[:, 0] == a) & (rows[:, 1] == b)]
    return out[np.argsort(out[:, 2])]


def best(rows, column):
    p1, p2, z = surface(rows, column)
    i, j = np.unravel_index(np.argmin(z), z.shape)
    return p1[i], p2[j], z[i, j]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pilot = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/pilot")
    grids = {(dt, tie): load_grid(pilot / "desempate" / name) for dt, tie, name in CASES}
    print("Δt | desempate | métrica | mejor par | error | ECM 1 excl. en ese par | ECM 2 en ese par | contactos en ese par")
    for label, column in METRICS.items():
        for dt, tie, _ in CASES:
            rows = grids[(dt, tie)]
            a, b, e = best(rows, column)
            there = at(rows, a, b)
            print(f"{dt} | {tie} | {label} | ({a:g}; {b:g}) | {e:.4f} | {there[:, 3].mean():.4f} | {there[:, 5].mean():.4f} | {int(there[:, CONTACT].sum())}")
    print("\nEfecto de cada paso, promediando sobre la grilla, en el mismo par: media de |cambio| / mayor |cambio| poblacional / pares con más de 1%")
    for label, column in METRICS.items():
        for name, u, v in (("Δt con desempate viejo", ("/32", "viejo"), ("/64", "viejo")),
                           ("Δt con desempate nuevo", ("/32", "nuevo"), ("/64", "nuevo")),
                           ("desempate a /32", ("/32", "viejo"), ("/32", "nuevo")),
                           ("desempate a /64", ("/64", "viejo"), ("/64", "nuevo"))):
            _, _, zu = surface(grids[u], column)
            _, _, zv = surface(grids[v], column)
            change = np.abs(zv / zu - 1) * 100
            print(f"{label} | {name} | {change.mean():.3f}% | {change.max():.3f}% | {int((change > 1).sum())}/{change.size}")


if __name__ == "__main__":
    main()
