#!/usr/bin/env python3
"""Animaciones nuevas de la presentación (además de la de R7 en presentation_figures.py), con su fotograma.

Uso (desde TP5/): py scripts/animation/presentation_videos.py
  Evento representativo: 16 (distancia mínima real y ECM 1 de A más cerca de las medianas de los 19; decisión del
  grupo del 11/11, antes era el 11). La capa F ya no está en las animaciones principales.
  1. anim-sin-capa-vs-A: evento 16, real vs sin capa vs A(3; 0,5).
  2. anim-recorte: evento 11 (decisión del grupo: el ángulo del objetivo en el 1.er s pasa de 17,5° a 1,8°), trayectoria
     completa y tramo recortado, con la flecha hacia el objetivo y su ángulo con x en cada inicio.
  3. anim-A-B: evento 16, real vs A(3; 0,5) vs B(3,5; 1) (reemplaza a la de A, B y F de R7).
  4. anim-lado-evento12: evento 12, real vs A(3; 0,5) (A elige el lado de cruce contrario al real).
Además copia los MP4 que usa la presentación a presentacion/animaciones/ con nombres por diapositiva.
Mismo estilo que R7: real en negro con círculo gris relleno, simulados con círculo de color hueco, reloj, coma
decimal, sin título. Un cuadro de video por cuadro experimental (Δt_exp), a 15 cuadros/s: tiempo real. Sin
interpolación: cada cuadro muestra las filas del motor con t ≤ instante del cuadro y los datos experimentales hasta
ese cuadro. MP4 en outputs/pilot/animaciones_presentacion/; fotogramas PNG (sin reloj) en presentacion/figuras/.
"""
import csv
import math
import shutil
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "graph_gen"))
from figure_data import R, experimental, read_run  # noqa: E402

DATA = Path("data")
OUT = Path("outputs/pilot/animaciones_presentacion")
DEST = Path("presentacion/figuras")
RUN_A = Path("outputs/pilot/figs/datos/a_3_0.5")
RUN_B = Path("outputs/pilot/figs/datos/b_3.5_1")
BASELINE = Path("outputs/baseline")
ANIM = Path("presentacion/animaciones")
EVENT = 16
# Mismos colores que presentation_figures.py (Okabe-Ito); "sin capa" en púrpura para no confundirlo con el gris real
COLORS = {"real": "#000000", "A": "#0072B2", "B": "#E69F00", "sin capa": "#CC79A7", "izq": "#0072B2", "der": "#E69F00"}
# MP4 que usa la presentación -> copia en presentacion/animaciones/ con el nombre de su diapositiva
COPIES = {
    "anim-recorte.mp4": "01_recorte_evento11.mp4",
    "anim-sin-capa-vs-A.mp4": "02_sin_capa_vs_A_evento16.mp4",
    "anim-A-B.mp4": "03_A_y_B_evento16.mp4",
    "anim-lado-evento12.mp4": "04_lado_contrario_evento12.mp4",
}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
MINUS = "−"
COMMA = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",").replace("-", MINUS))

# Letra grande: los cuadros van chicos en la diapositiva (dos apilados junto a d(t)); ver FRAME_SIZE
plt.rcParams.update({"font.size": 22, "axes.labelsize": 24, "legend.fontsize": 20, "xtick.labelsize": 21,
                     "ytick.labelsize": 21, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED})


# Rótulo de cada corrida en la leyenda (con el par: la diapositiva no lo repite)
LABELS = {"sin capa": "sin capa", "A": "A(3; 0,5)", "B": "B(3,5; 1)"}
FRAME_SIZE = (6.6, 3.4)     # pulgadas: a ~5,7 cm de ancho en la diapositiva, 20–24 pt quedan en ~7–9 pt
FRAME_SIZE_COMPACT = (8.4, 2.05)     # lámina 13: rango de y ajustado y leyenda a la derecha; el lienzo del MP4 sigue al PNG


