#!/usr/bin/env python3
"""Detecta cruces opuestos y compara ECM2 con el esquive real reflejado.

Uso: MPLCONFIGDIR=/tmp/tp5-matplotlib .venv/bin/python scripts/graph_gen/mirror_real_ecm2.py
Mantiene los óptimos poblacionales originales A/B/E, sin recalibrarlos.
"""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

from figure_data import common_times, experimental, read_run
from per_event import best_rows
from per_event_abe import PLOT_STYLE, event_axes
from pilot_analysis import load_grid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "animation"))
from events_3_6_ecm2 import COMMON

COLORS = {"A": "#0072B2", "B": "#E69F00", "E": "#D55E00"}


@plt.rc_context(PLOT_STYLE)
def slide_plot(records, out, metric="ecm2"):
    """Mismo formato y límites del gráfico original de la métrica en la presentación."""
    column = {"ecm1": 3, "ecm2": 5}[metric]
    fig, ax = event_axes()
    events = np.arange(1, 20)
    original_highest = 0
    for k, (layer, color) in enumerate(COLORS.items()):
        _, _, original = best_rows(load_grid(Path("outputs/pilot") / f"grid_{layer}.txt"), column)
        original_highest = max(original_highest, float(original[:, column].max()))
        at = sorted((r for r in records if r["capa"] == layer), key=lambda r: int(r["evento"]))
        assert [int(r["evento"]) for r in at] == list(events)
        values = np.array([float(r[f"{metric}_corregido"]) for r in at])
        assert np.isfinite(values).all() and (values >= 0).all()
        ax.bar(events + (k - 1) * .25, values, width=.235, color=color, label=f"Capa {layer}", zorder=3)
    ax.set_xticks(events)
    ax.set_xlim(.35, 19.65)
    ax.set_ylim(0, original_highest * 1.20)
    ax.set_xlabel("Evento")
    ax.set_ylabel(f"ECM {metric[-1]} [m²]")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}".replace(".", ",")))
    ax.grid(axis="y", color="#e6e5e0", linewidth=.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper center", ncol=3, frameon=False)
    for suffix in ("pdf", "png"):
        target = out / f"errores_por_evento_ABE_{metric}_espejada.{suffix}"
        fig.savefig(target, dpi=160)
        print(target)
    print(f"Escala original conservada: y = [0, {ax.get_ylim()[1]:.7f}] m²")
    plt.close(fig)


def mirror(track):
    """Reflexión ortogonal sobre la recta inicio-fin: conserva ambos extremos."""
    origin = track[0, 1:]
    direction = track[-1, 1:] - origin
    direction = direction / np.linalg.norm(direction)
    offset = track[:, 1:] - origin
    result = track.copy()
    result[:, 1:] = origin + 2 * np.outer(offset @ direction, direction) - offset
    return result


def crossing_side(a, b):
    """Separación lateral firmada al máximo acercamiento, criterio del proyecto."""
    k = np.argmin(np.sum((a - b) ** 2, axis=1))
    return float(a[k, 1] - b[k, 1])


def ecm2(real, run):
    values = []
    for i, track in enumerate(real):
        simulated = run[:, 1 + 4 * i:3 + 4 * i]
        simulated = simulated[np.isfinite(simulated).all(axis=1)]
        distances = np.sum((track[:, None, 1:] - simulated[None, :, :]) ** 2, axis=2)
        values.append(float(distances.min(axis=1).mean()))
    return float(np.mean(values))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("outputs/mirror_real_ecm2"))
    parser.add_argument("--plot-only", action="store_true", help="Genera el gráfico de diapositiva desde comparacion.csv")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.plot_only:
        with (args.out / "comparacion.csv").open(encoding="utf-8") as f:
            slide_plot(list(csv.DictReader(f)), args.out)
        return
    records, checks, pairs = [], [], {}
    for layer in COLORS:
        p1, p2, rows = best_rows(load_grid(Path("outputs/pilot") / f"grid_{layer}.txt"), 5)
        pairs[layer] = [float(p1), float(p2)]
        folder = args.out / "datos" / layer
        subprocess.run(["java", "-cp", "target/tp5.jar", "ar.edu.itba.sds.tp5.analysis.AnalysisMain",
                        "baseline", "--layer", layer, "--p1", str(p1), "--p2", str(p2),
                        "--out", str(folder)] + COMMON, check=True)
        for row in rows:
            event = int(row[2])
            header, run = read_run(folder / f"evento_{event:02d}.txt")
            real = experimental(Path("data"), header)
            _, a, b = common_times(*real)
            real_side = crossing_side(a, b)
            valid = np.isfinite(run[:, [1, 2, 5, 6]]).all(axis=1)
            sim_side = crossing_side(run[valid, 1:3], run[valid, 5:7])
            opposite = real_side * sim_side < 0
            reflected = [mirror(track) for track in real]
            for original, transformed in zip(real, reflected):
                np.testing.assert_allclose(transformed[[0, -1]], original[[0, -1]], atol=1e-12)
                np.testing.assert_allclose(mirror(transformed), original, atol=1e-12)
            original_error = ecm2(real, run)
            if abs(original_error - row[5]) > 2e-6:
                raise ValueError(f"No reproduce grilla {layer}/{event}: {original_error} vs {row[5]}")
            used = reflected if opposite else real
            corrected_error = ecm2(used, run)
            records.append(dict(evento=event, capa=layer, p1=float(p1), p2=float(p2),
                                lado_real_m=real_side, lado_sim_m=sim_side, espejada=bool(opposite),
                                ecm2_original=original_error, ecm2_corregido=corrected_error))
            if opposite:
                _, ma, mb = common_times(*reflected)
                if crossing_side(ma, mb) * sim_side <= 0:
                    raise ValueError(f"El espejo no invirtió el cruce: {layer}/{event}")
                checks.append((layer, event, real, reflected, run))
                for i, track in enumerate(reflected, 1):
                    np.savetxt(folder / f"real_espejada_{event:02d}_peaton{i}.txt", track,
                               header="t x y", fmt="%.12f")

    with (args.out / "comparacion.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    summary = {layer: {"parametros": pairs[layer],
                      "eventos_espejados": [r["evento"] for r in records if r["capa"] == layer and r["espejada"]],
                      "ecm2_original": float(np.mean([r["ecm2_original"] for r in records if r["capa"] == layer])),
                      "ecm2_corregido": float(np.mean([r["ecm2_corregido"] for r in records if r["capa"] == layer]))}
               for layer in COLORS}
    metadata = {"criterio_lado": "signo(y1-y2) en el máximo acercamiento de cada corrida",
                "espejo": "cada peatón real respecto de su recta inicio-fin en la ventana común",
                "ecm2": "media de distancias cuadradas al punto simulado más cercano; promedio de peatones y luego eventos",
                "calibracion": "óptimos poblacionales originales, sin recalibrar; espejo sólo con lado opuesto",
                "resumen": summary}
    (args.out / "parametros.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    slide_plot(records, args.out)

    plt.rcParams.update({"font.size": 14, "axes.labelsize": 17, "pdf.fonttype": 42})
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True, constrained_layout=True)
    for ax, layer in zip(axes, COLORS):
        at = [r for r in records if r["capa"] == layer]
        x = np.array([r["evento"] for r in at])
        ax.bar(x - .19, [r["ecm2_original"] for r in at], .37, color=COLORS[layer], alpha=.35, label="Real original")
        ax.bar(x + .19, [r["ecm2_corregido"] for r in at], .37, color=COLORS[layer], label="Real con esquives espejados (*)")
        for r in at:
            if r["espejada"]:
                ax.annotate("*", (r["evento"], max(r["ecm2_original"], r["ecm2_corregido"])),
                            xytext=(0, 3), textcoords="offset points", ha="center", fontsize=18)
        ax.set_ylabel(f"Capa {layer} · ECM2 [m²]")
        ax.set_ylim(0, max(max(r["ecm2_original"], r["ecm2_corregido"]) for r in at) * 1.22)
        ax.grid(axis="y", alpha=.2)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    axes[0].legend(frameon=False, ncol=2)
    axes[-1].set_xticks(range(1, 20))
    axes[-1].set_xlabel("Evento (*: lado de cruce opuesto; se espejó la trayectoria real)")
    for suffix in ("png", "pdf"):
        fig.savefig(args.out / f"comparacion_ecm2_espejada.{suffix}", dpi=170)
    plt.close(fig)

    # Evidencia visual de cada detección, con los dos peatones y los ejes usados.
    fig, axes = plt.subplots(len(checks), 1, figsize=(12, 3 * len(checks)), squeeze=False, constrained_layout=True)
    for ax, (layer, event, real, reflected, run) in zip(axes[:, 0], checks):
        for i in range(2):
            style = "-" if i == 0 else "--"
            ax.plot(real[i][:, 1], real[i][:, 2], style, color=".55", label="Real original" if i == 0 else None)
            ax.plot(reflected[i][:, 1], reflected[i][:, 2], style, color="black", label="Real espejada" if i == 0 else None)
            ax.plot(run[:, 1 + 4*i], run[:, 2 + 4*i], style, color=COLORS[layer], label=f"Capa {layer}" if i == 0 else None)
            ax.plot(real[i][[0, -1], 1], real[i][[0, -1], 2], ":", color=".75")
        ax.set_aspect("equal", adjustable="datalim")
        ax.set_xlabel(f"Evento {event} · capa {layer} · x [m]")
        ax.set_ylabel("y [m]")
        ax.legend(ncol=3, fontsize=11)
    fig.savefig(args.out / "trayectorias_detectadas.png", dpi=150)
    plt.close(fig)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
