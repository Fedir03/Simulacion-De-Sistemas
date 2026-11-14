#!/usr/bin/env python3
"""Capas A, B y E sobre el SFM y sobre el CPM: errores con los mismos parámetros.

Lee las grillas del SFM (outputs/ped/grid_A.txt, outputs/ped/grid_B.txt, outputs/egg/grid_E.txt) y las del CPM
(outputs/cpm/grid_*.txt, de `AnalysisMain grid --model cpm`), que recorren los mismos pares, y compara:
  1. sin capa (la fila ℓ = 0 de A, que es el modelo sin capa);
  2. el óptimo poblacional de cada modelo, evaluado también en el otro (mismos parámetros);
  3. toda la grilla, par por par;
  4. evento por evento en el óptimo del SFM.
Error poblacional = promedio de E_m sobre los 19 eventos; ± es el error estándar entre eventos. La diferencia pareada
CPM − SFM se calcula evento por evento con el mismo par.

Uso: python scripts/graph_gen/cpm_compare.py [carpeta CPM, por defecto outputs/cpm]
Escribe comparacion.md y figs/*.png en la carpeta. Necesita numpy y matplotlib.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/cpm")
SFM = {"A": Path("outputs/ped/grid_A.txt"), "B": Path("outputs/ped/grid_B.txt"), "E": Path("outputs/egg/grid_E.txt")}
PARAMS = {"A": ("t_a", "ℓ"), "B": ("t_a", "k"), "E": ("a", "b")}
METRICS = {"ecm1": ("ECM 1 excl.", 3), "ecm2": ("ECM 2", 5)}
LAYER_COLORS = {"A": "#0072B2", "B": "#E69F00", "E": "#009E73"}   # Okabe-Ito, como presentation_figures.py
MODEL_COLORS = {"SFM": "#0072B2", "CPM": "#D55E00"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
MINUS = "−"

plt.rcParams.update({"font.size": 14, "axes.labelsize": 15, "legend.fontsize": 12, "xtick.labelsize": 13, "ytick.labelsize": 13,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.titlesize": 15, "axes.spines.top": False, "axes.spines.right": False})


def num(value, fmt="{:.3f}"):
    return fmt.format(value).replace(".", ",").replace("-", MINUS)


def pct(value):
    return num(100 * value, "{:+.0f}") + "%"


COMMA = FuncFormatter(lambda v, _: num(v, "{:g}"))


class Grid:
    """Grilla como arreglos [par, evento]."""

    def __init__(self, path):
        rows = np.array([[float(x) if x not in ("true", "false") else float(x == "true") for x in line.split()]
                         for line in path.read_text().splitlines() if line and not line.startswith("#")])
        self.pairs = sorted({(r[0], r[1]) for r in rows})
        self.events = sorted({int(r[2]) for r in rows})
        index = {p: k for k, p in enumerate(self.pairs)}
        ev = {e: k for k, e in enumerate(self.events)}
        self.data = np.full((len(self.pairs), len(self.events), rows.shape[1]), np.nan)
        for r in rows:
            self.data[index[(r[0], r[1])], ev[int(r[2])]] = r
        self.index = index

    def metric(self, name):
        return self.data[:, :, METRICS[name][1]]

    def col(self, c):
        return self.data[:, :, c]


def mean_se(x):
    return x.mean(), x.std(ddof=1) / np.sqrt(len(x))


def pair_text(p):
    return f"({num(p[0], '{:g}')}; {num(p[1], '{:g}')})"


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return np.corrcoef(ra, rb)[0, 1]


def main():
    sfm = {layer: Grid(path) for layer, path in SFM.items()}
    cpm = {layer: Grid(OUT / f"grid_{layer}.txt") for layer in SFM}
    for layer in SFM:
        assert sfm[layer].pairs == cpm[layer].pairs and sfm[layer].events == cpm[layer].events, layer
    lines = ["# Capas A, B y E sobre el SFM y sobre el CPM, con los mismos parámetros", "",
             "Mismas grillas, mismos 19 eventos (tramo frontal, D3), misma condición inicial (D12), mismo δ_a (D13) y la misma "
             "capa (el mismo código). Solo cambia el modelo base:",
             "- **SFM** sin fuerza social: r = 0,25 m, Beeman con Δt = Δt_exp/64 (D1, D4, D5).",
             "- **CPM** (Baglietto y Parisi, 2011): r_min = 0,10 m y r_max = 0,25 m (enunciado), β = 0,9 y τ = 0,5 s (paper), "
             "v_e = v_d,max = v_d, Δt = r_min/(2 v_d,max) con la mayor v_d del evento (Ec. 2). La capa solo actúa sin contacto "
             "(Teórica 7, diapo 29); en contacto manda el escape.", "",
             "Error poblacional ⟨E⟩ = promedio sobre los 19 eventos (m²), ± error estándar entre eventos. "
             "Δ pareada = promedio de E_m(CPM) − E_m(SFM) con el mismo par, ± su error estándar. "
             "«CPM mejor» = eventos en que E_m(CPM) < E_m(SFM).", ""]

    # 1. Sin capa: A con ℓ = 0 es el modelo sin capa (lo verifica CpmSimulationTest y LayerSimulationTest)
    k0 = sfm["A"].index[(0.5, 0.0)]
    lines += ["## 1. Sin capa", "", "| métrica | SFM | CPM | Δ pareada | CPM mejor |", "|---|---|---|---|---|"]
    for m, (label, _) in METRICS.items():
        s, c = sfm["A"].metric(m)[k0], cpm["A"].metric(m)[k0]
        d = mean_se(c - s)
        lines.append(f"| {label} | {num(mean_se(s)[0])} ± {num(mean_se(s)[1])} | {num(mean_se(c)[0])} ± {num(mean_se(c)[1])} | "
                     f"{num(d[0], '{:+.3f}')} ± {num(d[1])} | {int((c < s).sum())} de 19 |")
    contacts_cpm = int(((cpm["A"].col(17)[k0] + cpm["A"].col(18)[k0]) > 0).sum())
    lines += ["", f"Contacto sin capa: SFM en {int(sfm['A'].col(10)[k0].sum())} de 19 eventos (discos de 0,25 m solapados); "
              f"CPM en {contacts_cpm} de 19 (r_ij < r_i + r_j, se activa el escape). Distancia mínima: SFM "
              f"{num(np.nanmin(sfm['A'].col(11)[k0]), '{:.2f}')} a {num(np.nanmax(sfm['A'].col(11)[k0]), '{:.2f}')} m, CPM "
              f"{num(np.nanmin(cpm['A'].col(11)[k0]), '{:.2f}')} a {num(np.nanmax(cpm['A'].col(11)[k0]), '{:.2f}')} m.", ""]

    # 2. Óptimos: el del SFM evaluado en el CPM y viceversa
    lines += ["## 2. Óptimo poblacional de cada modelo, evaluado en los dos", "",
              "Para cada métrica por separado (como en el punto b). La primera fila de cada capa usa el óptimo del SFM; la segunda, el del CPM.", "",
              "| capa | métrica | par (origen) | ⟨E⟩ SFM | ⟨E⟩ CPM | Δ pareada | CPM mejor |", "|---|---|---|---|---|---|---|"]
    optimum = {}
    for layer in SFM:
        for m, (label, _) in METRICS.items():
            s_all, c_all = sfm[layer].metric(m), cpm[layer].metric(m)
            ks, kc = int(np.argmin(s_all.mean(1))), int(np.argmin(c_all.mean(1)))
            optimum[(layer, m)] = (ks, kc)
            for k, origin in ((ks, "SFM"), (kc, "CPM")):
                s, c = s_all[k], c_all[k]
                d = mean_se(c - s)
                bold_s = "**" if origin == "SFM" else ""
                bold_c = "**" if origin == "CPM" else ""
                lines.append(f"| {layer} | {label} | {pair_text(sfm[layer].pairs[k])} ({origin}) | "
                             f"{bold_s}{num(s.mean())}{bold_s} ± {num(mean_se(s)[1])} | {bold_c}{num(c.mean())}{bold_c} ± {num(mean_se(c)[1])} | "
                             f"{num(d[0], '{:+.3f}')} ± {num(d[1])} ({pct(d[0] / s.mean())}) | {int((c < s).sum())} de 19 |")
    lines += ["", "En negrita, el error del modelo en su propio óptimo.", ""]

    # 3. Toda la grilla
    lines += ["## 3. Toda la grilla, par por par", "",
              "Sobre los ⟨E⟩ poblacionales de cada par. Cociente = ⟨E⟩ CPM / ⟨E⟩ SFM; Spearman = correlación de rangos entre las "
              "dos superficies (1 = mismo orden de los pares).", "",
              "| capa | métrica | pares | CPM mejor | cociente mediano (p10 a p90) | Spearman | ⟨E⟩ mín. SFM / CPM |",
              "|---|---|---|---|---|---|---|"]
    for layer in SFM:
        for m, (label, _) in METRICS.items():
            s, c = sfm[layer].metric(m).mean(1), cpm[layer].metric(m).mean(1)
            ratio = c / s
            lines.append(f"| {layer} | {label} | {len(s)} | {int((c < s).sum())} | {num(np.median(ratio), '{:.2f}')} "
                         f"({num(np.percentile(ratio, 10), '{:.2f}')} a {num(np.percentile(ratio, 90), '{:.2f}')}) | "
                         f"{num(spearman(s, c), '{:.2f}')} | {num(s.min())} / {num(c.min())} |")
    lines.append("")

    # 4. Observables en el óptimo del SFM (ECM 1)
    lines += ["## 4. Comportamiento en el óptimo del SFM (ECM 1 excl.)", "",
              "Distancia mínima simulada (real: 0,49 a 0,92 m), eventos con contacto (SFM: discos solapados; CPM: escape activado), "
              "conmutaciones máximas de la capa por peatón y llegada al mínimo respecto del real (mediana).", "",
              "| capa | par | modelo | d_min (m) | contacto | conmutaciones máx. | llegada al mínimo |", "|---|---|---|---|---|---|---|"]
    exp_t = exp_min_time()
    for layer in SFM:
        k = optimum[(layer, "ecm1")][0]
        for name, g in (("SFM", sfm[layer]), ("CPM", cpm[layer])):
            dmin = g.col(11)[k]
            contact = int(g.col(10)[k].sum()) if name == "SFM" else int(((g.col(17)[k] + g.col(18)[k]) > 0).sum())
            switches = int(np.nanmax(g.col(15)[k].tolist() + g.col(16)[k].tolist()))
            delay = np.median([g.col(12)[k][j] - exp_t[e] for j, e in enumerate(g.events)]) if exp_t else np.nan
            lines.append(f"| {layer} | {pair_text(g.pairs[k])} | {name} | {num(dmin.min(), '{:.2f}')} a {num(dmin.max(), '{:.2f}')} | "
                         f"{contact} de 19 | {switches} | {num(delay, '{:+.2f}')} s |")
    lines.append("")

    # 5. Por evento
    lines += ["## 5. Por evento, en el óptimo del SFM (ECM 1 excl.)", "",
              "| evento | " + " | ".join(f"{l} SFM | {l} CPM" for l in SFM) + " |", "|---" * (1 + 2 * len(SFM)) + "|"]
    for j, e in enumerate(sfm["A"].events):
        cells = []
        for layer in SFM:
            k = optimum[(layer, "ecm1")][0]
            s, c = sfm[layer].metric("ecm1")[k, j], cpm[layer].metric("ecm1")[k, j]
            cells += [num(s), ("**" + num(c) + "**") if c < s else num(c)]
        lines.append(f"| {e} | " + " | ".join(cells) + " |")
    lines += ["", "En negrita, los eventos en que el CPM da menos error.", ""]

    (OUT / "comparacion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    figures(sfm, cpm, optimum)
    print("\n".join(lines))


def exp_min_time():
    """t del mínimo real de cada evento, del ecm.txt de la línea base del SFM (columna t_d_min_exp)."""
    path = Path("outputs/ped/none/ecm.txt")
    if not path.exists():
        return {}
    return {int(p[1]): float(p[9]) for p in (line.split() for line in path.read_text().splitlines()) if p and p[0] == "E"}


def figures(sfm, cpm, optimum):
    """Una figura por métrica: por capa, tres barras con su error estándar entre eventos y el par usado."""
    figs = OUT / "figs"
    figs.mkdir(parents=True, exist_ok=True)
    for old in ("grilla_sfm_vs_cpm.png", "eventos_ecm1.png", "eventos_ecm2.png"):
        (figs / old).unlink(missing_ok=True)
    bars = (("SFM (su óptimo)", MODEL_COLORS["SFM"], "sfm", 0),
            ("CPM con el mismo par", "#F2B48C", "cpm", 0),
            ("CPM (su óptimo)", MODEL_COLORS["CPM"], "cpm", 1))
    width = 0.26
    for m, (label, _) in METRICS.items():
        fig, ax = plt.subplots(figsize=(11, 6.2), constrained_layout=True)
        top = 0
        for g, layer in enumerate(SFM):
            for b, (name, color, model, which) in enumerate(bars):
                k = optimum[(layer, m)][which]
                values = (sfm if model == "sfm" else cpm)[layer].metric(m)[k]
                mean, se = mean_se(values)
                x = g + (b - 1) * (width + 0.03)
                ax.bar(x, mean, width, color=color, label=name if g == 0 else None, zorder=3)
                ax.errorbar(x, mean, se, color=MUTED, capsize=4, lw=1.3, zorder=4)
                ax.text(x, mean + se + 0.01 * (1 if m == "ecm1" else 0.12), num(mean),
                        ha="center", va="bottom", fontsize=12, color=INK, fontweight="bold" if which == 1 or model == "sfm" else None)
                ax.text(x, -0.02 * (1 if m == "ecm1" else 0.12), pair_text(sfm[layer].pairs[k]), ha="center", va="top",
                        fontsize=10.5, color=MUTED)
                top = max(top, mean + se)
        ax.set_xticks(range(len(SFM)))
        ax.set_xticklabels([f"Capa {l}\n({PARAMS[l][0]}; {PARAMS[l][1]})" for l in SFM], fontsize=14)
        ax.tick_params(axis="x", length=0, pad=26)
        ax.set_ylim(0, top * 1.18)
        ax.set_ylabel(f"⟨{label}⟩ poblacional (m²)")
        ax.set_title(f"{label}: menor es mejor. Barras: error estándar entre los 19 eventos", loc="left")
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        ax.yaxis.set_major_formatter(COMMA)
        ax.spines["bottom"].set_visible(False)
        ax.legend(frameon=False, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.0))
        fig.savefig(figs / f"capas_{m}.png", dpi=150)
        plt.close(fig)


if __name__ == "__main__":
    main()
