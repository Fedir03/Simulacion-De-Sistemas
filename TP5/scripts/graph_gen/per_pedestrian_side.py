#!/usr/bin/env python3
"""Lado de cruce con cada calibración de la calibración por peatón (A y B): ¿pasan los dos por el mismo lado que en el real?

Lado = signo de y_izquierdo − y_derecho en el instante de máxima aproximación (real: el de la trayectoria experimental;
simulado: el de la corrida). Corre (o reutiliza) las corridas de los 19 eventos con scripts/animation/ped_videos.py.
Uso: python scripts/graph_gen/per_pedestrian_side.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "animation"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from figure_data import closest_approach, common_times, experimental, read_run  # noqa: E402
from ped_videos import CALIBS, prepare  # noqa: E402
from per_pedestrian import METRICS  # noqa: E402


def side(n, folder):
    header, run = read_run(folder / f"evento_{n:02d}.txt")
    t, a, b = common_times(*experimental(Path("data"), header))
    k, _ = closest_approach(t, a, b)
    real = np.sign(a[k, 1] - b[k, 1])
    keep = ~np.isnan(run[:, 1]) & ~np.isnan(run[:, 5])
    p1, p2 = run[keep][:, 1:3], run[keep][:, 5:7]
    j = int(np.argmin(np.hypot(*(p1 - p2).T)))
    return real == np.sign(p1[j, 1] - p2[j, 1])


events = list(range(1, 20))
print("| capa | métrica | " + " | ".join(f"lado correcto, {name}" for name, _ in CALIBS.values()) + " | eventos con el lado mal en ind. 2p |")
print("|---|---|" + "---|" * (len(CALIBS) + 1))
for layer in "AB":
    for metric, (mname, _, _) in METRICS.items():
        chosen = prepare(layer, metric, events)
        ok = {c: [side(n, chosen[n][c][3]) for n in events] for c in CALIBS}
        wrong = [n for n, good in zip(events, ok["ind2"]) if not good]
        print(f"| {layer} | {mname} | " + " | ".join(f"{sum(v)} de 19" for v in ok.values()) + f" | {', '.join(map(str, wrong)) or '—'} |")
