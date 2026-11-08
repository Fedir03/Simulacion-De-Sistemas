#!/usr/bin/env python3
"""Auditoría de las capas: resume las mediciones de scripts/sim_gen/audit_f.sh.

Las secciones de contacto, lado, conmutaciones y espejo salen de diagnostics/LayerChecks (no va al ZIP).
Uso: python scripts/graph_gen/audit_f.py [carpeta del piloto]
"""
import sys
from pathlib import Path

import numpy as np

from pilot_analysis import load_grid

GRID = {"a": "grid_A.txt", "b": "grid_B.txt", "f": "grid_F.txt"}
ECM1, ECM2, CONTACT = 3, 5, 10
# Columnas de una fila de agente en traza_capas.txt
ON, OVERLAP, ON_OVERLAP, TIE, LEFT, SIN, DIST, SW_FORCE, SW_CHECK, FLIP_ACT, FLIP_EV = range(6, 17)


def best_pairs(pilot):
    """Mejores pares de ECM 1 excl. y ECM 2 de cada capa, sin repetir."""
    out = []
    for line in (pilot / "mejores.txt").read_text(encoding="utf-8").splitlines():
        layer, metric, p1, p2 = line.split()
        pair = (layer.lower(), float(p1), float(p2))
        if metric != "ecm1_relleno" and pair not in out:
            out.append(pair)
    return out


def name(pair):
    return f"{pair[0].upper()}({pair[1]:g}; {pair[2]:g})"


def rows_for(grid, pair):
    rows = grid[(grid[:, 0] == pair[1]) & (grid[:, 1] == pair[2])]
    return rows[np.argsort(rows[:, 2])]


def best(grid, column):
    pairs = sorted({(float(r[0]), float(r[1])) for r in grid})
    means = [rows_for(grid, ("", *p))[:, column].mean() for p in pairs]
    k = int(np.argmin(means))
    return pairs[k], means[k]


def read_trace(path):
    agents, mirrors = [], []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        parts = line.split()
        if parts[0] == "E":
            mirrors.append((parts[1], float(parts[2]), float(parts[3]), int(parts[4]), *map(float, parts[5:10]), int(parts[10]), int(parts[11])))
        else:
            agents.append((parts[0], float(parts[1]), float(parts[2]), *map(float, parts[3:])))
    return agents, mirrors


def horizon(pilot, folder, pairs):
    print("== Horizonte de F (par fijo y mejor par de la grilla oficial) ==")
    base = load_grid(pilot / "grid_F.txt")
    grids = {"sin límite": base}
    for h in ("2.5", "5"):
        grids[h] = load_grid(folder / f"grid_F_ta{h}.txt")
    f_pairs = [p for p in pairs if p[0] == "f"]
    for label, column in (("ECM 1 excl.", ECM1), ("ECM 2", ECM2)):
        for pair in f_pairs:
            reference = rows_for(base, pair)
            for h, grid in grids.items():
                fixed = rows_for(grid, pair)
                change = fixed[:, column] - reference[:, column]
                bp, bv = best(grid, column)
                print(f"{label} | t_a {h:>10} | par ({pair[1]:g}; {pair[2]:g}): {fixed[:, column].mean():.4f} "
                      f"({(fixed[:, column].mean() / reference[:, column].mean() - 1) * 100:+.2f}%; máx. por evento {np.abs(change).max():.4f}) "
                      f"contactos {int(fixed[:, CONTACT].sum())} | mejor par ({bp[0]:g}; {bp[1]:g}): {bv:.4f}")


def contact_and_side(agents, pairs):
    print("\n== Contacto y lado aplicado (19 eventos, 2 agentes por evento) ==")
    print("par | pasos con capa | con solape | de esos con capa | desempate | terminan a la izquierda | cambios de lado (activación / evento) | conm. máx. fuerza / conteo")
    for pair in pairs:
        rows = [a for a in agents if a[0] == pair[0] and a[1] == pair[1] and a[2] == pair[2]]
        print(f"{name(pair)} | {sum(r[ON] for r in rows):.0f} | {sum(r[OVERLAP] for r in rows):.0f} | {sum(r[ON_OVERLAP] for r in rows):.0f} | {sum(r[TIE] for r in rows):.0f} | {sum(r[LEFT] for r in rows):.0f} | "
              f"{sum(r[FLIP_ACT] for r in rows):.0f} / {sum(r[FLIP_EV] for r in rows):.0f} | {max(r[SW_FORCE] for r in rows):.0f} / {max(r[SW_CHECK] for r in rows):.0f}")
        flips = [(r[3], r[4], r[FLIP_EV]) for r in rows if r[FLIP_EV] > 0]
        if flips:
            print("    cambios de lado: " + ", ".join(f"ev{e:.0f}/ag{a:.0f}: {n:.0f}" for e, a, n in flips))


