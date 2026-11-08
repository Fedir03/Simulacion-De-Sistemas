#!/usr/bin/env python3
"""Analiza el piloto: mejores pares, error de entrenamiento y forma de la superficie de cada capa.

El piloto usa los 19 eventos para elegir el par, así que el error informado es de entrenamiento.
Uso: python scripts/graph_gen/pilot_analysis.py [carpeta del piloto] [carpeta de la línea base]
"""
import sys
from pathlib import Path

import numpy as np

METRICS = {"ecm1_excl": 3, "ecm1_relleno": 4, "ecm2": 5}
NAMES = {"A": ("t_a", "l"), "B": ("t_a", "k"), "F": ("A_p", "B_p"), "F_angular5": ("A_p", "B_p"), "F_angular1": ("A_p", "B_p")}


def load_grid(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            p = line.split()
            rows.append([float(v) for v in p[:10]] + [p[10] == "true"] + [float(v) for v in p[11:]])
    return np.array(rows, dtype=float)


def load_baseline(folder):
    out = {}
    with open(Path(folder) / "ecm.txt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("E "):
                p = line.split()
                out[int(p[1])] = {"ecm1_excl": float(p[2]), "ecm1_relleno": float(p[3]), "ecm2": float(p[4]), "contacto": p[7] == "true"}
    return out


def ranks(x):
    order = np.argsort(x)
    r = np.empty(len(x))
    r[order] = np.arange(len(x))
    # Empates: rango promedio
    for v in np.unique(x):
        mask = x == v
        r[mask] = r[mask].mean()
    return r


def spearman(a, b):
    if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(ranks(a), ranks(b))[0, 1])


def surface(rows, column):
    p1 = np.unique(rows[:, 0])
    p2 = np.unique(rows[:, 1])
    z = np.zeros((len(p1), len(p2)))
    for i, a in enumerate(p1):
        for j, b in enumerate(p2):
            z[i, j] = rows[(rows[:, 0] == a) & (rows[:, 1] == b), column].mean()
    return p1, p2, z


def print_surface(name, p1, p2, z, best):
    n1, n2 = NAMES[name]
    print(f"  {n1} \\ {n2}: " + " ".join(f"{v:6.2f}" for v in p2))
    for i, a in enumerate(p1):
        marks = " ".join(f"{z[i, j]:5.3f}" + ("*" if (i, j) == best else " ") for j in range(len(p2)))
        print(f"  {a:9.2f}: {marks}")


def collapse(name, p1, p2, z):
    """¿La superficie depende de una sola combinación de parámetros? R² de E contra esa combinación (polinomio grado 4)."""
    a, b = np.meshgrid(p1, p2, indexing="ij")
    a, b, e = a.ravel(), b.ravel(), z.ravel()

    def r2(x):
        keep = np.isfinite(x)
        coef = np.polyfit(x[keep], e[keep], 4)
        residual = e[keep] - np.polyval(coef, x[keep])
        return 1 - residual.var() / e[keep].var()

    if name.startswith("F"):
        # Intensidad a una distancia típica: A_p exp(−d*/B_p)
        best = max(((r2(np.log(a) - d / b), d) for d in np.arange(0.25, 8.01, 0.25)))
        return f"E vs A_p exp(-d*/B_p): R2={best[0]:.3f} con d*={best[1]:.2f} m | E vs solo A_p: R2={r2(a):.3f} | E vs solo B_p: R2={r2(b):.3f}"
    keep = b > 0
    a, b, e = a[keep], b[keep], e[keep]
    return f"E vs {NAMES[name][1]}/t_a (angulo del desvio): R2={r2(b / a):.3f} | E vs solo t_a: R2={r2(a):.3f} | E vs solo {NAMES[name][1]}: R2={r2(b):.3f}"


def describe(name, rows, baseline):
    n1, n2 = NAMES[name]
    print(f"\n===== Capa {name} ({n1}, {n2}): {len(np.unique(rows[:, 0]))} x {len(np.unique(rows[:, 1]))} =====")
    events = sorted(baseline)
    results = {}
    for metric, column in METRICS.items():
        p1, p2, z = surface(rows, column)
        i, j = np.unravel_index(np.argmin(z), z.shape)
        a, b = p1[i], p2[j]
        at = rows[(rows[:, 0] == a) & (rows[:, 1] == b)]
        at = at[np.argsort(at[:, 2])]
        values = at[:, column]
        base = np.array([baseline[e][metric] for e in events])
        edge = i in (0, len(p1) - 1) or j in (0, len(p2) - 1)
        first_arrival = np.fmin(at[:, 13], at[:, 14])
        arrival_ok = np.all(np.isnan(first_arrival) | (first_arrival > at[:, 12]))
        results[metric] = dict(a=a, b=b, e=z[i, j], sem=values.std(ddof=1) / np.sqrt(len(values)), base=base.mean(),
                               improved=int((values < base).sum()), contacts=int(at[:, 10].sum()),
                               edge=edge, near5=int((z <= z.min() * 1.05).sum()), near10=int((z <= z.min() * 1.10).sum()),
                               total=z.size, switches=float(at[:, 15:17].mean()), max_switches=int(at[:, 15:17].max()),
                               retired=int(np.isfinite(at[:, 13:15]).sum()), arrival_ok=bool(arrival_ok),
                               spread=float(z.max() / z.min()))
        r = results[metric]
        print(f"\n{metric}: mejor ({n1}={a:g}, {n2}={b:g}) E={r['e']:.4f} +- {r['sem']:.4f} (SEM) | base={r['base']:.4f} | mejora {100 * (1 - r['e'] / r['base']):.1f}%")
        print(f"  eventos que mejoran: {r['improved']}/19 | eventos con contacto: {r['contacts']}/19 | en borde de grilla: {edge}")
        print(f"  conmutaciones por agente: media {r['switches']:.1f}, max {r['max_switches']} | retirados en ventana: {r['retired']}/38 | llegada posterior a d_min: {r['arrival_ok']}")
        print(f"  celdas a menos de 5%: {r['near5']}/{r['total']}, a menos de 10%: {r['near10']}/{r['total']} | max/min de la superficie: {r['spread']:.2f}")
        near = z <= z.min() * 1.10
        aa, bb = np.meshgrid(p1, p2, indexing="ij")
        print(f"  region a <10%: {n1} en [{aa[near].min():g}, {aa[near].max():g}], {n2} en [{bb[near].min():g}, {bb[near].max():g}] | Spearman({n1}, {n2}) en esa region: {spearman(aa[near], bb[near]):.2f}")
        print(f"  mejor {n2} por cada {n1}: " + " ".join(f"{p2[np.argmin(z[k])]:g}" for k in range(len(p1))))
        print(f"  mejor {n1} por cada {n2}: " + " ".join(f"{p1[np.argmin(z[:, k])]:g}" for k in range(len(p2))))
        print("  " + collapse(name, p1, p2, z))
        # Rugosidad: diferencia media entre vecinos contra el rango total
        rough = (np.abs(np.diff(z, axis=0)).mean() + np.abs(np.diff(z, axis=1)).mean()) / 2 / (z.max() - z.min())
        print(f"  salto medio entre celdas vecinas / rango: {rough:.3f}")
        print_surface(name, p1, p2, z, (i, j))
    return results


def paired(pilot, all_results):
    """Diferencia entre capas en su mejor par, evento por evento: los eventos son los mismos para todas."""
    print("\n===== Comparacion pareada entre mejores pares (por evento) =====")
    print("metrica par: dif media (primera - segunda) +- SEM | eventos donde gana la primera | |t|")
    grids = {name: load_grid(pilot / f"grid_{name}.txt") for name in ("A", "B", "F")}
    grids["Fx"] = load_grid(pilot / "exploratoria" / "F_amplia.txt")   # exploratoria, elegida post-hoc

    def values(name, metric):
        g = grids[name]
        p1, p2, z = surface(g, METRICS[metric])
        i, j = np.unravel_index(np.argmin(z), z.shape)
        at = g[(g[:, 0] == p1[i]) & (g[:, 1] == p2[j])]
        return at[np.argsort(at[:, 2]), METRICS[metric]]

    for metric in METRICS:
        for x, y in (("A", "B"), ("A", "F"), ("B", "F"), ("A", "Fx"), ("B", "Fx")):
            d = values(x, metric) - values(y, metric)
            sem = d.std(ddof=1) / np.sqrt(len(d))
            print(f"{metric} {x}-{y}: {d.mean():+.4f} +- {sem:.4f} | {int((d < 0).sum())}/19 | {abs(d.mean()) / sem:.2f}")
    print("\nconmutaciones por agente en TODA la grilla: media, percentil 99, maximo")
    for name, g in grids.items():
        sw = g[:, 15:17].ravel()
        print(f"{name}: {sw.mean():.2f} {np.percentile(sw, 99):.0f} {sw.max():.0f}")


def main():
    pilot = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/pilot")
    baseline = load_baseline(sys.argv[2] if len(sys.argv) > 2 else "outputs/baseline")
    all_results = {}
    for name in ("A", "B", "F", "F_angular5", "F_angular1"):
        path = pilot / f"grid_{name}.txt"
        if path.exists():
            all_results[name] = describe(name, load_grid(path), baseline)
    print("\n===== Tabla comparativa =====")
    print("capa metrica n1 n2 E SEM mejora% eventos_mejoran contactos borde")
    for name, results in all_results.items():
        for metric, r in results.items():
            print(f"{name} {metric} {r['a']:g} {r['b']:g} {r['e']:.4f} {r['sem']:.4f} {100 * (1 - r['e'] / r['base']):.1f} {r['improved']} {r['contacts']} {r['edge']}")
    paired(pilot, all_results)
    with open(pilot / "mejores.txt", "w", encoding="utf-8") as f:
        for name, results in all_results.items():
            if name.startswith("F_"):
                continue
            for metric, r in results.items():
                f.write(f"{name} {metric} {r['a']:g} {r['b']:g}\n")
    # La zona exploratoria se eligió después de ver los datos: va en su propio archivo
    with open(pilot / "mejores_exploratoria.txt", "w", encoding="utf-8") as f:
        wide = load_grid(pilot / "exploratoria" / "F_amplia.txt")
        for metric, column in METRICS.items():
            p1, p2, z = surface(wide, column)
            i, j = np.unravel_index(np.argmin(z), z.shape)
            f.write(f"F {metric} {p1[i]:g} {p2[j]:g}\n")


if __name__ == "__main__":
    main()
