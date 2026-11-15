#!/usr/bin/env python3
"""Compara v0 con 3, 5 y 7 frames y con módulo v_d, conservando la dirección del ajuste de 5 frames.

Uso: python scripts/graph_gen/pilot_sensitivity.py [carpeta del piloto]
"""
import sys
from pathlib import Path

import numpy as np

METRICS = ("ecm1_excl", "ecm1_relleno", "ecm2")


def read(folder):
    events = {}
    with open(Path(folder) / "ecm.txt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("E "):
                p = line.split()
                events[int(p[1])] = (float(p[2]), float(p[3]), float(p[4]), p[7] == "true")
    return events


def row(label, folder, metric):
    m = METRICS.index(metric)
    variants = (3, 5, 7, "desired")
    runs = {n: read(Path(folder) / f"v0_{n}") for n in variants}
    if any(set(run) != set(runs[5]) for run in runs.values()):
        raise ValueError(f"Las variantes no contienen los mismos eventos: {folder}")
    pop = {n: np.mean([v[m] for v in runs[n].values()]) for n in runs}
    out = [f"{label:16s} {metric:13s} " + " ".join(f"{pop[n]:.4f}" for n in variants)]
    for n in (3, 7, "desired"):
        change = abs(pop[n] - pop[5]) / pop[5] * 100
        per_event = {e: abs(runs[n][e][m] - runs[5][e][m]) / runs[5][e][m] * 100 for e in runs[5]}
        worst = max(per_event, key=per_event.get)
        out.append(f"{change:6.2f}% {per_event[worst]:6.1f}% (ev {worst:2d})")
    contacts = "/".join(str(sum(v[3] for v in runs[n].values())) for n in variants)
    return " | ".join(out) + f" | contactos {contacts}"


def main():
    pilot = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/pilot")
    base = pilot / "sensitivity_v0"
    print("v_d = longitud experimental / duración del tramo; dirección inicial = ajuste de 5 cuadros; parámetros fijos.")
    print("par              metrica       E(3) E(5) E(7) E(v_d) | 3vs5 pob, max evento | 7vs5 pob, max evento | vdvs5 pob, max evento | contactos 3/5/7/vd")
    for metric in METRICS:
        print(row("sin capa", base / "base", metric))
    for line in (pilot / "mejores.txt").read_text(encoding="utf-8").splitlines():
        layer, metric, p1, p2 = line.split()
        print(row(f"{layer}({p1},{p2})", base / f"{layer}_{p1}_{p2}", metric))
    print("exploratoria, elegida post-hoc:")
    for line in (pilot / "mejores_exploratoria.txt").read_text(encoding="utf-8").splitlines():
        layer, metric, p1, p2 = line.split()
        print(row(f"{layer}*({p1},{p2})", base / f"{layer}_{p1}_{p2}", metric))


if __name__ == "__main__":
    main()
