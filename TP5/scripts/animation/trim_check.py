#!/usr/bin/env python3
"""Verificación visual del recorte al tramo frontal, con el recorte que usa el motor.

Lee solo lo que exporta `java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain trim-export` (trayectorias_recortadas.csv y recorte_eventos.csv)
y genera, por evento: verificacion/evento_NN.mp4 (GIF con Pillow si no hay ffmpeg), verificacion/evento_NN_minimo.png
y verificacion/resumen.md. Frames reales a 15 fps, sin interpolar: un hueco de frames se ve como un salto.
Uso: py scripts/animation/trim_check.py [carpeta con los CSV] [eventos, p. ej. 1,4,9]
"""
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import animation  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

COLORS = ("#2a78d6", "#eb6834")      # izquierdo, derecho (los de f_figures.py)
GRAY, INK, MUTED = "#b8b7b2", "#0b0b0b", "#52514e"
SENSE = (1, -1)
CAREFUL = {1: "hueco de 32 frames (ID 36)", 4: "hueco de 16 frames (ID 10)", 9: "izquierdo termina en x ≈ 8",
           13: "1,7 s después del mínimo", 14: "izquierdo termina en x ≈ 8", 17: "izquierdo termina en x ≈ 8",
           19: "izquierdo termina en x ≈ 8"}
COMMA = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))

plt.rcParams.update({"font.size": 15, "axes.labelsize": 16, "legend.fontsize": 12, "xtick.labelsize": 13, "ytick.labelsize": 13,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})


def c(v, d=2):
    return f"{v:.{d}f}".replace(".", ",")


