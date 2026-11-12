#!/usr/bin/env python3
"""Videos para comparar A(3; 0,5) y B(3,5; 1) evento por evento (ρ = 0,9, Δt_exp/64, recorte vigente con compuerta).

Lee las corridas del motor (no simula): figs/datos/ (scripts/sim_gen/figures.sh), sensitivity_rho/B_3.5_1/rho_0.7 y
animaciones_AB/datos/a_5_0.75 (`java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain baseline --layer a --p1 5 --p2 0.75 --out ...`).
Cuadros reales a 15 fps (uno por cuadro experimental, sin interpolar). El overlay va en el margen superior, fuera de los
ejes, para que no tape las trayectorias.
Uso: py scripts/animation/ab_videos.py [eventos, p. ej. 3,6,11] [--sin-extras]
"""
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import animation  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "graph_gen"))
from figure_data import R, experimental, read_run  # noqa: E402
from pilot_analysis import load_grid  # noqa: E402

P = Path("outputs/pilot")
OUT = P / "animaciones_AB"
DATA = Path("data")
GRAY, BLUE, RED, PURPLE, INK, MUTED = "#8a8985", "#0072B2", "#D55E00", "#7B3294", "#0b0b0b", "#52514e"
COMMA = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
plt.rcParams.update({"font.size": 15, "axes.labelsize": 16, "xtick.labelsize": 13, "ytick.labelsize": 13,
                     "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})

A_NEW, A_OLD, B_PAIR = (3.0, 0.5), (5.0, 0.75), (3.5, 1.0)
RUNS = {"A(3; 0,5)": P / "figs" / "datos" / "a_3_0.5", "B(3,5; 1)": P / "figs" / "datos" / "b_3.5_1",
        "B(3,5; 1), ρ = 0,7": P / "sensitivity_rho" / "B_3.5_1" / "rho_0.7", "A(5; 0,75)": OUT / "datos" / "a_5_0.75"}


def c(v, d=2):
    return f"{v:.{d}f}".replace(".", ",")


def load_event(n, versions):
    """versions: [(etiqueta, color)]. Devuelve el real y las corridas en los instantes t_k (cada 4 filas)."""
    header, _ = read_run(RUNS[versions[0][0]] / f"evento_{n:02d}.txt")
    exp = experimental(DATA, header)
    dt = float(header["dt_exp"])
    nk = int(header["frame_final"]) - int(header["frame_inicial"]) + 1
    sims = {}
    for label, _ in versions:
        h, run = read_run(RUNS[label] / f"evento_{n:02d}.txt")
        assert h["frame_inicial"] == header["frame_inicial"] and h["frame_final"] == header["frame_final"], f"{label}: otra ventana"
        s = run[::4][:nk]
        if len(s) < nk:                                   # la corrida termina antes si los dos llegaron (D13)
            pad = np.full((nk - len(s), s.shape[1]), np.nan)
            pad[:, 0] = np.arange(len(s), nk) * dt
            s = np.vstack([s, pad])
        sims[label] = s
    real = np.full((nk, 4), np.nan)                      # x1 y1 x2 y2 en cada cuadro (NaN en los huecos)
    for i, e in enumerate(exp):
        k = np.rint(e[:, 0] / dt).astype(int)
        real[k, 2 * i], real[k, 2 * i + 1] = e[:, 1], e[:, 2]
    d_real = np.hypot(real[:, 0] - real[:, 2], real[:, 1] - real[:, 3])
    k_min = int(np.nanargmin(d_real))
    return {"n": n, "dt": dt, "nk": nk, "real": real, "sims": sims, "k_min": k_min, "d_real": d_real}


def positions(ev, label, k):
    if label == "real":
        r = ev["real"][k]
        return [(r[0], r[1]), (r[2], r[3])]
    s = ev["sims"][label][k]
    return [(s[1], s[2]), (s[5], s[6])]


def history(ev, label, k, i):
    if label == "real":
        r = ev["real"][: k + 1]
        return r[:, 2 * i], r[:, 2 * i + 1]
    s = ev["sims"][label][: k + 1]
    return s[:, 1 + 4 * i], s[:, 2 + 4 * i]


def limits(ev):
    xs = [ev["real"][:, [0, 2]].ravel()] + [ev["sims"][l][:, [1, 5]].ravel() for l in ev["sims"]]
    ys = [ev["real"][:, [1, 3]].ravel()] + [ev["sims"][l][:, [2, 6]].ravel() for l in ev["sims"]]
    x, y = np.concatenate(xs), np.concatenate(ys)
    return (np.nanmin(x) - 0.45, np.nanmax(x) + 0.45), (np.nanmin(y) - 0.55, np.nanmax(y) + 0.55)


class Scene:
    """Real + versiones simuladas en un solo cuadro; con overlay=False sirve para la grilla."""

    def __init__(self, ax, ev, versions, overlay=None, small=False):
        self.ax, self.ev, self.overlay = ax, ev, overlay
        self.labels = ["real"] + [l for l, _ in versions]
        colors = [GRAY] + [col for _, col in versions]
        xl, yl = limits(ev)
        ax.set_xlim(*xl)
        ax.set_ylim(*yl)
        ax.set_aspect("equal")
        ax.grid(color="#e6e5e0", lw=0.6)
        ax.xaxis.set_major_formatter(COMMA)
        ax.yaxis.set_major_formatter(COMMA)
        lw = 1.4 if small else 2.4
        self.lines, self.circles = {}, {}
        for label, col in zip(self.labels, colors):
            for i in (0, 1):
                self.lines[(label, i)], = ax.plot([], [], "-" if i == 0 else "--", color=col, lw=lw, alpha=0.95)
                circ = plt.Circle((np.nan, np.nan), R, fill=(label == "real"), facecolor=col, edgecolor=col,
                                  alpha=0.35 if label == "real" else 1.0, lw=1.2 if small else 2.2)
                ax.add_patch(circ)
                self.circles[(label, i)] = circ
        k = ev["k_min"]
        (a, b) = positions(ev, "real", k)
        self.min_line, = ax.plot([], [], ":", color=INK, lw=1.2 if small else 2)
        self.min_pts = (a, b)

    def update(self, k):
        k = min(k, self.ev["nk"] - 1)
        for label in self.labels:
            pos = positions(self.ev, label, k)
            for i in (0, 1):
                x, y = history(self.ev, label, k, i)
                self.lines[(label, i)].set_data(x, y)
                p = pos[i]
                if not np.isnan(p[0]):
                    self.circles[(label, i)].center = p
                elif label != "real":
                    self.circles[(label, i)].center = (np.nan, np.nan)   # peatón simulado retirado (D13)
        if k >= self.ev["k_min"]:
            a, b = self.min_pts
            self.min_line.set_data([a[0], b[0]], [a[1], b[1]])
        else:
            self.min_line.set_data([], [])


def distance_text(ev, label, k):
    p = positions(ev, label, k)
    d = math.hypot(p[0][0] - p[1][0], p[0][1] - p[1][1])
    return d


def video(n, versions, name, title_line):
    ev = load_event(n, versions)
    fig = plt.figure(figsize=(13, 6.6))
    ax = fig.add_axes([0.07, 0.11, 0.9, 0.66])
    scene = Scene(ax, ev, versions)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    handles = [Line2D([], [], color=GRAY, lw=2.4, label="real")] + [Line2D([], [], color=col, lw=2.4, label=l) for l, col in versions]
    handles += [Line2D([], [], color=MUTED, lw=2.4, ls="-", label="izquierdo"), Line2D([], [], color=MUTED, lw=2.4, ls="--", label="derecho"),
                Line2D([], [], color=INK, lw=2, ls=":", label="mínimo real")]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.985, 0.995), ncol=3, frameon=False, fontsize=12.5)
    line1 = fig.text(0.07, 0.95, "", fontsize=15, family="monospace", color=INK)
    line2 = fig.text(0.07, 0.905, "", fontsize=14, family="monospace", color=INK)
    line3 = fig.text(0.07, 0.86, "", fontsize=14, color=RED, fontweight="bold")
    fig.text(0.07, 0.815, title_line, fontsize=12, color=MUTED)
    labels = ["real"] + [l for l, _ in versions]
    short = {"real": "real"} | {l: l.split("(")[0] + ("ρ0,7" if "0,7" in l else ("'" if l == "A(5; 0,75)" else "")) for l, _ in versions}

    def update(k):
        scene.update(k)
        t = k * ev["dt"]
        mark = "  ← mínimo real" if abs(k - ev["k_min"]) <= 1 else ("  (pasó el mínimo real)" if k > ev["k_min"] else "")
        line1.set_text(f"evento {n:2d}   t = {c(t)} s{mark}")
        parts, contacts = [], []
        for label in labels:
            d = distance_text(ev, label, k)
            parts.append(f"d {short[label]} = {'  —  ' if np.isnan(d) else c(d)} m")
            if not np.isnan(d) and d < 2 * R:
                contacts.append(short[label])
        line2.set_text("   ".join(parts))
        line3.set_text(f"¡CONTACTO! ({', '.join(contacts)}: d < 2R = 0,5 m)" if contacts else "")
        return []

    update(ev["k_min"])
    fig.savefig(OUT / f"{name}_minimo.png", dpi=90)
    anim = animation.FuncAnimation(fig, update, frames=range(ev["nk"]), blit=False)
    anim.save(OUT / f"{name}.mp4", writer=animation.FFMpegWriter(fps=round(1 / ev["dt"]), bitrate=2600), dpi=100)
    plt.close(fig)


