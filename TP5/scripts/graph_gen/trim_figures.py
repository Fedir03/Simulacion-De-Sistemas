#!/usr/bin/env python3
"""Figuras del análisis con el recorte al tramo frontal (Fase 5), en outputs/pilot/figs/. Sin título embebido
(el título va en el caption), leyenda adentro, letra grande. También imprime la medición de la diagonal.

Lee las grillas y pruebas de outputs/pilot y outputs/pilot_sin_recorte, las líneas base y las series de dirección
de figs/datos (scripts/sim_gen/figures.sh). Δt = Δt_exp/64. ECM 1 = variante excluyente.
Uso: py scripts/graph_gen/trim_figures.py
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
from matplotlib.ticker import FuncFormatter  # noqa: E402

from cross_validation import error_matrix, evaluate_on_all  # noqa: E402
from figure_data import read_directions  # noqa: E402
from pilot_analysis import load_baseline, load_grid  # noqa: E402

CON, SIN = Path("outputs/pilot"), Path("outputs/pilot_sin_recorte")
BASE = {"con": Path("outputs/baseline"), "sin": SIN / "baseline"}
FOLDER = {"con": CON, "sin": SIN}
OUT = CON / "figs"
COLORS = {"base": "#8a8985", "A": "#2a78d6", "B": "#eb6834", "F": "#1baf7a"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
METRICS = {"ecm1_excl": (3, "ECM 1 excl. (m²)"), "ecm2": (5, "ECM 2 (m²)")}
COMMA = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))

plt.rcParams.update({"font.size": 16, "axes.labelsize": 17, "legend.fontsize": 14, "xtick.labelsize": 15, "ytick.labelsize": 15,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})


def best_pairs(folder):
    out = {}
    for line in (folder / "mejores.txt").read_text(encoding="utf-8").splitlines():
        layer, m, p1, p2 = line.split()
        if m in METRICS:
            out[(layer, m)] = (float(p1), float(p2))
    return out


def per_event(folder, layer, pair, column):
    rows = load_grid(folder / f"grid_{layer}.txt")
    sel = rows[(rows[:, 0] == pair[0]) & (rows[:, 1] == pair[1])]
    return sel[np.argsort(sel[:, 2]), column]


def label(layer, pair):
    return f"{layer}({pair[0]:g}; {pair[1]:g})".replace(".", ",")


def style(ax):
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(COMMA)


def population():
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.8), constrained_layout=True)
    for ax, (m, (column, ylabel)) in zip(axes, METRICS.items()):
        groups = ["sin capa", "A", "B", "F"]
        for g, (tag, alpha, hatch) in enumerate((("sin", 0.45, "//"), ("con", 1.0, None))):
            base = load_baseline(BASE[tag])
            pairs = best_pairs(FOLDER[tag])
            vals = [np.array([v[m] for v in base.values()])] + [per_event(FOLDER[tag], l, pairs[(l, m)], column) for l in "ABF"]
            x = np.arange(4) + (g - 0.5) * 0.38
            means = [v.mean() for v in vals]
            sem = [v.std(ddof=1) / math.sqrt(len(v)) for v in vals]
            colors = [COLORS["base"]] + [COLORS[l] for l in "ABF"]
            ax.bar(x, means, 0.36, yerr=sem, color=colors, alpha=alpha, hatch=hatch, edgecolor="white", linewidth=1.5,
                   error_kw={"ecolor": MUTED, "elinewidth": 1.4, "capsize": 4})
            for xi, mv in zip(x, means):
                ax.text(xi, mv + max(means) * 0.02, f"{mv:.2f}".replace(".", ","), ha="center", va="bottom", fontsize=12, color=INK)
        ax.set_xticks(np.arange(4), groups)
        ax.set_ylabel(ylabel)
        style(ax)
    from matplotlib.patches import Patch
    axes[0].legend(handles=[Patch(facecolor=MUTED, alpha=0.45, hatch="//", edgecolor="white", label="sin recorte"),
                            Patch(facecolor=MUTED, label="con recorte D(45°)")], loc="upper right", frameon=False)
    fig.savefig(OUT / "ecm_poblacional.png", dpi=130)
    plt.close(fig)


def paired():
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.8), constrained_layout=True, sharey=False)
    pairs = best_pairs(CON)
    for ax, (m, (column, ylabel)) in zip(axes, METRICS.items()):
        ev = {l: per_event(CON, l, pairs[(l, m)], column) for l in "ABF"}
        for k, (p, q) in enumerate((("A", "B"), ("A", "F"), ("B", "F"))):
            d = ev[p] - ev[q]
            jitter = (np.arange(19) % 5 - 2) * 0.05
            ax.plot(k + jitter, d, "o", color=COLORS[p], mec=COLORS[q], mew=2, ms=8, alpha=0.9)
            ax.errorbar(k + 0.32, d.mean(), yerr=d.std(ddof=1) / math.sqrt(19), fmt="D", color=INK, ms=8, capsize=5, lw=1.6)
            ax.text(k + 0.4, d.mean(), f"{(d < 0).sum()}/19", va="center", fontsize=12, color=MUTED)
        ax.axhline(0, color=MUTED, lw=1)
        ax.set_xticks(range(3), [f"{p}−{q}" for p, q in (("A", "B"), ("A", "F"), ("B", "F"))])
        ax.set_xlim(-0.5, 2.8)
        ax.set_ylabel(f"diferencia por evento, {ylabel}")
        style(ax)
    from matplotlib.lines import Line2D
    axes[0].legend(handles=[Line2D([], [], marker="o", ls="none", color=MUTED, ms=8, label="evento (relleno: 1.ª capa; borde: 2.ª)"),
                            Line2D([], [], marker="D", ls="none", color=INK, ms=8, label="media ± error estándar")],
                   loc="lower left", frameon=False, fontsize=12)
    fig.savefig(OUT / "diferencias_pareadas.png", dpi=130)
    plt.close(fig)


def coin():
    rows = [l.split() for l in (CON / "pruebas" / "moneda.txt").read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    pairs = best_pairs(CON)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.6), constrained_layout=True)
    for ax, (m, (column, ylabel)) in zip(axes, METRICS.items()):
        idx = 5 if m == "ecm1_excl" else 6
        groups = sorted({(r[0], r[1], r[2]) for r in rows}, key=lambda g: (g[0], float(g[1])))
        for k, g in enumerate(groups):
            sub = [r for r in rows if (r[0], r[1], r[2]) == g]
            e = np.zeros((20, 19))
            for r in sub:
                e[int(r[3]), int(r[4]) - 1] = float(r[idx])
            pop = e.mean(axis=1)
            layer = g[0].upper()
            rule = per_event(CON, layer, (float(g[1]), float(g[2])), column).mean()
            ax.plot(k + (np.arange(20) % 5 - 2) * 0.05, pop, "o", color=COLORS[layer], ms=8, alpha=0.75)
            ax.plot([k - 0.25, k + 0.25], [rule, rule], color=INK, lw=3)
        ax.set_xticks(range(len(groups)), [label(g[0].upper(), (float(g[1]), float(g[2]))) for g in groups])
        ax.set_ylabel(ylabel)
        style(ax)
    from matplotlib.lines import Line2D
    axes[0].legend(handles=[Line2D([], [], marker="o", ls="none", color=MUTED, ms=8, label="lado por moneda (20 semillas)"),
                            Line2D([], [], color=INK, lw=3, label="regla de lado")], loc="upper right", frameon=False)
    fig.savefig(OUT / "lado_azar.png", dpi=130)
    plt.close(fig)


def recovery():
    rows = [l.split() for l in (CON / "pruebas" / "recuperacion.txt").read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.4), constrained_layout=True)
    names = {"a": ("t_a (s)", "ℓ (m)"), "b": ("t_a (s)", "k"), "f": ("A_p", "B_p (m)")}
    for ax, gen in zip(axes, sorted({r[0] for r in rows}, key=lambda g: "abf".index(g[0]))):
        layer, g1, g2 = gen.split(":")
        sub = np.array([[float(r[2]), float(r[3]), float(r[4])] for r in rows if r[0] == gen and r[1] == layer])
        p1, p2 = np.unique(sub[:, 0]), np.unique(sub[:, 1])
        z = np.full((len(p2), len(p1)), np.nan)
        for a, b, e in sub:
            z[np.searchsorted(p2, b), np.searchsorted(p1, a)] = e
        im = ax.imshow(np.log10(z + 1e-4), origin="lower", aspect="auto", cmap="Blues_r",
                       extent=(-0.5, len(p1) - 0.5, -0.5, len(p2) - 0.5))
        ax.plot(np.searchsorted(p1, float(g1)), np.searchsorted(p2, float(g2)), "*", color="#eb6834", ms=22, mec="white", mew=1.5, label="generador")
        k = np.nanargmin(z)
        ax.plot(k % len(p1), k // len(p1), "o", mfc="none", mec=INK, ms=18, mew=2.5, label="mínimo de ECM 1")
        ax.set_xticks(range(len(p1)), [f"{v:g}".replace(".", ",") for v in p1], fontsize=11, rotation=90 if len(p1) > 9 else 0)
        ax.set_yticks(range(len(p2)), [f"{v:g}".replace(".", ",") for v in p2], fontsize=11)
        ax.set_xlabel(names[layer][0])
        ax.set_ylabel(names[layer][1])
        ax.text(0.03, 0.97, f"datos de {layer.upper()}({g1}; {g2})".replace(".", ","), transform=ax.transAxes, va="top", fontsize=14,
                color=INK, bbox=dict(facecolor="white", edgecolor="none", alpha=0.85))
        cb = fig.colorbar(im, ax=ax, shrink=0.9)
        cb.set_label("log₁₀ ECM 1 excl. (m²)", fontsize=13)
    axes[0].legend(loc="lower right", frameon=True, framealpha=0.9, fontsize=12)
    fig.savefig(OUT / "recuperacion.png", dpi=130)
    plt.close(fig)


def turning():
    tracks = defaultdict(dict)
    with open("outputs/recorte/trayectorias_recortadas.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            tracks[int(r["evento"])].setdefault(int(r["peaton"]) - 1, []).append((int(r["frame"]), float(r["x"]), float(r["y"])))
    meta = defaultdict(dict)
    with open("outputs/recorte/recorte_eventos.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            meta[int(r["evento"])][int(r["peaton"]) - 1] = r
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.6), constrained_layout=True, sharey=True)
    for n in sorted(tracks):
        m = meta[n][0]
        dt, fmin, s, e = float(m["dt_exp"]), int(m["frame_min"]), int(m["frame_ini_rec"]), int(m["frame_fin_rec"])
        other = {i: {r[0]: r[1:] for r in tracks[n][1 - i]} for i in (0, 1)}
        for i in (0, 1):
            t = np.array([r for r in tracks[n][i] if s <= r[0] <= e])
            p0, p1 = t[0, 1:], t[-1, 1:]
            u = (p1 - p0) / np.linalg.norm(p1 - p0)
            dev = np.abs((t[:, 1] - p0[0]) * (-u[1]) + (t[:, 2] - p0[1]) * u[0])
            tt = (t[:, 0] - fmin) * dt
            dist = np.array([math.hypot(r[1] - other[i][int(r[0])][0], r[2] - other[i][int(r[0])][1]) if int(r[0]) in other[i] else np.nan for r in t])
            signed = np.where(tt < 0, dist, -dist)
            axes[0].plot(tt, dev, color=COLORS["A" if i == 0 else "B"], lw=1.1, alpha=0.55)
            axes[1].plot(signed, dev, color=COLORS["A" if i == 0 else "B"], lw=1.1, alpha=0.55)
    axes[0].axvline(0, color=INK, lw=1.2, ls=":")
    axes[1].axvline(0, color=INK, lw=1.2, ls=":")
    axes[1].invert_xaxis()
    axes[0].set_xlabel("t − t del mínimo real (s)")
    axes[1].set_xlabel("distancia al otro (m); positiva antes del cruce")
    axes[0].set_ylabel("desvío lateral (m)")
    from matplotlib.lines import Line2D
    axes[0].legend(handles=[Line2D([], [], color=COLORS["A"], lw=2, label="peatón izquierdo"), Line2D([], [], color=COLORS["B"], lw=2, label="peatón derecho")],
                   loc="upper left", frameon=False)
    for ax in axes:
        style(ax)
        ax.xaxis.set_major_formatter(COMMA)
    fig.savefig(OUT / "perfil_giro.png", dpi=130)
    plt.close(fig)


def diagonal():
    """Ángulo de e_t (hacia el target final) con el eje x en el primer segundo de la simulación, sin y con recorte."""
    print("Diagonal: máximo |ángulo de e_t con el eje x| en el primer segundo simulado, por evento (máx. de los 2 peatones), mejor par de ECM 1 excl. de A.")
    out = {}
    for tag, folder in (("sin", SIN), ("con", CON)):
        p = best_pairs(folder)[("A", "ecm1_excl")]
        d = folder / "figs" / "datos" / f"a_{p[0]:g}_{p[1]:g}"
        vals = []
        for n in range(1, 20):
            s = read_directions(d / f"direccion_{n:02d}.txt")
            s = s[s[:, 0] <= 1.0]
            worst = 0
            for i, sense in ((0, 1), (1, -1)):
                ex, ey = s[:, 2 + 5 * i], s[:, 3 + 5 * i]
                ok = ~np.isnan(ex)
                worst = max(worst, float(np.max(np.abs(np.degrees(np.arctan2(ey[ok], sense * ex[ok]))))))
            vals.append(worst)
        out[tag] = np.array(vals)
        print(f"  {tag} recorte, A({p[0]:g}; {p[1]:g}): mediana {np.median(vals):.1f}°, máximo {max(vals):.1f}° (evento {int(np.argmax(vals)) + 1})".replace(".", ","))
    drop = out["sin"] - out["con"]
    k = int(np.argmax(drop))
    print(f"  mayor reducción: evento {k + 1}, de {out['sin'][k]:.1f}° a {out['con'][k]:.1f}°".replace(".", ","))
    print("  por evento (sin → con): " + "; ".join(f"{n + 1}: {a:.1f}→{b:.1f}".replace(".", ",") for n, (a, b) in enumerate(zip(out["sin"], out["con"]))))
    return k + 1


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    population()
    paired()
    coin()
    recovery()
    turning()
    diagonal()


if __name__ == "__main__":
    main()
