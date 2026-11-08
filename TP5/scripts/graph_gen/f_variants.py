#!/usr/bin/env python3
"""Variantes declaradas de F contra A, B y F, sobre la grilla oficial y con la validación de D8.

F1 = sin compuerta de choque predicho; F2 = d_ij − 2R en la exponencial (sin bajar de 0); F3 = F1 + F2.
Cada variante es una comparación más: con A, B, F, F1, F2 y F3 son 6 capas y 15 pares de capas.
Uso: python scripts/graph_gen/f_variants.py [carpeta del piloto]
"""
import sys
from pathlib import Path

import numpy as np

from cross_validation import error_matrix, evaluate, partitions
from pilot_analysis import load_grid

METRICS = {"ECM 1 excl.": 3, "ECM 1 rell.": 4, "ECM 2": 5}
CONTACT = 10


def layers(pilot):
    out = {name: load_grid(pilot / f"grid_{name}.txt") for name in "ABF"}
    for name in ("F1", "F2", "F3"):
        out[name] = load_grid(pilot / "variantes" / f"grid_{name}.txt")
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pilot = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/pilot")
    grids = layers(pilot)
    parts = partitions()
    print("Variantes declaradas antes de correr: F1 sin compuerta, F2 d_ij entre bordes (max(0, d_ij − 2R) solo en la exponencial), F3 = F1 + F2.")
    print(f"Comparaciones: {len(grids)} capas, {len(grids) * (len(grids) - 1) // 2} pares de capas (3 más que con A, B y F).")
    for label, column in METRICS.items():
        print(f"\n===== {label} =====")
        print("capa | mejor par | E ± SEM | contactos | eventos con contacto | entrenamiento | validación ± desvío | coincide con el par de 19")
        best_rows, validation = {}, {}
        for name, rows in grids.items():
            pairs, matrix = error_matrix([tuple(r) for r in rows], column)
            means = matrix.mean(axis=1)
            k = int(np.argmin(means))
            at = rows[(rows[:, 0] == pairs[k][0]) & (rows[:, 1] == pairs[k][1])]
            at = at[np.argsort(at[:, 2])]
            best_rows[name] = at
            train, val, chosen = evaluate(matrix, parts)
            validation[name] = val
            sem = at[:, column].std(ddof=1) / np.sqrt(len(at))
            print(f"{name} | ({pairs[k][0]:g}; {pairs[k][1]:g}) | {means[k]:.4f} ± {sem:.4f} | {int(at[:, CONTACT].sum())} | "
                  f"{','.join(str(int(e)) for e in at[at[:, CONTACT] == 1][:, 2]) or '-'} | {train.mean():.4f} | {val.mean():.4f} ± {val.std(ddof=1):.4f} | {int((chosen == k).sum())}/{len(parts)}")
        print("diferencia pareada por evento (media ± SEM, eventos donde gana la primera) | validación (media ± desvío, particiones donde gana la primera)")
        for x in ("A", "B", "F"):
            for y in ("F1", "F2", "F3"):
                d = best_rows[x][:, column] - best_rows[y][:, column]
                v = validation[x] - validation[y]
                print(f"  {x} − {y}: {d.mean():+.4f} ± {d.std(ddof=1) / np.sqrt(len(d)):.4f} ({int((d < 0).sum())}/19) | {v.mean():+.4f} ± {v.std(ddof=1):.4f} ({int((v < 0).sum())}/{len(v)})")


if __name__ == "__main__":
    main()
