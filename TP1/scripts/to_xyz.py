#!/usr/bin/env python3
"""Convierte Static/Dynamic a XYZ extendido para abrir en Ovito.

Uso:
  python3 scripts/to_xyz.py <static> <dynamic> [--out=particulas.xyz] [--neighbors=vecinos.txt] [--highlight=ID]

Columnas: type x y z Radius id NeighborCount [Selection]
Con --highlight, la columna Selection marca 2 = la particula elegida,
1 = sus vecinos, 0 = el resto, para colorear por "Selection" en Ovito.
"""
import sys
from pathlib import Path

from visualize import read_input, read_neighbors


def main():
    positional, out, neighbors_path, highlight = [], "particulas.xyz", None, None
    for arg in sys.argv[1:]:
        if arg.startswith("--out="):
            out = arg.split("=", 1)[1]
        elif arg.startswith("--neighbors="):
            neighbors_path = arg.split("=", 1)[1]
        elif arg.startswith("--highlight="):
            highlight = int(arg.split("=", 1)[1])
        elif arg.startswith("--"):
            sys.exit(f"Opcion desconocida: {arg}\n{__doc__}")
        else:
            positional.append(arg)

    if len(positional) != 2:
        sys.exit(__doc__)

    n, l, particles = read_input(positional[0], positional[1])
    neighbors = read_neighbors(neighbors_path) if neighbors_path else {}
    focus = set(neighbors.get(highlight, [])) if highlight else set()

    columns = 'Properties=species:S:1:pos:R:3:Radius:R:1:id:I:1:NeighborCount:I:1'
    if highlight:
        columns += ':Selection:I:1'

    with Path(out).open("w") as f:
        f.write(f"{n}\n")
        # la celda de Ovito es el cuadrado L x L (z plano)
        f.write(f'Lattice="{l} 0 0 0 {l} 0 0 0 1" {columns}\n')
        for pid, x, y, r in particles:
            count = len(neighbors.get(pid, []))
            line = f"P {x:.6f} {y:.6f} 0.0 {r:.6f} {pid} {count}"
            if highlight:
                line += f" {2 if pid == highlight else (1 if pid in focus else 0)}"
            f.write(line + "\n")

    print(f"Guardado en {out} ({n} particulas, L={l:g})")


if __name__ == "__main__":
    main()