def style(ax):
    ax.grid(color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(COMMA)
    ax.yaxis.set_major_formatter(COMMA)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")


def clock_text(t):
    return f"t = {t:.2f} s".replace(".", ",")


def real_minimum(exp):
    """Instante (cuadro experimental común) de la distancia mínima real."""
    a, b = exp
    common = np.intersect1d(np.round(a[:, 0], 6), np.round(b[:, 0], 6))
    d = [math.hypot(*(a[np.argmin(np.abs(a[:, 0] - t)), 1:] - b[np.argmin(np.abs(b[:, 0] - t)), 1:])) for t in common]
    return float(common[int(np.argmin(d))])


# ---------------------------------------------------------------- real vs simulados (1 y 3)
class Overlay:
    """Real (negro, círculo gris relleno) y una o más corridas simuladas (color, círculo hueco)."""

    def __init__(self, exp, runs, figsize=FRAME_SIZE, compact=False):
        """compact (lámina 13, dos animaciones apiladas): rango de y ajustado a las trayectorias, leyenda a la derecha del eje
        (fuera del área del gráfico, como en el recorte) y reloj arriba a la derecha, también afuera. Así la figura queda
        más apaisada y las trayectorias se ven más grandes con la misma altura en la diapositiva."""
        self.exp, self.runs, self.compact = exp, runs, compact
        self.fig, self.ax = plt.subplots(figsize=figsize, constrained_layout=True)
        ax = self.ax
        ax.set_xlim(min(e[:, 1].min() for e in exp) - 0.4, max(e[:, 1].max() for e in exp) + 0.4)
        ys = np.concatenate([e[:, 2] for e in exp] + [r[:, 2] for r in runs.values()] + [r[:, 6] for r in runs.values()])
        if compact:
            ax.set_ylim(np.nanmin(ys) - R - 0.1, np.nanmax(ys) + R + 0.1)     # el círculo de radio R entra entero
        else:
            ax.set_ylim(np.nanmin(ys) - 0.5, np.nanmax(ys) + 2.1)     # franja libre arriba para la leyenda
        style(ax)
        self.lines, self.dots = {}, {}
        for name in ["real"] + list(runs):
            color = COLORS[name]
            for i in (0, 1):
                self.lines[(name, i)], = ax.plot([], [], "-" if i == 0 else "--", color=color, lw=2.4, alpha=0.9)
                c = plt.Circle((np.nan, np.nan), R, fill=(name == "real"), color=color,
                               alpha=0.35 if name == "real" else 1, lw=2)
                ax.add_patch(c)
                self.dots[(name, i)] = c
        handles = [Line2D([], [], color=COLORS["real"], lw=2.4, label="real")]
        handles += [Line2D([], [], color=COLORS[n], lw=3, label=LABELS[n]) for n in runs]
        handles += [Line2D([], [], ls="none", marker="o", ms=17, color=COLORS["real"], alpha=0.35, label="posición real")]
        if compact:
            # A la derecha del eje, fuera del área del gráfico, una entrada por fila, letra 19 pt (≤ ticks, 21 pt). Así el
            # área del gráfico usa toda la altura de la figura (la leyenda ya no ocupa una franja debajo)
            ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.02, 0.5), borderaxespad=0, ncol=1, frameon=False,
                      fontsize=19, handlelength=1.5, borderpad=0.3, labelspacing=0.35)
            self.clock = ax.text(1.0, 1.03, "", transform=ax.transAxes, ha="right", va="bottom", fontsize=19, color=INK)
        else:
            ax.legend(handles=handles, loc="upper right", ncol=2, frameon=True, framealpha=0.95, fontsize=20,
                      handlelength=1.5, columnspacing=0.9, borderpad=0.3)
            self.clock = ax.text(0.02, 0.95, "", transform=ax.transAxes, va="top", fontsize=20, color=INK)

    def update(self, t, with_clock=True):
        for i, e in enumerate(self.exp):
            k = e[:, 0] <= t + 1e-9
            self.lines[("real", i)].set_data(e[k, 1], e[k, 2])
            if k.any():
                self.dots[("real", i)].center = (e[k][-1, 1], e[k][-1, 2])
        for name, run in self.runs.items():
            k = run[:, 0] <= t + 1e-9
            for i in (0, 1):
                x, y = run[k, 1 + 4 * i], run[k, 2 + 4 * i]
                self.lines[(name, i)].set_data(x, y)
                ok = ~np.isnan(x)
                self.dots[(name, i)].center = (x[ok][-1], y[ok][-1]) if ok.any() else (np.nan, np.nan)
        if self.compact:
            # En el cuadro del PDF el reloj es transparente pero ocupa su lugar: el PNG y el MP4 quedan con el mismo
            # encuadre y el PPTX pone el video exacto sobre el cuadro
            self.clock.set_text(clock_text(t))
            self.clock.set_alpha(1 if with_clock else 0)
        else:
            self.clock.set_text(clock_text(t) if with_clock else "")
        return []


