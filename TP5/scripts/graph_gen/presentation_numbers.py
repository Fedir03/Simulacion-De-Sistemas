#!/usr/bin/env python3
"""Números para la presentación con el recorte vigente: D(45°), persistencia 5, opción 1, compuerta de tramo
compartido X = 1,5 m (post-hoc). Δt = Δt_exp/64 salvo donde se indica. ECM 1 = variante excluyente.
Uso: py scripts/graph_gen/presentation_numbers.py > outputs/pilot/numeros_presentacion.md
"""
import sys
from pathlib import Path

import numpy as np

from pilot_analysis import load_grid

P = Path("outputs/pilot")
D45 = Path("outputs/pilot_d45")
X = P / "recorte_extra"
BASE = Path("outputs/baseline")
PAIRS = {"A": (3.0, 0.5), "B": (3.5, 1.0), "F": (0.9, 3.0)}      # mejores de ECM 1 excl. con la compuerta
COL = {"ecm1": 3, "ecm2": 5, "contact": 10, "dmin": 11, "tdmin": 12, "sw1": 15, "sw2": 16}


def c(v, d=4):
    return f"{v:.{d}f}".replace(".", ",")


def pct(new, old):
    return f"{100 * (new / old - 1):+.1f}%".replace(".", ",")


def lbl(layer, pair):
    return f"{layer}({pair[0]:g}; {pair[1]:g})".replace(".", ",")


def rows_of(path, pair=None):
    r = load_grid(path)
    if pair is not None:
        r = r[(r[:, 0] == pair[0]) & (r[:, 1] == pair[1])]
    return r[np.argsort(r[:, 2])]


def rho_file(layer, pair, rho):
    return X / "rho" / f"con_{layer.lower()}_{pair[0]:g}_{pair[1]:g}_rho{rho}.txt"


