#!/usr/bin/env python3
"""Figuras de la presentación (PDF vectorial), con el recorte vigente: D(45°) + compuerta de tramo compartido.

Reglas de la cátedra: sin título embebido, leyenda adentro en la esquina libre, letra grande, ejes cortos, colores aptos
para daltónicos (azul / naranja / verde de Okabe-Ito y negro para lo experimental), todo en español, parámetros fijos
fuera de la leyenda (van en el caption). Salen en outputs/pilot/figs/ y se copian a presentacion/figuras/.
Uso: py scripts/graph_gen/presentation_figures.py [evento]
"""
import csv
import math
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import animation  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from cross_validation import error_matrix, evaluate, evaluate_on_all, partitions  # noqa: E402
from figure_data import R, common_times, experimental, read_run  # noqa: E402
from pilot_analysis import load_grid  # noqa: E402

P = Path("outputs/pilot")
FIGS = P / "figs"
DEST = Path("presentacion/figuras")
DATA = Path("data")
PAIRS = {"A": (3.0, 0.5), "B": (3.5, 1.0), "F": (0.9, 3.0)}     # mejores de ECM 1 excl. con la compuerta
COLORS = {"A": "#0072B2", "B": "#E69F00", "F": "#009E73", "exp": "#000000", "base": "#CC79A7"}   # Okabe-Ito; sin capa en púrpura, como en las animaciones
MARKERS = {"A": "o", "B": "s", "F": "^"}
RHO = 0.9
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
MINUS = "−"     # signo menos tipográfico (U+2212): con el formateador propio matplotlib no lo pone solo


def num(text):
    """Coma decimal y signo menos real en un número ya formateado."""
    return text.replace(".", ",").replace("-", MINUS)


COMMA = FuncFormatter(lambda v, _: num(f"{v:g}"))
CREATED = []

plt.rcParams.update({"font.size": 18, "axes.labelsize": 20, "legend.fontsize": 16, "xtick.labelsize": 17, "ytick.labelsize": 17,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "pdf.fonttype": 42, "axes.titlesize": 18})