def order(agents, pairs):
    print("\n== Conmutaciones según la velocidad con que se evalúa ==")
    for pair in pairs:
        rows = [a for a in agents if a[0] == pair[0] and a[1] == pair[1] and a[2] == pair[2]]
        different = [r for r in rows if r[SW_FORCE] != r[SW_CHECK]]
        print(f"{name(pair)} | fuerza (v predicha) {sum(r[SW_FORCE] for r in rows):.0f} | conteo (v corregida) {sum(r[SW_CHECK] for r in rows):.0f} | agentes con distinto conteo: {len(different)} de {len(rows)}")


def dt(pilot, folder, pairs):
    print("\n== Δt_exp/64 contra Δt_exp/128 (criterio: menos de 1%) ==")
    for pair in pairs:
        fine = load_grid(folder / f"dt128_{pair[0]}_{pair[1]:g}_{pair[2]:g}.txt")
        fine = fine[np.argsort(fine[:, 2])]
        coarse = rows_for(load_grid(pilot / GRID[pair[0]]), pair)
        for label, column in (("ECM 1 excl.", ECM1), ("ECM 1 rell.", 4), ("ECM 2", ECM2)):
            pop = abs(fine[:, column].mean() / coarse[:, column].mean() - 1) * 100
            per = np.abs(fine[:, column] / coarse[:, column] - 1) * 100
            k = int(np.argmax(per))
            over = [f"ev{coarse[j, 2]:.0f} {coarse[j, column]:.4f}->{fine[j, column]:.4f}" for j in np.nonzero(per > 1)[0]]
            print(f"{name(pair)} | {label} | poblacional {pop:.3f}% | máx. por evento {per[k]:.3f}% (evento {coarse[k, 2]:.0f}) | eventos >1%: {int((per > 1).sum())} | >5%: {int((per > 5).sum())} | contactos {int(coarse[:, CONTACT].sum())} -> {int(fine[:, CONTACT].sum())}" + (" | " + ", ".join(over) if over else ""))


def mirror(mirrors, pairs):
    print("\n== Evento reflejado (y -> -y) ==")
    for pair in pairs:
        rows = [m for m in mirrors if m[0] == pair[0] and m[1] == pair[1] and m[2] == pair[2]]
        ecm1 = np.array([m[4] for m in rows]); ecm1m = np.array([m[5] for m in rows])
        ecm2 = np.array([m[6] for m in rows]); ecm2m = np.array([m[7] for m in rows])
        exact = [m for m in rows if m[8] < 1e-9]
        tied = [m for m in rows if m[9] + m[10] > 0]
        broken = [m for m in rows if m[8] >= 1e-9]
        print(f"{name(pair)} | ECM 1 {ecm1.mean():.4f} -> {ecm1m.mean():.4f} | ECM 2 {ecm2.mean():.4f} -> {ecm2m.mean():.4f} | espejo exacto {len(exact)}/19 | con desempate {len(tied)} | sin espejo y sin desempate: {sum(1 for m in broken if m[9] + m[10] == 0)}")
        for m in broken:
            print(f"    evento {m[3]}: dif {m[8]:.3f} m | ECM 1 {m[4]:.4f} -> {m[5]:.4f} | ECM 2 {m[6]:.4f} -> {m[7]:.4f} | pasos de desempate {m[9]} / {m[10]}")


def main():
    pilot = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("outputs/pilot")
    folder = pilot / "auditoria"
    pairs = best_pairs(pilot)
    agents, mirrors = read_trace(folder / "traza_capas.txt")
    horizon(pilot, folder, pairs)
    contact_and_side(agents, pairs)
    order(agents, pairs)
    dt(pilot, folder, pairs)
    mirror(mirrors, pairs)


if __name__ == "__main__":
    main()
