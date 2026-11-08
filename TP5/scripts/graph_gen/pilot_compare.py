#!/usr/bin/env python3
"""Compara F entre criterios de desempate y mide si B_p aporta (B_p fijo, barriendo A_p).

Lo que sale de outputs/pilot/exploratoria va rotulado: esa zona se eligió después de ver los datos.
Uso: python scripts/graph_gen/pilot_compare.py [carpeta del piloto]
"""
import sys
from pathlib import Path

import numpy as np

from pilot_analysis import METRICS, collapse, load_grid, surface

CRITERIA = {"metrico |s_c|<=0,05": "", "angular 5": "_angular5", "angular 1": "_angular1"}


def best(rows, column):
    p1, p2, z = surface(rows, column)
    i, j = np.unravel_index(np.argmin(z), z.shape)
    return p1[i], p2[j], z[i, j]


def at_pair(rows, a, b):
    at = rows[(rows[:, 0] == a) & (rows[:, 1] == b)]
    return at[np.argsort(at[:, 2])]


def compare_zone(title, files):
    print(f"\n===== {title} =====")
    grids = {name: load_grid(path) for name, path in files.items()}
    print("criterio metrica mejor(A_p,B_p) E SEM ecm1_excl_ahi ecm1_rell_ahi ecm2_ahi contactos_ahi")
    for name, rows in grids.items():
        for metric, column in METRICS.items():
            a, b, e = best(rows, column)
            at = at_pair(rows, a, b)
            print(f"{name} | {metric} | ({a:g}; {b:g}) | {e:.4f} | {at[:, column].std(ddof=1) / np.sqrt(19):.4f} | "
                  f"{at[:, 3].mean():.4f} {at[:, 4].mean():.4f} {at[:, 5].mean():.4f} | {int(at[:, 10].sum())}")
    base = grids["metrico |s_c|<=0,05"]
    print("\nEfecto del desempate en el MISMO par, contra el metrico (positivo = el otro criterio da menos error):")
    print("criterio metrica media_sobre_grilla_% celdas_donde_mejora mediana_abs max_abs")
    for name, rows in grids.items():
        if rows is base:
            continue
        for metric, column in METRICS.items():
            _, _, z0 = surface(base, column)
            _, _, z1 = surface(rows, column)
            gain = z0 - z1
            print(f"{name} | {metric} | {100 * (gain / z0).mean():+.2f}% | {int((gain > 0).sum())}/{gain.size} | {np.median(np.abs(gain)):.4f} | {np.abs(gain).max():.4f}")
    print("\nColapso a un parametro (R2 de E contra la intensidad A_p exp(-d*/B_p)):")
    for name, rows in grids.items():
        for metric, column in METRICS.items():
            p1, p2, z = surface(rows, column)
            print(f"{name} | {metric}: {collapse('F', p1, p2, z)}")
    return grids


def fixed_range(pilot):
    print("\n===== Tarea 7: F con B_p fijo, barriendo A_p (grilla oficial, desempate metrico) =====")
    rows = load_grid(pilot / "grid_F.txt")
    print("metrica B_p mejor_A_p E empeora_abs empeora_% pareado(media +- SEM) eventos_peor")
    for metric, column in METRICS.items():
        a0, b0, e0 = best(rows, column)
        ref = at_pair(rows, a0, b0)[:, column]
        print(f"{metric}: mejor par (A_p={a0:g}, B_p={b0:g}) E={e0:.4f}")
        for bp in np.unique(rows[:, 1]):
            sub = rows[rows[:, 1] == bp]
            means = {a: sub[sub[:, 0] == a, column].mean() for a in np.unique(sub[:, 0])}
            a = min(means, key=means.get)
            d = at_pair(rows, a, bp)[:, column] - ref
            mark = " <-- pedido" if bp in (1, 3) else ""
            print(f"  B_p={bp:<5g} A_p={a:g} E={means[a]:.4f} +{means[a] - e0:.4f} (+{100 * (means[a] / e0 - 1):.1f}%) {d.mean():+.4f} +- {d.std(ddof=1) / np.sqrt(19):.4f} {int((d > 0).sum())}/19{mark}")
    wide = load_grid(pilot / "exploratoria" / "F_amplia.txt")
    print("\nReferencia EXPLORATORIA (post-hoc), B_p grande, barriendo A_p:")
    for metric, column in METRICS.items():
        a0, b0, e0 = best(wide, column)
        print(f"{metric}: mejor de la zona (A_p={a0:g}, B_p={b0:g}) E={e0:.4f}")
        for bp in (10, 60, 1000):
            sub = wide[wide[:, 1] == bp]
            means = {a: sub[sub[:, 0] == a, column].mean() for a in np.unique(sub[:, 0])}
            a = min(means, key=means.get)
            print(f"  B_p={bp:<5g} A_p={a:g} E={means[a]:.4f} (+{100 * (means[a] / e0 - 1):.1f}% contra el mejor de la zona)")


def main():
    pilot = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/pilot")
    compare_zone("F, grilla OFICIAL", {name: pilot / f"grid_F{suffix}.txt" for name, suffix in CRITERIA.items()})
    compare_zone("F, zona EXPLORATORIA (elegida post-hoc)", {name: pilot / "exploratoria" / f"F_amplia{suffix}.txt" for name, suffix in CRITERIA.items()})
    fixed_range(pilot)


if __name__ == "__main__":
    main()
