#!/usr/bin/env python3
"""Nuevas corridas y videos real vs A/B/E, eventos 3 y 6, con los pares del gráfico de ECM2.

Uso: MPLCONFIGDIR=/tmp/tp5-matplotlib .venv/bin/python scripts/animation/events_3_6_ecm2.py
Salida independiente: outputs/animaciones_eventos_3_6_ecm2. Videos a media velocidad.
"""
import argparse
import json
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
    fig, axes = plt.subplots(3, 1, figsize=(13, 8.5))
    fig.subplots_adjust(left=0.07, right=0.98, bottom=0.09, top=0.85, hspace=0.48)
    scenes = []
    distances = []
    for ax, (layer, color) in zip(axes, versions):
        scenes.append(ab.Scene(ax, ev, [(layer, color)]))
        info = meta[layer]
        names = "a; b" if layer == "E" else ("t_a; ℓ" if layer == "A" else "t_a; k")
        p = f"{info['p1']:g}; {info['p2']:g}".replace(".", ",")
        ax.set_title(f"Capa {layer} ({names}) = ({p})     ECM 2 = {ab.c(info['ecm2'], 4)} m²", loc="left", fontsize=12, color=color, pad=7)
        ax.set_ylabel("y [m]", fontsize=12)
        distances.append(ax.text(0.99, 0.96, "", transform=ax.transAxes, ha="right", va="top", fontsize=10,
                                 color=ab.INK, bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=2)))
    axes[-1].set_xlabel("x [m]")
    title = fig.text(0.07, 0.97, "", fontsize=17)
    fig.text(0.07, 0.923, "SFM · parámetros poblacionales óptimos de ECM2 · velocidad inicial: ajuste de 5 cuadros · reproducción 0,5×", fontsize=11, color=ab.MUTED)
    handles = [Line2D([], [], color=ab.GRAY, lw=2.4, label="Real")]
    handles += [Line2D([], [], color=color, lw=2.4, label=layer) for layer, color in versions]
    handles += [Line2D([], [], color=ab.MUTED, lw=2.4, label="Peatón izquierdo"),
                Line2D([], [], color=ab.MUTED, lw=2.4, ls="--", label="Peatón derecho"),
                Line2D([], [], color=ab.INK, lw=2, ls=":", label="Mínimo real")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0), ncol=7, frameon=False, fontsize=10)

    def update(k):
        marker = " · mínimo acercamiento real" if k == ev["k_min"] else ""
        title.set_text(f"Evento {event} · t = {ab.c(k * ev['dt'])} s{marker}")
        for scene, distance, (layer, _) in zip(scenes, distances, versions):
            scene.update(k)
            for i, point in enumerate(ab.positions(ev, "real", k)):
                if not np.isfinite(point).all():
                    scene.circles[("real", i)].center = (np.nan, np.nan)
            real_d, sim_d = ab.distance_text(ev, "real", k), ab.distance_text(ev, layer, k)
            distance.set_text(f"Distancia real: {ab.c(real_d)} m · simulada: {ab.c(sim_d)} m")

    update(ev["k_min"])
    fig.savefig(out / f"evento_{event:02d}_minimo.png", dpi=120)
    update(ev["nk"] - 1)
    fig.savefig(out / f"evento_{event:02d}_trayectorias.png", dpi=120)
    anim = animation.FuncAnimation(fig, update, frames=range(ev["nk"]), blit=False)
    target = out / f"evento_{event:02d}_real_A_B_E_ecm2.mp4"
    anim.save(target, writer=animation.FFMpegWriter(fps=1 / (2 * ev["dt"]), bitrate=2300,
                                                  extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"]), dpi=100)
    plt.close(fig)
    print(f"Video: {target}", flush=True)


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
