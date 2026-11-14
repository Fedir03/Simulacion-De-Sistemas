#!/usr/bin/env python3
"""Animaciones del CPM con las capas A, B y E en su óptimo poblacional (una por capa y métrica).

Toma el óptimo de cada capa de las grillas del CPM (outputs/cpm/grid_*.txt, de scripts/sim_gen/cpm.sh), corre el motor
con ese par (`AnalysisMain baseline --model cpm`), verifica que el ⟨E⟩ de la corrida sea el de la grilla y arma un video
con tres eventos apilados (por defecto 6, 12 y 16). Cada peatón simulado es un disco de radio r(t), el radio dinámico
del CPM (entre r_min = 0,10 m y r_max = 0,25 m; la circunferencia punteada es r_max); el disco se pinta de rojo cuando
está en contacto (r = r_min y velocidad de escape). El real va en gris con radio 0,25 m. Un cuadro de video cada
Δt_exp/2 a 30 cuadros/s: tiempo real. El real se muestra en su último cuadro experimental.
Uso (desde TP5/): python scripts/animation/cpm_videos.py [eventos, p. ej. 6,12,16] [--metricas ecm1,ecm2] [--capas A,B,E]
Escribe outputs/cpm/animaciones/cpm_<capa>_<métrica>_eventos_<...>.mp4 y un PNG del cuadro de máximo acercamiento real.
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
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "graph_gen"))
from cpm_compare import Grid  # noqa: E402
from figure_data import R, experimental, read_run  # noqa: E402

CPM = Path("outputs/cpm")
OUT = CPM / "animaciones"
DATA = Path("data")
JAR = Path("target/tp5.jar")
R_MIN, R_MAX = 0.10, 0.25
METRICS = {"ecm1": ("ECM 1", 3, 3), "ecm2": ("ECM 2", 5, 5)}   # nombre, columna en la grilla, columna en la línea de ecm.txt
NAMES = {"A": ("A", "t_a", "ℓ"), "B": ("B", "t_a", "k"), "E": ("E", "a", "b")}
COLORS = {"A": "#0072B2", "B": "#E69F00", "E": "#009E73"}       # Okabe-Ito, como cpm_compare.py
GRAY, INK, MUTED, CONTACT = "#8a8985", "#0b0b0b", "#52514e", "#D55E00"
SUB = 2                                                         # filas del motor (Δt_exp/4) por cuadro de video
FPS = 30
COMMA = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",").replace("-", "−"))
plt.rcParams.update({"font.size": 14, "axes.labelsize": 15, "xtick.labelsize": 12, "ytick.labelsize": 12,
                     "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})


def c(v, fmt="{:g}"):
    return fmt.format(v).replace(".", ",")


def optimum(layer, metric):
    g = Grid(CPM / f"grid_{layer}.txt")
    mean = np.nanmean(g.metric(metric), axis=1)
    k = int(np.nanargmin(mean))
    return g.pairs[k], mean[k]


def run_dir(layer, pair):
    return OUT / "datos" / f"{layer.lower()}_{pair[0]:g}_{pair[1]:g}"


def ensure_run(layer, pair):
    out = run_dir(layer, pair)
    if not (out / "ecm.txt").exists():
        subprocess.run(["java", "-cp", str(JAR), "ar.edu.itba.sds.tp5.analysis.AnalysisMain", "baseline", "--model", "cpm",
                        "--layer", layer.lower(), "--p1", f"{pair[0]:g}", "--p2", f"{pair[1]:g}", "--out", str(out)],
                       check=True, stdout=subprocess.DEVNULL)
    return out


def event_ecm(run, metric):
    """E_m de cada evento (promedio de los dos peatones), de las líneas por peatón del ecm.txt de la corrida."""
    col = METRICS[metric][2]
    per = {}
    for line in (run / "ecm.txt").read_text().splitlines():
        p = line.split()
        if line.startswith("#") or len(p) < 6 or not p[0].isdigit():
            continue
        per.setdefault(int(p[0]), []).append(float(p[col]))
    return {e: float(np.mean(v)) for e, v in per.items()}


def load_event(run, event):
    header, sim = read_run(run / f"evento_{event:02d}.txt")
    exp = experimental(DATA, header)
    dt = float(header["dt_exp"])
    nk = int(header["frame_final"]) - int(header["frame_inicial"]) + 1
    real = np.full((nk, 4), np.nan)
    for i, e in enumerate(exp):
        k = np.rint(e[:, 0] / dt).astype(int)
        real[k, 2 * i], real[k, 2 * i + 1] = e[:, 1], e[:, 2]
    d_real = np.hypot(real[:, 0] - real[:, 2], real[:, 1] - real[:, 3])
    return {"event": event, "dt": dt, "nk": nk, "real": real, "sim": sim, "k_min": int(np.nanargmin(d_real)),
            "frames": len(sim) // SUB + 1}


class Panel:
    def __init__(self, ax, ev, color, title):
        self.ax, self.ev = ax, ev
        sim, real = ev["sim"], ev["real"]
        x = np.concatenate([real[:, [0, 2]].ravel(), sim[:, [1, 5]].ravel()])
        y = np.concatenate([real[:, [1, 3]].ravel(), sim[:, [2, 6]].ravel()])
        ax.set_xlim(np.nanmin(x) - 0.45, np.nanmax(x) + 0.45)
        ax.set_ylim(np.nanmin(y) - 0.55, np.nanmax(y) + 0.55)
        ax.set_aspect("equal")
        ax.grid(color="#e6e5e0", lw=0.6)
        ax.xaxis.set_major_formatter(COMMA)
        ax.yaxis.set_major_formatter(COMMA)
        ax.set_ylabel("y (m)")
        ax.set_title(title, fontsize=13, loc="left", color=INK)
        self.color = color
        self.real_lines = [ax.plot([], [], "-" if i == 0 else "--", color=GRAY, lw=2)[0] for i in (0, 1)]
        self.sim_lines = [ax.plot([], [], "-" if i == 0 else "--", color=color, lw=2)[0] for i in (0, 1)]
        self.real_disks = [ax.add_patch(plt.Circle((np.nan, np.nan), R, color=GRAY, alpha=0.35, lw=0)) for _ in (0, 1)]
        self.rmax = [ax.add_patch(plt.Circle((np.nan, np.nan), R_MAX, fill=False, ec=color, ls=":", lw=1.2)) for _ in (0, 1)]
        self.disks = [ax.add_patch(plt.Circle((np.nan, np.nan), R_MIN, fc=color, ec=color, alpha=0.55, lw=1.5)) for _ in (0, 1)]
        self.clock = ax.text(0.995, 0.03, "", transform=ax.transAxes, ha="right", va="bottom", fontsize=12, color=MUTED)

    def update(self, f):
        ev = self.ev
        row = min(f * SUB, len(ev["sim"]) - 1)
        k = min(int(ev["sim"][row, 0] / ev["dt"] + 1e-9), ev["nk"] - 1)
        for i in (0, 1):
            r = ev["real"][: k + 1]
            self.real_lines[i].set_data(r[:, 2 * i], r[:, 2 * i + 1])
            p = ev["real"][k, 2 * i: 2 * i + 2]
            if not np.isnan(p[0]):
                self.real_disks[i].center = tuple(p)
            s = ev["sim"][: row + 1]
            self.sim_lines[i].set_data(s[:, 1 + 4 * i], s[:, 2 + 4 * i])
            x, y, rad = ev["sim"][row, 1 + 4 * i], ev["sim"][row, 2 + 4 * i], ev["sim"][row, 9 + i]
            if np.isnan(x):            # retirado (D13)
                self.disks[i].center = self.rmax[i].center = (np.nan, np.nan)
                continue
            self.disks[i].center = self.rmax[i].center = (x, y)
            self.disks[i].set_radius(rad)
            contact = abs(rad - R_MIN) < 1e-9
            self.disks[i].set_facecolor(CONTACT if contact else self.color)
            self.disks[i].set_edgecolor(CONTACT if contact else self.color)
        self.clock.set_text(f"t = {c(ev['sim'][row, 0], '{:.2f}')} s")


def video(layer, metric, events):
    pair, mean = optimum(layer, metric)
    run = ensure_run(layer, pair)
    ecm = event_ecm(run, metric)
    got = float(np.mean(list(ecm.values())))
    assert abs(got - mean) < 1e-6, f"{layer} {metric}: corrida {got} vs grilla {mean}"
    name, p1, p2 = NAMES[layer]
    label, _, _ = METRICS[metric]
    evs = [load_event(run, e) for e in events]
    fig, axes = plt.subplots(len(evs), 1, figsize=(12, 3.3 * len(evs) + 1.3))
    axes = np.atleast_1d(axes)
    panels = [Panel(ax, ev, COLORS[layer], f"Evento {ev['event']}: {label} = {c(ecm[ev['event']], '{:.3f}')} m²")
              for ax, ev in zip(axes, evs)]
    axes[-1].set_xlabel("x (m)")
    fig.suptitle(f"CPM + capa {name}, óptimo poblacional de {label}: {p1} = {c(pair[0])}, {p2} = {c(pair[1])}"
                 f"  (⟨E⟩ = {c(mean, '{:.3f}')} m²)", fontsize=15, color=INK, x=0.01, ha="left")
    handles = [Line2D([], [], color=GRAY, lw=2, label="real (peatón 1 —, 2 – –)"),
               Line2D([], [], color=COLORS[layer], lw=2, label="CPM, disco de radio r(t)"),
               Line2D([], [], color=COLORS[layer], ls=":", lw=1.2, label="r_max = 0,25 m"),
               Patch(color=CONTACT, alpha=0.6, label="contacto (r = r_min, escape)")]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=11.5)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    frames = max(ev["frames"] for ev in evs)
    stem = f"cpm_{layer}_{metric}_eventos_{'_'.join(str(e) for e in events)}"

    def draw(f):
        for p in panels:
            p.update(f)
        return []

    OUT.mkdir(parents=True, exist_ok=True)
    anim = animation.FuncAnimation(fig, draw, frames=frames, blit=False)
    anim.save(OUT / f"{stem}.mp4", writer=animation.FFMpegWriter(fps=FPS, bitrate=2400))
    # Fotograma: el máximo acercamiento real del primer evento
    ev = evs[0]
    draw(int(ev["k_min"] * ev["dt"] / (ev["dt"] / 4) / SUB))
    fig.savefig(OUT / f"{stem}_minimo.png", dpi=130)
    plt.close(fig)
    print(f"{layer} {label}: par {pair}, ⟨E⟩ = {mean:.4f} -> {OUT / (stem + '.mp4')}")


def main(argv):
    events, metrics, layers = [6, 12, 16], ["ecm1", "ecm2"], ["A", "B", "E"]
    rest = list(argv)
    while rest:
        a = rest.pop(0)
        if a == "--metricas":
            metrics = rest.pop(0).split(",")
        elif a == "--capas":
            layers = rest.pop(0).split(",")
        else:
            events = [int(x) for x in a.split(",")]
    for layer in layers:
        for metric in metrics:
            video(layer, metric, events)


if __name__ == "__main__":
    main(sys.argv[1:])
