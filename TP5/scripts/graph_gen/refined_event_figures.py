#!/usr/bin/env python3
"""Regenera las diapositivas 25, 28, 29 y 30 con los óptimos poblacionales refinados.

.venv/bin/python scripts/graph_gen/refined_event_figures.py [--plots-only]
ECM1 usa su propio óptimo y ECM2 el suyo. En ECM1 se espejan exactamente los
eventos detectados con ECM2, manteniendo el criterio de las figuras anteriores.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

from population_calibration import ROOT, FIG, plt, np
from individual_calibration import load_population
from figure_data import common_times, experimental, read_run
from mirror_real_ecm1 import ecm1
from mirror_real_ecm2 import COMMON, crossing_side, ecm2, mirror
from per_event_abe import COLORS, PLOT_STYLE, event_axes
from matplotlib.ticker import FuncFormatter

OUT = ROOT / "outputs/eventos_optimos_refinados"
SOURCE = ROOT / "outputs/calibracion_poblacional/resumen.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@plt.rc_context(PLOT_STYLE)
def plot(records, metric, mirrored, ymax):
    fig, ax = event_axes()
    events = np.arange(1, 20)
    key = "error_espejado" if mirrored else "error_original"
    for k, (layer, color) in enumerate(COLORS.items()):
        group = sorted((r for r in records if r["capa"] == layer and r["metrica"] == metric),
                       key=lambda r: r["evento"])
        assert [r["evento"] for r in group] == list(events)
        ax.bar(events+(k-1)*.25, [r[key] for r in group], width=.235, color=color,
               label=f"Capa {layer}", zorder=3)
    ax.set(xticks=events, xlim=(.35, 19.65), ylim=(0, ymax), xlabel="Evento",
           ylabel=f"ECM {metric} [m²]")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}".replace(".", ",")))
    ax.grid(axis="y", color="#e6e5e0", linewidth=.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper center", ncol=3, frameon=False)
    name = f"errores-por-evento-ABE-ecm{metric}" + ("-espejada" if mirrored else "")
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=160, bbox_inches="tight", pad_inches=.08)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plots-only", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    population = json.loads(SOURCE.read_text())
    provenance = {"population_sha256": sha(SOURCE), "jar_sha256": sha(ROOT / "target/tp5.jar"),
                  "data_sha256": {p.name: sha(p) for p in sorted((ROOT / "data").glob("*.txt"))},
                  "options": COMMON,
                  "mirror": "Reflexión de cada trayectoria experimental sobre su recta inicio-fin; "
                            "solo cruces de lado opuesto detectados con el nuevo óptimo ECM2; "
                            "mismos eventos reflejados en ECM1 y ECM2, sin recalibrar."}
    if args.plots_only:
        metadata = json.loads((OUT / "parametros.json").read_text())
        if metadata["procedencia"] != provenance:
            raise ValueError("Cambió la procedencia; regenerar sin --plots-only")
        with (OUT / "por_evento.csv").open() as f:
            records = list(csv.DictReader(f))
        for r in records:
            for key in ("evento", "metrica"):
                r[key] = int(r[key])
            for key in ("error_original", "error_espejado"):
                r[key] = float(r[key])
    else:
        records, summary, reflected_events = [], {}, {}
        for layer in COLORS:
            reference = load_population(layer)
            summary[layer] = {}
            # Primero ECM2: sus decisiones de espejo también se aplican a ECM1.
            for metric in (2, 1):
                optimum = population[layer][metric-1]
                pair = optimum["p1"], optimum["p2"]
                folder = OUT / "datos" / layer / f"ecm{metric}"
                subprocess.run(["java", "-cp", "target/tp5.jar",
                                "ar.edu.itba.sds.tp5.analysis.AnalysisMain", "baseline",
                                "--layer", layer, "--p1", str(pair[0]), "--p2", str(pair[1]),
                                "--out", str(folder)] + COMMON, cwd=ROOT, check=True)
                if metric == 2:
                    reflected_events[layer] = []
                for event in range(1, 20):
                    header, run = read_run(folder / f"evento_{event:02d}.txt")
                    real = experimental(ROOT / "data", header)
                    if metric == 2:
                        _, a, b = common_times(*real)
                        valid = np.isfinite(run[:, [1, 2, 5, 6]]).all(axis=1)
                        opposite = crossing_side(a, b)*crossing_side(run[valid, 1:3], run[valid, 5:7]) < 0
                        if opposite:
                            reflected_events[layer].append(event)
                    use_mirror = event in reflected_events[layer]
                    reflected = [mirror(track) for track in real]
                    for original, transformed in zip(real, reflected):
                        np.testing.assert_allclose(transformed[[0, -1]], original[[0, -1]], atol=1e-12)
                        np.testing.assert_allclose(mirror(transformed), original, atol=1e-12)
                    used = reflected if use_mirror else real
                    if metric == 1:
                        before, counts = ecm1(real, run, float(header["dt_exp"]))
                        after, new_counts = ecm1(used, run, float(header["dt_exp"]))
                        assert counts == new_counts
                    else:
                        before, after = ecm2(real, run), ecm2(used, run)
                    np.testing.assert_allclose(before, reference[pair][event-1, metric-1], atol=2e-6, rtol=0)
                    assert np.isfinite([before, after]).all() and min(before, after) >= 0
                    if not use_mirror:
                        assert before == after
                    records.append(dict(capa=layer, metrica=metric, evento=event,
                                        p1=pair[0], p2=pair[1], espejada=use_mirror,
                                        error_original=before, error_espejado=after))
                group = [r for r in records if r["capa"] == layer and r["metrica"] == metric]
                mean = float(np.mean([r["error_original"] for r in group]))
                np.testing.assert_allclose(mean, optimum["mean"][metric-1], atol=2e-6, rtol=0)
                summary[layer][f"ecm{metric}"] = dict(p1=pair[0], p2=pair[1], error_original=mean,
                    error_espejado=float(np.mean([r["error_espejado"] for r in group])),
                    eventos_espejados=reflected_events[layer])
        with (OUT / "por_evento.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        metadata = dict(procedencia=provenance, resumen=summary)
        (OUT / "parametros.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n")
    for metric in (1, 2):
        # La misma escala en el original y el espejado; ninguna barra queda recortada.
        ymax = 1.2*max(r[key] for r in records if r["metrica"] == metric
                      for key in ("error_original", "error_espejado"))
        for mirrored in (False, True):
            plot(records, metric, mirrored, ymax)
    print(json.dumps(metadata["resumen"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
