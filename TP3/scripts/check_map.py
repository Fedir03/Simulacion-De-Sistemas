"""Verifica y dibuja un mapa de obstáculos a partir de una condición inicial tp3-v1.

Discretiza el espacio de centros de partícula (puntos a distancia ≥ r de las paredes
y ≥ R_k + r de cada obstáculo), lo separa en componentes conexas y marca como
atrapadas las que no llegan a ningún arco: una partícula que nace ahí nunca hace gol.
"""
import argparse
import sys

import numpy as np
from scipy import ndimage

from simulation_io import parse_simulation


def accessible_grid(data, radius, step):
    xs = np.arange(step / 2, data.length, step)
    ys = np.arange(step / 2, data.width, step)
    x, y = np.meshgrid(xs, ys, indexing='ij')
    free = (x >= radius) & (x <= data.length - radius) & (y >= radius) & (y <= data.width - radius)
    for ox, oy, orad in data.obstacles:
        free &= np.hypot(x - ox, y - oy) >= orad + radius
    return xs, ys, free


def analyze(data, radius, step):
    xs, ys, free = accessible_grid(data, radius, step)
    labels, count = ndimage.label(free)
    in_goal = np.abs(ys - data.width / 2) <= data.goal_width / 2
    # Columnas cuyo centro puede tocar la pared corta (x = r o x = L - r).
    left = xs <= radius + step
    right = xs >= data.length - radius - step
    goal_labels = set(np.unique(labels[np.ix_(left, in_goal)])) | set(np.unique(labels[np.ix_(right, in_goal)]))
    goal_labels.discard(0)
    cell = step * step
    sizes = ndimage.sum(free, labels, range(1, count + 1)) * cell
    trapped = [(label, area) for label, area in zip(range(1, count + 1), sizes) if label not in goal_labels]
    left_open = bool(np.any(labels[np.ix_(left, in_goal)]))
    right_open = bool(np.any(labels[np.ix_(right, in_goal)]))
    particles = data.frames[0].particles
    ix = np.clip((np.array([p[1] for p in particles]) / step).astype(int), 0, len(xs) - 1)
    iy = np.clip((np.array([p[2] for p in particles]) / step).astype(int), 0, len(ys) - 1)
    # Una partícula en contacto con un obstáculo puede caer en una celda apenas bloqueada:
    # se usa la componente de las celdas libres vecinas.
    stuck = 0
    for i, j in zip(ix, iy):
        near = set(np.unique(labels[max(i - 1, 0):i + 2, max(j - 1, 0):j + 2])) - {0}
        stuck += bool(near) and not (near & goal_labels)
    return {
        'xs': xs, 'ys': ys, 'free': free, 'components': count,
        'area': free.sum() * cell, 'trapped': trapped,
        'left_open': left_open, 'right_open': right_open, 'stuck_particles': stuck,
    }


def plot(data, result, radius, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle

    fig, ax = plt.subplots(figsize=(8, 8 * data.width / data.length + 0.6))
    ax.add_patch(Rectangle((0, 0), data.length, data.width, fill=False, lw=1.5, color='black'))
    ax.imshow(result['free'].T, origin='lower', extent=(0, data.length, 0, data.width),
              cmap=matplotlib.colors.ListedColormap(['white', '#dbe9f6']), interpolation='none')
    for ox, oy, orad in data.obstacles:
        ax.add_patch(Circle((ox, oy), orad, color='0.45', lw=0))
    for p in data.frames[0].particles:
        ax.add_patch(Circle((p[1], p[2]), p[3], color=p[4], lw=0))
    lo, hi = (data.width - data.goal_width) / 2, (data.width + data.goal_width) / 2
    for x in (0, data.length):
        ax.plot([x, x], [lo, hi], color='#2ca02c', lw=5, solid_capstyle='butt')
    ax.set_xlim(-0.02, data.length + 0.02)
    ax.set_ylim(-0.02, data.width + 0.02)
    ax.set_aspect('equal')
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('initial', help='condición inicial o trayectoria tp3-v1 (se usa el primer cuadro)')
    parser.add_argument('--step', type=float, default=5e-4, help='paso de la grilla en metros (0.0005)')
    parser.add_argument('--png', help='guardar un dibujo del mapa con la condición inicial')
    args = parser.parse_args(argv)
    if args.step <= 0:
        parser.error('--step debe ser positivo')
    data = parse_simulation(args.initial)
    radius = data.frames[0].particles[0][3]
    result = analyze(data, radius, args.step)
    table = data.length * data.width
    obstacle_area = sum(np.pi * o[2] ** 2 for o in data.obstacles)
    print(f'K={len(data.obstacles)} área de obstáculos={obstacle_area:.4f} m² ({obstacle_area / table:.1%} de la mesa)')
    print(f'área accesible para centros={result["area"]:.4f} m² en {result["components"]} componente(s)')
    print(f'arco izquierdo alcanzable={result["left_open"]} arco derecho alcanzable={result["right_open"]}')
    trapped_area = sum(area for _, area in result['trapped'])
    print(f'componentes sin arco={len(result["trapped"])} (área {trapped_area:.2e} m²) '
          f'partículas iniciales atrapadas={result["stuck_particles"]}')
    if args.png:
        plot(data, result, radius, args.png)
        print(f'Mapa: {args.png}')
    return 1 if result['trapped'] or not (result['left_open'] or result['right_open']) else 0


if __name__ == '__main__':
    sys.exit(main())
