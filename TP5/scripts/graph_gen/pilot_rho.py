#!/usr/bin/env python3
"""Orden de las capas para ρ = 0,7 / 0,9 / 1,1, con cada par fijo en su óptimo de ρ = 0,9.

Uso: python scripts/graph_gen/pilot_rho.py [carpeta del piloto]
"""
import sys
from pathlib import Path

import numpy as np

COLUMNS = {"ecm1_excl": 0, "ecm2": 2}
RHOS = ("0.7", "0.9", "1.1")


def read(folder):
    out = {}
    with open(Path(folder) / "ecm.txt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("E "):
                p = line.split()
                out[int(p[1])] = [float(p[2]), float(p[3]), float(p[4]), p[7] == "true"]
    return np.array([out[k] for k in sorted(out)], dtype=float)


def best_pairs(path):
    pairs = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        layer, metric, p1, p2 = line.split()
        pairs[(layer, metric)] = (p1, p2)
    return pairs


def main():
    pilot = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/pilot")
    base = pilot / "sensitivity_rho"
    official = best_pairs(pilot / "mejores.txt")
    exploratory = best_pairs(pilot / "mejores_exploratoria.txt")
    for metric, column in COLUMNS.items():
        print(f"\n===== {metric} (par fijo, optimo de rho = 0,9) =====")
        print("capa par | E(0,7) E(0,9) E(1,1) | cambio 0,7 y 1,1 contra 0,9 | contactos 0,7/0,9/1,1")
        runs = {}
        rows = [(layer, official[(layer, metric)], f"{layer}") for layer in "ABF"]
        rows.append(("F", exploratory[("F", metric)], "F* (exploratoria, post-hoc)"))
        for layer, (p1, p2), label in rows:
            data = {rho: read(base / f"{layer}_{p1}_{p2}" / f"rho_{rho}") for rho in RHOS}
            runs[label] = data
            e = {rho: data[rho][:, column].mean() for rho in RHOS}
            contacts = "/".join(str(int(data[rho][:, 3].sum())) for rho in RHOS)
            print(f"{label} ({p1}; {p2}) | {e['0.7']:.4f} {e['0.9']:.4f} {e['1.1']:.4f} | {100 * (e['0.7'] / e['0.9'] - 1):+.1f}% {100 * (e['1.1'] / e['0.9'] - 1):+.1f}% | {contacts}")
        print("orden oficial A/B/F (menor error primero), y diferencias pareadas por evento:")
        for rho in RHOS:
            values = {layer: runs[layer][rho][:, column] for layer in "ABF"}
            order = sorted(values, key=lambda k: values[k].mean())
            diffs = []
            for x, y in (("A", "B"), ("A", "F"), ("B", "F")):
                d = values[x] - values[y]
                diffs.append(f"{x}-{y} {d.mean():+.3f} +- {d.std(ddof=1) / np.sqrt(len(d)):.3f}")
            print(f"  rho={rho}: {' < '.join(order)} | " + " | ".join(diffs))


if __name__ == "__main__":
    main()
