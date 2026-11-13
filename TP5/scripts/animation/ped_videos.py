#!/usr/bin/env python3
"""Animaciones de la calibración por peatón (punto c opcional) de A y B: real contra pob. 2p, ind. 2p e ind. 4p.

Toma los pares óptimos de las grillas de scripts/sim_gen/per_pedestrian.sh (outputs/ped/grid_ped_*.txt), corre el motor
con cada uno (`AnalysisMain run`, con --p1-ped2 y --p2-ped2 en ind. 4p), verifica que el ECM de la corrida sea el de la
grilla y arma un video por capa y métrica, con tres eventos apilados (por defecto 6, 10 y 12: los que más ganan con 4
parámetros en ECM 2, en las dos capas). Reutiliza la escena de ab_videos.py; cuadros reales a 15 fps.
Uso: python scripts/animation/ped_videos.py [eventos, p. ej. 6,10,12] [--metricas ecm2,ecm1] [--capas A,B]
"""
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import animation  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "graph_gen"))
import ab_videos as ab  # noqa: E402
from per_pedestrian import METRICS, Grid  # noqa: E402

P = Path("outputs/ped")
OUT = P / "animaciones"
CALIBS = {"pob2": ("pob. 2p", "#7B3294"), "ind2": ("ind. 2p", "#009E73"), "ind4": ("ind. 4p", "#0072B2")}
COL = {"ecm1": 5, "ecm2": 6}       # columnas de la línea E del ecm.txt de la corrida (ecm1_excl, ecm2), base 0 sin la "E"


def c(v, fmt="{:g}"):
    return fmt.format(v).replace(".", ",")


def pair(p):
    return f"({'—' if p[1] == 0 else c(p[0])}; {c(p[1])})"