def style(ax, grid_axis="both"):
    ax.grid(axis=grid_axis, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(COMMA)
    ax.yaxis.set_major_formatter(COMMA)


def save(fig, name):
    for ax in fig.axes:
        assert not ax.get_title(), f"{name}: título embebido"
    assert fig._suptitle is None, f"{name}: suptitle embebido"
    # bbox tight: con aspect="equal" constrained_layout deja franjas vacías arriba y abajo
    fig.savefig(FIGS / name, dpi=150 if name.endswith(".png") else None, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    CREATED.append(name)


def pair_rows(layer, pair=None, folder=P):
    rows = load_grid(folder / f"grid_{layer}.txt")
    pair = pair or PAIRS[layer]
    sel = rows[(rows[:, 0] == pair[0]) & (rows[:, 1] == pair[1])]
    return sel[np.argsort(sel[:, 2])]


def run_dir(layer):
    p = PAIRS[layer]
    return FIGS / "datos" / f"{layer.lower()}_{p[0]:g}_{p[1]:g}"


# ---------------------------------------------------------------- S1
def s1(event):
    tracks = defaultdict(dict)
    with open("outputs/recorte/trayectorias_recortadas.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if int(r["evento"]) == event:
                tracks[int(r["peaton"]) - 1].setdefault("rows", []).append((float(r["x"]), float(r["y"]), r["en_recorte"] == "1"))
    # Más chica en pulgadas con la misma letra: en la diapositiva la letra queda más grande
    fig, ax = plt.subplots(figsize=(10, 5.2), constrained_layout=True)
    names = ("izquierdo", "derecho")
    for i in (0, 1):
        t = np.array(tracks[i]["rows"], dtype=float)
        ax.plot(t[:, 0], t[:, 1], color="#b8b7b2", lw=3, label="trayectoria completa" if i == 0 else None)
        k = t[:, 2] > 0
        ax.plot(t[k, 0], t[k, 1], "-" if i == 0 else "--", color=COLORS["A" if i == 0 else "B"], lw=3.6, label=f"tramo, peatón {names[i]}")
        idx = np.flatnonzero(k)
        ax.plot(t[idx[0], 0], t[idx[0], 1], "o", color=COLORS["A" if i == 0 else "B"], ms=13, mec="white", mew=1.5)
        ax.plot(t[idx[-1], 0], t[idx[-1], 1], "X", color=COLORS["A" if i == 0 else "B"], ms=16, mec="white", mew=1.2)
    ax.plot([], [], "o", color=MUTED, ms=13, label="inicio")
    ax.plot([], [], "X", color=MUTED, ms=16, label="objetivo")
    ax.set_xlabel("x [m]", fontsize=24)
    ax.set_ylabel("y [m]", fontsize=24)
    ax.tick_params(labelsize=21)
    ax.set_aspect("equal")
    ax.set_xlim(-0.5, 12)
    ax.set_ylim(-2.4, 4.0)      # franja libre abajo para la leyenda, sin tapar trayectorias
    ax.set_yticks(range(0, 5))  # sin marcas en la franja de la leyenda, donde no hay datos
    style(ax)
    ax.legend(loc="lower center", ncol=3, frameon=True, framealpha=0.95, fontsize=17, columnspacing=1.0, handlelength=1.6)
    save(fig, "S1-recorte-evento.pdf")


# ---------------------------------------------------------------- R1 y R7
def r1(event):
    header, run = read_run(Path("outputs/baseline") / f"evento_{event:02d}.txt")
    exp = experimental(DATA, header)
    fig, ax = plt.subplots(figsize=(12, 5.2), constrained_layout=True)
    for i, e in enumerate(exp):
        ax.plot(e[:, 1], e[:, 2], "-" if i == 0 else "--", color=COLORS["exp"], lw=2.6, label="real" if i == 0 else None)
        x, y = run[:, 1 + 4 * i], run[:, 2 + 4 * i]
        ax.plot(x, y, "-" if i == 0 else "--", color=COLORS["base"], lw=2.6, label="simulado sin capa" if i == 0 else None)
    ax.plot([], [], "-", color=MUTED, lw=2.6, label="peatón izquierdo")
    ax.plot([], [], "--", color=MUTED, lw=2.6, label="peatón derecho")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_aspect("equal")
    style(ax)
    ax.set_ylim(0.6, 3.2)
    ax.legend(loc="lower right", ncol=2, frameon=True, framealpha=0.95, fontsize=14)
    save(fig, "R1-linea-base.pdf")


def legend_r7():
    """Leyenda de R7 y del video: trayectorias por capa y el círculo gris de la posición real."""
    from matplotlib.lines import Line2D
    return ([Line2D([], [], color=COLORS["exp"], lw=2.4, label="real")]
            + [Line2D([], [], color=COLORS[l], lw=2.4, label=l) for l in "ABF"]
            + [Line2D([], [], ls="none", marker="o", ms=15, color=COLORS["exp"], alpha=0.35, label="posición real")])


def r7(event):
    runs = {}
    for layer in "ABF":
        header, run = read_run(run_dir(layer) / f"evento_{event:02d}.txt")
        runs[layer] = run
    exp = experimental(DATA, header)
    dt_exp = float(header["dt_exp"])
    t_exp = [e[:, 0] for e in exp]
    fig, ax = plt.subplots(figsize=(12, 5.4), constrained_layout=True)
    ax.set_xlim(min(e[:, 1].min() for e in exp) - 0.4, max(e[:, 1].max() for e in exp) + 0.4)
    ys = np.concatenate([e[:, 2] for e in exp] + [runs[l][:, 2] for l in "ABF"] + [runs[l][:, 6] for l in "ABF"])
    ax.set_ylim(np.nanmin(ys) - 0.7, np.nanmax(ys) + 0.9)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    style(ax)
    series = [("real", COLORS["exp"], None)] + [(l, COLORS[l], l) for l in "ABF"]
    lines, dots = {}, {}
    for name, color, layer in series:
        for i in (0, 1):
            lines[(name, i)], = ax.plot([], [], "-" if i == 0 else "--", color=color, lw=2.4, alpha=0.9)
            dots[(name, i)] = plt.Circle((np.nan, np.nan), R, fill=(name == "real"), color=color, alpha=0.35 if name == "real" else 1, lw=2)
            ax.add_patch(dots[(name, i)])
    ax.legend(handles=legend_r7(), loc="upper right", ncol=3, frameon=True, framealpha=0.95, fontsize=15)
    clock = ax.text(0.02, 0.95, "", transform=ax.transAxes, va="top", fontsize=16, color=INK)
    t_end = min(t[-1] for t in t_exp)

    def update(t, with_clock):
        for i, e in enumerate(exp):
            k = e[:, 0] <= t + 1e-9
            lines[("real", i)].set_data(e[k, 1], e[k, 2])
            if k.any():
                dots[("real", i)].center = (e[k][-1, 1], e[k][-1, 2])
        for layer in "ABF":
            run = runs[layer]
            k = run[:, 0] <= t + 1e-9
            for i in (0, 1):
                x, y = run[k, 1 + 4 * i], run[k, 2 + 4 * i]
                lines[(layer, i)].set_data(x, y)
                ok = ~np.isnan(x)
                dots[(layer, i)].center = (x[ok][-1], y[ok][-1]) if ok.any() else (np.nan, np.nan)
        clock.set_text(f"t = {t:.2f} s".replace(".", ",") if with_clock else "")

    # Fotograma del mínimo de distancia real, sin reloj (va en el PDF)
    a, b = exp
    common = np.intersect1d(np.round(a[:, 0], 6), np.round(b[:, 0], 6))
    d = [math.hypot(*(a[np.argmin(np.abs(a[:, 0] - t)), 1:] - b[np.argmin(np.abs(b[:, 0] - t)), 1:])) for t in common]
    t_min = float(common[int(np.argmin(d))])
    update(t_min, False)
    save(fig, "R7-animacion-evento.png")
    return t_min, dt_exp, t_end


def r7_video(event, t_end, dt_exp):
    """Repite el armado de R7 para el MP4, con reloj, a 15 cuadros por segundo reales."""
    runs = {layer: read_run(run_dir(layer) / f"evento_{event:02d}.txt")[1] for layer in "ABF"}
    header = read_run(run_dir("A") / f"evento_{event:02d}.txt")[0]
    exp = experimental(DATA, header)
    fig, ax = plt.subplots(figsize=(12, 5.4), constrained_layout=True)
    ax.set_xlim(min(e[:, 1].min() for e in exp) - 0.4, max(e[:, 1].max() for e in exp) + 0.4)
    ys = np.concatenate([e[:, 2] for e in exp] + [runs[l][:, 2] for l in "ABF"] + [runs[l][:, 6] for l in "ABF"])
    ax.set_ylim(np.nanmin(ys) - 0.7, np.nanmax(ys) + 0.9)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    style(ax)
    ax.legend(handles=legend_r7(), loc="upper right", ncol=3, frameon=True, framealpha=0.95, fontsize=15)
    clock = ax.text(0.02, 0.95, "", transform=ax.transAxes, va="top", fontsize=16, color=INK)
    lines, dots = {}, {}
    for name, color in [("real", COLORS["exp"])] + [(l, COLORS[l]) for l in "ABF"]:
        for i in (0, 1):
            lines[(name, i)], = ax.plot([], [], "-" if i == 0 else "--", color=color, lw=2.4, alpha=0.9)
            dots[(name, i)] = plt.Circle((np.nan, np.nan), R, fill=(name == "real"), color=color, alpha=0.35 if name == "real" else 1, lw=2)
            ax.add_patch(dots[(name, i)])

    def update(t):
        for i, e in enumerate(exp):
            k = e[:, 0] <= t + 1e-9
            lines[("real", i)].set_data(e[k, 1], e[k, 2])
            if k.any():
                dots[("real", i)].center = (e[k][-1, 1], e[k][-1, 2])
        for layer in "ABF":
            run = runs[layer]
            k = run[:, 0] <= t + 1e-9
            for i in (0, 1):
                x, y = run[k, 1 + 4 * i], run[k, 2 + 4 * i]
                lines[(layer, i)].set_data(x, y)
                ok = ~np.isnan(x)
                dots[(layer, i)].center = (x[ok][-1], y[ok][-1]) if ok.any() else (np.nan, np.nan)
        clock.set_text(f"t = {t:.2f} s".replace(".", ","))
        return []

    times = np.arange(0, t_end + 1e-9, dt_exp)
    anim = animation.FuncAnimation(fig, update, frames=times, blit=False)
    out = P / f"evento_{event:02d}_animacion.mp4"
    anim.save(out, writer=animation.FFMpegWriter(fps=round(1 / dt_exp), bitrate=2400), dpi=110)
    plt.close(fig)
    return out


# ---------------------------------------------------------------- R2
def r2():
    # Paneles en orden A, B, F; la letra de cada capa va en la diapositiva, no dentro del panel.
    # Ejes con subíndice real (mathtext), una sola barra de color con la misma escala para las tres capas
    # y la leyenda de la estrella arriba, fuera de los mapas, para no tapar ninguna celda.
    names = {"A": (r"$t_a$ [s]", r"$\ell$ [m]"), "B": (r"$t_a$ [s]", r"$k$"), "F": (r"$A_p$", r"$B_p$ [m]")}
    grids = {}
    for layer in "ABF":
        rows = load_grid(P / f"grid_{layer}.txt")
        p1, p2 = np.unique(rows[:, 0]), np.unique(rows[:, 1])
        grids[layer] = (p1, p2, np.array([[rows[(rows[:, 0] == a) & (rows[:, 1] == b), 3].mean() for a in p1] for b in p2]))
    vmin = min(g[2].min() for g in grids.values())
    vmax = max(g[2].max() for g in grids.values())
    fig, axes = plt.subplots(1, 3, figsize=(12, 5.0), constrained_layout=True)
    for ax, layer in zip(axes, "ABF"):
        p1, p2, z = grids[layer]
        im = ax.imshow(z, origin="lower", aspect="auto", cmap="cividis_r", vmin=vmin, vmax=vmax,
                       extent=(-0.5, len(p1) - 0.5, -0.5, len(p2) - 0.5))
        k = np.unravel_index(np.argmin(z), z.shape)
        ax.plot(k[1], k[0], "*", color="white", ms=30, mec=INK, mew=1.5, label="mínimo")
        sx = 3 if len(p1) > 9 else 2
        ax.set_xticks(range(len(p1))[::sx], [num(f"{v:g}") for v in p1][::sx], fontsize=20)
        ax.set_yticks(range(len(p2))[::2], [num(f"{v:g}") for v in p2][::2], fontsize=20)
        ax.set_xlabel(names[layer][0], fontsize=24)
        ax.set_ylabel(names[layer][1], fontsize=24, labelpad=2)
    cb = fig.colorbar(im, ax=axes, shrink=0.95, pad=0.02)
    cb.set_label("ECM 1 [m²]", fontsize=24)
    cb.ax.tick_params(labelsize=20)
    cb.ax.yaxis.set_major_formatter(COMMA)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="outside upper center", frameon=False, fontsize=21)
    save(fig, "R2-mapas-ecm.pdf")


# ---------------------------------------------------------------- Tamaños de letra
# pt efectivo en la diapositiva = pt del script × ancho mostrado (mm) / (ancho de la figura (in) × 25,4).
# Columna de resultados (~85 mm) con figuras de 6,4 in: 19 pt → ~9,9 pt. Mapas de a 3 por fila (~38 mm) con
# figuras de 3,5 in: 21 pt → ~9 pt.
COL_FONT = {"font.size": 17, "axes.labelsize": 19, "legend.fontsize": 15, "xtick.labelsize": 16, "ytick.labelsize": 16}
SMALL_FONT = {"font.size": 19, "axes.labelsize": 21, "legend.fontsize": 17, "xtick.labelsize": 18, "ytick.labelsize": 18}
COL_SIZE = (6.4, 3.7)
SMALL_SIZE = (3.5, 3.4)
# Dos figuras por diapositiva (~55 mm cada una) con figuras de 4,6 in: 21 pt → ~9,9 pt; 19 pt → ~8,9 pt.
MAP_FONT = {"font.size": 20, "axes.labelsize": 22, "legend.fontsize": 19, "xtick.labelsize": 19, "ytick.labelsize": 19}
MAP_SIZE = (4.6, 4.1)
# C2 a ~58 mm con figuras de 4,8 in: 20 pt → ~9,5 pt.
HALF_FONT = {"font.size": 19, "axes.labelsize": 21, "legend.fontsize": 18, "xtick.labelsize": 18, "ytick.labelsize": 18}
HALF_SIZE = (4.8, 4.0)
MAIN_LAYERS = "AB"      # F salió del análisis principal (decisión del grupo, 11/11): queda solo en M1, R3 y el anexo
PAIRS_ECM2 = {"A": (2.0, 0.5), "B": (3.5, 1.0), "F": (0.8, 3.0)}     # mejores de ECM 1 excl. y de ECM 2, verificados abajo
METRIC_COL = {"ecm1": 3, "ecm2": 5}
METRIC_LABEL = {"ecm1": "ECM 1", "ecm2": "ECM 2"}
AXES = {"A": (r"$t_a$ [s]", r"$\ell$ [m]"), "B": (r"$t_a$ [s]", r"$k$"), "F": (r"$A_p$", r"$B_p$ [m]")}
NUMBERS = []      # líneas para numeros_figuras_nuevas.md


def note(line=""):
    NUMBERS.append(line)


def grid_matrix(layer, metric):
    """Pares, matriz (par × evento) de la métrica y valores únicos de p1 y p2 de la grilla oficial."""
    rows = load_grid(P / f"grid_{layer}.txt")
    pairs, matrix = error_matrix(rows, METRIC_COL[metric])
    return pairs, matrix, np.unique(rows[:, 0]), np.unique(rows[:, 1])


def population_optimum(layer, metric):
    pairs, matrix, _, _ = grid_matrix(layer, metric)
    k = int(np.argmin(matrix.mean(axis=1)))
    return pairs[k], float(matrix[k].mean())


def cell(p1, p2, value1, value2):
    """Índices de celda (columna, fila) de un par en la grilla."""
    return int(np.argmin(np.abs(p1 - value1))), int(np.argmin(np.abs(p2 - value2)))


def grid_ticks(ax, p1, p2):
    if len(p1) == 10:       # t_a de 0,5 a 5 s: marcas cada 1 s (1, 2, 3, 4, 5)
        ax.set_xticks(range(1, len(p1), 2), [num(f"{v:g}") for v in p1][1::2])
    else:                   # A_p (9 valores): 0,1 0,5 0,9
        ax.set_xticks(range(len(p1))[::4], [num(f"{v:g}") for v in p1][::4])
    ax.set_yticks(range(len(p2))[::2], [num(f"{v:g}") for v in p2][::2])
    ax.set_xlim(-0.5, len(p1) - 0.5)
    ax.set_ylim(-0.5, len(p2) - 0.5)


# ---------------------------------------------------------------- R2: mapas de ⟨E⟩ por capa y métrica
def top_legend(fig, handles, visible, **kwargs):
    """Leyenda arriba, fuera del área de datos. Va en las tres figuras de una fila para que las tres queden del
    mismo tamaño, pero solo se ve en la de A (en B y F es transparente)."""
    leg = fig.legend(handles=handles, loc="outside upper center", frameon=False, **kwargs)
    if not visible:
        for artist in list(leg.get_texts()) + list(leg.legend_handles):
            artist.set_alpha(0)
    return leg


def r2_maps():
    from matplotlib.colors import LogNorm
    from matplotlib.lines import Line2D
    other = {"ecm1": "ecm2", "ecm2": "ecm1"}
    note("## Óptimos poblacionales (grilla oficial)")
    for metric in ("ecm1", "ecm2"):
        data = {layer: grid_matrix(layer, metric) for layer in "ABF"}
        means = {layer: d[1].mean(axis=1) for layer, d in data.items()}
        # Escala de color compartida solo entre A y B (las dos que van juntas en la diapositiva). Los mapas de F del
        # anexo no se regeneran acá: conservan su escala compartida A/B/F de la tanda anterior.
        ab_range = (min(means[l].min() for l in MAIN_LAYERS), max(means[l].max() for l in MAIN_LAYERS))
        for layer in "ABF":
            # A y B comparten escala (van juntas); F (anexo) usa la suya
            vmin, vmax = ab_range if layer in MAIN_LAYERS else (means[layer].min(), means[layer].max())
            pairs, _, p1, p2 = data[layer]
            z = np.full((len(p2), len(p1)), np.nan)
            for (a, b), v in zip(pairs, means[layer]):
                i, j = cell(p1, p2, a, b)
                z[j, i] = v
            best, best_value = population_optimum(layer, metric)
            alt, alt_value = population_optimum(layer, other[metric])
            note(f"- {layer}, {METRIC_LABEL[metric]}: óptimo ({num(f'{best[0]:g}')}; {num(f'{best[1]:g}')}), "
                 f"⟨E⟩ = {num(f'{best_value:.4f}')} m²")
            with plt.rc_context(MAP_FONT):
                fig, ax = plt.subplots(figsize=MAP_SIZE, constrained_layout=True)
                im = ax.imshow(z, origin="lower", aspect="auto", cmap="cividis_r", norm=LogNorm(vmin=vmin, vmax=vmax),
                               extent=(-0.5, len(p1) - 0.5, -0.5, len(p2) - 0.5))
                ax.plot(*cell(p1, p2, *best), "*", color="white", ms=28, mec=INK, mew=1.5, zorder=4, clip_on=False)
                # Círculo más grande que la estrella: si los dos óptimos caen en la misma celda, el círculo la rodea
                ax.plot(*cell(p1, p2, *alt), "o", mfc="none", mec="white", ms=32, mew=3.0, zorder=3, clip_on=False)
                grid_ticks(ax, p1, p2)
                ax.set_xlabel(AXES[layer][0])
                ax.set_ylabel(AXES[layer][1], labelpad=8 if layer == "F" else 1)
                cb = fig.colorbar(im, ax=ax, pad=0.03, fraction=0.08)
                ticks = [t for t in (0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 1, 1.5, 2, 3) if vmin <= t <= vmax]
                cb.set_ticks(ticks)
                cb.ax.yaxis.set_major_formatter(COMMA)
                cb.ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
                cb.set_label(f"⟨E⟩, {METRIC_LABEL[metric]} [m²], escala log")
                # Leyenda dentro del mapa, en la esquina de arriba a la derecha (lejos de los óptimos)
                ax.legend(handles=[Line2D([], [], ls="none", marker="*", ms=20, mfc="white", mec=INK, label=f"óptimo {METRIC_LABEL[metric]}"),
                                   Line2D([], [], ls="none", marker="o", ms=17, mfc="none", mec=INK, mew=2.4,
                                          label=f"óptimo {METRIC_LABEL[other[metric]]}")],
                          loc="lower left" if layer == "F" else "upper right", frameon=True, framealpha=0.9, fontsize=16, handletextpad=0.2, borderpad=0.3)
                save(fig, f"R2-{layer}-{metric}.pdf")


# ---------------------------------------------------------------- C: calibración individual
def c1_optima():
    from matplotlib.lines import Line2D
    note()
    note("## Calibración individual (punto c): óptimo de cada evento en la grilla")
    for layer in "ABF":
        _, _, p1, p2 = grid_matrix(layer, "ecm1")
        draw = layer in MAIN_LAYERS      # C1-optimos-F.pdf (anexo) queda como estaba; de F solo se anotan los números
        with plt.rc_context(MAP_FONT):
            fig, ax = plt.subplots(figsize=MAP_SIZE, constrained_layout=True)
            ax.set_xticks(np.arange(-0.5, len(p1)), minor=True)
            ax.set_yticks(np.arange(-0.5, len(p2)), minor=True)
            ax.grid(which="minor", color=GRID, lw=0.8)
            ax.tick_params(which="minor", length=0)
            for metric, offset, filled in (("ecm1", -0.2, True), ("ecm2", 0.2, False)):
                pairs, matrix, _, _ = grid_matrix(layer, metric)
                best_idx = np.argmin(matrix, axis=0)
                counts = defaultdict(int)
                for k in best_idx:
                    counts[cell(p1, p2, *pairs[k])] += 1
                for (i, j), n in counts.items():
                    ax.scatter(i + offset, j, s=70 + 110 * n, color=COLORS[layer] if filled else "white",
                               edgecolors=COLORS[layer], linewidths=2.2, zorder=3, clip_on=False)
                best, _ = population_optimum(layer, metric)
                i, j = cell(p1, p2, *best)
                ax.plot(i + offset, j, "*", ms=28, color=INK if filled else "white", mec=INK, mew=1.5, zorder=4, clip_on=False)
                pop_k = pairs.index(best)
                same = int((best_idx == pop_k).sum())
                note(f"- {layer}, {METRIC_LABEL[metric]}: {same} de 19 eventos tienen el óptimo individual en el par poblacional "
                     f"({num(f'{best[0]:g}')}; {num(f'{best[1]:g}')}); celdas distintas usadas: {len(counts)}")
            grid_ticks(ax, p1, p2)
            ax.set_xlabel(AXES[layer][0])
            ax.set_ylabel(AXES[layer][1], labelpad=1)
            # Leyenda arriba, fuera de la grilla, visible en las dos figuras de la diapositiva
            top_legend(fig, [Line2D([], [], ls="none", marker="o", ms=13, color=MUTED, label="evento, ECM 1"),
                             Line2D([], [], ls="none", marker="o", ms=13, mfc="white", mec=MUTED, mew=2, label="evento, ECM 2"),
                             Line2D([], [], ls="none", marker="*", ms=19, color=INK, label="poblac., ECM 1"),
                             Line2D([], [], ls="none", marker="*", ms=19, mfc="white", mec=INK, label="poblac., ECM 2")],
                       True, ncol=2, fontsize=17, handletextpad=0.1, columnspacing=0.6)
            if draw:
                save(fig, f"C1-optimos-{layer}.pdf")
            else:
                plt.close(fig)
    note("  (Tamaño del círculo proporcional a la cantidad de eventos con el óptimo en esa celda; ECM 1 corrido a la izquierda "
         "y ECM 2 a la derecha dentro de la celda, solo para que no se tapen.)")


def c2_errors():
    note()
    note("## E_m con parámetros poblacionales contra individuales (19 eventos)")
    for metric in ("ecm1", "ecm2"):
        with plt.rc_context(HALF_FONT):
            fig, ax = plt.subplots(figsize=HALF_SIZE, constrained_layout=True)
            ticks, labels = [], []
            for g, layer in enumerate("ABF"):
                pairs, matrix, _, _ = grid_matrix(layer, metric)
                best, _ = population_optimum(layer, metric)
                pop = matrix[pairs.index(best)]
                ind = matrix.min(axis=0)
                gain = 100 * (1 - ind.mean() / pop.mean())
                note(f"- {layer}, {METRIC_LABEL[metric]}: E poblacional media {num(f'{pop.mean():.4f}')} (mediana {num(f'{np.median(pop):.4f}')}); "
                     f"individual media {num(f'{ind.mean():.4f}')} (mediana {num(f'{np.median(ind):.4f}')}); ganancia {num(f'{gain:.1f}')} % "
                     f"(base: media poblacional)")
                if layer not in MAIN_LAYERS:
                    continue
                x0, x1 = 3 * g, 3 * g + 1
                for a, b in zip(pop, ind):
                    ax.plot([x0, x1], [a, b], color=COLORS[layer], alpha=0.35, lw=1.4, zorder=2)
                ax.scatter(np.full(19, x0), pop, color=COLORS[layer], s=50, zorder=3)
                ax.scatter(np.full(19, x1), ind, color="white", edgecolors=COLORS[layer], linewidths=1.8, s=50, zorder=3)
                for x, v in ((x0, pop), (x1, ind)):
                    ax.plot([x - 0.3, x + 0.3], [v.mean()] * 2, color=INK, lw=3, zorder=4)
                ticks += [x0, x1]
                labels += [f"{layer}\npobl.", f"{layer}\nindiv."]
            ax.set_yscale("log")
            ax.set_xticks(ticks, labels)
            ax.set_xlim(-0.6, 4.6)
            ax.set_ylabel(f"{METRIC_LABEL[metric]} por evento [m²]")
            ax.grid(axis="y", which="major", color=GRID, lw=0.8)
            ax.set_axisbelow(True)
            ax.yaxis.set_major_formatter(COMMA)
            ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            from matplotlib.lines import Line2D
            # Arriba al centro, en el hueco entre los grupos A y B (abajo a la derecha tapaba los puntos más bajos de B)
            ax.legend(handles=[Line2D([], [], color=INK, lw=3, label="media")], loc="upper center", frameon=True, framealpha=0.95)
            save(fig, f"C2-{metric}.pdf")


def c1_counts():
    """Calibración individual: en cada celda de la grilla, cuántos eventos tienen ahí su óptimo (un número por celda).

    Reemplaza a los círculos de tamaño variable de c1_optima, que no se entendían. Una figura por capa y métrica:
    C1-conteo-{A,B}-{ecm1,ecm2}.pdf. Estrella: óptimo poblacional de esa métrica.
    """
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from matplotlib.lines import Line2D
    for metric in ("ecm1", "ecm2"):
        for layer in MAIN_LAYERS:
            pairs, matrix, p1, p2 = grid_matrix(layer, metric)
            counts = np.zeros((len(p2), len(p1)), dtype=int)
            for k in np.argmin(matrix, axis=0):
                i, j = cell(p1, p2, *pairs[k])
                counts[j, i] += 1
            best, _ = population_optimum(layer, metric)
            top = max(4, int(counts.max()))
            cmap = ListedColormap(["white"] + [matplotlib.colormaps["Blues" if layer == "A" else "Oranges"](0.25 + 0.6 * q / top)
                                               for q in range(1, top + 1)])
            with plt.rc_context(MAP_FONT):
                fig, ax = plt.subplots(figsize=(4.6, 4.9), constrained_layout=True)
                ax.imshow(counts, origin="lower", aspect="auto", cmap=cmap, norm=BoundaryNorm(np.arange(-0.5, top + 1), top + 1),
                          extent=(-0.5, len(p1) - 0.5, -0.5, len(p2) - 0.5))
                ax.set_xticks(np.arange(-0.5, len(p1)), minor=True)
                ax.set_yticks(np.arange(-0.5, len(p2)), minor=True)
                ax.grid(which="minor", color=GRID, lw=0.8)
                ax.tick_params(which="minor", length=0)
                for j in range(len(p2)):
                    for i in range(len(p1)):
                        if counts[j, i]:
                            ax.text(i, j, str(counts[j, i]), ha="center", va="center", fontsize=25, fontweight="bold", color=INK, zorder=4)
                bi, bj = cell(p1, p2, *best)
                # Recuadro (no estrella): la estrella tapaba el número de la celda
                ax.add_patch(plt.Rectangle((bi - 0.5, bj - 0.5), 1, 1, fill=False, ec=INK, lw=3.2, zorder=5, clip_on=False))
                grid_ticks(ax, p1, p2)
                ax.set_xlabel(AXES[layer][0])
                ax.set_ylabel(AXES[layer][1], labelpad=1)
                ax.legend(handles=[Line2D([], [], ls="none", marker="s", ms=15, color=COLORS[layer], label="n.º de eventos"),
                                   Line2D([], [], ls="none", marker="s", ms=17, mfc="none", mec=INK, mew=2.6,
                                          label="óptimo poblacional")],
                          loc="upper left", frameon=True, framealpha=0.9, fontsize=16, handletextpad=0.3, borderpad=0.3)
                save(fig, f"C1-conteo-{layer}-{metric}.pdf")


def c2_boxes():
    """Calibración individual: distribución de E_m con el par poblacional y con el par de cada evento (cajas).

    Reemplaza al gráfico de líneas emparejadas de c2_errors. Una figura por métrica (C2-ecm1.pdf, C2-ecm2.pdf).
    Encima de cada capa, la ganancia de la media (base: media poblacional).
    """
    for metric in ("ecm1", "ecm2"):
        with plt.rc_context(HALF_FONT):
            fig, ax = plt.subplots(figsize=HALF_SIZE, constrained_layout=True)
            ticks, labels, tops = [], [], []
            for g, layer in enumerate(MAIN_LAYERS):
                pairs, matrix, _, _ = grid_matrix(layer, metric)
                best, _ = population_optimum(layer, metric)
                pop = matrix[pairs.index(best)]
                ind = matrix.min(axis=0)
                gain = 100 * (1 - ind.mean() / pop.mean())
                x0, x1 = 3.4 * g, 3.4 * g + 1.4
                # Una línea por evento: une su E_m con el par poblacional y con su mejor par
                for a, b in zip(pop, ind):
                    ax.plot([x0, x1], [a, b], color=COLORS[layer], alpha=0.45, lw=1.3, zorder=2.5)
                for x, v, filled in ((x0, pop, True), (x1, ind, False)):
                    ax.boxplot(v, positions=[x], widths=0.6, showfliers=False, patch_artist=True, zorder=2,
                               boxprops=dict(facecolor=COLORS[layer] if filled else "white", alpha=0.45 if filled else 1,
                                             edgecolor=COLORS[layer], lw=1.8),
                               medianprops=dict(color=INK, lw=2), whiskerprops=dict(color=COLORS[layer], lw=1.6),
                               capprops=dict(color=COLORS[layer], lw=1.6))
                    ax.scatter(np.full(len(v), x), v, s=30, zorder=3,
                               color=COLORS[layer] if filled else "white", edgecolors=COLORS[layer], linewidths=1.3)
                tops.append(max(pop.max(), ind.max()))
                ax.text((x0 + x1) / 2, tops[-1] * (1.35 if metric == "ecm2" else 1.06), f"media {num(f'{-gain:+.1f}')} %",
                        ha="center", va="bottom", fontsize=15, color=INK)
                ticks += [x0, x1]
                labels += [f"{layer}\npobl.", f"{layer}\nindiv."]
            if metric == "ecm2":
                ax.set_yscale("log")
                ax.set_ylim(top=max(tops) * 3)
                ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            else:
                ax.set_ylim(0, max(tops) * 1.22)
            ax.set_xticks(ticks, labels)
            ax.set_xlim(-0.9, 5.7)
            ax.set_ylabel(f"$E_m$, {METRIC_LABEL[metric]} [m²]")
            ax.grid(axis="y", which="major", color=GRID, lw=0.8)
            ax.set_axisbelow(True)
            ax.yaxis.set_major_formatter(COMMA)
            save(fig, f"C2-{metric}.pdf")


# ---------------------------------------------------------------- T1: distancia entre peatones vs t
def t1_distance(event):
    header, base_run = read_run(Path("outputs/baseline") / f"evento_{event:02d}.txt")
    exp = experimental(DATA, header)
    # Ancha y baja: va abajo a la izquierda en la diapositiva de animaciones (~60 % del ancho, ~3,6 cm de alto)
    with plt.rc_context(HALF_FONT):
        fig, ax = plt.subplots(figsize=(6.4, 3.4), constrained_layout=True)
        t, a, b = common_times(*exp)
        ax.plot(t, np.hypot(*(a - b).T), color=COLORS["exp"], lw=2.6, label="real", zorder=4)
        d_real = np.hypot(*(a - b).T)
        runs = [("sin capa", COLORS["base"], base_run)] + [(l, COLORS[l], read_run(run_dir(l) / f"evento_{event:02d}.txt")[1]) for l in MAIN_LAYERS]
        note()
        note(f"## Evento representativo {event} (T1)")
        note(f"- D^exp = {num(f'{d_real.min():.3f}')} m en t = {num(f'{t[np.argmin(d_real)]:.2f}')} s")
        for name, color, run in runs:
            d = np.hypot(run[:, 1] - run[:, 5], run[:, 2] - run[:, 6])
            ax.plot(run[:, 0], d, color=color, lw=2.8 if name == "sin capa" else 2.2, ls="--" if name == "sin capa" else "-",
                    label=name, zorder=3)
            k = int(np.nanargmin(d))
            note(f"- {name}: D^sim = {num(f'{d[k]:.3f}')} m en t = {num(f'{run[k, 0]:.2f}')} s")
        for layer in MAIN_LAYERS:
            e = pair_rows(layer)
            row = e[e[:, 2] == event][0]
            note(f"- {layer}({num(f'{PAIRS[layer][0]:g}')}; {num(f'{PAIRS[layer][1]:g}')}): ECM 1 del evento {num(f'{row[3]:.4f}')} m², "
                 f"ECM 2 {num(f'{row[5]:.4f}')} m², d_min (grilla) {num(f'{row[11]:.3f}')} m")
        ax.axhline(2 * R, color=MUTED, ls=":", lw=1.6)
        ax.axhline(RHO, color=MUTED, ls="-.", lw=1.4)
        ax.text(0.05, 2 * R, r"$2R$", va="bottom", ha="left", color=INK, fontsize=19)
        ax.text(0.05, RHO, r"$\rho$", va="bottom", ha="left", color=INK, fontsize=21)
        ax.set_xlabel("t [s]")
        ax.set_ylabel("distancia [m]")
        ax.set_ylim(0, 3)       # zoom en el encuentro: arriba de 3 m solo se acercan en línea recta
        style(ax)
        ax.legend(loc="upper left", ncol=2, frameon=True, framealpha=0.95, fontsize=17, columnspacing=0.8)     # antes de t ≈ 2 s no hay datos debajo de 3 m
        save(fig, "T1-distancia-vs-t.pdf")


# ---------------------------------------------------------------- M1: mejores pares (reemplaza la tabla)
def baseline_mean():
    e1, e2 = [], []
    for line in (Path("outputs/baseline") / "ecm.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("E "):
            p = line.split()
            e1.append(float(p[2]))
            e2.append(float(p[4]))
    return float(np.mean(e1)), float(np.mean(e2))


def m1_best(layers="AB", fname="M1-mejores-pares.pdf"):
    """Mejores pares: M1-mejores-pares.pdf (sin capa, A y B; Resultados) y M1-mejores-pares-con-F.pdf (anexo de F)."""
    parts = partitions()
    b1, b2 = baseline_mean()
    rows = [("sin capa", b1, None, None, b2)]
    note()
    note(f"## Mejores pares ({fname})")
    note(f"- sin capa: ECM 1 {num(f'{b1:.4f}')}, ECM 2 {num(f'{b2:.4f}')}")
    for layer in layers:
        best1, v1 = population_optimum(layer, "ecm1")
        best2, v2 = population_optimum(layer, "ecm2")
        _, matrix = error_matrix(load_grid(P / f"grid_{layer}.txt"), 3)
        _, val, _ = evaluate(matrix, parts)
        rows.append((layer, v1, val.mean(), val.std(ddof=1), v2))
        note(f"- {layer}: ECM 1 {num(f'{v1:.4f}')} en ({num(f'{best1[0]:g}')}; {num(f'{best1[1]:g}')}); validación "
             f"{num(f'{val.mean():.4f}')} ± {num(f'{val.std(ddof=1):.4f}')} ({len(parts)} particiones); "
             f"ECM 2 {num(f'{v2:.4f}')} en ({num(f'{best2[0]:g}')}; {num(f'{best2[1]:g}')})")
        assert best1 == PAIRS[layer] and best2 == PAIRS_ECM2[layer], f"{layer}: óptimos distintos de los declarados"
    # Puntos (no barras: en escala log la altura de una barra no significa nada) con la barra de error de la validación.
    # Color por capa; marcador por métrica: lleno = ECM 1 de calibración, hueco = ECM 1 de validación (± DE entre
    # particiones), rombo = ECM 2.
    with plt.rc_context(COL_FONT):
        fig, ax = plt.subplots(figsize=(5.6, 4.2), constrained_layout=True)     # más alta que COL_SIZE: llena la columna de la lámina
        w = 0.22
        for g, (name, cal, vmean, vstd, e2) in enumerate(rows):
            color = COLORS["base"] if name == "sin capa" else COLORS[name]
            ax.plot(g - w, cal, "o", color=color, ms=14, mec=INK, mew=0.8, zorder=3)
            if vmean is not None:
                ax.errorbar(g, vmean, yerr=vstd, fmt="o", mfc="white", mec=color, mew=2.2, ms=14, ecolor=color, elinewidth=2,
                            capsize=5, zorder=3)
            ax.plot(g + w, e2, "D", color=color, ms=13, mec=INK, mew=0.8, zorder=3)
        from matplotlib.lines import Line2D
        ax.set_yscale("log")
        ax.set_ylim(0.02, 8)
        ax.set_xlim(-0.6, len(rows) - 0.4)
        ax.set_xticks(range(len(rows)), [r[0] for r in rows])
        ax.set_ylabel("error [m²], escala log")
        ax.grid(axis="y", which="major", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        ax.yaxis.set_major_formatter(COMMA)
        ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        fig.legend(handles=[Line2D([], [], ls="none", marker="o", ms=11, color=MUTED, mec=INK, label="ECM 1"),
                           Line2D([], [], ls="-", marker="o", ms=11, mfc="white", mec=MUTED, color=MUTED, mew=2, label="val. ECM 1 ± DE"),
                           Line2D([], [], ls="none", marker="D", ms=10, color=MUTED, mec=INK, label="ECM 2")],
                  loc="outside upper center", ncol=3, frameon=False, fontsize=16, handletextpad=0.3, columnspacing=1.0)     # fuera del eje, arriba: no toca ningún punto
        save(fig, fname)


# ---------------------------------------------------------------- R3: validación cruzada
def r3():
    parts = partitions()
    with plt.rc_context(COL_FONT):
        fig, ax = plt.subplots(figsize=COL_SIZE, constrained_layout=True)
        vals = {}
        for layer in "ABF":
            _, matrix = error_matrix(load_grid(P / f"grid_{layer}.txt"), 3)
            _, val, _ = evaluate(matrix, parts)
            vals[layer] = val
        bins = np.linspace(min(v.min() for v in vals.values()), max(v.max() for v in vals.values()), 70)
        for layer, val in vals.items():
            ax.hist(val, bins=bins, color=COLORS[layer], alpha=0.45, label=f"{layer} (media {num(f'{val.mean():.2f}')})", zorder=2)
            ax.hist(val, bins=bins, histtype="step", color=COLORS[layer], lw=1.4, zorder=3)
            ax.axvline(val.mean(), color=COLORS[layer], ls="--", lw=2, zorder=4)
        ax.set_xlabel("ECM 1 de validación [m²]")
        ax.set_ylabel("particiones")
        style(ax, "y")
        ax.legend(loc="upper center", frameon=True, framealpha=0.95)
        save(fig, "R3-validacion.pdf")


# ---------------------------------------------------------------- R4: diferencias por evento
def r4():
    ev = {l: pair_rows(l)[:, 3] for l in "ABF"}
    # Misma orientación en las tres: ECM 1(capa que pierde) − ECM 1(capa que gana); barra hacia arriba = gana la segunda
    for name, (loser, winner) in (("R4-pareadas.pdf", ("A", "B")), ("R4b-pareadas.pdf", ("F", "A")), ("R4c-pareadas.pdf", ("F", "B"))):
        d = ev[loser] - ev[winner]
        with plt.rc_context(COL_FONT):
            fig, ax = plt.subplots(figsize=COL_SIZE, constrained_layout=True)
            colors = [COLORS[winner] if v > 0 else COLORS[loser] for v in d]
            ax.bar(np.arange(1, 20), d, color=colors, edgecolor="white", linewidth=0.8, zorder=2)
            ax.axhline(0, color=MUTED, lw=1.2)
            ax.axhline(d.mean(), color=INK, lw=1.8, ls="--", zorder=3)
            ax.set_xticks(range(1, 20, 2))
            ax.set_xlim(0.3, 19.7)
            ax.set_xlabel("evento")
            ax.set_ylabel(f"ECM 1({loser}) − ECM 1({winner}) [m²]")
            style(ax, "y")
            span = d.max() - min(d.min(), 0)
            ax.set_ylim(min(d.min(), 0) - 0.05 * span, d.max() + 0.42 * span)
            from matplotlib.lines import Line2D
            from matplotlib.patches import Patch
            # Etiquetas cortas: con "(n eventos)" la leyenda de tres columnas era más ancha que el eje
            ax.legend(handles=[Patch(color=COLORS[winner], label=f"gana {winner} ({int((d > 0).sum())})"),
                               Patch(color=COLORS[loser], label=f"gana {loser} ({int((d < 0).sum())})"),
                               Line2D([], [], color=INK, ls="--", lw=1.8, label=num(f"media {d.mean():+.3f} m²"))],
                      loc="upper center", ncol=3, frameon=True, framealpha=0.95, fontsize=13, columnspacing=0.8, handlelength=1.4)
            save(fig, name)


# ---------------------------------------------------------------- R5: distancia mínima y corrimiento
def real_minimum():
    d, t = {}, {}
    for line in (Path("outputs/baseline") / "ecm.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("E "):
            p = line.split()
            d[int(p[1])], t[int(p[1])] = float(p[8]), float(p[9])
    return np.array([d[n] for n in range(1, 20)]), np.array([t[n] for n in range(1, 20)])


def r5():
    real_d, real_t = real_minimum()
    note()
    note("## Distancia mínima y corrimiento (mejor par de ECM 1; control contra numeros_presentacion.md)")
    with plt.rc_context(COL_FONT):
        fig, ax = plt.subplots(figsize=COL_SIZE, constrained_layout=True)
        lo, hi = 0.4, 1.0
        ax.plot([lo, hi], [lo, hi], color=INK, lw=1.4, label="identidad", zorder=2)
        ax.axhline(2 * R, color=MUTED, ls=":", lw=1.6, zorder=1)
        ax.axhline(RHO, color=MUTED, ls="-.", lw=1.4, zorder=1)
        ax.text(hi, 2 * R, r" $2R$", va="center", ha="left", color=INK, fontsize=19)
        ax.text(hi, RHO, r" $\rho$", va="center", ha="left", color=INK, fontsize=21)
        for layer in "ABF":
            r = pair_rows(layer)
            if layer in MAIN_LAYERS:
                ax.plot(real_d, r[:, 11], MARKERS[layer], color=COLORS[layer], ms=10, mec="white", mew=0.8, ls="none", label=layer, zorder=3)
            dd, lag = r[:, 11] - real_d, r[:, 12] - real_t
            note(f"- {layer}: mediana D^sim − D^exp {num(f'{np.median(dd):.2f}')} m; eventos con D^sim < D^exp {int((dd < 0).sum())}/19; "
                 f"mediana de c {num(f'{np.median(lag):.2f}')} s; eventos tarde (c > 0) {int((lag > 0).sum())}/19")
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_xlabel(r"$D^{\mathrm{exp}}$ [m]")
        ax.set_ylabel(r"$D^{\mathrm{sim}}$ [m]")
        style(ax)
        # Hay puntos en todas las esquinas: la leyenda va arriba, fuera del eje. Lo que significa estar debajo de la
        # identidad (pasa más cerca que el real) lo dice el texto de la diapositiva.
        fig.legend(*ax.get_legend_handles_labels(), loc="outside upper center", ncol=4, frameon=False, fontsize=15)
        save(fig, "R5-distancia-minima.pdf")

    with plt.rc_context(COL_FONT):
        fig, ax = plt.subplots(figsize=COL_SIZE, constrained_layout=True)
        rng = np.random.default_rng(1)
        for g, layer in enumerate(MAIN_LAYERS):
            lag = pair_rows(layer)[:, 12] - real_t
            x = g + rng.uniform(-0.18, 0.18, size=lag.size)      # dispersión horizontal solo para que no se tapen
            ax.plot(x, lag, MARKERS[layer], color=COLORS[layer], ms=10, mec="white", mew=0.8, ls="none", zorder=3)
            ax.plot([g - 0.3, g + 0.3], [np.median(lag)] * 2, color=INK, lw=3, zorder=4, label="mediana" if g == 0 else None)
        ax.axhline(0, color=MUTED, lw=1.4, zorder=1)
        lo, hi = ax.get_ylim()
        ax.set_ylim(lo, hi + 0.25 * (hi - lo))      # franja libre arriba para la leyenda, sin tocar puntos
        ax.set_xticks(range(len(MAIN_LAYERS)), list(MAIN_LAYERS))
        ax.set_xlim(-0.6, len(MAIN_LAYERS) - 0.4)
        ax.set_ylabel("corrimiento $c$ [s]")
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        ax.yaxis.set_major_formatter(COMMA)
        ax.legend(loc="upper right", frameon=True, framealpha=0.95)
        save(fig, "R5b-corrimiento.pdf")


# ---------------------------------------------------------------- V0: sensibilidad a la velocidad inicial
def v0_sensitivity():
    def mean_ecm1(folder):
        e = [float(line.split()[2]) for line in (folder / "ecm.txt").read_text(encoding="utf-8").splitlines() if line.startswith("E ")]
        return float(np.mean(e))

    note()
    note("## Sensibilidad a v_0 (ECM 1 excl. poblacional; control contra 0,4515/0,4282/0,3960 y 0,4333/0,4128/0,3861)")
    with plt.rc_context(COL_FONT):
        fig, ax = plt.subplots(figsize=COL_SIZE, constrained_layout=True)
        w = 0.26
        shades = {3: "#cfcfcf", 5: "#6e6e6e", 7: "#ffffff"}
        hatches = {3: None, 5: None, 7: "///"}
        for g, layer in enumerate("AB"):
            pair = PAIRS[layer]
            folder = P / "sensitivity_v0" / f"{layer}_{pair[0]:g}_{pair[1]:g}"
            vals = {n: mean_ecm1(folder / f"v0_{n}") for n in (3, 5, 7)}
            note(f"- {layer}({num(f'{pair[0]:g}')}; {num(f'{pair[1]:g}')}): " + " / ".join(num(f"{vals[n]:.4f}") for n in (3, 5, 7)))
            for k, n in enumerate((3, 5, 7)):
                x = g + (k - 1) * w
                ax.bar(x, vals[n], w, color=shades[n], edgecolor=INK, lw=1.0, hatch=hatches[n],
                       label=(f"{n} cuadros" + (" (base)" if n == 5 else "")) if g == 0 else None, zorder=2)
                ax.text(x, vals[n] + 0.008, num(f"{vals[n]:.3f}"), ha="center", va="bottom", fontsize=12, color=INK)
        ax.set_xticks(range(2), [f"A({num(f'{PAIRS[l][0]:g}')}; {num(f'{PAIRS[l][1]:g}')})" if l == "A"
                                  else f"B({num(f'{PAIRS[l][0]:g}')}; {num(f'{PAIRS[l][1]:g}')})" for l in "AB"])
        ax.set_xlim(-0.6, 1.6)
        ax.set_ylim(0, 0.62)
        ax.set_ylabel("ECM 1 [m²]")
        ax.grid(axis="y", color=GRID, lw=0.8)       # sin style(): su formateador numérico pisaría los nombres de los pares
        ax.set_axisbelow(True)
        ax.yaxis.set_major_formatter(COMMA)
        ax.legend(loc="upper center", ncol=3, frameon=True, framealpha=0.95, fontsize=13, columnspacing=0.8)
        save(fig, "V0-sensibilidad.pdf")


# ---------------------------------------------------------------- R6
def r6():
    rhos = (0.7, 0.8, 0.9, 1.0, 1.1)
    # Paneles apilados (ECM 1 arriba, contactos abajo) y eje x compartido: más chica en pulgadas, letra más grande
    # en la diapositiva
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.4), sharex=True, constrained_layout=True)
    for layer in "AB":
        p = PAIRS[layer]
        e, ct = [], []
        for rho in rhos:
            r = load_grid(P / "recorte_extra" / "rho" / f"con_{layer.lower()}_{p[0]:g}_{p[1]:g}_rho{rho:.1f}.txt")
            e.append(r[:, 3].mean())
            ct.append(int(r[:, 10].sum()))
        axes[0].plot(rhos, e, "-" + MARKERS[layer], color=COLORS[layer], lw=2.5, ms=11, label=layer)
        axes[1].plot(rhos, ct, "-" + MARKERS[layer], color=COLORS[layer], lw=2.5, ms=11, label=layer)
    axes[0].set_ylabel("ECM 1 [m²]", fontsize=22)
    axes[1].set_ylabel("eventos con\ncontacto", fontsize=22)
    axes[1].set_xlabel(r"$\rho$ [m]", fontsize=24)
    for ax in axes:
        ax.set_xticks(rhos)
        ax.tick_params(labelsize=20)
        ax.axvline(RHO, color=MUTED, ls=":", lw=1.5)
        style(ax)
    axes[1].set_ylim(-0.8, 19.8)
    axes[1].yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    axes[0].legend(loc="upper right", frameon=True, framealpha=0.95, fontsize=20)
    axes[1].legend(loc="upper right", frameon=True, framealpha=0.95, fontsize=20)
    save(fig, "R6-robustez-rho.pdf")


def main():
    """Uso: presentation_figures.py [evento] [figura ...].
    Claves: S1 R1 R2 (mapas por capa y métrica) R2old (mapas viejos, tres paneles) R3 R4 R5 R6 R7 C1 C2 T1 M1 V0.
    Sin claves, todas menos R2old."""
    sys.stdout.reconfigure(encoding="utf-8")
    event = int(sys.argv[1]) if len(sys.argv) > 1 else 11
    keys = ["S1", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "C1", "C2", "T1", "M1", "V0"]
    only = set(sys.argv[2:]) or set(keys)
    FIGS.mkdir(parents=True, exist_ok=True)
    if "S1" in only: s1(event)
    if "R1" in only: r1(event)
    if "R2" in only: r2_maps()
    if "R2old" in only: r2()
    if "R3" in only: r3()
    if "R4" in only: r4()
    if "R5" in only: r5()
    if "R6" in only: r6()
    if "C1" in only: c1_optima()
    if "C2" in only: c2_errors()
    if "T1" in only: t1_distance(event)
    if "M1" in only:
        m1_best("AB", "M1-mejores-pares.pdf")
        m1_best("ABF", "M1-mejores-pares-con-F.pdf")
    if "C1b" in only: c1_counts()
    if "C2b" in only: c2_boxes()
    if "V0" in only: v0_sensitivity()
    t_min, video = None, None
    if "R7" in only:
        t_min, dt_exp, t_end = r7(event)
        video = r7_video(event, t_end, dt_exp)
    DEST.mkdir(parents=True, exist_ok=True)
    for name in CREATED:
        shutil.copy(FIGS / name, DEST / name)
    if NUMBERS:
        header = ["# Números de las figuras nuevas de la presentación",
                  "Generado por `scripts/graph_gen/presentation_figures.py`. Recorte vigente (D(45°) + compuerta X = 1,5 m), ρ = 0,9, "
                  "Δt = Δt_exp/64, grilla oficial, ECM 1 = variante excluyente, 19 eventos.", ""]
        (FIGS / "numeros_figuras_nuevas.md").write_text("\n".join(header + NUMBERS) + "\n", encoding="utf-8")
    if t_min is not None:
        print(f"evento {event}; fotograma R7 en t = {t_min:.2f} s; video {video}")
    print("figuras: " + ", ".join(CREATED))


if __name__ == "__main__":
    main()
