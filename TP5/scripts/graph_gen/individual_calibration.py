#!/usr/bin/env python3
"""Calibración por evento (un par compartido por sus dos peatones), SFM A/B/E.

mvn -q package
.venv/bin/python scripts/graph_gen/individual_calibration.py [--reuse | --plots-only]
Requiere las corridas de population_calibration.py. Conserva sus óptimos como referencia.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import subprocess

from population_calibration import ROOT, FIG, SPECS, values, texnum, save, plt, np

OUT = ROOT / "outputs/calibracion_individual"
POP = ROOT / "outputs/calibracion_poblacional"
COLORS = ("#3939b5", "#d85b00")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_population(layer):
    groups = {}
    for path in sorted(POP.glob(f"{layer}_*.txt")):
        rows = np.loadtxt(path, usecols=(0, 1, 2, 3, 5), ndmin=2)
        for pair in np.unique(rows[:, :2], axis=0):
            group = rows[np.all(rows[:, :2] == pair, axis=1)]
            group = group[np.argsort(group[:, 2])]
            if not np.array_equal(group[:, 2], np.arange(1, 20)):
                raise ValueError(f"{path}: eventos incompletos o duplicados")
            key = tuple(pair)
            if key in groups:
                np.testing.assert_array_equal(groups[key], group[:, 3:])
            groups[key] = group[:, 3:]
    if not groups:
        raise ValueError(f"Faltan las grillas poblacionales de {layer}")
    return groups


def best(groups, metric):
    return min(groups, key=lambda p: (groups[p][metric], p))


def refine_event(layer, event, initial, args, fingerprint):
    groups = {p: errors[event-1].copy() for p, errors in initial.items()}
    original = dict(groups)
    s1, s2, _ = SPECS[layer]
    for metric in range(2):
        center = best(original, metric)
        steps = np.array([s1[2], s2[2]])
        for level in (1, 2):
            x, y = [values(max(s[0], c-d), min(s[1], c+d), d/5)
                    for s, c, d in zip((s1, s2), center, steps)]
            path = OUT / "grillas" / f"{layer}_evento{event:02d}_ecm{metric+1}_fina{level}.txt"
            cmd = ["java", "-Xmx512m", "-Djava.util.concurrent.ForkJoinPool.common.parallelism=2",
                   "-cp", "target/tp5.jar", "ar.edu.itba.sds.tp5.analysis.AnalysisMain", "grid",
                   "--layer", layer.lower(), "--event", str(event), "--model", "sfm", "--data", "data",
                   "--dt-div", "64", "--v0-frames", "5", "--p1-values", ",".join(map(str, x)),
                   "--p2-values", ",".join(map(str, y)), "--out", str(path)]
            stamp = path.with_suffix(".json")
            signature = dict(command=cmd, inputs=fingerprint)
            cached = (args.reuse and path.exists() and stamp.exists()
                      and json.loads(stamp.read_text()) == signature)
            if args.plots_only and (not stamp.exists() or json.loads(stamp.read_text()) != signature):
                raise ValueError(f"La procedencia de {path} cambió; regenerar sin --plots-only")
            if not args.plots_only and not cached:
                subprocess.run(cmd, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
                stamp.write_text(json.dumps(signature, indent=2) + "\n")
            rows = np.loadtxt(path, usecols=(0, 1, 2, 3, 5), ndmin=2)
            if (len(rows) != len(x)*len(y) or not np.all(rows[:, 2] == event)
                    or not np.array_equal(np.unique(rows[:, 0]), x)
                    or not np.array_equal(np.unique(rows[:, 1]), y)
                    or len(np.unique(rows[:, :2], axis=0)) != len(rows)
                    or not np.isfinite(rows).all()):
                raise ValueError(f"Grilla inválida: {path}")
            for row in rows:
                pair = tuple(row[:2])
                if pair in groups:
                    np.testing.assert_array_equal(groups[pair], row[3:])
                groups[pair] = row[3:]
            center = best(groups, metric)
            steps /= 5
    chosen = [best(groups, m) for m in range(2)]
    return chosen, [groups[p][m] for m, p in enumerate(chosen)]


def figures(layer, pairs, population, pop_errors, individual_errors):
    labels = SPECS[layer][2]

    def parameter_plot(ax, m, metric_label=True):
        points, counts = np.unique(pairs[:, m, :], axis=0, return_counts=True)
        ax.scatter(points[:, 0], points[:, 1], s=45+25*(counts-1), color=COLORS[m],
                   alpha=.75, label="Óptimos por evento", zorder=3)
        for point, count in zip(points, counts):
            if count > 1 and not (layer == "E" and m == 0):
                ax.annotate(f"×{count}", point, xytext=(5, 6), textcoords="offset points", fontsize=10)
        ax.plot(population[m]["p1"], population[m]["p2"], "*", ms=17,
                color="#ffbf00", mec="black", label="Óptimo poblacional", zorder=4)
        for dim, s in enumerate(SPECS[layer][:2]):
            margin = (s[1]-s[0])*.06
            (ax.set_xlim if dim == 0 else ax.set_ylim)(s[0]-margin, s[1]+margin)
        ax.set(xlabel=labels[0], ylabel=labels[1])
        if metric_label:
            ax.text(.04, .95, f"ECM {m+1}", transform=ax.transAxes, va="top", fontsize=17)
        ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.02), fontsize=12, frameon=False)
        ax.grid(alpha=.2)
    # Misma posición horizontal para cada evento a ambos lados: solo separa puntos superpuestos.
    jitter = np.linspace(-.1, .1, 19)

    def error_plot(ax, m):
        p, i = pop_errors[:, m], individual_errors[:, m]
        ax.boxplot([p, i], positions=[0, 1], widths=.4, showfliers=False,
                   medianprops={"color": "black", "linewidth": 2}, zorder=1)
        for k in range(19):
            ax.plot([jitter[k], 1+jitter[k]], [p[k], i[k]], color=".65", lw=.8, alpha=.7, zorder=2)
        ax.scatter(jitter, p, color=COLORS[0], s=30, label="Poblacional", zorder=3)
        ax.scatter(1+jitter, i, color=COLORS[1], s=30, label="Individual", zorder=3)
        ax.set(xticks=[0, 1], xticklabels=["Poblacional", "Individual"],
               ylabel=rf"$E_m^{{({m+1})}}$ [m$^2$]", xlim=(-.4, 1.4))
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", alpha=.2)
        ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.02), fontsize=12, frameon=False)

    # Se conservan las figuras completas como material de consulta.
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4), layout="constrained")
    for m, ax in enumerate(axes):
        parameter_plot(ax, m)
    save(fig, f"individual-{layer}-parametros")
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4), layout="constrained")
    for m, ax in enumerate(axes):
        error_plot(ax, m)
    save(fig, f"individual-{layer}-errores")

    # Presentación: solo ECM 1, parámetros a la izquierda y errores a la derecha.
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4), layout="constrained")
    parameter_plot(axes[0], 0, metric_label=False)
    error_plot(axes[1], 0)
    save(fig, f"individual-{layer}-ecm1")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--plots-only", action="store_true")
    args = parser.parse_args()
    (OUT / "grillas").mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 15, "axes.spines.top": False,
                         "axes.spines.right": False, "pdf.fonttype": 42})
    population = json.loads((POP / "resumen.json").read_text())
    fingerprint = {str(p.relative_to(ROOT)): digest(p) for p in
                   [ROOT / "target/tp5.jar", *sorted((ROOT / "data").glob("*.txt"))]}
    summary, records, slides = {}, [], []
    provenance = {"inputs": fingerprint, "population_sources": {},
                  "method": "Un par por evento, compartido por sus dos peatones; dos refinamientos /5; "
                            "mismos dominios y referencias poblacionales que (b); mínimos sobre la unión de muestras."}
    for layer in SPECS:
        initial = load_population(layer)
        provenance["population_sources"].update({str(p.relative_to(ROOT)): digest(p)
                                               for p in sorted(POP.glob(f"{layer}_*.txt"))})
        pop_errors = np.column_stack([initial[r["p1"], r["p2"]][:, m]
                                     for m, r in enumerate(population[layer])])
        for m in range(2):
            np.testing.assert_allclose(pop_errors[:, m].mean(), population[layer][m]["mean"][m])
        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(refine_event, layer, event, initial, args, fingerprint)
                       for event in range(1, 20)]
            for event, future in enumerate(futures, 1):
                results.append(future.result())
                print(f"{layer}: evento {event}/19 listo", flush=True)
        pairs = np.array([r[0] for r in results])
        errors = np.array([r[1] for r in results])
        if np.any(errors > pop_errors+1e-12):
            raise AssertionError("El óptimo por evento debe incluir el par poblacional entre sus candidatos")
        summary[layer] = []
        for m in range(2):
            gain = 100*(1-errors[:, m].mean()/pop_errors[:, m].mean())
            gains = 100*(1-errors[:, m]/pop_errors[:, m])
            boundary = np.array([any(np.isclose(p[d], s[0]) or np.isclose(p[d], s[1])
                                    for d, s in enumerate(SPECS[layer][:2])) for p in pairs[:, m]])
            item = dict(population_mean=float(pop_errors[:, m].mean()),
                        individual_mean=float(errors[:, m].mean()), gain_percent=float(gain),
                        median_event_gain_percent=float(np.median(gains)),
                        boundary_events=int(boundary.sum()),
                        p1_quantiles=np.quantile(pairs[:, m, 0], [.25, .5, .75]).tolist(),
                        p2_quantiles=np.quantile(pairs[:, m, 1], [.25, .5, .75]).tolist())
            summary[layer].append(item)
            for k in range(19):
                records.append([layer, m+1, k+1, *pairs[k, m], population[layer][m]["p1"],
                                population[layer][m]["p2"], pop_errors[k, m], errors[k, m], gains[k], boundary[k]])
            print(f"{layer} ECM{m+1}: {item}", flush=True)
        figures(layer, pairs, population[layer], pop_errors, errors)
        slides.append(rf"""\begin{{frame}}[c]{{Calibración por evento: capa {layer}, ECM 1}}
  \centering
  \includegraphics[width=\textwidth,height=5.2cm,keepaspectratio]{{figuras/individual-{layer}-ecm1.pdf}}
\end{{frame}}
""")
    with (OUT / "por_evento.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["capa", "metrica", "evento", "p1_ind", "p2_ind", "p1_pop", "p2_pop",
                         "error_pop", "error_ind", "ganancia_porcentaje", "borde"])
        writer.writerows(records)
    (OUT / "resumen.json").write_text(json.dumps(summary, indent=2)+"\n")
    (OUT / "procedencia.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False)+"\n")
    gains1 = "; ".join(f"{layer}: ${texnum(summary[layer][0]['gain_percent'],1)}\\,\\%$" for layer in SPECS)
    conclusion = (r"\newcommand{\individualGanancias}{Baja la media de $E_m$ en ECM 1 (" + gains1 + ")}\n")
    (ROOT / "presentacion/calibracion_individual.tex").write_text(conclusion+"% Generado por individual_calibration.py\n"+"\n".join(slides))
    print(f"Datos y resumen: {OUT}", flush=True)


if __name__ == "__main__":
    main()