def grid_video(versions):
    events = [load_event(n, versions) for n in range(1, 20)]
    fig, axes = plt.subplots(4, 5, figsize=(22, 13))
    fig.subplots_adjust(left=0.03, right=0.99, top=0.9, bottom=0.03, wspace=0.12, hspace=0.25)
    scenes = []
    for ax, ev in zip(axes.flat, events):
        scenes.append(Scene(ax, ev, versions, small=True))
        ax.text(0.02, 0.96, f"{ev['n']}", transform=ax.transAxes, va="top", fontsize=14, fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=1))
        ax.tick_params(labelsize=9)
    ax = axes.flat[-1]
    ax.axis("off")
    handles = [Line2D([], [], color=GRAY, lw=2.4, label="real")] + [Line2D([], [], color=col, lw=2.4, label=l) for l, col in versions]
    handles += [Line2D([], [], color=INK, lw=2, ls=":", label="mínimo real")]
    ax.legend(handles=handles, loc="center", frameon=False, fontsize=16)
    clock = fig.text(0.03, 0.94, "", fontsize=18, family="monospace")
    nk = max(ev["nk"] for ev in events)
    dt = events[0]["dt"]

    def update(k):
        for s in scenes:
            s.update(k)
        clock.set_text(f"t = {c(k * dt)} s  (cada evento se congela al terminar su ventana)")
        return []

    update(0)
    anim = animation.FuncAnimation(fig, update, frames=range(nk), blit=False)
    anim.save(OUT / "grilla_19_eventos.mp4", writer=animation.FFMpegWriter(fps=round(1 / dt), bitrate=5000), dpi=70)
    plt.close(fig)


