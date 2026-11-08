#!/usr/bin/env python3
"""Tarea 8: compara las capas evento por evento, cada una con su mejor par de cada métrica (grilla oficial).

Uso: python scripts/graph_gen/per_event.py [carpeta del piloto]
"""
import sys
from pathlib import Path

import numpy as np

from pilot_analysis import load_grid, surface

METRICS = {"ecm1_excl": 3, "ecm2": 5}


def best_rows(rows, column):
    p1, p2, z = surface(rows, column)
    i, j = np.unravel_index(np.argmin(z), z.shape)
    at = rows[(rows[:, 0] == p1[i]) & (rows[:, 1] == p2[j])]
    return p1[i], p2[j], at[np.argsort(at[:, 2])]


def main():
    pilot = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/pilot")
    grids = {name: load_grid(pilot / f"grid_{name}.txt") for name in "ABF"}
    tables = {}
    for metric, column in METRICS.items():
        print(f"\n===== {metric} (grilla oficial, F metrico) =====")
        data = {}
        for name, rows in grids.items():
            a, b, at = best_rows(rows, column)
            data[name] = at
            print(f"{name}: par ({a:g}; {b:g}), poblacional {at[:, column].mean():.4f}")
        print("evento A B F gana margen_contra_segunda contactos_A/B/F")
        wins = {name: [] for name in grids}
        for k in range(19):
            values = {name: data[name][k, column] for name in grids}
            order = sorted(values, key=values.get)
            margin = values[order[1]] - values[order[0]]
            wins[order[0]].append(margin)
            contacts = "/".join("si" if data[name][k, 10] else "-" for name in grids)
            print(f"{int(data['A'][k, 2])} {values['A']:.4f} {values['B']:.4f} {values['F']:.4f} {order[0]} {margin:.4f} {contacts}")
        print("gana: " + " | ".join(f"{name} {len(v)} eventos, margen medio {np.mean(v) if v else 0:.4f}, mediana {np.median(v) if v else 0:.4f}" for name, v in wins.items()))
        print("eventos con contacto: " + " | ".join(f"{name} {int(data[name][:, 10].sum())}" for name in grids))
        tables[metric] = data


if __name__ == "__main__":
    main()
