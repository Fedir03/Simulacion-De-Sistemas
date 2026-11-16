#!/usr/bin/env python3
"""5000 particiones 14/5: búsqueda amplia + dos refinamientos SOLO en entrenamiento.

mvn -q package
.venv/bin/python scripts/graph_gen/refined_cross_validation.py [--reuse | --plots-only]
La caché guarda errores por par/evento. Cada partición solo puede elegir entre
su grilla amplia y las ventanas propuestas por sus propios datos de entrenamiento.
"""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess

from population_calibration import ROOT, FIG, SPECS, values, texnum, plt, np
from individual_calibration import load_population
from cross_validation import partitions, SEED, N_PARTITIONS

OUT = ROOT / "outputs/validacion_refinada"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_cache(path):
    rows = np.loadtxt(path, usecols=(0, 1, 2, 3, 5), ndmin=2)
    result = {}
    for pair in np.unique(rows[:, :2], axis=0):
        group = rows[np.all(rows[:, :2] == pair, axis=1)]
        group = group[np.argsort(group[:, 2])]
        if not np.array_equal(group[:, 2], np.arange(1, 20)) or not np.isfinite(group).all():
            raise ValueError(f"Caché incompleta o no finita: {path}")
        result[tuple(pair)] = group[:, 3:]
    return result


