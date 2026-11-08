#!/usr/bin/env python3
"""Lectura de corridas y datos experimentales para las figuras y la animación. Solo numpy: los tests no necesitan matplotlib."""
import re
from pathlib import Path

import numpy as np

R = 0.25
EXPERIMENTAL = "exp."


def read_run(path):
    """Archivo evento_XX.txt del motor: (encabezado como dict, filas t x1 y1 vx1 vy1 x2 y2 vx2 vy2)."""
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        first = f.readline()
    header = dict(re.findall(r"(\w+)=(\S+)", first))
    return header, np.genfromtxt(path, comments="#")


def read_directions(path):
    """Archivo direccion_XX.txt: t on1 ex1 ey1 tx1 ty1 on2 ex2 ey2 tx2 ty2."""
    return np.genfromtxt(path, comments="#")


def experimental(data_dir, header):
    """Trayectorias experimentales de los dos peatones en la ventana común, con t = 0 en el primer frame común."""
    first, last, dt = int(header["frame_inicial"]), int(header["frame_final"]), float(header["dt_exp"])
    out = []
    for key in ("id1", "id2"):
        target = int(header[key])
        rows = []
        for line in (Path(data_dir) / "elusion_1_contra_1.txt").read_text(encoding="latin1").splitlines():
            p = line.split()
            if len(p) == 5 and not line.startswith("#") and int(p[0]) == target and first <= int(p[1]) <= last:
                rows.append(((int(p[1]) - first) * dt, float(p[2]), float(p[3])))
        out.append(np.array(sorted(rows)))
    return out


def marks(t, every=0.5):
    """Índices de las muestras más cercanas a 0, every, 2 every, ..."""
    targets = np.arange(0, t[-1] + 1e-9, every)
    return np.unique([int(np.argmin(np.abs(t - x))) for x in targets])


def closest_approach(t, a, b):
    """Índice del máximo acercamiento entre dos series (t, x, y) a los mismos tiempos; ignora NaN."""
    d = np.hypot(a[:, 0] - b[:, 0], a[:, 1] - b[:, 1])
    return int(np.nanargmin(d)), d


def deviation_degrees(ex, ey, tx, ty):
    """Ángulo de e_target respecto de e_t; positivo hacia la derecha del peatón."""
    return np.degrees(np.arctan2(tx * ey - ty * ex, tx * ex + ty * ey))


def common_times(exp_a, exp_b):
    """Instantes con posición de los dos peatones experimentales (por los huecos de frames)."""
    t = np.intersect1d(np.round(exp_a[:, 0], 9), np.round(exp_b[:, 0], 9))
    ia = [int(np.argmin(np.abs(exp_a[:, 0] - x))) for x in t]
    ib = [int(np.argmin(np.abs(exp_b[:, 0] - x))) for x in t]
    return t, exp_a[ia, 1:], exp_b[ib, 1:]


def best_pairs(pilot, metric):
    """Mejor par de cada capa para la métrica, de outputs/pilot/mejores.txt."""
    out = {}
    for line in (Path(pilot) / "mejores.txt").read_text(encoding="utf-8").splitlines():
        layer, m, p1, p2 = line.split()
        if m == metric:
            out[layer] = (p1, p2)
    return out