def overlay_video(name, exp, runs, dt_exp, t_end, t_frame, compact=False):
    ov = Overlay(exp, runs, figsize=FRAME_SIZE_COMPACT if compact else FRAME_SIZE, compact=compact)
    ov.update(t_frame, with_clock=False)
    if compact:
        # Lienzo completo, igual que el MP4: misma proporción, así el PPTX pone el video exacto sobre el cuadro
        ov.fig.savefig(DEST / f"{name}.png", dpi=150)
    else:
        ov.fig.savefig(DEST / f"{name}.png", dpi=150, bbox_inches="tight", pad_inches=0.06)
    times = np.arange(0, t_end + 1e-9, dt_exp)
    anim = animation.FuncAnimation(ov.fig, lambda t: ov.update(t), frames=times, blit=False)
    out = OUT / f"{name}.mp4"
    anim.save(out, writer=animation.FFMpegWriter(fps=round(1 / dt_exp), bitrate=2400), dpi=110)
    plt.close(ov.fig)
    return out


def sin_capa_vs_a(event=EVENT):
    header, run_a = read_run(RUN_A / f"evento_{event:02d}.txt")
    _, run_base = read_run(BASELINE / f"evento_{event:02d}.txt")
    exp = experimental(DATA, header)
    dt_exp = float(header["dt_exp"])
    # Fotograma: primer cuadro experimental con contacto sin capa (distancia entre centros < 2R); si no hay, el
    # mínimo real
    d = np.hypot(run_base[:, 1] - run_base[:, 5], run_base[:, 2] - run_base[:, 6])
    frame_times = run_base[::4, 0]              # filas cada Δt_exp/4: una de cada 4 cae en un cuadro experimental
    contact = [t for t, dd in zip(frame_times, d[::4]) if dd < 2 * R]
    if contact:
        t_frame, why = float(contact[0]), "primer cuadro con contacto sin capa"
    else:
        t_frame, why = real_minimum(exp), "mínimo real (sin capa no tiene contacto)"
    t_end = min(e[-1, 0] for e in exp)
    out = overlay_video("anim-sin-capa-vs-A", exp, {"sin capa": run_base, "A": run_a}, dt_exp, t_end, t_frame, compact=True)
    return out, t_frame, t_end, why


def a_y_b(event=EVENT):
    header, run_a = read_run(RUN_A / f"evento_{event:02d}.txt")
    _, run_b = read_run(RUN_B / f"evento_{event:02d}.txt")
    exp = experimental(DATA, header)
    dt_exp = float(header["dt_exp"])
    t_frame = real_minimum(exp)
    t_end = min(e[-1, 0] for e in exp)
    out = overlay_video("anim-A-B", exp, {"A": run_a, "B": run_b}, dt_exp, t_end, t_frame, compact=True)
    return out, t_frame, t_end


def lado_evento12():
    header, run_a = read_run(RUN_A / "evento_12.txt")
    exp = experimental(DATA, header)
    dt_exp = float(header["dt_exp"])
    t_frame = real_minimum(exp)
    t_end = min(e[-1, 0] for e in exp)
    out = overlay_video("anim-lado-evento12", exp, {"A": run_a}, dt_exp, t_end, t_frame)
    return out, t_frame, t_end


# ---------------------------------------------------------------- recorte (2)
RECORTE_EVENT = 11   # decisión del grupo (11/11): ángulo del objetivo en el 1.er s, 17,5° -> 1,8° (outputs/recorte/verificacion/resumen.md)
GRAY = "#9a9994"
HIDE_NEAR = 2.0      # m: la flecha se oculta cerca del objetivo (ahí gira sola y su ángulo no dice nada)


