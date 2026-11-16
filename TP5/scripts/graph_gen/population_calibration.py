#!/usr/bin/env python3
"""Calibración SFM reproducible: grilla amplia + dos refinamientos independientes.

Desde TP5/: mvn -q package && .venv/bin/python scripts/graph_gen/population_calibration.py
--plots-only reutiliza las corridas de esta herramienta. No modifica el piloto.
"""
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess

os.environ.setdefault("MPLCONFIGDIR", "/tmp/tp5-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import FormatStrFormatter
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/calibracion_poblacional"
FIG = ROOT / "presentacion/figuras"
SPECS = {
    "A": ((.5, 5, .5), (0, 2.5, .25), (r"$t_a$ [s]", r"$\ell$ [m]")),
    "B": ((.5, 5, .5), (0, 4, .5), (r"$t_a$ [s]", r"$k$")),
    "E": ((.5, 6, .5), (.25, .5, .05), (r"$a$ [m]", r"$b$ [m]")),
}
REUSE = False


def values(lo, hi, step):
    return np.round(np.arange(lo, hi + step / 2, step), 8)


def run_grid(layer, x, y, name, plots_only):
    path = OUT / f"{layer}_{name}.txt"
    cached = False
    if REUSE and path.exists():
        coordinates = np.loadtxt(path, usecols=(0, 1), ndmin=2)
        cached = (np.array_equal(np.unique(coordinates[:, 0]), x)
                  and np.array_equal(np.unique(coordinates[:, 1]), y))
    if not plots_only and not cached:
        cmd = ["java", "-Xmx2g", "-Djava.util.concurrent.ForkJoinPool.common.parallelism=4",
               "-cp", "target/tp5.jar", "ar.edu.itba.sds.tp5.analysis.AnalysisMain",
               "grid", "--layer", layer.lower(), "--model", "sfm", "--data", "data",
               "--dt-div", "64", "--v0-frames", "5",
               "--p1-values", ",".join(map(str, x)), "--p2-values", ",".join(map(str, y)),
               "--out", str(path)]
        print(f"{layer} {name}: {len(x)*len(y)} pares", flush=True)
        subprocess.run(cmd, cwd=ROOT, check=True)
    # Conservamos un registro de los errores por evento, no solo sus promedios.
    rows = np.loadtxt(path, usecols=(0, 1, 2, 3, 5), ndmin=2)
    groups = {}
    for pair in np.unique(rows[:, :2], axis=0):
        group = rows[np.all(rows[:, :2] == pair, axis=1)]
        group = group[np.argsort(group[:, 2])]
        if not np.array_equal(group[:, 2], np.arange(1, 20)):
            raise ValueError(f"{path}: cada par debe contener los 19 eventos, una vez")
        if not np.isfinite(group[:, 3:]).all():
            raise ValueError(f"{path}: error no finito")
        groups[tuple(pair)] = group[:, 3:]
    if len(groups) != len(x) * len(y):
        raise ValueError(f"{path}: grilla incompleta")
    if (not np.array_equal(np.unique(rows[:, 0]), x)
            or not np.array_equal(np.unique(rows[:, 1]), y)):
        raise ValueError(f"{path}: ejes distintos de los solicitados")
    return groups


def best(groups, metric):
    return min(groups, key=lambda pair: (groups[pair][:, metric].mean(), pair))


def stats(errors):
    return errors.mean(axis=0), errors.std(axis=0, ddof=1) / np.sqrt(len(errors))


def heatmaps(layer, groups, optima, suffix):
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.3), layout="constrained")
    x = np.unique([p[0] for p in groups])
    y = np.unique([p[1] for p in groups])
    for m, ax in enumerate(axes):
        z = np.array([[groups[a, b][:, m].mean() for a in x] for b in y])
        mesh = ax.pcolormesh(x, y, z, shading="nearest", cmap="viridis_r", rasterized=True,
                             norm=LogNorm(vmin=z.min(), vmax=z.max()))
        bar = fig.colorbar(mesh, ax=ax, pad=.02, ticks=np.geomspace(z.min(), z.max(), 4),
                           format=FormatStrFormatter("%.2f"))
        bar.minorticks_off()
        bar.set_label(rf"$\langle E\rangle^{{({m+1})}}$ [m$^2$]", fontsize=16)
        bar.ax.tick_params(labelsize=13)
        ax.plot(*optima[0], "*", ms=15, color="#f97316", mec="black", mew=.7,
                label="Mínimo ECM 1")
        ax.plot(*optima[1], "o", ms=11, mfc="none", mec="black", mew=1.6,
                label="Mínimo ECM 2")
        ax.legend(loc="upper right", fontsize=14, framealpha=.95, edgecolor="0.75",
                  handlelength=1.3, borderpad=.5, labelspacing=.4)
        ax.set(xlabel=SPECS[layer][2][0], ylabel=SPECS[layer][2][1])
        ax.xaxis.label.set_size(16)
        ax.yaxis.label.set_size(16)
        ax.tick_params(labelsize=14)
        # Los mínimos quedan dentro de los límites aunque estén en el borde.
    save(fig, f"calibracion-{layer}-{suffix}")


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=180)
    plt.close(fig)


def texnum(value, digits=4):
    return f"{value:.{digits}f}".rstrip("0").rstrip(".").replace(".", "{,}")


