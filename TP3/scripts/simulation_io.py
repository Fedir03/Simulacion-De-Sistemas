"""Lectura y muestreo temporal del formato tp3-v1."""
from bisect import bisect_right
from dataclasses import dataclass
from pathlib import Path
import math


@dataclass(frozen=True)
class Frame:
    time: float
    events: int
    goals: int
    particles: tuple


@dataclass(frozen=True)
class Simulation:
    length: float
    width: float
    goal_width: float
    obstacles: tuple
    frames: tuple


def parse_simulation(path):
    line_number = 0
    with Path(path).open(encoding='utf-8-sig') as source:
        def next_line():
            nonlocal line_number
            for raw in source:
                line_number += 1
                line = raw.split('#', 1)[0].strip()
                if line:
                    return line
            return None

        def fields(line):
            return dict(token.split('=', 1) for token in (line or '').split())

        def numbers(tokens):
            values = tuple(float(v) for v in tokens)
            if not all(math.isfinite(v) for v in values):
                raise ValueError('se esperaban números finitos')
            return values

        try:
            header = fields(next_line())
            if header['format'] != 'tp3-v1':
                raise ValueError('se esperaba format=tp3-v1')
            n, k = int(header['N']), int(header['K'])
            length, width, goal = numbers(header[key] for key in ('L', 'W', 'd'))
            if n <= 0 or k < 0 or min(length, width, goal) <= 0 or goal > width:
                raise ValueError('dimensiones o cantidades inválidas')
            obstacles = []
            for _ in range(k):
                row = (next_line() or '').split()
                if len(row) != 4 or row[0] != 'obstacle':
                    raise ValueError('se esperaba obstacle x y radio')
                obstacle = numbers(row[1:])
                if obstacle[2] <= 0:
                    raise ValueError('radio de obstáculo inválido')
                obstacles.append(obstacle)
            frames, ids = [], None
            while (line := next_line()) is not None:
                marker = fields(line)
                time, fraction = numbers((marker['t'], marker['Fu']))
                events, goals = int(marker['events']), int(marker['Ng'])
                if time < 0 or (frames and time < frames[-1].time):
                    raise ValueError('tiempos negativos o decrecientes')
                if events < 0 or not 0 <= goals <= n or not math.isclose(fraction, goals / n):
                    raise ValueError('contadores inválidos')
                particles = []
                for _ in range(n):
                    row = (next_line() or '').split()
                    if len(row) != 10:
                        raise ValueError('se esperaban 10 columnas por partícula')
                    pid = int(row[0])
                    x, y, vx, vy, radius, mass = numbers(row[1:7])
                    rgb = tuple(int(v) for v in row[7:])
                    if radius <= 0 or mass <= 0 or rgb not in ((0, 0, 255), (255, 0, 0)):
                        raise ValueError('radio, masa o color inválido')
                    particles.append((pid, x, y, radius, tuple(v / 255 for v in rgb)))
                particles.sort()
                current_ids = tuple(p[0] for p in particles)
                if len(set(current_ids)) != n or (ids is not None and current_ids != ids):
                    raise ValueError('IDs duplicados o diferentes entre cuadros')
                ids = current_ids
                frames.append(Frame(time, events, goals, tuple(particles)))
            if not frames:
                raise ValueError('el archivo no contiene cuadros')
            return Simulation(length, width, goal, tuple(obstacles), tuple(frames))
        except (ValueError, KeyError) as exc:
            raise ValueError(f'{path}:{line_number}: {exc}') from exc


def sample_frame(data, times, time):
    """Interpola posiciones; usa el último evento en instantes repetidos.

    Si se guardaron todos los choques, los segmentos son rectilíneos exactos.
    Los colores y contadores cambian al alcanzar el estado correspondiente.
    """
    index = max(0, bisect_right(times, time) - 1)
    left = data.frames[index]
    if index == len(times) - 1:
        return left, [(p[1], p[2]) for p in left.particles]
    right = data.frames[index + 1]
    alpha = max(0.0, (time - left.time) / (right.time - left.time))
    return left, [(p[1] + alpha * (q[1] - p[1]), p[2] + alpha * (q[2] - p[2]))
                  for p, q in zip(left.particles, right.particles)]
