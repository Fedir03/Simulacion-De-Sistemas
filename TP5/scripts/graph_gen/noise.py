#!/usr/bin/env python3
"""Estima el ruido de seguimiento (D12) con segundas diferencias de la trayectoria de cada peatón.

Para ruido blanco de desvío s, Var(x[k+1] - 2 x[k] + x[k-1]) = 6 s^2. La aceleración real aporta
a Δt^2, que a 15 fps es del orden de 1 cm por cada 2 m/s^2. Por eso se informa también la versión
robusta (MAD), menos sensible a los tramos con aceleración.

Uso: python scripts/graph_gen/noise.py [carpeta de datos]
"""
import math
import re
import sys
from pathlib import Path

import numpy as np

DT_EXP = 1 / 15.0192
EVENT = re.compile(r"prueba\s+\d+:\s+sale izquierda\s+(\S+),\s+sale derecha\s+(\S+),\s+cuadros\s+(\d+)-(\d+)")


def load(data_dir):
    rows = {}
    for line in (data_dir / "elusion_1_contra_1.txt").read_text(encoding="latin1").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        p = line.split()
        rows.setdefault(int(p[0]), []).append((int(p[1]), float(p[2]), float(p[3])))
    return {k: np.array(v) for k, v in rows.items()}


def second_differences(track):
    """Segundas diferencias solo sobre tríos de frames consecutivos."""
    consecutive = (track[1:-1, 0] - track[:-2, 0] == 1) & (track[2:, 0] - track[1:-1, 0] == 1)
    d = track[2:, 1:] - 2 * track[1:-1, 1:] + track[:-2, 1:]
    return d[consecutive]


def main():
    data_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
    rows = load(data_dir)
    all_d = []
    for line in (data_dir / "LEEME_elusion1contra1.txt").read_text(encoding="latin1").splitlines():
        m = EVENT.search(line)
        if not m:
            continue
        lo, hi = int(m.group(3)), int(m.group(4))
        for text in m.group(1, 2):
            track = rows[1000 if text == "V?" else int(text)]
            all_d.append(second_differences(track[(track[:, 0] >= lo) & (track[:, 0] <= hi)]))
    d = np.concatenate(all_d).ravel()
    sigma_rms = float(np.std(d)) / math.sqrt(6)
    sigma_mad = 1.4826 * float(np.median(np.abs(d - np.median(d)))) / math.sqrt(6)
    print(f"muestras={d.size}")
    print(f"sigma_rms={sigma_rms * 100:.3f} cm  sigma_mad={sigma_mad * 100:.3f} cm")
    print("error de velocidad esperado con ese ruido (sigma_mad):")
    print(f"  hacia adelante: {math.sqrt(2) * sigma_mad / DT_EXP:.3f} m/s")
    print(f"  central:        {sigma_mad / (math.sqrt(2) * DT_EXP):.3f} m/s")
    for n in (3, 5, 7):
        stt = sum((k - (n - 1) / 2) ** 2 for k in range(n)) * DT_EXP ** 2
        print(f"  ajuste de {n}:     {sigma_mad / math.sqrt(stt):.3f} m/s")


if __name__ == "__main__":
    main()