def load(folder):
    tracks = defaultdict(dict)
    with open(folder / "trayectorias_recortadas.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            tracks[int(r["evento"])].setdefault(int(r["peaton"]) - 1, []).append((int(r["frame"]), float(r["x"]), float(r["y"]), r["en_recorte"] == "1"))
    meta = defaultdict(dict)
    with open(folder / "recorte_eventos.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            meta[int(r["evento"])][int(r["peaton"]) - 1] = r
    out = {}
    for n in sorted(tracks):
        peds = []
        for i in (0, 1):
            arr = np.array(tracks[n][i], dtype=float)
            m = meta[n][i]
            peds.append({"f": arr[:, 0].astype(int), "x": arr[:, 1], "y": arr[:, 2], "in": arr[:, 3].astype(bool), "id": int(m["id"]),
                         "target": (float(m["target_x"]), float(m["target_y"])), "target_rec": (float(m["target_x_rec"]), float(m["target_y_rec"])),
                         "vd": float(m["vd"]), "vd_rec": float(m["vd_rec"]), "frames_rec": int(m["frames_rec"])})
        m = meta[n][0]
        out[n] = {"peds": peds, "dt": float(m["dt_exp"]), "win": (int(m["frame_ini"]), int(m["frame_fin"])),
                  "rec": (int(m["frame_ini_rec"]), int(m["frame_fin_rec"])), "min": int(m["frame_min"]), "dmin": float(m["d_min"]),
                  "label": m["recorte"]}
    return out


def pos(p, frame):
    k = np.searchsorted(p["f"], frame)
    return (p["x"][k], p["y"][k]) if k < len(p["f"]) and p["f"][k] == frame else None


def axis_angle(dx, dy, sense):
    """Ángulo con signo (°) entre el vector y el sentido de avance sobre x; positivo hacia +y."""
    return math.degrees(math.atan2(dy, sense * dx))


def etarget_max_first_second(ev, start, end, rec):
    """Ángulo máximo |e_target| con el eje x en el primer segundo de la ventana (máx. de los dos peatones)."""
    worst = 0.0
    last = start + round(1 / ev["dt"])
    for i, p in enumerate(ev["peds"]):
        tx, ty = p["target_rec"] if rec else p["target"]
        for k in np.flatnonzero((p["f"] >= start) & (p["f"] <= min(end, last))):
            worst = max(worst, abs(axis_angle(tx - p["x"][k], ty - p["y"][k], SENSE[i])))
    return worst


def summary_line(ev):
    s, e = ev["rec"]
    dt = ev["dt"]
    full = ev["win"]
    p = ev["peds"]
    return (f"frames comunes {full[1] - full[0] + 1} → {e - s + 1} (izq. {p[0]['frames_rec']}, der. {p[1]['frames_rec']} con datos) | "
            f"antes del mínimo {c((ev['min'] - full[0]) * dt)} → {c((ev['min'] - s) * dt)} s, después {c((full[1] - ev['min']) * dt)} → {c((e - ev['min']) * dt)} s | "
            f"v_d izq. {c(p[0]['vd'])} → {c(p[0]['vd_rec'])}, der. {c(p[1]['vd'])} → {c(p[1]['vd_rec'])} m/s")


class Panel:
    def __init__(self, ax, ev, rec):
        self.ax, self.ev, self.rec = ax, ev, rec
        lo, hi = ev["rec"] if rec else ev["win"]
        self.lo, self.hi = lo, hi
        for i, p in enumerate(ev["peds"]):
            ax.plot(p["x"], p["y"], color=GRAY, lw=1.5, zorder=1)
            if rec:
                k = (p["f"] >= lo) & (p["f"] <= hi)
                ax.plot(p["x"][k], p["y"][k], "-" if i == 0 else "--", color=COLORS[i], lw=2.4, zorder=2)
            # target actual (cuadrado vacío) y recortado (X)
            ax.plot(*p["target"], "s", mfc="none", mec=COLORS[i], ms=11, mew=2, zorder=3)
            ax.plot(*p["target_rec"], "X", color=COLORS[i], ms=12, mec="white", mew=0.8, zorder=3)
        a, b = pos(ev["peds"][0], ev["min"]), pos(ev["peds"][1], ev["min"])
        ax.plot([a[0], b[0]], [a[1], b[1]], ":", color=INK, lw=1.8, zorder=2)
        ax.set_xlim(-0.5, 12)
        ax.set_ylim(-0.9, 4.4)
        ax.set_aspect("equal")
        ax.grid(color="#e6e5e0", lw=0.8)
        ax.xaxis.set_major_formatter(COMMA)
        ax.yaxis.set_major_formatter(COMMA)
        ax.set_xlabel("x (m)")
        ax.text(0.02, 0.97, "evento completo (D3 anterior)" if not rec else "tramo recortado (" + ev["label"].split("=")[1].split("_")[0] + ")",
                transform=ax.transAxes, va="top", fontsize=14, color=INK)
        self.dots = [ax.plot([], [], "o", color=COLORS[i], ms=12, mec=INK, mew=1, zorder=5)[0] for i in (0, 1)]
        self.arrows = [None, None]
        self.angles = [ax.text(0, 0, "", fontsize=13, color=COLORS[i], zorder=6, fontweight="bold") for i in (0, 1)]
        self.flash = ax.text(0.98, 0.97, "", transform=ax.transAxes, ha="right", va="top", fontsize=14, color=INK, fontweight="bold")

    def update(self, frame):
        active = self.lo <= frame <= self.hi
        for i, p in enumerate(self.ev["peds"]):
            q = pos(p, frame)
            if self.arrows[i] is not None:
                self.arrows[i].remove()
                self.arrows[i] = None
            if q is None or not active:
                self.dots[i].set_data([], [])
                self.angles[i].set_text("")
                continue
            self.dots[i].set_data([q[0]], [q[1]])
            tx, ty = p["target_rec"] if self.rec else p["target"]
            dx, dy = tx - q[0], ty - q[1]
            norm = math.hypot(dx, dy) or 1
            self.arrows[i] = self.ax.annotate("", xy=(q[0] + 1.3 * dx / norm, q[1] + 1.3 * dy / norm), xytext=q,
                                              arrowprops=dict(arrowstyle="-|>", color=COLORS[i], lw=2.4, mutation_scale=18), zorder=6)
            ang = axis_angle(dx, dy, SENSE[i])
            tip = (q[0] + 1.3 * dx / norm, q[1] + 1.3 * dy / norm)
            self.angles[i].set_position((tip[0] + (0.1 if SENSE[i] > 0 else -0.95), tip[1] + (-0.45 if i == 0 else 0.15)))
            self.angles[i].set_text(f"{ang:+.0f}°")
        near = abs(frame - self.ev["min"]) <= 2
        self.flash.set_text("distancia mínima real" if near else "")


def draw(ev, n, out, video):
    fig, axes = plt.subplots(1, 2, figsize=(17, 6.1), sharey=True)
    fig.subplots_adjust(left=0.05, right=0.99, top=0.84, bottom=0.11, wspace=0.05)
    panels = [Panel(axes[0], ev, False), Panel(axes[1], ev, True)]
    axes[0].set_ylabel("y (m)")
    handles = [Line2D([], [], color=GRAY, lw=1.5, label="trayectoria completa"),
               Line2D([], [], color=COLORS[0], lw=2.4, label=f"tramo, izq. (ID {ev['peds'][0]['id']})"),
               Line2D([], [], color=COLORS[1], lw=2.4, ls="--", label=f"tramo, der. (ID {ev['peds'][1]['id']})"),
               Line2D([], [], marker="s", mfc="none", mec=MUTED, ls="none", ms=10, mew=2, label="target actual"),
               Line2D([], [], marker="X", color=MUTED, ls="none", ms=11, label="target recortado"),
               Line2D([], [], color=INK, ls=":", lw=1.8, label="distancia mínima real"),
               Line2D([], [], color=MUTED, lw=2.2, marker=">", ms=8, label="e_target (° con x)")]
    axes[1].legend(handles=handles, loc="lower right", frameon=True, framealpha=0.92, ncol=2, fontsize=11)
    t0 = ev["win"][0]
    clock = fig.text(0.05, 0.94, "", fontsize=16, color=INK, family="monospace")
    fig.text(0.05, 0.885, summary_line(ev), fontsize=12.5, color=MUTED)
    first = min(p["f"][0] for p in ev["peds"])
    last = max(p["f"][-1] for p in ev["peds"])

    def update(frame):
        for p in panels:
            p.update(frame)
        clock.set_text(f"t = {c((frame - t0) * ev['dt'])} s   frame {frame}   (mínimo en t = {c((ev['min'] - t0) * ev['dt'])} s)")
        return []

    update(ev["min"])
    fig.savefig(out / f"evento_{n:02d}_minimo.png", dpi=100)
    if video:
        anim = animation.FuncAnimation(fig, update, frames=range(first, last + 1), blit=False)
        if animation.writers.is_available("ffmpeg"):
            anim.save(out / f"evento_{n:02d}.mp4", writer=animation.FFMpegWriter(fps=15, bitrate=2400), dpi=90)
        else:
            anim.save(out / f"evento_{n:02d}.gif", writer=animation.PillowWriter(fps=15), dpi=70)
    plt.close(fig)


def summary(events, out):
    lines = ["# Verificación del recorte al tramo frontal",
             "",
             f"Recorte que usa el motor: `{next(iter(events.values()))['label']}` (sale de `java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain trim-export`).",
             "Márgenes medidos desde el frame de distancia mínima real hasta el borde de la ventana. Ángulo de e_target: máximo de los dos peatones,",
             "en el primer segundo de la ventana, entre (target − posición experimental) y el eje x. ⚠️ = mirar con más cuidado.",
             "",
             "| evento | tramo (frames) | frames comunes antes → después | margen antes del mínimo (s) | margen después (s) | e_target 1.er s antes → después (°) | v_d izq. / der. antes → después (m/s) | nota | ¿OK? |",
             "|---|---|---|---|---|---|---|---|---|"]
    for n, ev in events.items():
        s, e = ev["rec"]
        w = ev["win"]
        dt = ev["dt"]
        p = ev["peds"]
        before = etarget_max_first_second(ev, *w, False)
        after = etarget_max_first_second(ev, s, e, True)
        flag = "⚠️ " + CAREFUL[n] if n in CAREFUL else ""
        lines.append(f"| {n} | {s}–{e} | {w[1] - w[0] + 1} → {e - s + 1} | {c((ev['min'] - s) * dt)} | {c((e - ev['min']) * dt)} | "
                     f"{c(before, 1)} → {c(after, 1)} | {c(p[0]['vd'])} / {c(p[1]['vd'])} → {c(p[0]['vd_rec'])} / {c(p[1]['vd_rec'])} | {flag} |  |")
    (out / "resumen.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("outputs/recorte")
    events = load(folder)
    only = {int(x) for x in sys.argv[2].split(",")} if len(sys.argv) > 2 else set(events)
    out = folder / "verificacion"
    out.mkdir(parents=True, exist_ok=True)
    summary(events, out)
    for n in sorted(only):
        draw(events[n], n, out, video=True)
        print(f"evento {n} listo")


if __name__ == "__main__":
    main()
