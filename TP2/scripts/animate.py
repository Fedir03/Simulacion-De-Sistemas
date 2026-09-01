#!/usr/bin/env python3
"""Genera una animacion MP4 a partir del archivo de salida del motor TP2.

El parseo del archivo de corrida vive en simulation_io.py; aca solo queda el render.

Uso:
    python3 TP2/scripts/animate.py corrida.txt --out=animacion.mp4
    python3 TP2/scripts/animate.py corrida.txt --out=animacion.mp4 --fps=15 --stride=5

Para resaltar el cluster mas grande en cada cuadro hay que generar antes el archivo de
miembros con el motor (que es quien sabe calcular clusters), y pasarlo con --clusters:

    java -jar TP2/target/tp2.jar clusters --in=corrida.txt --out=S.csv --members=miembros.txt
    python3 TP2/scripts/animate.py corrida.txt --out=animacion.mp4 --clusters=miembros.txt
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Sequence, TextIO

from simulation_io import (
    TWO_PI,
    Frame,
    ParticleState,
    SimulationData,
    SimulationFormatError,
    SimulationHeader,
    parse_header,
    parse_simulation,
    stream_simulation,
)

__all__ = [
    "TWO_PI",
    "Frame",
    "ParticleState",
    "ProgressBar",
    "SimulationData",
    "SimulationFormatError",
    "SimulationHeader",
    "parse_cluster_members",
    "parse_header",
    "parse_simulation",
    "render_animation",
    "select_frames",
    "stream_simulation",
    "velocity_components",
]


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


def parse_cluster_members(path: str | Path) -> dict[int, set[int]]:
    """Lee el archivo que escribe `clusters --members`: una linea por cuadro con el paso
    seguido de los ids del cluster mas grande."""
    members: dict[int, set[int]] = {}
    for line_number, raw in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        try:
            members[int(parts[0])] = {int(token) for token in parts[1:]}
        except ValueError as exc:
            raise SimulationFormatError(
                f"{path}:{line_number}: se esperaba '<paso> <id> <id> ...'") from exc
    if not members:
        raise SimulationFormatError(f"{path}: no hay cuadros con miembros")
    return members


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
    fps: int = 15,
    stride: int = 1,
    dpi: int = 150,
    cluster_members: dict[int, set[int]] | None = None,
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
    # capa de resaltado del cluster mas grande: un anillo detras de cada particula miembro
    highlight = ax.scatter([], [], s=90, facecolors="none", edgecolors="#111111",
                           linewidths=0.9, zorder=1) if cluster_members is not None else None

    colorbar = fig.colorbar(arrows, ax=ax, pad=0.02)
    colorbar.set_label("Angulo de velocidad θ [rad]")
    colorbar.set_ticks([0, math.pi / 2, math.pi, 3 * math.pi / 2, TWO_PI])
    colorbar.set_ticklabels(["0", "π/2", "π", "3π/2", "2π"])

    ax.set_xlim(0.0, header.l)
    ax.set_ylim(0.0, header.l)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Animación de Viseck")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(alpha=0.15)

    def members_of(frame: Frame) -> list[tuple[float, float]]:
        ids = cluster_members.get(frame.step)
        if ids is None:
            return []
        return [(p.x, p.y) for p in frame.particles if p.particle_id in ids]

    def title_for(frame: Frame) -> str:
        base = (
            f"Modelo {header.model} | ρ={header.density:g} | η={header.eta:g} | "
            f"t={frame.step * header.dt:g}"
        )
        if cluster_members is None:
            return base
        ids = cluster_members.get(frame.step)
        s_value = len(ids) / header.n if ids is not None else float("nan")
        return base + f" | S={s_value:.2f}"

    ax.set_title(title_for(first))
    if highlight is not None:
        highlight.set_offsets(members_of(first) or [(float("nan"), float("nan"))])

    def update(frame: Frame):
        frame_x = [p.x for p in frame.particles]
        frame_y = [p.y for p in frame.particles]
        frame_angles = [p.theta % TWO_PI for p in frame.particles]
        frame_u, frame_v = velocity_components(frame, header.v0)
        arrows.set_offsets(list(zip(frame_x, frame_y)))
        arrows.set_UVC(frame_u, frame_v, frame_angles)
        return arrows,
        ax.set_title(title_for(frame))
        if highlight is None:
            return arrows,
        highlight.set_offsets(members_of(frame) or [(float("nan"), float("nan"))])
        return arrows, highlight

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
        metadata={"title": "Animación de Viseck"},
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
    parser.add_argument("--fps", type=int, default=15, help="cuadros por segundo (default: 15)")
    parser.add_argument(
        "--stride", type=int, default=1,
        help="usar un cuadro de cada STRIDE pasos, conservando siempre el ultimo (default: 1)",
    )
    parser.add_argument("--dpi", type=int, default=150, help="resolucion de salida (default: 150)")
    parser.add_argument(
        "--clusters", type=Path, default=None,
        help="archivo de miembros generado con 'clusters --members=...'; resalta en cada "
             "cuadro las particulas del cluster mas grande",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        data = parse_simulation(args.input)
        members = parse_cluster_members(args.clusters) if args.clusters is not None else None
        render_animation(data, args.out, fps=args.fps, stride=args.stride, dpi=args.dpi,
                         cluster_members=members)
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
