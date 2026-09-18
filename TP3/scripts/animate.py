#!/usr/bin/env python3
"""Exporta una trayectoria TP3 a MP4 o GIF respetando sus tiempos físicos."""
import argparse
import math
from pathlib import Path
import subprocess
import sys

from simulation_io import parse_simulation, sample_frame


MAX_GAP = 0.01

def render_animation(data, output, *, fps=30, speed=1.0, dpi=120):
    if fps <= 0 or dpi <= 0 or not math.isfinite(speed) or speed <= 0:
        raise ValueError('fps, dpi y speed deben ser positivos y finitos')
    output = Path(output)
    if output.suffix.lower() not in ('.mp4', '.gif'):
        raise ValueError('--out debe terminar en .mp4 o .gif')
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.animation import FFMpegWriter, PillowWriter
        from matplotlib.patches import Circle
        from matplotlib.lines import Line2D
    except ImportError as exc:
        raise RuntimeError('Instalá las dependencias: python3 -m pip install -r TP3/requirements.txt') from exc
    if output.suffix.lower() == '.mp4':
        if not FFMpegWriter.isAvailable():
            raise RuntimeError('MP4 requiere FFmpeg en PATH; también podés usar --out animacion.gif')
        writer = FFMpegWriter(fps=fps, codec='libx264', extra_args=['-pix_fmt', 'yuv420p'])
    else:
        writer = PillowWriter(fps=fps)
    times = [frame.time for frame in data.frames]
    count = math.ceil((times[-1] - times[0]) * fps / speed) + 1
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set(xlim=(0, data.length), ylim=(0, data.width), xlabel='x [m]', ylabel='y [m]')
    ax.set_aspect('equal')
    ax.set_facecolor('#f1f5f9')
    for x, y, radius in data.obstacles:
        ax.add_patch(Circle((x, y), radius, color='#475569'))
    for x in (0, data.length):
        ax.plot([x, x], [(data.width - data.goal_width) / 2,
                        (data.width + data.goal_width) / 2],
                color='#16a34a', linewidth=6, clip_on=False, zorder=4)
    circles = []
    for pid, x, y, radius, color in data.frames[0].particles:
        circle = Circle((x, y), radius, facecolor=color, edgecolor='white', linewidth=0.4)
        ax.add_patch(circle)
        circles.append(circle)
    ax.legend(handles=[Line2D([], [], marker='o', linestyle='', color=color, label=label)
                       for color, label in [('blue', 'Fresca'), ('red', 'Usada'),
                                            ('#475569', 'Obstáculo'), ('#16a34a', 'Arco')]],
              loc='upper center', bbox_to_anchor=(0.5, -0.14), ncol=4)
    title = ax.set_title('')
    fig.subplots_adjust(bottom=0.22, top=0.88)
    try:
        with writer.saving(fig, str(output), dpi):
            for i in range(count):
                time = min(times[-1], times[0] + i * speed / fps)
                frame, positions = sample_frame(data, times, time)
                for circle, p, position in zip(circles, frame.particles, positions):
                    circle.center = position
                    circle.set_radius(p[3])
                    circle.set_facecolor(p[4])
                title.set_text(f'TP3 · t = {time:.3f} s · Goles: {frame.goals}/{len(circles)}'
                               f' · Fu = {frame.goals / len(circles):.1%} · Eventos: {frame.events}')
                writer.grab_frame()
                if i % max(1, count // 100) == 0 or i == count - 1:
                    print(f'\rGenerando animación: {i + 1}/{count} cuadros', end='', flush=True)
        print()
    finally:
        plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='salida .txt del motor TP3')
    parser.add_argument('--out', type=Path, help='salida .mp4 o .gif; por defecto, junto al TXT')
    parser.add_argument('--fps', type=int, default=30, help='cuadros por segundo (30)')
    parser.add_argument('--speed', type=float, default=1.0, help='velocidad: 1 real, 2 doble, 0.5 mitad')
    parser.add_argument('--dpi', type=int, default=120, help='resolución (120)')
    args = parser.parse_args(argv)
    output = args.out or args.input.with_suffix('.mp4')
    try:
        if output.resolve() == args.input.resolve():
            raise ValueError('entrada y salida deben ser distintas')
        data = parse_simulation(args.input)
        # Entre estados guardados se interpola en línea recta: un choque omitido se ve como
        # un atajo, despreciable si los estados están a lo sumo a MAX_GAP segundos.
        gaps = [b.time - a.time for a, b in zip(data.frames, data.frames[1:]) if b.events - a.events > 1]
        if gaps and max(gaps) > MAX_GAP * (1 + 1e-6):
            print(f'Aviso: faltan choques intermedios; el recorrido se aproxima. '
                  f'Usá simulate --dt {MAX_GAP} (o menor) o --every 1.', file=sys.stderr)
        render_animation(data, output, fps=args.fps, speed=args.speed, dpi=args.dpi)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    print(f'Animación guardada en {output.resolve()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
