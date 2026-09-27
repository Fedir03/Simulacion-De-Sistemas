"""Mapas de ejemplo de cada familia de configuraciones (columna derecha de las
diapositivas de Resultados): solo la mesa, los arcos y los obstáculos, sin ejes ni
partículas, para que el dibujo ocupe todo el ancho disponible.

Cada mapa es un archivo de obstáculos en formato de competencia ("x y R" por línea).
Los que no están en TP3/configs/ se generan con `generate --obstacles-out`:
    java -jar TP3/target/tp3.jar generate --obstacle-algorithm single --obstacle-radius 0.34 \\
        --out /tmp/ic.txt --obstacles-out TP3/generated/mapas/central_R0.34.txt
    java -jar TP3/target/tp3.jar generate --obstacle-algorithm semicircle --obstacle-goals both \\
        --obstacle-free-radius 0.35 --obstacle-center-offset 0.2 \\
        --out /tmp/ic.txt --obstacles-out TP3/generated/mapas/cuenco_desplazado_s0.20.txt

Uso, desde la raíz del repositorio:
    python3 TP3/presentacion/figuras/plot_mapas.py obstaculos.txt mapa-salida.png [...]
(pares archivo de obstáculos / figura; una figura relativa se guarda en este directorio).
"""

import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from pathlib import Path

L, W, D = 1.20, 0.68, 0.20
COLOR_OBSTACULO = "#475569"  # mismos colores que animate.py
COLOR_MESA = "#f1f5f9"
COLOR_ARCO = "#16a34a"


def leer(path):
    obstaculos = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#")[0].split()
            if line:
                obstaculos.append(tuple(float(v) for v in line[:3]))
    return obstaculos


def dibujar(obstaculos, out):
    fig, ax = plt.subplots(figsize=(4, 4 * W / L), dpi=250)
    ax.add_patch(Rectangle((0, 0), L, W, facecolor=COLOR_MESA, edgecolor="black", linewidth=1.2))
    for x, y, r in obstaculos:
        ax.add_patch(Circle((x, y), r, facecolor=COLOR_OBSTACULO, edgecolor="none"))
    for x in (0, L):
        ax.plot([x, x], [(W - D) / 2, (W + D) / 2], color=COLOR_ARCO, linewidth=5, solid_capstyle="butt")
    ax.set_xlim(-0.02, L + 0.02)
    ax.set_ylim(-0.02, W + 0.02)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(out)
    plt.close(fig)


def main(args):
    if not args or len(args) % 2:
        sys.exit(__doc__)
    for config, out in zip(args[::2], args[1::2]):
        out = Path(out)
        if not out.is_absolute():
            out = Path(__file__).parent / out
        dibujar(leer(config), out)
        print(f"{config} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