def run(layer, event, first, second, folder):
    """Corre el motor y devuelve (ecm1_excl, ecm2) del evento, del ecm.txt."""
    if not (folder / f"evento_{event:02d}.txt").exists():
        args = ["java", "-cp", "target/tp5.jar", "ar.edu.itba.sds.tp5.analysis.AnalysisMain", "run", "--event", str(event),
                "--data", "data", "--layer", layer.lower(), "--p1", str(first[0]), "--p2", str(first[1]), "--out", str(folder)]
        if first != second:
            args += ["--p1-ped2", str(second[0]), "--p2-ped2", str(second[1])]
        subprocess.run(args, check=True, stdout=subprocess.DEVNULL)
    for line in (folder / "ecm.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith(f"E {event} "):
            p = line.split()
            return float(p[2]), float(p[4])
    raise ValueError(f"{folder}: sin la línea del evento {event}")


def prepare(layer, metric, events):
    """Corridas de las tres calibraciones en cada evento; devuelve {evento: {calib: (par1, par2, error)}}."""
    grid = Grid(P / f"grid_ped_{layer}.txt")
    ij, err = grid.calibrate(metric)
    out = {}
    for n in events:
        k = int(np.where(grid.events == n)[0][0])
        out[n] = {}
        for calib in CALIBS:
            first, second = grid.pairs[ij[calib][k][0]], grid.pairs[ij[calib][k][1]]
            tag = f"{first[0]}_{first[1]}" + ("" if first == second else f"__{second[0]}_{second[1]}")
            folder = OUT / "datos" / f"{layer.lower()}_{tag}" / f"evento_{n:02d}"   # ecm.txt es de cada corrida
            e1, e2 = run(layer, n, first, second, folder)
            got = e1 if metric == "ecm1" else e2
            assert abs(got - err[calib][k]) < 2e-6, f"{layer} {metric} {calib} evento {n}: corrida {got} contra grilla {err[calib][k]}"
            out[n][calib] = (first, second, got, folder)
    return out


def video(layer, metric, events, chosen):
    mname = METRICS[metric][0]
    labels = {calib: f"{name}" for calib, (name, _) in CALIBS.items()}
    evs = []
    for n in events:
        ab.RUNS = {labels[calib]: chosen[n][calib][3] for calib in CALIBS}
        evs.append(ab.load_event(n, [(labels[calib], col) for calib, (_, col) in CALIBS.items()]))
    versions = [(labels[calib], col) for calib, (_, col) in CALIBS.items()]
    heights = [np.diff(ab.limits(ev)[1])[0] for ev in evs]
    fig = plt.figure(figsize=(13, 2.6 + 1.75 * sum(heights)))
    gs = fig.add_gridspec(len(evs), 1, height_ratios=heights, left=0.07, right=0.98, top=0.86, bottom=0.06, hspace=0.38)
    scenes = []
    for row, (n, ev) in enumerate(zip(events, evs)):
        ax = fig.add_subplot(gs[row])
        scenes.append(ab.Scene(ax, ev, versions))
        ch = chosen[n]
        parts = [f"pob. 2p {pair(ch['pob2'][0])}: {c(ch['pob2'][2], '{:.3f}')}",
                 f"ind. 2p {pair(ch['ind2'][0])}: {c(ch['ind2'][2], '{:.3f}')}",
                 f"ind. 4p izq. {pair(ch['ind4'][0])}, der. {pair(ch['ind4'][1])}: {c(ch['ind4'][2], '{:.3f}')}"]
        ax.set_title(f"evento {n}  ·  {mname} (m²)  ·  " + "   ".join(parts), fontsize=12.5, loc="left", color=ab.INK)
        ax.set_ylabel("y [m]")
        if row == len(evs) - 1:
            ax.set_xlabel("x [m]")
    handles = [Line2D([], [], color=ab.GRAY, lw=2.4, label="real")] + [Line2D([], [], color=col, lw=2.4, label=l) for l, col in versions]
    handles += [Line2D([], [], color=ab.MUTED, lw=2.4, ls="-", label="izquierdo"), Line2D([], [], color=ab.MUTED, lw=2.4, ls="--", label="derecho"),
                Line2D([], [], color=ab.INK, lw=2, ls=":", label="mínimo real")]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.98, 0.975), ncol=4, frameon=False, fontsize=12.5)
    fig.text(0.07, 0.955, f"Capa {layer}, calibrada con {mname}", fontsize=17, color=ab.INK, fontweight="bold")
    clock = fig.text(0.07, 0.915, "", fontsize=15, family="monospace", color=ab.INK)
    fig.text(0.07, 0.885, "pob. = mismo par en todos los eventos; ind. = por evento; 4p = un par por peatón (t_a; "
             + ("ℓ" if layer == "A" else "k") + ")", fontsize=11.5, color=ab.MUTED)
    dt = evs[0]["dt"]
    frames = max(ev["nk"] for ev in evs)

    def update(k):
        for s in scenes:
            s.update(k)
        clock.set_text(f"t = {c(k * dt, '{:.2f}')} s")
        return []

    update(max(ev["k_min"] for ev in evs))
    name = f"ped_{layer}_{metric}_eventos_{'_'.join(map(str, events))}"
    fig.savefig(OUT / f"{name}_minimo.png", dpi=90)
    anim = animation.FuncAnimation(fig, update, frames=range(frames), blit=False)
    anim.save(OUT / f"{name}.mp4", writer=animation.FFMpegWriter(fps=round(1 / dt), bitrate=3000), dpi=100)
    plt.close(fig)
    return OUT / f"{name}.mp4"


def main():
    args = sys.argv[1:]
    opt = {"--metricas": "ecm2,ecm1", "--capas": "A,B"}
    events = [6, 10, 12]
    i = 0
    while i < len(args):
        if args[i] in opt:
            opt[args[i]] = args[i + 1]
            i += 2
        else:
            events = [int(v) for v in args[i].split(",")]
            i += 1
    OUT.mkdir(parents=True, exist_ok=True)
    for layer in opt["--capas"].split(","):
        for metric in opt["--metricas"].split(","):
            chosen = prepare(layer, metric, events)
            print(video(layer, metric, events, chosen))


if __name__ == "__main__":
    main()
