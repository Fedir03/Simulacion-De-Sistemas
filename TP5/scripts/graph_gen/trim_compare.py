#!/usr/bin/env python3
"""Tabla antes y después del recorte al tramo frontal (D3, 11/11): sin recorte contra recorte D(45°), opción 1.

Lee las dos carpetas del piloto (grillas, sensibilidades, pruebas) y las dos líneas base. Todo a Δt_exp/64.
ECM 1 = variante excluyente. Cada porcentaje dice su base.
Uso: py scripts/graph_gen/trim_compare.py [piloto sin recorte] [piloto con recorte] [base sin] [base con]
"""
import sys
from pathlib import Path

import numpy as np

from cross_validation import error_matrix, evaluate, evaluate_on_all, partitions
from pilot_analysis import load_baseline, load_grid

METRICS = {"ecm1_excl": (3, "ECM 1 excl."), "ecm2": (5, "ECM 2")}
GRID_EDGES = {"A": ((0.5, 5), (0, 2.5)), "B": ((0.5, 5), (0, 4)), "F": ((0.1, 0.9), (0.25, 3))}
NAMES = {"A": ("t_a", "l"), "B": ("t_a", "k"), "F": ("A_p", "B_p")}
COL_CONTACT, COL_DMIN, COL_SW1, COL_SW2 = 10, 11, 15, 16


def fmt_pair(p):
    return f"({p[0]:g}; {p[1]:g})".replace(".", ",")


def num(v, d=4):
    return f"{v:.{d}f}".replace(".", ",")


def pct(new, old):
    return f"{100 * (new / old - 1):+.1f}%".replace(".", ",")


def best(rows, column):
    pairs, matrix = error_matrix(rows, column)
    k, e = evaluate_on_all(matrix)
    return pairs, matrix, k, e


def layer_summary(folder, base):
    out = {}
    parts = partitions()
    for layer in "ABF":
        rows = load_grid(folder / f"grid_{layer}.txt")
        for metric, (column, _) in METRICS.items():
            pairs, matrix, k, e = best(rows, column)
            pair = pairs[k]
            sel = rows[(rows[:, 0] == pair[0]) & (rows[:, 1] == pair[1])]
            sel = sel[np.argsort(sel[:, 2])]
            train, valid, chosen = evaluate(matrix, parts)
            lo1, hi1 = GRID_EDGES[layer][0]
            lo2, hi2 = GRID_EDGES[layer][1]
            out[(layer, metric)] = {
                "pair": pair, "E": e, "base": base[metric], "per_event": matrix[k], "contacts": int(sel[:, COL_CONTACT].sum()),
                "train": train.mean(), "valid": valid.mean(), "valid_sd": valid.std(ddof=1), "same": int((chosen == k).sum()),
                "edge1": pair[0] in (lo1, hi1), "edge2": pair[1] in (lo2, hi2),
                "switch_max": int(max(sel[:, COL_SW1].max(), sel[:, COL_SW2].max())),
                "switch_mean": float(np.concatenate([sel[:, COL_SW1], sel[:, COL_SW2]]).mean()),
                "dmin": sel[:, COL_DMIN],
                "ta_profile": ta_profile(rows, column, layer) if layer in "AB" else None,
            }
    return out


def ta_profile(rows, column, layer):
    """Mejor E para cada t_a (minimizando sobre el segundo parámetro)."""
    out = {}
    for ta in np.unique(rows[:, 0]):
        sub = rows[rows[:, 0] == ta]
        out[float(ta)] = min(sub[(sub[:, 1] == p2), column].mean() for p2 in np.unique(sub[:, 1]))
    return out


def baseline_population(folder):
    b = load_baseline(folder)
    return {m: float(np.mean([v[m] for v in b.values()])) for m in METRICS}, sum(v["contacto"] for v in b.values())