class Cache:
    def __init__(self, layer, args, fingerprint):
        self.layer, self.args, self.fingerprint = layer, args, fingerprint
        self.errors = load_population(layer)
        self.folder = OUT / "cache" / layer
        self.folder.mkdir(parents=True, exist_ok=True)
        if args.reuse or args.plots_only:
            for stamp in sorted(self.folder.glob("*.json")):
                meta = json.loads(stamp.read_text())
                path = stamp.with_suffix(".txt")
                if meta["inputs"] == fingerprint and path.exists():
                    self.errors.update(read_cache(path))

    def ensure(self, requested):
        missing = sorted(set(requested)-self.errors.keys())
        if not missing:
            return
        if self.args.plots_only:
            raise ValueError(f"Faltan {len(missing)} pares de {self.layer}; ejecutar sin --plots-only")
        print(f"{self.layer}: simular {len(missing)} pares nuevos × 19 eventos", flush=True)
        chunks = [missing[k:k+96] for k in range(0, len(missing), 96)]

        def run(chunk):
            content = "".join(f"{a:.8f} {b:.8f}\n" for a, b in chunk)
            key = hashlib.sha256(content.encode()).hexdigest()[:20]
            source = self.folder / f"{key}.pairs"
            target = self.folder / f"{key}.txt"
            source.write_text(content)
            cmd = ["java", "-Xmx1g", "-Djava.util.concurrent.ForkJoinPool.common.parallelism=2",
                   "-cp", "target/tp5.jar", "ar.edu.itba.sds.tp5.analysis.AnalysisMain", "grid",
                   "--layer", self.layer.lower(), "--pairs-file", str(source), "--out", str(target),
                   "--model", "sfm", "--data", "data", "--dt-div", "64", "--v0-frames", "5"]
            subprocess.run(cmd, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
            measured = read_cache(target)
            if set(measured) != set(chunk):
                raise ValueError("La caché no reproduce los pares solicitados")
            target.with_suffix(".json").write_text(json.dumps(dict(inputs=self.fingerprint, command=cmd), indent=2)+"\n")
            return measured

        with ThreadPoolExecutor(max_workers=2) as executor:
            for measured in executor.map(run, chunks):
                self.errors.update(measured)


@lru_cache(None)
def window(layer, center, level):
    axes = [values(max(s[0], c-s[2]/5**(level-1)), min(s[1], c+s[2]/5**(level-1)), s[2]/5**level)
            for s, c in zip(SPECS[layer][:2], center)]
    return frozenset((a, b) for a in axes[0] for b in axes[1])


def select(errors, allowed, weights, metric):
    """La única información usada para elegir es errors @ pesos de entrenamiento."""
    grouped = defaultdict(list)
    for k, candidates in enumerate(allowed):
        grouped[candidates].append(k)
    chosen = [None]*len(allowed)
    for candidates, indices in grouped.items():
        pairs = sorted(candidates)  # desempate lexicográfico, igual que (b)
        matrix = np.array([errors[p][:, metric] for p in pairs])
        best = np.argmin(matrix @ weights[:, indices], axis=0)
        for index, row in zip(indices, best):
            chosen[index] = pairs[row]
    return chosen


def fit(cache, coarse, masks):
    weights = masks.T.astype(float)/masks.sum(axis=1)
    allowed = [frozenset(coarse)]*len(masks)
    for metric in range(2):
        centers = select(cache.errors, [frozenset(coarse)]*len(masks), weights, metric)
        for level in (1, 2):
            windows = {p: window(cache.layer, p, level) for p in set(centers)}
            print(f"{cache.layer} ECM{metric+1}, nivel {level}: {len(windows)} ventanas de entrenamiento", flush=True)
            cache.ensure(set().union(*windows.values()))
            unions = {}
            next_allowed = []
            for previous, center in zip(allowed, centers):
                key = previous, center
                if key not in unions:
                    unions[key] = previous | windows[center]
                next_allowed.append(unions[key])
            allowed = next_allowed
            centers = select(cache.errors, allowed, weights, metric)
    chosen = [select(cache.errors, allowed, weights, m) for m in range(2)]
    return chosen


def figure(results, summary, metric):
    fig, ax = plt.subplots(figsize=(10.5, 4.5), layout="constrained")
    x = np.arange(3)
    for offset, key, color, label in [(-.16, "train", "#3939b5", "Entrenamiento"),
                                       (.16, "validation", "#d85b00", "Validación")]:
        means = [results[layer][key][:, metric].mean() for layer in SPECS]
        sd = [results[layer][key][:, metric].std(ddof=1) for layer in SPECS]
        ax.bar(x+offset, means, .3, yerr=sd, capsize=5, color=color, label=label)
    ax.plot(x, [summary[layer][metric]["error_b"] for layer in SPECS], "D", ms=8,
            color="black", label="Óptimo: ajuste con 19 eventos")
    ax.set(xticks=x, xticklabels=[f"Capa {s}" for s in SPECS], ylabel=rf"$\langle E\rangle^{{({metric+1})}}$ [m$^2$]")
    ax.set_ylim(bottom=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    ax.legend(loc="upper center", ncol=3, fontsize=12, frameon=False)
    # Reservar espacio para que la leyenda no cubra las barras de error.
    ax.set_ylim(top=ax.get_ylim()[1]*1.18)
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"validacion-refinada-ecm{metric+1}.{ext}", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--plots-only", action="store_true")
    parser.add_argument("--partitions", type=int, default=N_PARTITIONS)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    parts = partitions(args.partitions)
    # Control adicional: entrenar con todos debe reproducir exactamente (b).
    masks = np.vstack([parts, np.ones((1, 19), dtype=bool)])
    fingerprint = {str(p.relative_to(ROOT)): digest(p) for p in
                   [ROOT / "target/tp5.jar", *sorted((ROOT / "data").glob("*.txt"))]}
    population = json.loads((ROOT / "outputs/calibracion_poblacional/resumen.json").read_text())
    records, summary, results = [], {}, {}
    plt.rcParams.update({"font.size": 16, "pdf.fonttype": 42})
    for layer in SPECS:
        cache = Cache(layer, args, fingerprint)
        coarse = read_cache(ROOT / f"outputs/calibracion_poblacional/{layer}_amplia.txt")
        chosen = fit(cache, coarse, masks)
        train, val = np.zeros((len(parts), 2)), np.zeros((len(parts), 2))
        summary[layer] = []
        for metric in range(2):
            control = chosen[metric][-1]
            reference = population[layer][metric]
            assert control == (reference["p1"], reference["p2"]), (layer, metric, control, reference)
            np.testing.assert_allclose(cache.errors[control][:, metric].mean(), reference["mean"][metric], atol=1e-12)
            for k, pair in enumerate(chosen[metric][:-1]):
                errors = cache.errors[pair][:, metric]
                train[k, metric] = errors[parts[k]].mean()
                val[k, metric] = errors[~parts[k]].mean()
                records.append([layer, metric+1, k+1, *pair, train[k, metric], val[k, metric]])
            item = dict(error_b=reference["mean"][metric], training_mean=float(train[:, metric].mean()),
                        training_sd=float(train[:, metric].std(ddof=1)),
                        validation_mean=float(val[:, metric].mean()), validation_sd=float(val[:, metric].std(ddof=1)),
                        validation_quantiles=np.quantile(val[:, metric], [.025, .5, .975]).tolist(),
                        control_pair=list(control),
                        half_sample_change_percent=float(100*abs(val[:len(parts)//2, metric].mean()/val[:, metric].mean()-1)))
            item["change_vs_b_percent"] = 100*(item["validation_mean"]/item["error_b"]-1)
            summary[layer].append(item)
            print(layer, f"ECM{metric+1}", item, flush=True)
        results[layer] = dict(train=train, validation=val)
    with (OUT / "particiones.csv").open("w", newline="") as f:
        writer = csv.writer(f); writer.writerow(["particion", "entrenamiento", "validacion"])
        for k, mask in enumerate(parts, 1):
            writer.writerow([k, " ".join(map(str, np.flatnonzero(mask)+1)), " ".join(map(str, np.flatnonzero(~mask)+1))])
    with (OUT / "resultados.csv").open("w", newline="") as f:
        writer = csv.writer(f); writer.writerow(["capa", "metrica", "particion", "p1", "p2", "error_entrenamiento", "error_validacion"])
        writer.writerows(records)
    metadata = dict(seed=SEED, partitions=len(parts), train_events=14, validation_events=5,
                    fingerprint=fingerprint, resumen=summary,
                    population_sources={str(p.relative_to(ROOT)): digest(p) for p in
                        sorted((ROOT / "outputs/calibracion_poblacional").glob("*.txt"))},
                    reference_sha256=digest(ROOT / "outputs/calibracion_poblacional/resumen.json"),
                    method="Grilla amplia + dos refinamientos /5 por métrica usando solo entrenamiento; "
                           "selección final en la unión de las ventanas propias de cada partición; "
                           "caché compartida de simulaciones, sin compartir candidatos propuestos por otras particiones.")
    (OUT / "resumen.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n")
    slides = ["% Generado por refined_cross_validation.py\n"]
    for metric in range(2):
        figure(results, summary, metric)
        rows = []
        for layer in SPECS:
            r = summary[layer][metric]
            rows.append(rf"{layer} & ${texnum(r['error_b'],4)}$ & "
                        rf"${texnum(r['change_vs_b_percent'],1)}\,\%$ \\")
        slides.append(rf"""\begin{{frame}}[c]{{Validación cruzada: ECM {metric+1}}}
  \centering
  \includegraphics[width=\textwidth,height=3.7cm,keepaspectratio]{{figuras/validacion-refinada-ecm{metric+1}.pdf}}
  \par\vspace{{1mm}}
  {{\footnotesize\renewcommand{{\arraystretch}}{{1.2}}
  \begin{{tabular}}{{@{{}}lcc@{{}}}}
  \hline Capa & Óptimo & Validación vs. óptimo (\%) \\ \hline
  {chr(10).join(rows)}
  \hline
  \end{{tabular}}\par}}
\end{{frame}}
""")
    gains = summary
    conclusion = (r"\newcommand{\validacionConclusion}{Validación ECM 1: "
                  + "; ".join(rf"{layer}, ${texnum(gains[layer][0]['validation_mean'],3)}\pm {texnum(gains[layer][0]['validation_sd'],3)}$"
                              for layer in SPECS) + r" m$^2$}"+"\n")
    (ROOT / "presentacion/validacion_cruzada.tex").write_text(conclusion+"\n".join(slides))


if __name__ == "__main__":
    main()