def main():
    global REUSE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plots-only", action="store_true")
    parser.add_argument("--reuse", action="store_true", help="Reutilizar grillas existentes si sus ejes coinciden")
    args = parser.parse_args()
    REUSE = args.reuse
    os.chdir(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42})
    summary, slides = {}, []
    with (OUT / "comparacion.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["capa", "criterio", "p1", "p2", "ecm1", "se1", "ecm2", "se2",
                         "ecm_objetivo_gruesa", "borde_dominio"])
        for layer, (s1, s2, labels) in SPECS.items():
            coarse = run_grid(layer, values(*s1), values(*s2), "amplia", args.plots_only)
            all_groups = dict(coarse)
            optima, refinements, layer_summary, coarse_errors = [], [], [], []
            for metric in range(2):
                center = best(coarse, metric)
                coarse_error = coarse[center][:, metric].mean()
                coarse_errors.append(coarse_error)
                steps = np.array([s1[2], s2[2]])
                for level in (1, 2):
                    # Ventana de +/- un paso anterior; resolución cinco veces menor.
                    axes = [values(max(s[0], c-d), min(s[1], c+d), d/5)
                            for s, c, d in zip((s1, s2), center, steps)]
                    local = run_grid(layer, *axes, f"ecm{metric+1}_fina{level}", args.plots_only)
                    all_groups.update(local)
                    center = best(all_groups, metric)
                    steps /= 5
                refinements.append(local)
            # Ambas métricas se evalúan en TODAS las corridas. Cada mínimo final
            # se selecciona de la unión, incluida la región refinada por la otra.
            for metric in range(2):
                center = best(all_groups, metric)
                optima.append(center)
                means, se = stats(all_groups[center])
                on_boundary = any(np.isclose(c, s[0]) or np.isclose(c, s[1])
                                  for c, s in zip(center, (s1, s2)))
                result = dict(p1=center[0], p2=center[1], mean=means.tolist(), se=se.tolist(),
                              coarse_error=coarse_errors[metric], boundary=bool(on_boundary),
                              resolution=[s1[2]/25, s2[2]/25])
                layer_summary.append(result)
                writer.writerow([layer, f"ECM{metric+1}", *center, means[0], se[0], means[1], se[1],
                                 coarse_errors[metric], on_boundary])
                print(f"{layer} ECM{metric+1}: {center}; medias={means}; SE={se}", flush=True)
            heatmaps(layer, coarse, optima, "mapas")
            fig, axes = plt.subplots(2, 2, figsize=(10, 7.2), layout="constrained")
            for m in range(2):
                center = optima[m]
                for dim in range(2):
                    # Cortes amplios, más densos en la región refinada, al otro parámetro EXACTO.
                    ticks = sorted(set(values(*(s1, s2)[dim])) |
                                   {p[dim] for p in refinements[m]} | {center[dim]})
                    xx, yy = ([np.array(ticks), [center[1]]] if dim == 0
                              else [[center[0]], np.array(ticks)])
                    cut = run_grid(layer, xx, yy, f"ecm{m+1}_corte{dim+1}", args.plots_only)
                    pairs = sorted(cut, key=lambda p: p[dim])
                    means, errors = zip(*(stats(cut[p]) for p in pairs))
                    means, errors = np.array(means), np.array(errors)
                    ax = axes[m, dim]
                    ax.errorbar([p[dim] for p in pairs], means[:, m], yerr=errors[:, m],
                                fmt=".-", capsize=2, color="#3939b5", lw=1)
                    ax.axvline(center[dim], color="#f97316", ls="--", lw=1.3)
                    ax.set(xlabel=labels[dim], ylabel=rf"$\langle E\rangle^{{({m+1})}}$ [m$^2$]")
                    ax.text(.97, .97, f"{labels[1-dim]} = {center[1-dim]:g}",
                            transform=ax.transAxes, ha="right", va="top", fontsize=10)
            save(fig, f"calibracion-{layer}-cortes")
            summary[layer] = layer_summary
            # Elegir el menor sacrificio relativo respecto de los dos mínimos.
            # En un empate (B), marcar la primera fila como representante del par.
            means = np.array([result["mean"] for result in layer_summary])
            relative_loss = means / means.min(axis=0) - 1
            selected = int(np.argmin(relative_loss.max(axis=1)))
            rows = []
            for m, result in enumerate(layer_summary):
                highlight = r"\rowcolor{yellow!35} " if m == selected else ""
                rows.append(highlight + rf"ECM {m+1} & $({texnum(result['p1'])};\ {texnum(result['p2'])})$ & "
                            rf"${texnum(result['mean'][0], 5)}$ & ${texnum(result['mean'][1], 5)}$ \\")
            slides.append(rf"""\begin{{frame}}[c]{{Calibración poblacional: capa {layer}}}
  \centering
  \includegraphics[width=\textwidth,height=4.4cm,keepaspectratio]{{figuras/calibracion-{layer}-mapas.pdf}}
  \par\vspace{{2mm}}
  {{\footnotesize\renewcommand{{\arraystretch}}{{1.15}}
  \begin{{tabular}}{{@{{}}lccc@{{}}}}
    \hline Criterio & $(p_1^*,p_2^*)$ & ECM 1 (m$^2$) & ECM 2 (m$^2$) \\ \hline
    {chr(10).join(rows)}
    \hline
  \end{{tabular}}\par}}
\end{{frame}}
""")
    (OUT / "resumen.json").write_text(json.dumps(summary, indent=2) + "\n")
    (ROOT / "presentacion/calibracion_resultados.tex").write_text("% Generado por population_calibration.py\n" + "\n".join(slides))
    print(f"Resultados: {OUT}; figuras: {FIG}", flush=True)


if __name__ == "__main__":
    main()
