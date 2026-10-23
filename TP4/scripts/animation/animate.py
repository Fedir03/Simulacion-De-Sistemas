#!/usr/bin/env python3
"""Anima el output primario tp4-billiard-v1 sin ejecutar la simulación."""
import argparse
from dataclasses import dataclass
import math
from pathlib import Path

import numpy as np


@dataclass
class Simulation:
    metadata: dict
    obstacles: list
    times: np.ndarray
    positions: np.ndarray
    used: np.ndarray


def read_simulation(path):
    """Lee y valida una trayectoria completa; ordena partículas por id."""
    metadata, obstacles, times, positions, states = {}, [], [], [], []
    pending, expected_used, current_time, footer = [], None, None, None

    def finish_frame():
        if current_time is None:
            return
        n = int(metadata['N'])
        if len(pending) != n or {p[0] for p in pending} != set(range(1, n + 1)):
            raise ValueError(f'Cuadro t={current_time}: se requieren N ids únicos de 1 a {n}')
        ordered = sorted(pending)
        used = [p[3] for p in ordered]
        if sum(used) != expected_used:
            raise ValueError(f'Cuadro t={current_time}: Nu no coincide con los estados')
        if states and any(old > new for old, new in zip(states[-1], used)):
            raise ValueError('Una partícula usada volvió a fresca')
        if times and current_time <= times[-1]:
            raise ValueError('Los tiempos deben ser estrictamente crecientes')
        times.append(current_time)
        positions.append([(p[1], p[2]) for p in ordered])
        states.append(used)

    with Path(path).open(encoding='utf-8') as source:
        for number, raw in enumerate(source, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                if line.startswith('# format='):
                    metadata = dict(item.split('=', 1) for item in line[2:].split() if '=' in item)
                    if metadata['format'] != 'tp4-billiard-v1':
                        raise ValueError('Formato no soportado')
                    if int(metadata['N']) <= 0:
                        raise ValueError('N debe ser positivo')
                    for key in ('dt', 'dt2', 'tf', 'R', 'r'):
                        value = float(metadata[key])
                        if not math.isfinite(value) or value <= 0:
                            raise ValueError(f'{key} debe ser positivo y finito')
                elif line.startswith('# obstacle '):
                    obstacle = tuple(map(float, line.split()[2:]))
                    if len(obstacle) != 3 or not all(map(math.isfinite, obstacle)) or obstacle[2] <= 0:
                        raise ValueError('Obstáculo inválido')
                    obstacles.append(obstacle)
                elif line.startswith('# fin '):
                    finish_frame()
                    current_time = None
                    pending = []
                    footer = dict(item.split('=', 1) for item in line.split() if '=' in item)
                elif line.startswith('#'):
                    continue
                elif footer is not None:
                    raise ValueError('Datos después del pie de simulación')
                elif line.startswith('t='):
                    if not metadata:
                        raise ValueError('Falta cabecera')
                    finish_frame()
                    fields = dict(item.split('=', 1) for item in line.split())
                    current_time, expected_used = float(fields['t']), int(fields['Nu'])
                    if not math.isfinite(current_time) or current_time < 0:
                        raise ValueError('Tiempo inválido')
                    pending = []
                else:
                    if current_time is None:
                        raise ValueError('Partícula fuera de un cuadro')
                    pid, x, y, vx, vy, used = line.split()
                    x, y, vx, vy = map(float, (x, y, vx, vy))
                    if not all(map(math.isfinite, (x, y, vx, vy))) or used not in ('0', '1'):
                        raise ValueError('Estado de partícula inválido')
                    pending.append((int(pid), x, y, int(used)))
            except (ValueError, KeyError) as exc:
                raise ValueError(f'{path}:{number}: {exc}') from exc
    finish_frame()
    if not times or footer is None or footer.get('estado') not in ('completa', 't100'):
        raise ValueError('La trayectoria debe tener cuadros y un pie de finalización válido')
    if not math.isclose(times[0], 0, abs_tol=1e-9):
        raise ValueError('Falta el cuadro inicial t=0')
    if not np.allclose(np.diff(times), float(metadata['dt2']), rtol=1e-7, atol=1e-9):
        raise ValueError('Los tiempos no corresponden al dt2 declarado')
    if not math.isclose(times[-1], float(footer['t']), abs_tol=1e-9):
        raise ValueError('El tiempo final no coincide con el pie')
    if footer['estado'] == 'completa' and not math.isclose(times[-1], float(metadata['tf']), abs_tol=1e-9):
        raise ValueError('Faltan cuadros hasta tf')
    if not obstacles and any(any(s) for s in states):
        raise ValueError('Hay partículas usadas en una trayectoria sin obstáculos')
    return Simulation(metadata, obstacles, np.array(times), np.array(positions), np.array(states, dtype=bool))


def render_animation(data, output, *, dpi=100):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.animation import FFMpegWriter
    from matplotlib.collections import PatchCollection
    from matplotlib.lines import Line2D
    from matplotlib.patches import Circle

    if not FFMpegWriter.isAvailable():
        raise RuntimeError('Se requiere FFmpeg en PATH para exportar MP4')
    output = Path(output)
    if output.suffix.lower() != '.mp4':
        raise ValueError('--out debe terminar en .mp4')
    output.parent.mkdir(parents=True, exist_ok=True)
    meta = data.metadata
    radius, particle_radius = float(meta['R']), float(meta['r'])
    fig, ax = plt.subplots(figsize=(10, 8), dpi=dpi)
    ax.set_aspect('equal')
    ax.set(xlim=(-radius * 1.04, radius * 1.04), ylim=(-radius * 1.04, radius * 1.04))
    ax.set_axis_off()
    ax.add_patch(Circle((0, 0), radius, facecolor='#f1f5f9', edgecolor='#334155', linewidth=2))
    for x, y, r in data.obstacles:
        ax.add_patch(Circle((x, y), r, color='black', zorder=4))
    particles = PatchCollection([], edgecolor='white', linewidth=0.35, zorder=3)
    ax.add_collection(particles)
    counter = ax.text(0.5, 1.025, '', transform=ax.transAxes, ha='center', fontsize=28)
    colors = np.array(['#2563eb', '#dc2626'])
    entries = [(colors[0], 'No usadas'), (colors[1], 'Usadas')]
    if data.obstacles:
        entries.append(('black', 'Obstáculos'))
    ax.legend(handles=[Line2D([], [], marker='o', linestyle='', color=c, label=label) for c, label in entries],
              loc='upper center', bbox_to_anchor=(0.5, -0.035), ncol=len(entries), frameon=False,
              fontsize=22, markerscale=1.6, columnspacing=1.2, handletextpad=0.4)
    fig.subplots_adjust(top=0.86, bottom=0.10)
    writer = FFMpegWriter(fps=1 / float(meta['dt2']), codec='libx264',
                         extra_args=['-pix_fmt', 'yuv420p', '-crf', '20'])
    try:
        with writer.saving(fig, str(output), dpi):
            for i, time in enumerate(data.times):
                particles.set_paths([Circle(xy, particle_radius) for xy in data.positions[i]])
                particles.set_facecolors(colors[data.used[i].astype(int)])
                used = int(data.used[i].sum())
                counter.set_text(f't = {time:.2f} s    |    Usadas: {used}/{int(meta["N"])}')
                writer.grab_frame()
                if i % 250 == 0 or i == len(data.times) - 1:
                    print(f'{output.name}: {i + 1}/{len(data.times)} cuadros (t={time:.2f} s)', flush=True)
    finally:
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path, help='dynamic.txt del motor TP4')
    parser.add_argument('--out', required=True, type=Path, help='Video .mp4 a generar')
    args = parser.parse_args()
    try:
        render_animation(read_simulation(args.input), args.out)
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
