#!/usr/bin/env python3
"""Compara corridas de `baseline`: ECM poblacional y por evento, y energía cinética.

Uso: python scripts/graph_gen/compare_runs.py ETIQUETA=CARPETA [ETIQUETA=CARPETA ...]
Cada corrida se compara contra la siguiente, que es la referencia del cambio relativo. Si se compara
resolución, van de mayor a menor Δt (por ejemplo div16, div32, div64).
"""
import sys
from pathlib import Path

import numpy as np

MASS = 80.0
METRICS = ("ecm1_excl", "ecm1_relleno", "ecm2")


def read_ecm(folder):
    events = {}
    with open(Path(folder) / "ecm.txt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("E "):
                p = line.split()
                events[int(p[1])] = tuple(float(v) for v in p[2:5])
    return events


def kinetic_jump(folder):
    """Mayor salto de energía cinética de un peatón entre filas, y evento donde ocurre."""
    worst, where = 0.0, None
    for path in sorted(Path(folder).glob("evento_*.txt")):
        rows = np.loadtxt(path)
        for vx, vy in ((3, 4), (7, 8)):
            k = 0.5 * MASS * (rows[:, vx] ** 2 + rows[:, vy] ** 2)
            jumps = np.abs(np.diff(k))
            jumps = jumps[np.isfinite(jumps)]     # el retiro deja NaN: no es un salto
            if jumps.size and jumps.max() > worst:
                worst, where = float(jumps.max()), path.stem
    return worst, where


def main():
    runs = [a.split("=", 1) for a in sys.argv[1:]]
    if len(runs) < 2:
        sys.exit(__doc__)
    data = {label: read_ecm(folder) for label, folder in runs}

    print("corrida " + " ".join(METRICS) + " salto_K_max_J evento")
    for label, folder in runs:
        means = np.mean(list(data[label].values()), axis=0)
        jump, where = kinetic_jump(folder)
        print(f"{label} " + " ".join(f"{v:.6f}" for v in means) + f" {jump:.2f} {where}")

    print("\ncambio relativo entre corridas consecutivas, en %: poblacional | maximo por evento (evento)")
    labels = [label for label, _ in runs]
    for a, b in zip(labels, labels[1:]):
        for m, name in enumerate(METRICS):
            pa = np.mean([v[m] for v in data[a].values()])
            pb = np.mean([v[m] for v in data[b].values()])
            per_event = {e: abs(data[a][e][m] - data[b][e][m]) / data[b][e][m] * 100 for e in data[b]}
            worst = max(per_event, key=per_event.get)
            print(f"{a} -> {b} {name}: {abs(pa - pb) / pb * 100:.4f} | {per_event[worst]:.4f} (evento {worst})")


if __name__ == "__main__":
    main()
