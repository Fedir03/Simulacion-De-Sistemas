#!/usr/bin/env python3
"""Pruebas adicionales 4a (recuperación de parámetros), 4c (lado por moneda) y 4d (piso de error por evento).

4a y 4c salen de diagnostics/LayerChecks (no va al ZIP); 4d sale de las grillas del motor.
Uso: python scripts/graph_gen/layer_checks.py [carpeta del piloto]
"""
import sys
from pathlib import Path

import numpy as np

from pilot_analysis import load_grid


def recovery(folder):
    print("===== 4a: recuperación de parámetros (datos sintéticos sin ruido, sobre los t_k; agentes con x_0, v_0, target y v_d reales) =====")
    rows = [l.split() for l in (folder / "recuperacion.txt").read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    for generator in dict.fromkeys(r[0] for r in rows):
        print(f"\ngenerador {generator.replace(':', ' ').upper()}")
        for layer in "abf":
            sub = [r for r in rows if r[0] == generator and r[1] == layer]
            for label, column in (("ECM 1 excl.", 4), ("ECM 2", 5)):
                ranked = sorted(sub, key=lambda r: float(r[column]))
                tops = "; ".join(f"({float(r[2]):g}; {float(r[3]):g}) {float(r[column]):.4f}" for r in ranked[:3])
                print(f"  ajusta {layer.upper()} | {label} | mejores: {tops} | contactos del mejor: {ranked[0][6]}")


def coin(folder, pilot):
    print("\n===== 4c: lado por moneda (una por agente y evento, 20 semillas) contra la regla de lado, en los mejores pares =====")
    print("Sesgo declarado: los pares se calibraron con la regla de lado.")
    rows = [l.split() for l in (folder / "moneda.txt").read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    grids = {"a": load_grid(pilot / "grid_A.txt"), "b": load_grid(pilot / "grid_B.txt")}
    for pair in dict.fromkeys((r[0], r[1], r[2]) for r in rows):
        sub = [r for r in rows if (r[0], r[1], r[2]) == pair]
        grid = grids[pair[0]]
        rule = grid[(grid[:, 0] == float(pair[1])) & (grid[:, 1] == float(pair[2]))]
        e1 = np.array([[float(r[5]) for r in sub if int(r[3]) == s] for s in range(20)])
        e2 = np.array([[float(r[6]) for r in sub if int(r[3]) == s] for s in range(20)])
        contacts = np.array([sum(r[7] == "true" for r in sub if int(r[3]) == s) for s in range(20)])
        print(f"{pair[0].upper()}({float(pair[1]):g}; {float(pair[2]):g}) | ECM 1 excl.: regla {rule[:, 3].mean():.4f}, moneda {e1.mean(axis=1).mean():.4f} ± {e1.mean(axis=1).std(ddof=1):.4f} "
              f"(mín. {e1.mean(axis=1).min():.4f}, máx. {e1.mean(axis=1).max():.4f}; semillas mejores que la regla {int((e1.mean(axis=1) < rule[:, 3].mean()).sum())}/20) | "
              f"ECM 2: regla {rule[:, 5].mean():.4f}, moneda {e2.mean(axis=1).mean():.4f} ± {e2.mean(axis=1).std(ddof=1):.4f} (mejores {int((e2.mean(axis=1) < rule[:, 5].mean()).sum())}/20) | "
              f"eventos con contacto: regla {int(rule[:, 10].sum())}, moneda {contacts.mean():.1f} (de {contacts.min()} a {contacts.max()})")


def floor(pilot):
    print("\n===== 4d: piso de error, mejor par de cada evento en la grilla oficial (calibración individual sobre la grilla gruesa) =====")
    for name in "AB":
        grid = load_grid(pilot / f"grid_{name}.txt")
        for label, column in (("ECM 1 excl.", 3), ("ECM 1 rell.", 4), ("ECM 2", 5)):
            pairs = sorted({(r[0], r[1]) for r in grid})
            means = [grid[(grid[:, 0] == a) & (grid[:, 1] == b)][:, column].mean() for a, b in pairs]
            k = int(np.argmin(means))
            per_event, chosen = [], []
            for event in range(1, 20):
                sub = grid[grid[:, 2] == event]
                j = int(np.argmin(sub[:, column]))
                per_event.append(sub[j, column])
                chosen.append((sub[j, 0], sub[j, 1]))
            per_event = np.array(per_event)
            population = means[k]
            print(f"{name} | {label} | poblacional ({pairs[k][0]:g}; {pairs[k][1]:g}) {population:.4f} | piso {per_event.mean():.4f} "
                  f"({(1 - per_event.mean() / population) * 100:.1f}% menos) | pares distintos elegidos: {len(set(chosen))}/19")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pilot = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/pilot")
    folder = pilot / "pruebas"
    recovery(folder)
    coin(folder, pilot)
    floor(pilot)


if __name__ == "__main__":
    main()