def baseline_events(folder):
    ev = {}
    for line in (folder / "ecm.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("E "):
            p = line.split()
            ev[int(p[1])] = {"ecm1": float(p[2]), "ecm2": float(p[4]), "contact": p[7] == "true", "dmin_exp": float(p[8]), "tdmin_exp": float(p[9])}
    return ev


def ecm_folder(folder):
    ev = baseline_events(folder)
    return np.mean([e["ecm1"] for e in ev.values()]), np.mean([e["ecm2"] for e in ev.values()]), sum(e["contact"] for e in ev.values())


def switches(rows):
    sw = np.concatenate([rows[:, COL["sw1"]], rows[:, COL["sw2"]]])
    return sw.mean(), int(sw.max())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("# Números para la presentación (recorte vigente con compuerta)")
    print("Recorte: D(45°), persistencia 5, target y v_d en la ventana común (opción 1), compuerta de tramo compartido X = 1,5 m "
          "(post-hoc). Δt = Δt_exp/64 y salida cada Δt_exp/4 salvo que se indique. ECM 1 = variante excluyente. "
          "Pares: los mejores de ECM 1 excl. de la grilla oficial, A(3; 0,5), B(3,5; 1), F(0,9; 3).\n")

    print("## Robustez a ρ (par fijo en su óptimo de ρ = 0,9; base de los cambios: ρ = 0,9)")
    print("| par | ρ | ECM 1 excl. | cambio | ECM 2 | eventos con contacto | conmutaciones por peatón (media / máx.) |")
    print("|---|---|---|---|---|---|---|")
    for layer in ("A", "B"):
        pair = PAIRS[layer]
        ref = rows_of(rho_file(layer, pair, "0.9"))[:, 3].mean()
        for rho in ("0.7", "0.8", "0.9", "1.0", "1.1"):
            r = rows_of(rho_file(layer, pair, rho))
            m, mx = switches(r)
            print(f"| {lbl(layer, pair)} | {rho.replace('.', ',')} | {c(r[:, 3].mean())} | {pct(r[:, 3].mean(), ref)} | {c(r[:, 5].mean())} | "
                  f"{int(r[:, 10].sum())} | {c(m, 2)} / {mx} |")

    print("\n## Velocidad inicial (3, 5 y 7 cuadros del ajuste lineal, D12) y paso de tiempo (Δt_exp/32 contra /64)")
    print("Base de los cambios: 5 cuadros y Δt_exp/64.")
    print("| par | ECM 1 excl. con 3 / 5 / 7 cuadros | cambio 3 y 7 | ECM 2 con 3 / 5 / 7 | contactos 3 / 5 / 7 | ECM 1 excl. Δt/32 vs /64 | ECM 2 Δt/32 vs /64 | máx. por evento (ECM 1) |")
    print("|---|---|---|---|---|---|---|---|")
    for layer in ("A", "B"):
        pair = PAIRS[layer]
        d = P / "sensitivity_v0" / f"{layer}_{pair[0]:g}_{pair[1]:g}"
        v = {n: ecm_folder(d / f"v0_{n}") for n in (3, 5, 7)}
        r64 = rows_of(P / f"grid_{layer}.txt", pair)
        r32 = rows_of(X / "dt" / f"{layer.lower()}_{pair[0]:g}_{pair[1]:g}_dt32.txt")
        per = np.abs(r32[:, 3] / r64[:, 3] - 1) * 100
        print(f"| {lbl(layer, pair)} | {' / '.join(c(v[n][0]) for n in (3, 5, 7))} | {pct(v[3][0], v[5][0])}, {pct(v[7][0], v[5][0])} | "
              f"{' / '.join(c(v[n][1]) for n in (3, 5, 7))} | {' / '.join(str(v[n][2]) for n in (3, 5, 7))} | "
              f"{c(r32[:, 3].mean())} / {c(r64[:, 3].mean())} ({pct(r32[:, 3].mean(), r64[:, 3].mean())}) | "
              f"{c(r32[:, 5].mean())} / {c(r64[:, 5].mean())} ({pct(r32[:, 5].mean(), r64[:, 5].mean())}) | {c(per.max(), 2)}% (evento {int(np.argmax(per)) + 1}) |")

    ev = baseline_events(BASE)
    real_d = np.array([ev[n]["dmin_exp"] for n in range(1, 20)])
    real_t = np.array([ev[n]["tdmin_exp"] for n in range(1, 20)])
    print("\n## Retraso de fase y distancia mínima (mejores pares de ECM 1 excl.; 19 eventos)")
    print("Corrimiento = t(mínimo simulado) − t(mínimo real), con t = 0 al inicio de la ventana. Diferencia de distancia = simulada − real (entre centros).")
    print("| par | corrimiento: mediana (s) | eventos tarde (corrimiento > 0) | |corrimiento| medio (s) | diferencia de d_min: mediana (m) | eventos que pasan más cerca que el real | eventos con contacto |")
    print("|---|---|---|---|---|---|---|")
    for layer in "ABF":
        r = rows_of(P / f"grid_{layer}.txt", PAIRS[layer])
        lag = r[:, COL["tdmin"]] - real_t
        dd = r[:, COL["dmin"]] - real_d
        print(f"| {lbl(layer, PAIRS[layer])} | {c(float(np.median(lag)), 2)} | {int((lag > 0).sum())}/19 | {c(float(np.abs(lag).mean()), 2)} | "
              f"{c(float(np.median(dd)), 2)} | {int((dd < 0).sum())}/19 | {int(r[:, COL['contact']].sum())}/19 |")

    # Evento representativo de las láminas 13 y 14 (el mismo punto que en los gráficos de la lámina 32): mínimo de la
    # distancia entre centros medido en cada paso (grilla) y real de la línea base; c = t(D^sim) − t(D^exp)
    rep = 16
    print(f"\n## Evento representativo {rep} (láminas 14 y 32): distancia mínima y corrimiento")
    print("| | D (m) | t del mínimo (s) | c (s) |")
    print("|---|---|---|---|")
    print(f"| real | {c(real_d[rep - 1], 4)} | {c(real_t[rep - 1], 4)} | — |")
    for layer in "AB":
        row = rows_of(P / f"grid_{layer}.txt", PAIRS[layer])[rep - 1]
        assert int(row[2]) == rep
        print(f"| {lbl(layer, PAIRS[layer])} | {c(row[COL['dmin']], 4)} | {c(row[COL['tdmin']], 4)} | "
              f"{c(row[COL['tdmin']] - real_t[rep - 1], 4)} |")

    print("\n## Sobre-esquive de B(3,5; 1): distancia mínima simulada por evento (m) según ρ, contra la real")
    print("| evento | real | ρ = 0,7 | ρ = 0,8 | ρ = 0,9 |")
    print("|---|---|---|---|---|")
    b = {rho: rows_of(rho_file("B", PAIRS["B"], rho)) for rho in ("0.7", "0.8", "0.9")}
    for k in range(19):
        print(f"| {k + 1} | {c(real_d[k], 2)} | " + " | ".join(c(b[rho][k, COL['dmin']], 2) + ("*" if b[rho][k, COL['contact']] else "") for rho in b) + " |")
    print(f"| mediana | {c(float(np.median(real_d)), 2)} | " + " | ".join(c(float(np.median(b[rho][:, COL['dmin']])), 2) for rho in b) + " |")
    print("(*) evento con contacto.")

    print("\n## Fragilidad de A: ECM 1 excl. por evento con el par anterior (5; 0,75) y el nuevo (3; 0,5)")
    old_pair, new_pair = (5.0, 0.75), (3.0, 0.5)
    cols = [("D(45°), (5; 0,75)", rows_of(D45 / "grid_A.txt", old_pair)), ("D(45°), (3; 0,5)", rows_of(D45 / "grid_A.txt", new_pair)),
            ("compuerta, (5; 0,75)", rows_of(P / "grid_A.txt", old_pair)), ("compuerta, (3; 0,5)", rows_of(P / "grid_A.txt", new_pair))]
    print("| evento | " + " | ".join(n for n, _ in cols) + " |")
    print("|---|" + "---|" * len(cols))
    for k in range(19):
        mark = " ⚠️" if k + 1 in (3, 6) else ""
        print(f"| {k + 1}{mark} | " + " | ".join(c(r[k, 3], 3) for _, r in cols) + " |")
    print("| poblacional | " + " | ".join(c(r[:, 3].mean()) for _, r in cols) + " |")
    print("| sin 3 y 6 (17 eventos) | " + " | ".join(c(np.delete(r[:, 3], [2, 5]).mean()) for _, r in cols) + " |")
    g_old, g_new = cols[2][1][:, 3], cols[3][1][:, 3]
    diff = g_new - g_old
    print(f"\nCon la compuerta, (3; 0,5) − (5; 0,75) = {c(diff.mean())} poblacional; aporte de los eventos 3 y 6: "
          f"{c((diff[2] + diff[5]) / 19)} ({c(100 * (diff[2] + diff[5]) / diff.sum(), 0)}% de la diferencia). En los otros 17 eventos la "
          f"diferencia media es {c(np.delete(diff, [2, 5]).mean())} (base: los 17).")

    print("\n## Perfil de giro real (datos recortados con la compuerta)")
    text = (P / "fase4.md").read_text(encoding="utf-8")
    sec = text[text.index("## Fase 4.4"):]
    for line in sec.splitlines()[1:12]:
        if line.startswith("- ") or line.startswith("Desvío"):
            print(line)

    print("\n## Chattering en los pares elegidos (ρ = 0,9): conmutaciones de la capa por peatón (38 peatones)")
    for layer in ("A", "B"):
        r = rows_of(P / f"grid_{layer}.txt", PAIRS[layer])
        m, mx = switches(r)
        print(f"- {lbl(layer, PAIRS[layer])}: media {c(m, 2)}, máximo {mx}; peatones con más de 2: "
              f"{int((np.concatenate([r[:, COL['sw1']], r[:, COL['sw2']]]) > 2).sum())}/38.")

    b0, b1, bc = ecm_folder(BASE)
    print(f"\n## Línea base sin capa con la compuerta: ECM 1 excl. {c(b0)}, ECM 2 {c(b1)}, eventos con contacto {bc}/19.")


if __name__ == "__main__":
    main()
