#!/usr/bin/env python3
"""Nuevas corridas y videos real vs A/B/E, eventos 3 y 6, con los pares del gráfico de ECM2.

Uso: MPLCONFIGDIR=/tmp/tp5-matplotlib .venv/bin/python scripts/animation/events_3_6_ecm2.py
Salida: outputs/animaciones_eventos_3_6_ecm2 y copias en presentacion/. Videos a media velocidad.
Una sola vista por evento: real y las tres capas superpuestas, con sus trayectorias.
"""
import argparse
import json
import shutil
from pathlib import Path
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.lines import Line2D
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "graph_gen"))
import ab_videos as ab
from per_event import best_rows
from pilot_analysis import load_grid

COLORS = {"A": "#0072B2", "B": "#E69F00", "E": "#D55E00"}
COMMON = ["--data", "data", "--model", "sfm", "--integrator", "beeman", "--dt-div", "64",
          "--v0-frames", "5", "--delta-a", "0.1", "--rho", "0.9", "--trim", "on", "--trim-deg", "45",
          "--trim-persist", "5", "--trim-half", "2", "--trim-target", "common", "--trim-shared", "on", "--trim-shared-x", "1.5"]


def prepare(out):
    metadata = {"modelo": "SFM", "velocidad_inicial": "Ajuste de 5 cuadros", "reproduccion": "0,5x",
                "criterio": "Mejor par poblacional para ECM2; mismo par para ambos peatones", "eventos": {}}
    grids = {layer: load_grid(Path("outputs/pilot") / f"grid_{layer}.txt") for layer in COLORS}
    for event in (3, 6):
        metadata["eventos"][event] = {}
        for layer in COLORS:
            p1, p2, rows = best_rows(grids[layer], 5)
            expected = float(rows[rows[:, 2] == event, 5][0])
            folder = out / "datos" / layer / f"evento_{event:02d}"
            args = ["java", "-cp", "target/tp5.jar", "ar.edu.itba.sds.tp5.analysis.AnalysisMain", "run",
                    "--event", str(event), "--layer", layer, "--p1", str(p1), "--p2", str(p2), "--out", str(folder)] + COMMON
            subprocess.run(args, check=True)
            row = next(l.split() for l in (folder / "ecm.txt").read_text().splitlines() if l.startswith("E "))
            measured = float(row[4])
            if abs(measured - expected) > 1e-6:
                raise ValueError(f"ECM2 distinto del gráfico: {event}/{layer}: {measured} vs {expected}")
            metadata["eventos"][event][layer] = {"p1": float(p1), "p2": float(p2), "ecm2": measured, "carpeta": str(folder)}
    (out / "parametros.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    return metadata


def video(event, meta, out):
    versions = list(COLORS.items())
    ab.RUNS = {layer: Path(meta[layer]["carpeta"]) for layer in COLORS}
    ev = ab.load_event(event, versions)
    fig, ax = plt.subplots(figsize=(13, 6.8))
    fig.subplots_adjust(left=0.075, right=0.98, bottom=0.20, top=0.82)
    scene = ab.Scene(ax, ev, versions)
    for i in (0, 1):
        scene.lines[("real", i)].set_color(ab.INK)
        scene.lines[("real", i)].set_zorder(3)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    title = fig.text(0.075, 0.95, "", fontsize=19)
    handles = [Line2D([], [], color=ab.INK, lw=2.4, label="Real")]
    for layer, color in versions:
        info = meta[layer]
        pair = f"{info['p1']:g}; {info['p2']:g}".replace(".", ",")
        handles.append(Line2D([], [], color=color, lw=2.4, label=f"{layer}({pair})"))
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.91),
               ncol=4, frameon=False, fontsize=15)
    fig.legend(handles=[Line2D([], [], color=ab.MUTED, lw=2.4, label="Peatón izquierdo"),
                        Line2D([], [], color=ab.MUTED, lw=2.4, ls="--", label="Peatón derecho"),
                        Line2D([], [], color=ab.INK, lw=2, ls=":", label="Mínimo real")],
               loc="lower center", bbox_to_anchor=(0.5, 0.065), ncol=3, frameon=False, fontsize=13)

    def update(k):
        title.set_text(f"Evento {event} · t = {ab.c(k * ev['dt'])} s")
        scene.update(k)
        for i, point in enumerate(ab.positions(ev, "real", k)):
            if not np.isfinite(point).all():
                scene.circles[("real", i)].center = (np.nan, np.nan)

    update(ev["k_min"])
    fig.savefig(out / f"evento_{event:02d}_minimo.png", dpi=120)
    update(ev["nk"] - 1)
    fig.savefig(out / f"evento_{event:02d}_trayectorias.png", dpi=120)
    anim = animation.FuncAnimation(fig, update, frames=range(ev["nk"]), blit=False)
    target = out / f"evento_{event:02d}_real_A_B_E_ecm2.mp4"
    anim.save(target, writer=animation.FFMpegWriter(fps=1 / (2 * ev["dt"]), bitrate=2300,
                                                  extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"]), dpi=100)
    plt.close(fig)
    presentation = Path(__file__).resolve().parents[2] / "presentacion"
    shutil.copy2(target, presentation / "animaciones" / f"ecm2_evento{event:02d}.mp4")
    shutil.copy2(out / f"evento_{event:02d}_minimo.png",
                 presentation / "figuras" / f"anim-evento-{event:02d}-ecm2.png")
    print(f"Video y fotograma actualizados: {target}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("outputs/animaciones_eventos_3_6_ecm2"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    metadata = prepare(args.out)
    for event in (3, 6):
        video(event, metadata["eventos"][event], args.out)


if __name__ == "__main__":
    main()