def recorte(event=RECORTE_EVENT):
    """Un panel: trayectoria completa (gris) y tramo recortado (color), con reloj. En cada cuadro, flecha desde la
    posición real hacia el objetivo que corresponde (fuera del tramo: gris, hacia el cuadrado; dentro: color, hacia la
    cruz) y su ángulo con el eje x, que cambian en el tiempo. El PNG del PDF es el cuadro del primer segundo con el
    mayor ángulo.
    Sale de lo que exporta `trim-export` (mismos datos que scripts/animation/trim_check.py)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    # trim_check cambia los rcParams al importarse: rc_context los restaura, para que este cuadro y los que se
    # generan después (ab, lado) tengan la misma letra que el resto
    with plt.rc_context():
        from trim_check import SENSE, axis_angle, load, pos
    ev = load(Path("outputs/recorte"))[event]
    dt_exp = ev["dt"]
    (w0, w1), (r0, r1) = ev["win"], ev["rec"]
    peds = ev["peds"]
    names = ("izq", "der")
    fig, ax = plt.subplots(figsize=(7.6, 4.3), constrained_layout=True)
    style(ax)
    allx = np.concatenate([p["x"] for p in peds])
    ally = np.concatenate([p["y"] for p in peds])
    ax.set_xlim(allx.min() - 0.6, allx.max() + 0.6)
    ax.set_ylim(ally.min() - 0.5, ally.max() + 0.9)     # margen arriba solo para el reloj (la leyenda va debajo del eje)

    def arrow(q, target, color, lw):
        dx, dy = target[0] - q[0], target[1] - q[1]
        n = math.hypot(dx, dy) or 1
        tip = (q[0] + 1.2 * dx / n, q[1] + 1.2 * dy / n)
        art = ax.annotate("", xy=tip, xytext=q, arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=22), zorder=6)
        return art, tip

    for i, p in enumerate(peds):
        ax.plot(p["x"], p["y"], color="#c9c8c3", lw=2.5, zorder=1)
        k = (p["f"] >= r0) & (p["f"] <= r1)
        ax.plot(p["x"][k], p["y"][k], "-" if i == 0 else "--", color=COLORS[names[i]], lw=3.4, zorder=2)
        ax.plot(*p["target"], "s", mfc="none", mec=GRAY, ms=15, mew=2.5, zorder=3)
        ax.plot(*p["target_rec"], "X", color=COLORS[names[i]], ms=16, mec="white", mew=1, zorder=3)

    # Ángulo dinámico (como outputs/recorte/verificacion/evento_NN.mp4): en cada cuadro, flecha desde la posición real
    # hacia el objetivo que corresponde (fuera del tramo recortado: gris, hacia el objetivo de la trayectoria completa;
    # dentro: color, hacia el del tramo) y su ángulo con el eje x en el sentido de avance, junto a la punta.
    angle_texts = [ax.text(np.nan, np.nan, "", fontsize=23, fontweight="bold", zorder=7) for _ in peds]

    def target_now(i, p, frame):
        inside = r0 <= frame <= r1
        return (p["target_rec"], COLORS[names[i]]) if inside else (p["target"], GRAY)

    def max_angle(frame):
        """Mayor |ángulo hacia el objetivo| de los dos peatones en ese cuadro (NaN si ninguno está en la ventana)."""
        vals = []
        for i, p in enumerate(peds):
            q = pos(p, frame)
            if q is not None and w0 <= frame <= w1:
                target, _ = target_now(i, p, frame)
                vals.append(abs(axis_angle(target[0] - q[0], target[1] - q[1], SENSE[i])))
        return max(vals) if vals else np.nan

    dots = [plt.Circle((np.nan, np.nan), R, fill=True, color=COLORS["real"], alpha=0.35, lw=2) for _ in peds]
    for d in dots:
        ax.add_patch(d)
    moving = [None, None]
    handles = [Line2D([], [], color="#c9c8c3", lw=2.5, label="trayectoria completa"),
               Line2D([], [], color=COLORS["izq"], lw=3.4, label="tramo recortado, izq."),
               Line2D([], [], color=COLORS["der"], lw=3.4, ls="--", label="tramo recortado, der."),
               Line2D([], [], marker="s", mfc="none", mec=GRAY, mew=2.5, ls="none", ms=13, label="objetivo, completa"),
               Line2D([], [], marker="X", color=MUTED, mec="white", ls="none", ms=14, label="objetivo, recortado"),
               Line2D([], [], ls="none", marker="o", ms=15, color=COLORS["real"], alpha=0.35, label="posición real")]
    # Leyenda fuera del área del gráfico, debajo del eje, para no tapar ejes ni trayectorias. 2 columnas × 3 filas a
    # 19 pt (≤ ticks, 21 pt): en 2 filas solo entraba a 13 pt en las 7,6 in de la figura. Va dentro del lienzo
    # (constrained_layout le reserva lugar) para que también salga en el MP4. Anclada al eje, debajo del rótulo x.
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.33), ncol=2, frameon=False, fontsize=19,
              handlelength=1.5, columnspacing=0.9, borderpad=0.3)
    clock = ax.text(0.01, 0.97, "", transform=ax.transAxes, va="top", fontsize=20, color=INK)
    f0 = int(min(p["f"][0] for p in peds))
    f1 = int(max(p["f"][-1] for p in peds))

    def update(frame):
        for i, p in enumerate(peds):
            if moving[i] is not None:
                moving[i].remove()
                moving[i] = None
            angle_texts[i].set_text("")
            q = pos(p, frame)
            dots[i].center = q if q is not None else (np.nan, np.nan)
            if q is None or not (w0 <= frame <= w1):
                continue
            target, color = target_now(i, p, frame)
            if math.hypot(target[0] - q[0], target[1] - q[1]) > HIDE_NEAR:
                moving[i], tip = arrow(q, target, color, 3.0)
                a = axis_angle(target[0] - q[0], target[1] - q[1], SENSE[i])
                angle_texts[i].set_position((tip[0] + (0.15 if SENSE[i] > 0 else -0.15), tip[1] - 0.15))
                angle_texts[i].set_text(f"{a:+.0f}°".replace("-", MINUS))
                angle_texts[i].set_color(color)
                angle_texts[i].set_ha("left" if SENSE[i] > 0 else "right")
                angle_texts[i].set_va("top")
        clock.set_text(clock_text((frame - f0) * dt_exp))
        return []

    # Cuadro del PDF: el del primer segundo de la ventana con el mayor ángulo hacia el objetivo (de los dos peatones)
    first = range(w0, min(w1, w0 + round(1 / dt_exp)) + 1)
    pdf_frame = max(first, key=lambda fr: np.nan_to_num(max_angle(fr), nan=-1))
    update(pdf_frame)
    fig.savefig(DEST / "anim-recorte.png", dpi=150, bbox_inches="tight", pad_inches=0.06)
    print(f"recorte: cuadro del PDF en t = {(pdf_frame - f0) * dt_exp:.2f} s (frame {pdf_frame}), "
          f"ángulo máximo {max_angle(pdf_frame):.1f}°")
    anim = animation.FuncAnimation(fig, update, frames=range(f0, f1 + 1), blit=False)
    out = OUT / "anim-recorte.mp4"
    anim.save(out, writer=animation.FFMpegWriter(fps=round(1 / dt_exp), bitrate=2400), dpi=110)
    plt.close(fig)
    return out, (f1 - f0) * dt_exp


def main():
    """Uso: presentation_videos.py [clave ...] con claves recorte, sincapa, ab, lado; sin claves, todas."""
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    DEST.mkdir(parents=True, exist_ok=True)
    ANIM.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:]) or {"recorte", "sincapa", "ab", "lado"}
    if "sincapa" in only:
        out, tf, te, why = sin_capa_vs_a()
        print(f"{out}: fotograma en t = {tf:.2f} s ({why}), duración {te:.2f} s")
    if "recorte" in only:
        out, te = recorte()
        print(f"{out}: duración {te:.2f} s")
    if "ab" in only:
        out, tf, te = a_y_b()
        print(f"{out}: fotograma en t = {tf:.2f} s (mínimo real), duración {te:.2f} s")
    if "lado" in only:
        out, tf, te = lado_evento12()
        print(f"{out}: fotograma en t = {tf:.2f} s (mínimo real), duración {te:.2f} s")
    for src, dst in COPIES.items():
        if (OUT / src).exists():
            shutil.copy(OUT / src, ANIM / dst)
            print(f"copia: {ANIM / dst}")


if __name__ == "__main__":
    main()
