#!/usr/bin/env python3
"""Visualiza el input del TP1 y la grilla del Cell Index Method.

Uso:
  python3 scripts/visualize.py <static> <dynamic> [opciones]

Opciones:
  --out=ARCHIVO    archivo de vecinos generado por CimRunner (dibuja los enlaces)
  --rc=FLOAT       radio de interaccion (default 1.0), solo para dibujar y calcular M
  --m=INT          celdas por lado (default: el M maximo valido, igual que en Java)
  --periodic       la vecindad de celdas envuelve por los bordes
  --highlight=ID   resalta esa particula, sus vecinos y las celdas que CIM recorre
  --save=ARCHIVO   guarda un PNG en vez de abrir una ventana
  --interactive    click sobre una particula para resaltarla en vivo
"""
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle


def strip_bom(line):
    return line.lstrip("﻿")


def read_input(static_path, dynamic_path):
    static_lines = Path(static_path).read_text().splitlines()
    n = int(strip_bom(static_lines[0]).strip())
    l = float(strip_bom(static_lines[1]).strip())
    radii = [float(static_lines[i + 2].split()[0]) for i in range(n)]

    dynamic_lines = Path(dynamic_path).read_text().splitlines()
    coords = []
    for i in range(n):
        parts = strip_bom(dynamic_lines[i + 1]).split()
        coords.append((float(parts[0]), float(parts[1])))

    # ids 1-indexed, igual que InputReader
    return n, l, [(i + 1, x, y, r) for i, ((x, y), r) in enumerate(zip(coords, radii))]


def read_neighbors(path):
    neighbors = {}
    for line in Path(path).read_text().splitlines():
        line = strip_bom(line).strip()
        if not line:
            continue
        fields = [int(f) for f in line.split(",")]
        neighbors[fields[0]] = fields[1:]
    return neighbors


def max_valid_m(l, rc, r_max):
    """Mismo criterio que CellIndexMethod.maxValidM: L/M > rc + 2*rMax."""
    min_cell = rc + 2 * r_max
    if min_cell <= 0:
        return 1
    return max(1, math.ceil(l / min_cell) - 1)


def parse_args(argv):
    opts = {
        "out": None, "rc": 1.0, "m": None, "periodic": False,
        "highlight": None, "save": None, "interactive": False,
    }
    positional = []
    for arg in argv:
        if arg == "--periodic":
            opts["periodic"] = True
        elif arg == "--interactive":
            opts["interactive"] = True
        elif arg.startswith("--out="):
            opts["out"] = arg.split("=", 1)[1]
        elif arg.startswith("--rc="):
            opts["rc"] = float(arg.split("=", 1)[1])
        elif arg.startswith("--m="):
            opts["m"] = int(arg.split("=", 1)[1])
        elif arg.startswith("--highlight="):
            opts["highlight"] = int(arg.split("=", 1)[1])
        elif arg.startswith("--save="):
            opts["save"] = arg.split("=", 1)[1]
        elif arg.startswith("--"):
            sys.exit(f"Opcion desconocida: {arg}\n{__doc__}")
        else:
            positional.append(arg)

    if len(positional) != 2:
        sys.exit(__doc__)
    return positional[0], positional[1], opts


def draw(ax, l, m, particles, neighbors, rc, periodic, highlight):
    cell_size = l / m
    ax.clear()

    # grilla de celdas
    # zorder 1: las lineas de la grilla se dibujan por encima del sombreado de celdas
    for k in range(m + 1):
        ax.axvline(k * cell_size, color="0.85", lw=0.6, zorder=1)
        ax.axhline(k * cell_size, color="0.85", lw=0.6, zorder=1)
    ax.add_patch(Rectangle((0, 0), l, l, fill=False, ec="black", lw=1.4, zorder=3))

    by_id = {p[0]: p for p in particles}
    highlighted = by_id.get(highlight)
    neighbor_ids = set(neighbors.get(highlight, [])) if highlighted else set()

    if highlighted:
        # las 9 celdas que CIM recorre alrededor de la particula consultada
        cx = min(m - 1, int(highlighted[1] / cell_size))
        cy = min(m - 1, int(highlighted[2] / cell_size))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = cx + dx, cy + dy
                if periodic:
                    nx, ny = nx % m, ny % m
                elif not (0 <= nx < m and 0 <= ny < m):
                    continue
                ax.add_patch(Rectangle((nx * cell_size, ny * cell_size), cell_size, cell_size,
                                       fc="#fdf5d4", ec="none", zorder=0))
        # alcance rc medido borde a borde desde la particula resaltada
        ax.add_patch(Circle((highlighted[1], highlighted[2]), highlighted[3] + rc,
                            fill=False, ec="#d62728", ls="--", lw=1.0, zorder=4))
        for j in neighbor_ids:
            if j in by_id:
                ax.plot([highlighted[1], by_id[j][1]], [highlighted[2], by_id[j][2]],
                        color="#d62728", lw=0.9, alpha=0.7, zorder=4)
    elif neighbors:
        # sin foco: todos los enlaces, cada par una sola vez
        for i, js in neighbors.items():
            for j in js:
                if i < j and i in by_id and j in by_id:
                    ax.plot([by_id[i][1], by_id[j][1]], [by_id[i][2], by_id[j][2]],
                            color="#1f77b4", lw=0.5, alpha=0.35, zorder=2)

    for pid, x, y, r in particles:
        if pid == highlight:
            fc, ec = "#d62728", "black"
        elif pid in neighbor_ids:
            fc, ec = "#ff9d3c", "black"
        else:
            fc, ec = "#7fb3d5", "0.35"
        ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=0.5, zorder=5, picker=True,
                            gid=str(pid)))

    margin = 0.03 * l
    ax.set_xlim(-margin, l + margin)
    ax.set_ylim(-margin, l + margin)
    ax.set_aspect("equal")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    title = f"N={len(particles)}  L={l:g}  M={m}  celda={cell_size:.3f}  rc={rc:g}"
    if periodic:
        title += "  (periodico)"
    if highlighted:
        title += f"\nparticula {highlight}: {len(neighbor_ids)} vecinos"
    ax.set_title(title, fontsize=10)


def main():
    static_path, dynamic_path, opts = parse_args(sys.argv[1:])
    n, l, particles = read_input(static_path, dynamic_path)
    neighbors = read_neighbors(opts["out"]) if opts["out"] else {}

    r_max = max(p[3] for p in particles)
    m = opts["m"] or max_valid_m(l, opts["rc"], r_max)
    cell_size = l / m
    if cell_size <= opts["rc"] + 2 * r_max:
        print(f"Aviso: M={m} no cumple L/M > rc + 2*rMax "
              f"({cell_size:.4f} <= {opts['rc'] + 2 * r_max:.4f}); se grafica igual.",
              file=sys.stderr)

    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    state = {"highlight": opts["highlight"]}
    draw(ax, l, m, particles, neighbors, opts["rc"], opts["periodic"], state["highlight"])

    if opts["interactive"]:
        def on_pick(event):
            gid = event.artist.get_gid()
            if gid is None:
                return
            pid = int(gid)
            state["highlight"] = None if state["highlight"] == pid else pid
            draw(ax, l, m, particles, neighbors, opts["rc"], opts["periodic"], state["highlight"])
            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("pick_event", on_pick)
        if not neighbors:
            print("Aviso: sin --out no hay vecinos para resaltar.", file=sys.stderr)

    fig.tight_layout()
    if opts["save"]:
        fig.savefig(opts["save"], dpi=200)
        print(f"Guardado en {opts['save']}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
