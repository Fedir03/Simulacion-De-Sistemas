#!/usr/bin/env python3
"""Anexo ECM1: reducción de <E> al pasar de un par por evento a un par por peatón.

.venv/bin/python scripts/graph_gen/shared_vs_per_pedestrian.py [--plots-only]
Ambas optimizaciones usan la misma grilla amplia, con los peatones interactuando.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import subprocess

from population_calibration import ROOT, FIG, plt, np, texnum
from per_pedestrian import Grid, check_diagonal
from per_pedestrian_abe import COMMON

SOURCE = ROOT / "outputs/ped_abe_20261115_111241"
OUT = ROOT / "outputs/compartido_vs_por_peaton"
COLORS = {"A": "#0072B2", "B": "#E69F00", "E": "#D55E00"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(task):
    layer, event, parameters, expected = task
    folder = OUT / "verificacion" / layer / f"evento_{event:02d}"
    cmd = ["java", "-cp", "target/tp5.jar", "ar.edu.itba.sds.tp5.analysis.AnalysisMain", "run",
           "--event", str(event), "--layer", layer,
           "--p1", str(parameters[0]), "--p2", str(parameters[1]),
           "--p1-ped2", str(parameters[2]), "--p2-ped2", str(parameters[3]), "--out", str(folder)] + COMMON
    subprocess.run(cmd, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    row = next(s.split() for s in (folder / "ecm.txt").read_text().splitlines() if s.startswith("E "))
    measured = float(row[2])
    np.testing.assert_allclose(measured, expected, atol=1e-6, rtol=0)
    return dict(layer=layer, event=event, parameters=parameters, expected=expected, measured=measured)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plots-only", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    fingerprint = {"jar": sha(ROOT / "target/tp5.jar"),
                   "data": {p.name: sha(p) for p in sorted((ROOT / "data").glob("*.txt"))}}
    if args.plots_only:
        metadata = json.loads((OUT / "resumen.json").read_text())
        if metadata["fingerprint"] != fingerprint:
            raise ValueError("Cambió el motor o los datos; regenerar sin --plots-only")
        summary = metadata["summary"]
    else:
        manifest = json.loads((SOURCE / "grillas.sha256.json").read_text())
        for name, expected in manifest.items():
            if sha(SOURCE / name) != expected:
                raise ValueError(f"La grilla {name} cambió respecto de su manifiesto")
        summary, records, tasks = {}, [], []
        for layer in COLORS:
            grid = Grid(SOURCE / f"grid_ped_{layer}.txt")
            assert list(grid.events) == list(range(1, 20))
            assert np.isfinite(grid.err["ecm1"]).all()
            assert check_diagonal(grid, SOURCE / f"grid_{layer}.txt") <= 1e-6
            # La diagonal debe reproducir además la grilla amplia de la calibración actual.
            current = np.loadtxt(ROOT / f"outputs/calibracion_poblacional/{layer}_amplia.txt",
                                 usecols=(0, 1, 2, 3), ndmin=2)
            for k, pair in enumerate(grid.pairs):
                rows = current[np.all(current[:, :2] == pair, axis=1)]
                rows = rows[np.argsort(rows[:, 2])]
                np.testing.assert_array_equal(rows[:, 2], np.arange(1, 20))
                np.testing.assert_allclose(grid.err["ecm1"][:, k, k], rows[:, 3], atol=1e-6, rtol=0)
            indices, errors = grid.calibrate("ecm1")
            two, four = errors["ind2"], errors["ind4"]
            assert np.all(four <= two + 1e-12)
            difference = two-four
            summary[layer] = dict(shared_mean=float(two.mean()), per_pedestrian_mean=float(four.mean()),
                                  difference_mean=float(difference.mean()),
                                  difference_se=float(difference.std(ddof=1)/np.sqrt(19)),
                                  gain_percent=float(100*difference.mean()/two.mean()), events=19,
                                  pairs_per_pedestrian=len(grid.pairs))
            for k, event in enumerate(grid.events):
                a, b = indices["ind4"][k]
                parameters = [float(v) for i in (a, b) for v in grid.pairs[i]]
                tasks.append((layer, int(event), parameters, float(four[k])))
                records.append([layer, int(event), float(two[k]), float(four[k]), float(difference[k]), *parameters])
            print(layer, summary[layer], flush=True)
        with ThreadPoolExecutor(max_workers=3) as executor:
            checks = list(executor.map(verify, tasks))
        metadata = dict(fingerprint=fingerprint, source=str(SOURCE.relative_to(ROOT)), source_sha256=manifest,
                        metric="ECM1 excluyendo retiros", scope="Optimizaciones por evento (2p y 4p), misma grilla amplia",
                        difference="Error compartido menos error por peatón; promedio de 19 eventos",
                        uncertainty="Error estándar de las diferencias pareadas entre eventos", summary=summary,
                        current_engine_checks=checks)
        (OUT / "resumen.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n")
        with (OUT / "por_evento.csv").open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["capa", "evento", "ecm1_compartido", "ecm1_por_peaton", "diferencia",
                             "p1_izq", "p2_izq", "p1_der", "p2_der"])
            writer.writerows(records)
    plt.rcParams.update({"font.size": 17, "pdf.fonttype": 42})
    fig, ax = plt.subplots(figsize=(10, 3.8), layout="constrained")
    mean = np.array([summary[layer]["difference_mean"] for layer in COLORS])
    se = np.array([summary[layer]["difference_se"] for layer in COLORS])
    ax.bar(np.arange(3), mean, yerr=se, capsize=5, width=.55, color=list(COLORS.values()), zorder=3)
    for k, value in enumerate(mean):
        ax.annotate(f"{value:.4f}".replace(".", ","), (k, value+se[k]), xytext=(0, 6),
                    textcoords="offset points", ha="center", fontsize=15)
    ax.set(xticks=np.arange(3), xticklabels=[f"Capa {layer}" for layer in COLORS],
           ylabel=r"$\Delta\langle E\rangle$ [m$^2$]", ylim=(0, float(max(mean+se)*1.35)))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=.2); ax.set_axisbelow(True)
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"compartido-vs-por-peaton-ecm1.{ext}", dpi=180, bbox_inches="tight")
    plt.close(fig)
    rows = []
    for layer, r in summary.items():
        rows.append(rf"{layer} & ${texnum(r['shared_mean'],4)}$ & ${texnum(r['per_pedestrian_mean'],4)}$ & "
                    rf"${texnum(r['gain_percent'],1)}\,\%$ \\")
    slide = r"""% Generado por shared_vs_per_pedestrian.py
\begin{frame}[c]{Anexo: parámetros compartidos o por peatón (ECM 1)}
  \centering
  \includegraphics[width=\textwidth,height=3.4cm,keepaspectratio]{figuras/compartido-vs-por-peaton-ecm1.pdf}
  \par\vspace{1mm}
  {\footnotesize\renewcommand{\arraystretch}{1.15}
  \begin{tabular}{@{}lccc@{}}
  \hline Capa & $\langle E\rangle_{2p}$ (m$^2$) & $\langle E\rangle_{4p}$ (m$^2$) & Reducción \\ \hline
""" + "\n".join(rows) + r"""
  \hline
  \end{tabular}\par}
  \vspace{1mm}
  {\scriptsize 2p: un par compartido por evento; 4p: un par por peatón y por evento.\\
  Misma grilla amplia en ambos casos; los dos peatones se simulan juntos.\\
  $\Delta\langle E\rangle=\langle E\rangle_{2p}-\langle E\rangle_{4p}$; barras: $\pm$ error estándar entre eventos.\par}
\end{frame}
"""
    (ROOT / "presentacion/comparacion_por_peaton.tex").write_text(slide)
    print(f"Verificación actual y resultados: {OUT}", flush=True)


if __name__ == "__main__":
    main()