def read_e(folder):
    events = {}
    with open(Path(folder) / "ecm.txt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("E "):
                p = line.split()
                events[int(p[1])] = (float(p[2]), float(p[4]), p[7] == "true", float(p[5]))
    return events


def sensitivity(folder, sub, layer, pair, values, prefix):
    out = {}
    d = folder / sub / f"{layer}_{pair[0]:g}_{pair[1]:g}"
    for v in values:
        f = d / f"{prefix}{v}"
        if (f / "ecm.txt").exists():
            ev = read_e(f)
            out[v] = (np.mean([x[0] for x in ev.values()]), np.mean([x[1] for x in ev.values()]), sum(x[2] for x in ev.values()))
    return out


def coin(folder, layer, pair, rule_e):
    f = folder / "pruebas" / "moneda.txt"
    if not f.exists():
        return None
    rows = [l.split() for l in f.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    rows = [r for r in rows if r[0] == layer.lower() and float(r[1]) == pair[0] and float(r[2]) == pair[1]]
    if not rows:
        return None
    e1 = np.zeros((20, 19)); e2 = np.zeros((20, 19)); contact = np.zeros((20, 19), bool)
    for r in rows:
        e1[int(r[3]), int(r[4]) - 1] = float(r[5]); e2[int(r[3]), int(r[4]) - 1] = float(r[6]); contact[int(r[3]), int(r[4]) - 1] = r[7] == "true"
    return {"ecm1_excl": e1, "ecm2": e2, "contact": contact}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    a = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("outputs/pilot_sin_recorte")
    b = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("outputs/pilot")
    base_a = Path(sys.argv[3]) if len(sys.argv) > 3 else a / "baseline"
    base_b = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("outputs/baseline")
    (pa, ca), (pb, cb) = baseline_population(base_a), baseline_population(base_b)
    sa, sb = layer_summary(a, pa), layer_summary(b, pb)

    print("# Antes (sin recorte) y después (recorte D(45°), persistencia 5, opción 1). Δt = Δt_exp/64, salida cada Δt_exp/4.")
    print("# ECM 1 = variante excluyente. 'cambio' tiene como base el valor sin recorte; 'mejora' tiene como base la línea base de la misma columna.")
    print("# Grilla oficial; F con desempate métrico. Validación: 1000 particiones 14/5, semilla 20261116.")
    print()
    print("## Línea base (sin capa), poblacional (19 eventos)")
    print("| métrica | sin recorte | con recorte | cambio | eventos con contacto (sin / con) |")
    print("|---|---|---|---|---|")
    for m, (_, label) in METRICS.items():
        print(f"| {label} | {num(pa[m])} | {num(pb[m])} | {pct(pb[m], pa[m])} | {ca} / {cb} |")

    for m, (_, label) in METRICS.items():
        print(f"\n## Mejor par de cada capa: {label}")
        print("| capa | par sin → con | E sin | E con | cambio | mejora sobre la línea base (sin / con) | eventos con contacto (sin / con) | validación media sin / con (± DE) | entren. sin / con | identificabilidad: particiones que eligen el par de los 19 eventos (sin / con, de 1000) | par en el borde de la grilla (con) |")
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        for layer in "ABF":
            x, y = sa[(layer, m)], sb[(layer, m)]
            edge = []
            if y["edge1"]: edge.append(NAMES[layer][0])
            if y["edge2"]: edge.append(NAMES[layer][1])
            print(f"| {layer} | {fmt_pair(x['pair'])} → {fmt_pair(y['pair'])} | {num(x['E'])} | {num(y['E'])} | {pct(y['E'], x['E'])} | "
                  f"{num(100 * (1 - x['E'] / x['base']), 1)}% / {num(100 * (1 - y['E'] / y['base']), 1)}% | {x['contacts']} / {y['contacts']} | "
                  f"{num(x['valid'])} ± {num(x['valid_sd'])} / {num(y['valid'])} ± {num(y['valid_sd'])} | {num(x['train'])} / {num(y['train'])} | "
                  f"{x['same']} / {y['same']} | {', '.join(edge) if edge else 'no'} |".replace("%", "%"))

    print("\n## Óptimo de t_a (A y B): mejor E para cada t_a, minimizando sobre el segundo parámetro (con recorte)")
    for m, (_, label) in METRICS.items():
        for layer in "AB":
            prof = sb[(layer, m)]["ta_profile"]
            ta_best = min(prof, key=prof.get)
            border = "sí (borde de la grilla 0,5–5 s)" if ta_best in (0.5, 5.0) else "no"
            line = " ".join(f"{t:g}:{num(v, 3)}" for t, v in prof.items())
            print(f"- {layer}, {label}: t_a óptimo = {ta_best:g} s, ¿en el borde? {border}. Perfil: {line}")
            prof_a = sa[(layer, m)]["ta_profile"]
            ta_a = min(prof_a, key=prof_a.get)
            print(f"  (sin recorte: t_a óptimo = {ta_a:g} s)")

    print("\n## Diferencias pareadas por evento entre los mejores pares (media ± error estándar; eventos en que gana la primera, de 19)")
    print("| métrica | par | sin recorte | con recorte |")
    print("|---|---|---|---|")
    for m, (_, label) in METRICS.items():
        for p, q in (("A", "B"), ("A", "F"), ("B", "F")):
            cells = []
            for s in (sa, sb):
                d = s[(p, m)]["per_event"] - s[(q, m)]["per_event"]
                cells.append(f"{num(d.mean())} ± {num(d.std(ddof=1) / np.sqrt(len(d)))} ({int((d < 0).sum())}/19)")
            print(f"| {label} | {p}−{q} | {cells[0]} | {cells[1]} |")

    print("\n## Robustez de los mejores pares (par fijo, sin recalibrar)")
    print("| capa y métrica | par | ρ: E(0,7) / E(0,9) / E(1,1) sin | con | v_0 con 3 / 5 / 7 frames: E sin | con |")
    print("|---|---|---|---|---|---|")
    for m, (_, label) in METRICS.items():
        idx = 0 if m == "ecm1_excl" else 1
        for layer in "ABF":
            cells = []
            for folder, s in ((a, sa), (b, sb)):
                pair = s[(layer, m)]["pair"]
                r = sensitivity(folder, "sensitivity_rho", layer, pair, ("0.7", "0.9", "1.1"), "rho_")
                v = sensitivity(folder, "sensitivity_v0", layer, pair, (3, 5, 7), "v0_")
                cells.append((" / ".join(num(r[k][idx]) for k in r) if r else "n/d", " / ".join(num(v[k][idx]) for k in v) if v else "n/d"))
            print(f"| {layer} {label} | {fmt_pair(sa[(layer, m)]['pair'])} → {fmt_pair(sb[(layer, m)]['pair'])} | {cells[0][0]} | {cells[1][0]} | {cells[0][1]} | {cells[1][1]} |")

    print("\n## Lado al azar (una moneda por agente y evento, 20 semillas) contra la regla de lado, en los mejores pares de ECM 1 excl.")
    print("| capa | par | regla (sin / con) | moneda media ± DE (sin / con) | semillas mejores que la regla (sin / con) | mejor lado por evento: E con el mejor de las 20 semillas en cada evento (sin / con) | eventos en que la regla es la mejor de las 21 opciones (sin / con) |")
    print("|---|---|---|---|---|---|---|")
    for layer in "AB":
        cells = []
        for folder, s in ((a, sa), (b, sb)):
            info = s[(layer, "ecm1_excl")]
            c = coin(folder, layer, info["pair"], info["E"])
            if c is None:
                cells.append(None)
                continue
            e = c["ecm1_excl"]
            pop = e.mean(axis=1)
            best_side = np.minimum(e.min(axis=0), info["per_event"])
            cells.append((info["E"], pop.mean(), pop.std(ddof=1), int((pop < info["E"]).sum()), best_side.mean(), int((info["per_event"] <= e.min(axis=0)).sum())))
        if None in cells:
            print(f"| {layer} | — | falta pruebas/moneda.txt en alguna carpeta |||||")
            continue
        x, y = cells
        print(f"| {layer} | {fmt_pair(sa[(layer, 'ecm1_excl')]['pair'])} → {fmt_pair(sb[(layer, 'ecm1_excl')]['pair'])} | {num(x[0])} / {num(y[0])} | "
              f"{num(x[1])} ± {num(x[2])} / {num(y[1])} ± {num(y[2])} | {x[3]}/20 / {y[3]}/20 | {num(x[4])} / {num(y[4])} | {x[5]}/19 / {y[5]}/19 |")

    print("\n## Chattering en los mejores pares (ρ = 0,9): conmutaciones de la capa por peatón (media / máximo de 38)")
    for m, (_, label) in METRICS.items():
        print("- " + label + ": " + "; ".join(f"{layer} {sa[(layer, m)]['switch_mean']:.1f}/{sa[(layer, m)]['switch_max']} → {sb[(layer, m)]['switch_mean']:.1f}/{sb[(layer, m)]['switch_max']}".replace(".", ",") for layer in "ABF"))


if __name__ == "__main__":
    main()
