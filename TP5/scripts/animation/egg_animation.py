#!/usr/bin/env python3
"""Animación de la capa E (huevo): tres simulaciones, una por panel, a media velocidad.

Cada peatón simulado lleva su huevo (punta hacia la velocidad); el huevo se pinta de rojo, rayado y con el rótulo
"solape" cuando se mete en el del otro. La flecha negra es e_target (la dirección que elige la capa) y la gris, e_t
(hacia el target final). Las trayectorias experimentales van punteadas, con un círculo hueco en la posición real.
Lee las salidas del motor (scripts/sim_gen/egg.sh). Necesita matplotlib y ffmpeg.
Uso: python scripts/animation/egg_animation.py [carpeta de corridas] [carpeta de datos]
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.animation import FFMpegWriter, FuncAnimation  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Circle, FancyArrow, Patch, Polygon  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "graph_gen"))
from egg_geometry import MIN_SPEED, R, boundary, egg_gaps, placed, read_run  # noqa: E402
from figure_data import experimental  # noqa: E402

INK, MUTED, GRID, SURFACE = "#0b0b0b", "#8a8984", "#e6e5e0", "#fcfcfb"
PED = ("#2a78d6", "#eb6834")          # categóricos 1 y 2
PED_FILL = ("#cde2fb", "#fbe1d5")
CRITICAL = "#d03b3b"                  # estado: solape (siempre con rayado y rótulo)
A, B = 3.0, 0.35
FPS = 30                              # una fila (Δt_exp/4) por cuadro: media velocidad
ARROW = 0.75

PANELS = [
    ("e_3_0.35", 2, "Evento 2 · a = 3 m, b = 0,35 m · al tocarse las puntas se deslizan a su derecha"),
    ("e_3_0.35", 14, "Evento 14 · a = 3 m, b = 0,35 m · el contacto los manda a su izquierda"),
    ("e_3_0.35_dt4", 19, "Evento 19 · a = 3 m · paso grueso Δt = Δt_exp/4 · el solape crece (hasta 7 mm) y se corrige girando al revés"),
]


def fmt(x, digits=2):
    return f"{x:+.{digits}f}".replace(".", ",") if x < 0 else f"{x:.{digits}f}".replace(".", ",")


def load(folder, event, data_dir):
    header, run = read_run(folder / f"evento_{event:02d}.txt")
    directions = np.genfromtxt(folder / f"direccion_{event:02d}.txt", comments="#")
    exp = experimental(data_dir, header)
    gaps = egg_gaps(run, A, B)
    return dict(header=header, run=run, dirs=directions, exp=exp, gaps=gaps, dt_exp=float(header["dt_exp"]))


def heading(row, ped, fallback):
    vx, vy = row[3 + 4 * ped], row[4 + 4 * ped]
    return np.arctan2(vy, vx) if np.hypot(vx, vy) > MIN_SPEED else fallback


def main():
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/egg")
    data_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "data")
    sims = [load(folder / sub, ev, data_dir) for sub, ev, _ in PANELS]
    shape = boundary(A, B)
    frames = max(len(s["run"]) for s in sims)

    plt.rcParams.update({"font.size": 12, "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})
    fig, axes = plt.subplots(len(sims), 1, figsize=(13, 11), facecolor=SURFACE)
    fig.subplots_adjust(left=0.06, right=0.985, top=0.885, bottom=0.05, hspace=0.42)
    fig.suptitle("Capa E: espacio personal con forma de huevo (punta hacia la velocidad)", fontsize=16, color=INK, x=0.06, ha="left", y=0.985)
    handles = [
        Line2D([], [], color=PED[0], lw=2, label="peatón 1 simulado"),
        Line2D([], [], color=PED[1], lw=2, label="peatón 2 simulado"),
        Line2D([], [], color=MUTED, lw=1.2, ls=(0, (2, 2)), marker="o", mfc="none", ms=8, label="experimental"),
        Line2D([], [], color=INK, lw=2, label="e_target"),
        Line2D([], [], color=MUTED, lw=2, label="e_t (al target)"),
        Patch(facecolor="none", edgecolor=CRITICAL, hatch="///", lw=2, label="huevo solapado"),
    ]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.055, 0.955), ncol=6, frameon=False, fontsize=11, handlelength=2.2)
    clock = fig.text(0.985, 0.985, "", ha="right", va="top", fontsize=14, color=INK)

    artists = []
    for ax, sim, (_, _, title) in zip(axes, sims, PANELS):
        run, exp = sim["run"], sim["exp"]
        xs = np.concatenate([run[:, 1], run[:, 5]] + [e[:, 1] for e in exp])
        ys = np.concatenate([run[:, 2], run[:, 6]] + [e[:, 2] for e in exp])
        ax.set_xlim(np.nanmin(xs) - 0.6, np.nanmax(xs) + 0.6)
        ax.set_ylim(np.nanmin(ys) - 0.9, np.nanmax(ys) + 0.9)
        ax.set_aspect("equal")
        ax.set_facecolor(SURFACE)
        ax.grid(color=GRID, lw=0.8)
        ax.tick_params(labelsize=10)
        ax.set_ylabel("y (m)", color=MUTED)
        ax.set_title(title, loc="left", fontsize=12.5, color=INK)
        a = dict(trail=[], body=[], egg=[], ghost=[], arrow=[None, None], arrow_t=[None, None])
        for p in (0, 1):
            ax.plot(exp[p][:, 1], exp[p][:, 2], color=PED[p], lw=1.2, ls=(0, (2, 2)), alpha=0.55)
            a["trail"].append(ax.plot([], [], color=PED[p], lw=2)[0])
            egg = Polygon(np.zeros((3, 2)), closed=True, facecolor="none", edgecolor=PED[p], lw=1.6)
            egg.set_facecolor((*matplotlib.colors.to_rgb(PED[p]), 0.12))
            ax.add_patch(egg)
            a["egg"].append(egg)
            body = Circle((np.nan, np.nan), R, facecolor=PED_FILL[p], edgecolor=PED[p], lw=2, zorder=4)
            ax.add_patch(body)
            a["body"].append(body)
            ghost = Circle((np.nan, np.nan), R, facecolor="none", edgecolor=PED[p], lw=1.2, ls=(0, (2, 2)), alpha=0.8, zorder=3)
            ax.add_patch(ghost)
            a["ghost"].append(ghost)
        # Target final de cada peatón: la última posición experimental de la ventana
        for p in (0, 1):
            ax.plot(*exp[p][-1, 1:], marker="x", color=PED[p], ms=10, mew=2, zorder=2)
        a["stats"] = ax.text(0.995, 0.04, "", transform=ax.transAxes, ha="right", va="bottom", fontsize=11.5, color=INK,
                             bbox=dict(facecolor=SURFACE, edgecolor=GRID, boxstyle="round,pad=0.3"), zorder=6)
        a["flag"] = ax.text(0.005, 0.965, "", transform=ax.transAxes, ha="left", va="top", fontsize=12, color=CRITICAL,
                            fontweight="bold", zorder=6)
        a["min"] = [np.inf, 0.0]
        artists.append(a)
    axes[-1].set_xlabel("x (m)", color=MUTED)

    def update(k):
        clock.set_text(f"t = {fmt(k * sims[0]['dt_exp'] / 4)} s  (½ velocidad)")
        changed = [clock]
        for ax, sim, a in zip(axes, sims, artists):
            run, dirs = sim["run"], sim["dirs"]
            i = min(k, len(run) - 1)
            row, gap = run[i], sim["gaps"][i]
            t = row[0]
            overlap = np.isfinite(gap) and gap < -1e-3
            for p in (0, 1):
                x, y = row[1 + 4 * p], row[2 + 4 * p]
                past = run[: i + 1]
                a["trail"][p].set_data(past[:, 1 + 4 * p], past[:, 2 + 4 * p])
                for key in ("arrow", "arrow_t"):
                    if a[key][p] is not None:
                        a[key][p].remove()
                        a[key][p] = None
                if np.isnan(x):
                    a["body"][p].set_center((np.nan, np.nan))
                    a["egg"][p].set_xy(np.zeros((3, 2)) + np.nan)
                else:
                    a["body"][p].set_center((x, y))
                    a["egg"][p].set_xy(placed(shape, x, y, heading(row, p, 0.0 if p == 0 else np.pi)))
                    a["egg"][p].set_edgecolor(CRITICAL if overlap else PED[p])
                    a["egg"][p].set_hatch("///" if overlap else None)
                    a["egg"][p].set_linewidth(2.4 if overlap else 1.6)
                    d = dirs[i]
                    on, ex, ey, tx, ty = d[1 + 5 * p], d[2 + 5 * p], d[3 + 5 * p], d[4 + 5 * p], d[5 + 5 * p]
                    a["arrow_t"][p] = ax.add_patch(FancyArrow(x, y, ARROW * ex, ARROW * ey, width=0.025, head_width=0.13,
                                                              head_length=0.13, color=MUTED, alpha=0.8, zorder=5, length_includes_head=True))
                    if on == 1:
                        a["arrow"][p] = ax.add_patch(FancyArrow(x, y, ARROW * tx, ARROW * ty, width=0.03, head_width=0.15,
                                                                head_length=0.15, color=INK, zorder=5, length_includes_head=True))
                # Posición experimental en el mismo instante (si hay frame)
                e = sim["exp"][p]
                j = int(np.argmin(np.abs(e[:, 0] - t)))
                a["ghost"][p].set_center(e[j, 1:] if abs(e[j, 0] - t) < sim["dt_exp"] / 2 else (np.nan, np.nan))
            dist = np.hypot(row[1] - row[5], row[2] - row[6])
            if np.isfinite(dist):
                a["min"][0] = min(a["min"][0], dist)
            if np.isfinite(gap):
                a["min"][1] = min(a["min"][1], gap)
            gap_text = fmt(gap, 3) if np.isfinite(gap) else "—"
            done = " · fin" if k >= len(run) - 1 else ""
            a["stats"].set_text(f"separación de huevos {gap_text} m · distancia mín. {fmt(a['min'][0])} m · "
                                f"peor solape {fmt(min(0, a['min'][1]), 3)} m{done}")
            a["flag"].set_text("⚠ solape: giran al revés" if overlap else "")
            changed += [a["stats"], a["flag"]]
        return changed

    anim = FuncAnimation(fig, update, frames=frames, blit=False)
    out = folder / "egg_animation.mp4"
    anim.save(out, writer=FFMpegWriter(fps=FPS, bitrate=4000), dpi=110, savefig_kwargs={"facecolor": SURFACE})
    # Cuadros sueltos para revisar sin el video
    worst = int(np.nanargmin(sims[-1]["gaps"]))      # el peor solape del paso grueso
    for k in (int(frames * 0.25), int(frames * 0.45), int(frames * 0.6), worst):
        update(k)
        fig.savefig(folder / f"egg_frame_{k:04d}.png", dpi=80, facecolor=SURFACE)
    print("Animación:", out)


if __name__ == "__main__":
    main()