def table(versions):
    rows = {}
    ga, gb = load_grid(P / "grid_A.txt"), load_grid(P / "grid_B.txt")
    a = ga[(ga[:, 0] == A_NEW[0]) & (ga[:, 1] == A_NEW[1])]
    b = gb[(gb[:, 0] == B_PAIR[0]) & (gb[:, 1] == B_PAIR[1])]
    a, b = a[np.argsort(a[:, 2])], b[np.argsort(b[:, 2])]
    real = {}
    for line in (Path("outputs/baseline") / "ecm.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("E "):
            p = line.split()
            real[int(p[1])] = float(p[8])
    diffs = {}
    for n in range(1, 20):
        ev = load_event(n, versions)
        sa, sb = ev["sims"]["A(3; 0,5)"], ev["sims"]["B(3,5; 1)"]
        d = np.concatenate([np.hypot(sa[:, 1] - sb[:, 1], sa[:, 2] - sb[:, 2]), np.hypot(sa[:, 5] - sb[:, 5], sa[:, 6] - sb[:, 6])])
        diffs[n] = (float(np.sqrt(np.nanmean(d ** 2))), float(np.nanmax(d)))
    lines = ["# Comparación A(3; 0,5) contra B(3,5; 1), evento por evento",
             "",
             "ρ = 0,9, Δt = Δt_exp/64, recorte D(45°) con compuerta de tramo compartido (X = 1,5 m). ECM 1 = variante excluyente. "
             "d_min entre centros. Diferencia A–B = distancia entre las posiciones simuladas de A y de B en los mismos t_k "
             "(RMS y máximo sobre los dos peatones).",
             "",
             "| evento | d_min real (m) | d_min A (m) | d_min B (m) | ECM 1 A (m²) | ECM 1 B (m²) | contacto A | contacto B | diferencia A–B RMS / máx. (m) | video |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for k in range(19):
        n = k + 1
        lines.append(f"| {n} | {c(real[n])} | {c(a[k, 11])} | {c(b[k, 11])} | {c(a[k, 3], 3)} | {c(b[k, 3], 3)} | "
                     f"{'sí' if a[k, 10] else 'no'} | {'sí' if b[k, 10] else 'no'} | {c(diffs[n][0], 3)} / {c(diffs[n][1], 3)} | evento_{n:02d}.mp4 |")
    order = sorted(diffs, key=lambda n: diffs[n][0], reverse=True)
    lines += ["", f"Más distintos (diferencia RMS A–B): {', '.join(f'{n} ({c(diffs[n][0], 3)} m)' for n in order[:3])}.",
              f"Casi iguales: {', '.join(f'{n} ({c(diffs[n][0], 3)} m)' for n in order[-3:][::-1])}."]
    lines += ["", "Extras: `evento_NN_B_rho0.7.mp4` (real, B con ρ = 0,9 y con ρ = 0,7) en los eventos con contacto de B con ρ = 0,7; "
              "`evento_03_A_5_0.75.mp4` y `evento_06_A_5_0.75.mp4` (real, A(3; 0,5) y A(5; 0,75)); `grilla_19_eventos.mp4`."]
    (OUT / "resumen.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return order


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    ab = [("A(3; 0,5)", BLUE), ("B(3,5; 1)", RED)]
    order = table(ab)
    print("más distintos:", order[:3], "casi iguales:", order[-3:])
    only = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
    first = [3, 6, 11] + [n for n in order[:3] if n not in (3, 6, 11)]
    events = only or (first + [n for n in range(1, 20) if n not in first])
    for n in events:
        video(n, ab, f"evento_{n:02d}", "A(3; 0,5) y B(3,5; 1), ρ = 0,9, Δt_exp/64, recorte D(45°) + compuerta; círculos de radio R = 0,25 m")
        print("evento", n, flush=True)
    if "--sin-extras" in sys.argv:
        return
    rho07 = load_grid(P / "recorte_extra" / "rho" / "con_b_3.5_1_rho0.7.txt")
    contact_events = [int(r[2]) for r in rho07 if r[10]]
    for n in contact_events:
        video(n, [("B(3,5; 1)", RED), ("B(3,5; 1), ρ = 0,7", PURPLE)], f"evento_{n:02d}_B_rho0.7",
              "B(3,5; 1) con ρ = 0,9 (rojo) y con ρ = 0,7 (violeta), Δt_exp/64, recorte D(45°) + compuerta")
    print("B con ρ = 0,7:", contact_events, flush=True)
    for n in (3, 6):
        video(n, [("A(3; 0,5)", BLUE), ("A(5; 0,75)", PURPLE)], f"evento_{n:02d}_A_5_0.75",
              "A(3; 0,5) (azul, par actual) y A(5; 0,75) (violeta, par anterior), ρ = 0,9, Δt_exp/64, recorte D(45°) + compuerta")
    grid_video(ab)
    print("grilla lista")


if __name__ == "__main__":
    main()
