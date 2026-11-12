#!/usr/bin/env python3
"""Tabla de tres columnas: sin recorte, D(45°) y D(45°) con compuerta de tramo compartido (X = 1,5 m, vigente).

Δt = Δt_exp/64, salida cada Δt_exp/4, grilla oficial, semilla 20261116, 5000 particiones (14/5) para todas las
columnas (también se recalcula la validación de las dos anteriores). ECM 1 = variante excluyente.
Uso: py scripts/graph_gen/trim_compare3.py > outputs/pilot/antes_despues_compuerta.md
"""
import sys
from pathlib import Path

import numpy as np

from cross_validation import N_PARTITIONS
from pilot_analysis import load_grid
from trim_compare import METRICS, baseline_population, fmt_pair, layer_summary, num, pct, read_e, sensitivity

COLS = [("sin recorte", Path("outputs/pilot_sin_recorte"), Path("outputs/pilot_sin_recorte/baseline")),
        ("D(45°)", Path("outputs/pilot_d45"), Path("outputs/pilot_d45/baseline")),
        ("D(45°) + compuerta", Path("outputs/pilot"), Path("outputs/baseline"))]


def coin_stats(path, layer, pair):
    if not path.exists():
        return None
    rows = [l.split() for l in path.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    rows = [r for r in rows if r[0] == layer.lower() and float(r[1]) == pair[0] and float(r[2]) == pair[1]]
    if not rows:
        return None
    e1 = np.zeros((20, 19)); contact = np.zeros((20, 19), bool)
    for r in rows:
        e1[int(r[3]), int(r[4]) - 1] = float(r[5]); contact[int(r[3]), int(r[4]) - 1] = r[7] == "true"
    pop, ct = e1.mean(axis=1), contact.sum(axis=1)
    return pop.mean(), pop.std(ddof=1), ct.mean(), ct.std(ddof=1)


def rule_at_rho(folder, layer, pair, rho):
    f = folder / "recorte_extra" / "rho" / f"con_{layer.lower()}_{pair[0]:g}_{pair[1]:g}_rho{rho}.txt"
    if not f.exists():
        return None
    rows = load_grid(f)
    return rows[:, 3].mean(), int(rows[:, 10].sum())


def order(values, reverse=False):
    keys = sorted(values, key=values.get, reverse=reverse)
    out = keys[0]
    for a, b in zip(keys, keys[1:]):
        out += (" = " if abs(values[a] - values[b]) < 1e-12 else (" > " if reverse else " < ")) + b
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    summaries, bases = [], []
    for name, folder, base in COLS:
        pop, contacts = baseline_population(base)
        bases.append((pop, contacts))
        summaries.append(layer_summary(folder, pop))
    names = [c[0] for c in COLS]
    print("# Sin recorte → D(45°) → D(45°) con compuerta de tramo compartido (X = 1,5 m, vigente)")
    print(f"Δt = Δt_exp/64, salida cada Δt_exp/4, grilla oficial; validación con {N_PARTITIONS} particiones 14/5, semilla 20261116, "
          "recalculada igual para las tres columnas. ECM 1 = variante excluyente. Cambios con base en la columna D(45°).\n")

    print("## Línea base (sin capa), poblacional")
    print(f"| métrica | {' | '.join(names)} | cambio contra D(45°) |")
    print("|---|---|---|---|---|")
    for m, (_, label) in METRICS.items():
        v = [b[0][m] for b in bases]
        print(f"| {label} | {' | '.join(num(x) for x in v)} | {pct(v[2], v[1])} |")
    print(f"| eventos con contacto | {' | '.join(str(b[1]) for b in bases)} | |")

    for m, (_, label) in METRICS.items():
        print(f"\n## Mejores pares, {label}")
        print(f"| capa | dato | {' | '.join(names)} |")
        print("|---|---|---|---|---|")
        for layer in "ABF":
            s = [x[(layer, m)] for x in summaries]
            print(f"| {layer} | par | {' | '.join(fmt_pair(x['pair']) for x in s)} |")
            print(f"| | E (19 eventos) | {' | '.join(num(x['E']) for x in s)} ({pct(s[2]['E'], s[1]['E'])} contra D(45°)) |")
            print(f"| | validación media ± DE | {' | '.join(num(x['valid']) + ' ± ' + num(x['valid_sd']) for x in s)} |")
            print(f"| | entrenamiento | {' | '.join(num(x['train']) for x in s)} |")
            print(f"| | eventos con contacto (de 19) | {' | '.join(str(x['contacts']) for x in s)} |")
            print(f"| | identificabilidad (particiones de {N_PARTITIONS} que eligen el par de los 19) | {' | '.join(str(x['same']) for x in s)} |")
            edges = []
            for x in s:
                e = [n for n, flag in zip(("p1", "p2"), (x["edge1"], x["edge2"])) if flag]
                edges.append(", ".join(e) if e else "no")
            print(f"| | parámetro en el borde de la grilla (p1 = t_a o A_p) | {' | '.join(edges)} |")

    print("\n## Óptimo de t_a (A y B), minimizando sobre el segundo parámetro")
    for m, (_, label) in METRICS.items():
        for layer in "AB":
            cells = []
            for s in summaries:
                prof = s[(layer, m)]["ta_profile"]
                ta = min(prof, key=prof.get)
                cells.append(f"{ta:g} s{' (borde)' if ta in (0.5, 5.0) else ''}".replace(".", ","))
            print(f"- {layer}, {label}: {' → '.join(cells)}")

    print("\n## Lado al azar (moneda por agente y evento, 20 semillas), mejores pares de ECM 1 excl.")
    print("ECM 1 excl. poblacional y eventos con contacto por semilla: media ± DE de las 20 semillas. Regla = la regla de lado.")
    print(f"| capa, ρ | {' | '.join(names[1:])} |")
    print("|---|---|---|")
    for layer, rhos in (("A", ("0.9",)), ("B", ("0.7", "0.8", "0.9"))):
        for rho in rhos:
            cells = []
            for k, (name, folder, _) in enumerate(COLS[1:], 1):
                pair = summaries[k][(layer, "ecm1_excl")]["pair"]
                if rho == "0.9":
                    st = coin_stats(folder / "pruebas" / "moneda.txt", layer, pair)
                    rule = (summaries[k][(layer, "ecm1_excl")]["E"], summaries[k][(layer, "ecm1_excl")]["contacts"])
                else:
                    tag = "compuerta" if k == 2 else "d45"
                    st = coin_stats(Path("outputs/pilot/pruebas") / f"moneda_{tag}_rho{rho}.txt", layer, pair)
                    rule = rule_at_rho(folder, layer, pair, rho)
                if st is None or rule is None:
                    cells.append("n/d")
                    continue
                cells.append(f"{fmt_pair(pair)}: moneda {num(st[0])} ± {num(st[1])}, contactos {num(st[2], 1)} ± {num(st[3], 1)} | "
                             f"regla {num(rule[0])}, contactos {rule[1]}")
            print(f"| {layer}, ρ = {rho.replace('.', ',')} | {' | '.join(cells)} |")

    print("\n## Robustez de los mejores pares de ECM 1 excl. (par fijo): ρ 0,7 / 0,9 / 1,1 y v_0 con 3 / 5 / 7 frames")
    print(f"| capa | {' | '.join(names)} |")
    print("|---|---|---|---|")
    robust = []
    for k, (name, folder, _) in enumerate(COLS):
        r = {}
        for layer in "ABF":
            pair = summaries[k][(layer, "ecm1_excl")]["pair"]
            rho = sensitivity(folder, "sensitivity_rho", layer, pair, ("0.7", "0.9", "1.1"), "rho_")
            v0 = sensitivity(folder, "sensitivity_v0", layer, pair, (3, 5, 7), "v0_")
            worst = max(abs(rho[x][0] / rho["0.9"][0] - 1) for x in ("0.7", "1.1"))
            worst_v0 = max(abs(v0[x][0] / v0[5][0] - 1) for x in (3, 7))
            r[layer] = (rho, v0, worst, worst_v0)
        robust.append(r)
    for layer in "ABF":
        cells = []
        for r in robust:
            rho, v0, w, wv = r[layer]
            cells.append(f"ρ {' / '.join(num(rho[x][0]) for x in rho)} (máx. {num(100 * w, 1)}%); v_0 {' / '.join(num(v0[x][0]) for x in v0)} (máx. {num(100 * wv, 1)}%)")
        print(f"| {layer} | {' | '.join(cells)} |")

    print("\n## Criterios de D2 (no se elige capa): orden de A, B y F en cada columna")
    print("Validación: menor media de validación primero. Identificabilidad: más particiones que reproducen el óptimo primero. "
          "Robustez: menor cambio máximo de E con ρ 0,7–1,1 primero. Contactos: menos eventos con contacto primero.")
    print(f"| criterio | métrica | {' | '.join(names)} |")
    print("|---|---|---|---|---|")
    for m, (_, label) in METRICS.items():
        print(f"| validación | {label} | {' | '.join(order({l: s[(l, m)]['valid'] for l in 'ABF'}) for s in summaries)} |")
        print(f"| identificabilidad | {label} | {' | '.join(order({l: s[(l, m)]['same'] for l in 'ABF'}, reverse=True) for s in summaries)} |")
        print(f"| contactos | {label} | {' | '.join(order({l: s[(l, m)]['contacts'] for l in 'ABF'}) for s in summaries)} |")
    print(f"| robustez a ρ | ECM 1 excl. | {' | '.join(order({l: r[l][2] for l in 'ABF'}) for r in robust)} |")
    print(f"| robustez a v_0 | ECM 1 excl. | {' | '.join(order({l: r[l][3] for l in 'ABF'}) for r in robust)} |")


if __name__ == "__main__":
    main()
