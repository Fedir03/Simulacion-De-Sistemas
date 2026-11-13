#!/usr/bin/env python3
"""Calibración por peatón (punto c opcional, 4 parámetros) de las capas A y B: tablas y figuras comparativas.

Lee las grillas de `AnalysisMain grid-ped` (todas las combinaciones par del peatón 1 × par del peatón 2, por evento) y
compara cuatro calibraciones, para cada métrica por separado:
  pob. 2p  un par para todos los eventos y los dos peatones (punto b)
  pob. 4p  un par para el peatón izquierdo y otro para el derecho, los mismos en todos los eventos
  ind. 2p  un par por evento, el mismo para los dos peatones (punto c)
  ind. 4p  un par por peatón y por evento (punto c opcional)
La diagonal de la grilla por peatón (los dos pares iguales) es la grilla de 2 parámetros, así que las cuatro salen del
mismo archivo; si está la grilla de 2 parámetros, se verifica que la diagonal coincida.
Peatón 1 = el que sale por la izquierda; peatón 2 = el de la derecha.

Uso: python scripts/graph_gen/per_pedestrian.py [carpeta, por defecto outputs/ped]
Necesita matplotlib. Escribe resumen.md y figs/*.png en la carpeta.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter  # noqa: E402

LAYERS = {"A": ("t_a", "ℓ", "s", "m"), "B": ("t_a", "k", "s", "")}
METRICS = {"ecm1": ("ECM 1 excl.", 5, (7, 8)), "ecm2": ("ECM 2", 6, (9, 10))}   # nombre, columna evento, columnas por peatón
CALIBS = ("pob2", "pob4", "ind2", "ind4")
CALIB_NAMES = {"pob2": "poblacional, 2 parámetros", "pob4": "poblacional, 4 parámetros",
               "ind2": "individual, 2 parámetros", "ind4": "individual, 4 parámetros"}
CALIB_SHORT = {"pob2": "pob. 2p", "pob4": "pob. 4p", "ind2": "ind. 2p", "ind4": "ind. 4p"}
COLORS = {"A": "#0072B2", "B": "#E69F00"}   # los de presentation_figures.py (Okabe-Ito)
INK, MUTED, GRID, FAINT = "#0b0b0b", "#52514e", "#e6e5e0", "#b8b7b2"
MINUS = "−"

plt.rcParams.update({"font.size": 15, "axes.labelsize": 16, "legend.fontsize": 13, "xtick.labelsize": 14, "ytick.labelsize": 14,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.titlesize": 16, "axes.spines.top": False, "axes.spines.right": False})


def num(value, fmt="{:.3f}"):
    return fmt.format(value).replace(".", ",").replace("-", MINUS)


COMMA = FuncFormatter(lambda v, _: num(v, "{:g}"))


def style(ax, grid_axis="both"):
    ax.grid(axis=grid_axis, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(COMMA)
    ax.yaxis.set_major_formatter(COMMA)


class Grid:
    """Grilla por peatón como arreglos [evento, par del peatón 1, par del peatón 2]."""

    def __init__(self, path):
        raw = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.startswith("#"):
                    p = line.split()
                    raw.append([float(v) for v in p[:11]] + [p[11] == "true", float(p[12])])
        raw = np.array(raw, dtype=float)
        self.p1 = np.unique(raw[:, 0])
        self.p2 = np.unique(raw[:, 1])
        self.pairs = [(a, b) for a in self.p1 for b in self.p2]
        index = {pair: i for i, pair in enumerate(self.pairs)}
        self.events = np.unique(raw[:, 4]).astype(int)
        ev_index = {e: i for i, e in enumerate(self.events)}
        n, m = len(self.pairs), len(self.events)
        shape = (m, n, n)
        self.err = {k: np.full(shape, np.nan) for k in METRICS}
        self.ped = {k: np.full(shape + (2,), np.nan) for k in METRICS}
        self.contact = np.zeros(shape, dtype=bool)
        self.dmin = np.full(shape, np.nan)
        for r in raw:
            e, i, j = ev_index[int(r[4])], index[(r[0], r[1])], index[(r[2], r[3])]
            for k, (_, col, cols) in METRICS.items():
                self.err[k][e, i, j] = r[col]
                self.ped[k][e, i, j] = r[list(cols)]
            self.contact[e, i, j] = bool(r[11])
            self.dmin[e, i, j] = r[12]
        missing = int(np.isnan(self.err["ecm1"]).sum())
        if missing:
            raise ValueError(f"{path}: faltan {missing} combinaciones")

    def calibrate(self, metric):
        """Para cada calibración: índices (i, j) por evento y error por evento."""
        e = self.err[metric]
        m, n, _ = e.shape
        diag = e[:, np.arange(n), np.arange(n)]                     # [evento, par]
        out = {}
        k = int(np.argmin(diag.mean(axis=0)))
        out["pob2"] = np.array([[k, k]] * m)
        flat = e.reshape(m, n * n)
        k = int(np.argmin(flat.mean(axis=0)))
        out["pob4"] = np.array([[k // n, k % n]] * m)
        k = np.argmin(diag, axis=1)
        out["ind2"] = np.stack([k, k], axis=1)
        k = np.argmin(flat, axis=1)
        out["ind4"] = np.stack([k // n, k % n], axis=1)
        errors = {c: e[np.arange(m), ij[:, 0], ij[:, 1]] for c, ij in out.items()}
        return out, errors

    def on_edge(self, i):
        a, b = self.pairs[i]
        return a in (self.p1[0], self.p1[-1]) or b in (self.p2[0], self.p2[-1])


def check_diagonal(grid, path2):
    """Máxima diferencia entre la diagonal de la grilla por peatón y la grilla de 2 parámetros."""
    if not path2.exists():
        return None
    worst = 0.0
    ev_index = {e: i for i, e in enumerate(grid.events)}
    index = {pair: i for i, pair in enumerate(grid.pairs)}
    with open(path2, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            p = line.split()
            e, i = ev_index[int(p[2])], index[(float(p[0]), float(p[1]))]
            worst = max(worst, abs(float(p[3]) - grid.err["ecm1"][e, i, i]), abs(float(p[5]) - grid.err["ecm2"][e, i, i]))
    return worst


def baseline(folder):
    out = {}
    path = folder / "none" / "ecm.txt"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("E "):
                p = line.split()
                out[int(p[1])] = {"ecm1": float(p[2]), "ecm2": float(p[4])}
    return out


def pair_text(grid, i, layer):
    a, b = grid.pairs[i]
    return f"({'—' if b == 0 else num(a, '{:g}')}; {num(b, '{:g}')})"     # con ℓ = 0 o k = 0, t_a es indistinto


def calib_text(grid, ij, layer):
    i, j = ij
    return pair_text(grid, i, layer) if i == j else f"{pair_text(grid, i, layer)} / {pair_text(grid, j, layer)}"


# ------------------------------------------------------------------ tablas

def tables(grids, results, base):
    md = ["# Calibración por peatón (4 parámetros) de las capas A y B", "",
          "Grilla oficial de la especificación (A: t_a × ℓ, 110 pares; B: t_a × k, 90 pares), todas las combinaciones "
          "par del peatón 1 (izquierdo) × par del peatón 2 (derecho) en los 19 eventos: 12 100 y 8 100 corridas por evento.",
          "Los errores individuales son de entrenamiento (se elige y se mide sobre el mismo evento): son cotas inferiores.", ""]

    md += ["## 1. Error poblacional según la calibración", "",
           "Promedio de E_m sobre los 19 eventos (m²). Entre paréntesis, el cambio respecto de la poblacional de 2 parámetros "
           "(punto b). En las poblacionales, el par elegido; en las individuales, la desviación estándar entre eventos.", ""]
    md.append("| capa | métrica | sin capa | pob. 2p | pob. 4p | ind. 2p | ind. 4p |")
    md.append("|---|---|---|---|---|---|---|")
    for layer, grid in grids.items():
        for metric, (mname, _, _) in METRICS.items():
            ij, err = results[layer][metric]
            ref = err["pob2"].mean()
            cells = [layer, mname, num(np.mean([base[e][metric] for e in grid.events])) if base else "—"]
            for c in CALIBS:
                v = err[c].mean()
                change = "" if c == "pob2" else f" ({num(100 * (v / ref - 1), '{:+.0f}')}%)"
                extra = calib_text(grid, ij[c][0], layer) if c.startswith("pob") else f"± {num(err[c].std(ddof=1))}"
                cells.append(f"{'**' if c == 'ind4' else ''}{num(v)}{change}{'**' if c == 'ind4' else ''}<br>{extra}")
            md.append("| " + " | ".join(cells) + " |")
    md.append("")

    md += ["## 2. Qué eligen los peatones con 4 parámetros por evento", "",
           "Sobre los 19 eventos. «Esquiva uno solo»: uno de los dos queda con ℓ = 0 (A) o k = 0 (B), o sea sin desvío lateral. Con ℓ = 0 o k = 0 el t_a de ese "
           "peatón no influye (el ECM es idéntico para todos los t_a) y el empate se resuelve en t_a = 0,5 s, el primero. "
           "«Borde»: algún parámetro de algún peatón en el mínimo o el máximo de la grilla. Contactos: eventos con solape de "
           "discos en la corrida óptima.", ""]
    md.append("| capa | métrica | pares distintos | esquiva uno solo | borde (4p) | borde (2p) | contactos 2p → 4p | d_min mediana 2p → 4p (m) | mejora mediana 4p vs 2p ind. |")
    md.append("|---|---|---|---|---|---|---|---|---|")
    for layer, grid in grids.items():
        for metric, (mname, _, _) in METRICS.items():
            ij, err = results[layer][metric]
            m = len(grid.events)
            i4, i2 = ij["ind4"], ij["ind2"]
            distinct = int((i4[:, 0] != i4[:, 1]).sum())
            lone = sum(1 for i, j in i4 if (grid.pairs[i][1] == 0) != (grid.pairs[j][1] == 0))
            edge4 = sum(1 for i, j in i4 if grid.on_edge(i) or grid.on_edge(j))
            edge2 = sum(1 for i, _ in i2 if grid.on_edge(i))
            ev = np.arange(m)
            c2, c4 = grid.contact[ev, i2[:, 0], i2[:, 1]].sum(), grid.contact[ev, i4[:, 0], i4[:, 1]].sum()
            d2, d4 = np.median(grid.dmin[ev, i2[:, 0], i2[:, 1]]), np.median(grid.dmin[ev, i4[:, 0], i4[:, 1]])
            gain = np.median(100 * (1 - err["ind4"] / err["ind2"]))
            md.append(f"| {layer} | {mname} | {distinct} de {m} | {lone} de {m} | {edge4} de {m} | {edge2} de {m} | "
                      f"{c2} → {c4} | {num(d2, '{:.2f}')} → {num(d4, '{:.2f}')} | {num(gain, '{:.0f}')}% |")
    md.append("")

    md += ["## 3. Diferencia entre el peatón izquierdo y el derecho (ind. 4p)", "",
           "Mediana de |p₁ − p₂| entre los dos peatones del mismo evento, y cuál de los dos tiene el desvío lateral mayor. "
           "Δt_a, solo en los eventos en que los dos tienen desvío lateral (con ℓ = 0 o k = 0, t_a es indistinto).", ""]
    md.append("| capa | métrica | mediana \\|Δt_a\\| (s) | mediana \\|Δℓ\\| o \\|Δk\\| | lateral mayor: izq. / der. / igual |")
    md.append("|---|---|---|---|---|")
    for layer, grid in grids.items():
        for metric, (mname, _, _) in METRICS.items():
            i4 = results[layer][metric][0]["ind4"]
            P = np.array([[grid.pairs[i], grid.pairs[j]] for i, j in i4])   # [evento, peatón, parámetro]
            both = (P[:, 0, 1] > 0) & (P[:, 1, 1] > 0)
            d_ta, d_l = np.abs(P[both, 0, 0] - P[both, 1, 0]), np.abs(P[:, 0, 1] - P[:, 1, 1])
            left = int((P[:, 0, 1] > P[:, 1, 1]).sum())
            right = int((P[:, 0, 1] < P[:, 1, 1]).sum())
            md.append(f"| {layer} | {mname} | {num(np.median(d_ta), '{:g}')} ({both.sum()} eventos) | {num(np.median(d_l), '{:g}')} | "
                      f"{left} / {right} / {len(i4) - left - right} |")
    md.append("")

    md += ["## 4. Por evento", ""]
    for layer, grid in grids.items():
        for metric, (mname, _, _) in METRICS.items():
            ij, err = results[layer][metric]
            names = LAYERS[layer]
            md += [f"### Capa {layer}, {mname}", "",
                   f"Pares ({names[0]}; {names[1]}); en 4p, peatón izquierdo / derecho. Mejora = 1 − ind. 4p / ind. 2p.", ""]
            md.append("| evento | sin capa | pob. 2p | ind. 2p | par 2p | ind. 4p | pares 4p | mejora |")
            md.append("|---|---|---|---|---|---|---|---|")
            for k, e in enumerate(grid.events):
                md.append(f"| {e} | {num(base[e][metric]) if base else '—'} | {num(err['pob2'][k])} | {num(err['ind2'][k])} | "
                          f"{calib_text(grid, ij['ind2'][k], layer)} | {num(err['ind4'][k])} | {calib_text(grid, ij['ind4'][k], layer)} | "
                          f"{num(100 * (1 - err['ind4'][k] / err['ind2'][k]), '{:.0f}')}% |")
            md.append("")
    return md


# ------------------------------------------------------------------ figuras

def fig_summary(grids, results, out):
    """Error poblacional de cada calibración: barras por capa, un panel por métrica (escalas distintas)."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.6), constrained_layout=True)
    x = np.arange(len(CALIBS))
    width = 0.36
    for ax, (metric, (mname, _, _)) in zip(axes, METRICS.items()):
        top = 0
        for s, layer in enumerate(grids):
            err = results[layer][metric][1]
            means = np.array([err[c].mean() for c in CALIBS])
            sem = np.array([err[c].std(ddof=1) / np.sqrt(len(err[c])) for c in CALIBS])
            pos = x + (s - 0.5) * width
            ax.bar(pos, means, width * 0.94, color=COLORS[layer], label=f"capa {layer}", zorder=2)
            ax.errorbar(pos, means, sem, fmt="none", ecolor=INK, elinewidth=1.3, capsize=4, zorder=3)
            for p, v, s_ in zip(pos, means, sem):
                ax.text(p, v + s_ + 0.003 * (1 if metric == "ecm2" else 6), num(v), ha="center", va="bottom", fontsize=12, color=INK)
            top = max(top, (means + sem).max())
        ax.set_ylim(0, top * 1.18)
        ax.set_xticks(x, [CALIB_SHORT[c] for c in CALIBS])
        ax.set_ylabel(f"⟨{mname}⟩ (m²)")
        ax.set_title(mname)
        style(ax, "y")
        ax.xaxis.set_major_formatter(matplotlib.ticker.FixedFormatter([CALIB_SHORT[c] for c in CALIBS]))
    axes[0].legend(frameon=False, loc="upper right")
    fig.text(0.5, -0.04, "Barras: promedio sobre los 19 eventos; barras de error: error estándar (desv. est. / √19). "
             "p = parámetros; pob. = mismos para todos los eventos; ind. = por evento.", ha="center", fontsize=12, color=MUTED)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_distribution(grids, results, out):
    """Error por evento con cada calibración: cajas y una línea gris por evento (comparación pareada)."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True, sharex=True)
    for col, layer in enumerate(grids):
        for row, (metric, (mname, _, _)) in enumerate(METRICS.items()):
            ax = axes[row, col]
            err = results[layer][metric][1]
            data = np.array([err[c] for c in CALIBS])          # [calib, evento]
            x = np.arange(len(CALIBS))
            for k in range(data.shape[1]):
                ax.plot(x, data[:, k], color=FAINT, lw=1, zorder=1)
            ax.boxplot(data.T, positions=x, widths=0.42, showfliers=False, zorder=2, patch_artist=True,
                       boxprops=dict(facecolor="none", edgecolor=COLORS[layer], lw=2),
                       medianprops=dict(color=COLORS[layer], lw=2.5), whiskerprops=dict(color=COLORS[layer], lw=1.5),
                       capprops=dict(color=COLORS[layer], lw=1.5))
            ax.scatter(np.repeat(x, data.shape[1]), data.ravel(), s=34, color=COLORS[layer], edgecolor="white", lw=0.8, zorder=3)
            ax.plot(x, data.mean(axis=1), "D", color=INK, ms=8, zorder=4, label="promedio")
            ax.set_yscale("log")
            ax.yaxis.set_major_formatter(COMMA)
            ax.yaxis.set_minor_formatter(NullFormatter())
            ax.yaxis.set_major_locator(LogLocator(subs=(1, 2, 5)))
            ax.grid(axis="y", color=GRID, lw=0.8)
            ax.set_axisbelow(True)
            ax.set_xticks(x, [CALIB_SHORT[c] for c in CALIBS])
            ax.set_title(f"Capa {layer}, {mname}")
            if col == 0:
                ax.set_ylabel("E_m (m², escala log)")
    handles = [Line2D([], [], color=FAINT, lw=1, label="un evento"), Line2D([], [], ls="none", marker="D", color=INK, ms=8, label="promedio"),
               Line2D([], [], color=MUTED, lw=2.5, label="mediana y cuartiles (caja)")]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def jitter(values, step, seed):
    rng = np.random.default_rng(seed)
    return values + rng.uniform(-0.18, 0.18, len(values)) * step


def fig_parameters(grid, results, layer, out):
    """Óptimos en el plano (p1, p2): por evento, el par de cada peatón unidos por un segmento; estrellas = poblacionales."""
    n1, n2, u1, u2 = LAYERS[layer]
    s1, s2 = np.diff(grid.p1).min(), np.diff(grid.p2).min()
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.6), constrained_layout=True, sharey=True)
    for ax, (metric, (mname, _, _)) in zip(axes, METRICS.items()):
        ij = results[layer][metric][0]
        P = np.array([[grid.pairs[i], grid.pairs[j]] for i, j in ij["ind4"]])
        Q = np.array([grid.pairs[i] for i, _ in ij["ind2"]])
        m = len(P)
        lx, ly = jitter(P[:, 0, 0], s1, 1), jitter(P[:, 0, 1], s2, 2)
        rx, ry = jitter(P[:, 1, 0], s1, 3), jitter(P[:, 1, 1], s2, 4)
        qx, qy = jitter(Q[:, 0], s1, 5), jitter(Q[:, 1], s2, 6)
        ax.scatter(qx, qy, marker="x", s=60, color=MUTED, lw=1.6, zorder=2, label="ind. 2p (los dos peatones)")
        ax.scatter(lx, ly, s=80, color=COLORS[layer], edgecolor="white", lw=1, zorder=3, label="ind. 4p, peatón izquierdo")
        ax.scatter(rx, ry, s=80, facecolor="white", edgecolor=COLORS[layer], lw=2, zorder=3, label="ind. 4p, peatón derecho")
        a, b = grid.pairs[ij["pob2"][0][0]]
        ax.plot(a, b, "*", ms=26, color=INK, mec="white", mew=1.2, zorder=5, label="pob. 2p")
        (a1, b1), (a2, b2) = grid.pairs[ij["pob4"][0][0]], grid.pairs[ij["pob4"][0][1]]
        ax.plot(a1, b1, "P", ms=16, color=INK, mec="white", mew=1.2, zorder=5, label="pob. 4p, izquierdo")
        ax.plot(a2, b2, "P", ms=16, color="white", mec=INK, mew=1.8, zorder=5, label="pob. 4p, derecho")
        ax.annotate(f"{n2} = 0: sin desvío,\n{n1} indistinto", (grid.p1[0], grid.p2[0]), xytext=(18, 14),
                    textcoords="offset points", fontsize=12, color=MUTED)
        ax.set_xlim(grid.p1[0] - 0.6 * s1, grid.p1[-1] + 0.6 * s1)
        ax.set_ylim(grid.p2[0] - 0.6 * s2, grid.p2[-1] + 0.6 * s2)
        ax.set_xticks(grid.p1)
        ax.set_yticks(grid.p2)
        style(ax)
        ax.set_xlabel(f"{n1} ({u1})")
        ax.set_title(f"Capa {layer}, {mname}")
    axes[0].set_ylabel(f"{n2}" + (f" ({u2})" if u2 else ""))
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.12))
    fig.text(0.5, -0.15, "Puntos desplazados al azar dentro de la celda para que no se tapen; los valores son los de la grilla. "
             "La pareja de cada evento está en ped_asimetria.png.",
             ha="center", fontsize=12, color=MUTED)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_asymmetry(grids, results, out):
    """Parámetro del peatón izquierdo contra el del derecho (ind. 4p): fuera de la diagonal, prefieren cosas distintas."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 12), constrained_layout=True)
    markers = {"ecm1": dict(marker="o"), "ecm2": dict(marker="s")}
    for col, (layer, grid) in enumerate(grids.items()):
        n1, n2, u1, u2 = LAYERS[layer]
        for row, (values, name, unit) in enumerate(((grid.p1, n1, u1), (grid.p2, n2, u2))):
            ax = axes[row, col]
            lo, hi = values[0], values[-1]
            pad = 0.6 * np.diff(values).min()
            ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color=MUTED, lw=1, ls="--", zorder=1)
            for metric, (mname, _, _) in METRICS.items():
                ij = results[layer][metric][0]["ind4"]
                a = np.array([grid.pairs[i][row] for i, _ in ij])
                b = np.array([grid.pairs[j][row] for _, j in ij])
                if row == 0:                                           # con ℓ = 0 o k = 0, t_a es indistinto
                    keep = np.array([grid.pairs[i][1] > 0 and grid.pairs[j][1] > 0 for i, j in ij])
                    a, b = a[keep], b[keep]
                pts, counts = np.unique(np.stack([a, b], axis=1), axis=0, return_counts=True)
                shift = (-0.15 if metric == "ecm1" else 0.15) * np.diff(values).min()
                filled = metric == "ecm1"
                ax.scatter(pts[:, 0] + shift, pts[:, 1], s=60 + 90 * (counts - 1), zorder=3, lw=2, edgecolor=COLORS[layer],
                           facecolor=COLORS[layer] if filled else "white", label=mname, **markers[metric])
            ax.set_xlim(lo - pad, hi + pad)
            ax.set_ylim(lo - pad, hi + pad)
            ax.set_aspect("equal")
            ax.set_xticks(values)
            ax.set_yticks(values)
            style(ax)
            every = 1.0 if row == 0 else 0.5                           # t_a: enteros; ℓ y k: múltiplos de 0,5
            ticks = [num(v, "{:g}") if abs(v / every - round(v / every)) < 1e-9 else "" for v in values]
            ax.set_xticklabels(ticks)
            ax.set_yticklabels(ticks)
            full = f"{name}" + (f" ({unit})" if unit else "")
            ax.set_xlabel(f"{full}, peatón izquierdo")
            ax.set_ylabel(f"{full}, peatón derecho")
            ax.set_title(f"Capa {layer}: {name}")
    handles = [Line2D([], [], ls="none", marker="o", ms=11, color=MUTED, label="ECM 1 excl."),
               Line2D([], [], ls="none", marker="s", ms=11, mfc="white", mec=MUTED, mew=2, label="ECM 2")]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.06),
               title="ind. 4p; tamaño = n.º de eventos; cada métrica corrida un poco a cada lado del valor; "
                     "t_a solo con los dos peatones con desvío lateral", title_fontsize=12)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("outputs/ped")
    figs = folder / "figs"
    figs.mkdir(parents=True, exist_ok=True)
    grids = {layer: Grid(folder / f"grid_ped_{layer}.txt") for layer in LAYERS}
    for layer, grid in grids.items():
        worst = check_diagonal(grid, folder / f"grid_{layer}.txt")
        print(f"{layer}: diagonal contra grid_{layer}.txt: " + ("no está" if worst is None else f"diferencia máxima {worst:.2e}"))
    results = {layer: {metric: grid.calibrate(metric) for metric in METRICS} for layer, grid in grids.items()}
    md = tables(grids, results, baseline(folder))
    (folder / "resumen.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    fig_summary(grids, results, figs / "ped_resumen.png")
    fig_distribution(grids, results, figs / "ped_distribucion_errores.png")
    for layer, grid in grids.items():
        fig_parameters(grid, results, layer, figs / f"ped_parametros_{layer}.png")
    fig_asymmetry(grids, results, figs / "ped_asimetria.png")
    print("\n".join(md[:40]))
    print(f"\nTablas: {folder / 'resumen.md'} | figuras: {figs}")


if __name__ == "__main__":
    main()
