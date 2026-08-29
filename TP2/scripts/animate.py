#!/usr/bin/env python3
"""Genera una animacion MP4 a partir del archivo de salida del motor TP2.

Uso:
    python3 TP2/scripts/animate.py corrida.txt --out=animacion.mp4
    python3 TP2/scripts/animate.py corrida.txt --out=animacion.mp4 --fps=30 --stride=5
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, TextIO


TWO_PI = 2.0 * math.pi
TIME_MARKER = re.compile(r"t=(\d+)")
REQUIRED_HEADER_FIELDS = {
    "model", "N", "L", "rc", "dt", "v0", "eta", "periodic", "seedIC", "seedLoop"
}


class SimulationFormatError(ValueError):
    """El archivo no respeta el formato de salida del motor."""


@dataclass(frozen=True)
class SimulationHeader:
    model: str
    n: int
    l: float
    rc: float
    dt: float
    v0: float
    eta: float
    periodic: bool
    seed_ic: int
    seed_loop: int

    @property
    def density(self) -> float:
        return self.n / (self.l * self.l)


@dataclass(frozen=True)
class ParticleState:
    particle_id: int
    x: float
    y: float
    theta: float


@dataclass(frozen=True)
class Frame:
    step: int
    particles: tuple[ParticleState, ...]


@dataclass(frozen=True)
class SimulationData:
    header: SimulationHeader
    frames: tuple[Frame, ...]


class ProgressBar:
    """Barra de progreso de terminal para la codificacion de los cuadros."""

    def __init__(self, total: int, stream: TextIO = sys.stdout, width: int = 36):
        self.total = max(1, total)
        self.stream = stream
        self.width = width
        self.last_completed = -1

    def update(self, frame_number: int, _total_frames: int) -> None:
        completed = min(frame_number + 1, self.total)
        if completed == self.last_completed:
            return
        self.last_completed = completed
        ratio = completed / self.total
        filled = round(self.width * ratio)
        bar = "#" * filled + "-" * (self.width - filled)
        ending = "\n" if completed == self.total else ""
        print(
            f"\rGenerando video [{bar}] {ratio:6.1%} ({completed}/{self.total} cuadros)",
            end=ending,
            file=self.stream,
            flush=True,
        )


def _finite_float(field: str, value: str, line_number: int = 1) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise SimulationFormatError(
            f"linea {line_number}: {field} debe ser numerico, se recibio {value!r}"
        ) from exc
    if not math.isfinite(parsed):
        raise SimulationFormatError(f"linea {line_number}: {field} debe ser finito")
    return parsed


def _integer(field: str, value: str, line_number: int = 1) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise SimulationFormatError(
            f"linea {line_number}: {field} debe ser entero, se recibio {value!r}"
        ) from exc


def parse_header(line: str) -> SimulationHeader:
    fields: dict[str, str] = {}
    for token in line.lstrip("\ufeff").split():
        if "=" not in token:
            raise SimulationFormatError(f"linea 1: campo de cabecera invalido: {token!r}")
        key, value = token.split("=", 1)
        if not key or not value:
            raise SimulationFormatError(f"linea 1: campo de cabecera invalido: {token!r}")
        if key in fields:
            raise SimulationFormatError(f"linea 1: campo de cabecera duplicado: {key}")
        fields[key] = value

    missing = sorted(REQUIRED_HEADER_FIELDS - fields.keys())
    if missing:
        raise SimulationFormatError(
            "linea 1: faltan campos obligatorios: " + ", ".join(missing)
        )

    n = _integer("N", fields["N"])
    l = _finite_float("L", fields["L"])
    rc = _finite_float("rc", fields["rc"])
    dt = _finite_float("dt", fields["dt"])
    v0 = _finite_float("v0", fields["v0"])
    eta = _finite_float("eta", fields["eta"])
    if n <= 0:
        raise SimulationFormatError("linea 1: N debe ser positivo")
    if l <= 0 or rc < 0 or dt <= 0 or v0 <= 0 or eta < 0:
        raise SimulationFormatError(
            "linea 1: se requiere L>0, rc>=0, dt>0, v0>0 y eta>=0"
        )

    periodic_text = fields["periodic"].lower()
    if periodic_text not in {"true", "false"}:
        raise SimulationFormatError("linea 1: periodic debe ser true o false")

    return SimulationHeader(
        model=fields["model"],
        n=n,
        l=l,
        rc=rc,
        dt=dt,
        v0=v0,
        eta=eta,
        periodic=periodic_text == "true",
        seed_ic=_integer("seedIC", fields["seedIC"]),
        seed_loop=_integer("seedLoop", fields["seedLoop"]),
    )


def parse_simulation(path: str | Path) -> SimulationData:
    input_path = Path(path)
    try:
        lines = input_path.read_text(encoding="utf-8-sig").splitlines()
    except UnicodeDecodeError as exc:
        raise SimulationFormatError(f"{input_path}: el archivo no es texto UTF-8 valido") from exc

    if not lines:
        raise SimulationFormatError(f"{input_path}: el archivo esta vacio")
    if not lines[0].strip():
        raise SimulationFormatError("linea 1: se esperaba la cabecera")

    header = parse_header(lines[0])
    frames: list[Frame] = []
    expected_ids: tuple[int, ...] | None = None
    seen_steps: set[int] = set()
    index = 1

    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue

        marker_line = index + 1
        marker = TIME_MARKER.fullmatch(lines[index].strip())
        if marker is None:
            raise SimulationFormatError(
                f"linea {marker_line}: se esperaba un marcador t=<entero>"
            )
        step = int(marker.group(1))
        if step in seen_steps:
            raise SimulationFormatError(f"linea {marker_line}: bloque t={step} duplicado")
        if frames and step <= frames[-1].step:
            raise SimulationFormatError(
                f"linea {marker_line}: los tiempos deben estar en orden creciente"
            )
        seen_steps.add(step)
        index += 1

        particles: list[ParticleState] = []
        ids_in_frame: set[int] = set()
        for particle_number in range(header.n):
            if index >= len(lines) or TIME_MARKER.fullmatch(lines[index].strip()):
                raise SimulationFormatError(
                    f"bloque t={step}: se esperaban {header.n} particulas y se encontraron "
                    f"{particle_number}"
                )
            line_number = index + 1
            parts = lines[index].split()
            if len(parts) != 4:
                raise SimulationFormatError(
                    f"linea {line_number}: se esperaba 'id x y theta'"
                )
            particle_id = _integer("id", parts[0], line_number)
            if particle_id in ids_in_frame:
                raise SimulationFormatError(
                    f"linea {line_number}: id de particula duplicado: {particle_id}"
                )
            ids_in_frame.add(particle_id)
            particles.append(ParticleState(
                particle_id=particle_id,
                x=_finite_float("x", parts[1], line_number),
                y=_finite_float("y", parts[2], line_number),
                theta=_finite_float("theta", parts[3], line_number),
            ))
            index += 1

        current_ids = tuple(p.particle_id for p in particles)
        if expected_ids is None:
            expected_ids = current_ids
        elif current_ids != expected_ids:
            raise SimulationFormatError(
                f"bloque t={step}: los IDs o su orden no coinciden con el primer bloque"
            )
        frames.append(Frame(step=step, particles=tuple(particles)))

    if not frames:
        raise SimulationFormatError("el archivo no contiene bloques de tiempo")
    return SimulationData(header=header, frames=tuple(frames))


def select_frames(frames: Sequence[Frame], stride: int) -> tuple[Frame, ...]:
    if stride <= 0:
        raise ValueError("stride debe ser un entero positivo")
    selected = list(frames[::stride])
    if selected and selected[-1] is not frames[-1]:
        selected.append(frames[-1])
    return tuple(selected)


def velocity_components(frame: Frame, v0: float) -> tuple[list[float], list[float]]:
    return (
        [v0 * math.cos(p.theta) for p in frame.particles],
        [v0 * math.sin(p.theta) for p in frame.particles],
    )


def render_animation(
    data: SimulationData,
    output: str | Path,
    *,
    fps: int = 30,
    stride: int = 1,
    dpi: int = 150,
) -> None:
    if fps <= 0:
        raise ValueError("fps debe ser un entero positivo")
    if dpi <= 0:
        raise ValueError("dpi debe ser un entero positivo")

    output_path = Path(output)
    if output_path.suffix.lower() != ".mp4":
        raise ValueError("--out debe tener extension .mp4")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib import colors
        from matplotlib.animation import FFMpegWriter, FuncAnimation
    except ImportError as exc:
        raise RuntimeError(
            "falta Matplotlib; instalar con: python3 -m pip install -r TP2/requirements.txt"
        ) from exc

    if not FFMpegWriter.isAvailable():
        raise RuntimeError("FFmpeg no esta disponible en PATH; es necesario para exportar MP4")

    frames = select_frames(data.frames, stride)
    header = data.header
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 8))
    norm = colors.Normalize(vmin=0.0, vmax=TWO_PI)
    first = frames[0]
    x = [p.x for p in first.particles]
    y = [p.y for p in first.particles]
    angles = [p.theta % TWO_PI for p in first.particles]
    u, v = velocity_components(first, header.v0)

    target_length = min(0.04 * header.l, 0.7 * header.l / math.sqrt(header.n))
    quiver_scale = header.v0 / target_length
    arrows = ax.quiver(
        x, y, u, v, angles,
        angles="xy", scale_units="xy", scale=quiver_scale,
        cmap="hsv", norm=norm, pivot="tail", width=0.003,
    )
    colorbar = fig.colorbar(arrows, ax=ax, pad=0.02)
    colorbar.set_label("Angulo de velocidad θ [rad]")
    colorbar.set_ticks([0, math.pi / 2, math.pi, 3 * math.pi / 2, TWO_PI])
    colorbar.set_ticklabels(["0", "π/2", "π", "3π/2", "2π"])

    ax.set_xlim(0.0, header.l)
    ax.set_ylim(0.0, header.l)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(alpha=0.15)

    def title_for(frame: Frame) -> str:
        return (
            f"Modelo {header.model} | ρ={header.density:g} | η={header.eta:g} | "
            f"t={frame.step * header.dt:g}"
        )

    ax.set_title(title_for(first))

    def update(frame: Frame):
        frame_x = [p.x for p in frame.particles]
        frame_y = [p.y for p in frame.particles]
        frame_angles = [p.theta % TWO_PI for p in frame.particles]
        frame_u, frame_v = velocity_components(frame, header.v0)
        arrows.set_offsets(list(zip(frame_x, frame_y)))
        arrows.set_UVC(frame_u, frame_v, frame_angles)
        ax.set_title(title_for(frame))
        return arrows,

    animation = FuncAnimation(
        fig,
        update,
        frames=frames,
        interval=1000.0 / fps,
        blit=False,
        repeat=False,
    )
    writer = FFMpegWriter(
        fps=fps,
        codec="libx264",
        metadata={"title": f"Vicsek {header.model}"},
        extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )
    progress = ProgressBar(len(frames))
    try:
        animation.save(
            output_path,
            writer=writer,
            dpi=dpi,
            progress_callback=progress.update,
        )
    finally:
        plt.close(fig)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Genera un MP4 a partir del archivo de salida de una simulacion TP2."
    )
    parser.add_argument("input", type=Path, help="archivo .txt producido por el motor")
    parser.add_argument("--out", required=True, type=Path, help="archivo MP4 de salida")
    parser.add_argument("--fps", type=int, default=30, help="cuadros por segundo (default: 30)")
    parser.add_argument(
        "--stride", type=int, default=1,
        help="usar un cuadro de cada STRIDE pasos, conservando siempre el ultimo (default: 1)",
    )
    parser.add_argument("--dpi", type=int, default=150, help="resolucion de salida (default: 150)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        data = parse_simulation(args.input)
        render_animation(data, args.out, fps=args.fps, stride=args.stride, dpi=args.dpi)
    except (OSError, SimulationFormatError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    rendered_frames = len(select_frames(data.frames, args.stride))
    print(
        f"Animacion guardada en {args.out.resolve()} "
        f"({rendered_frames} cuadros, {args.fps} FPS)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
