#!/usr/bin/env python3
"""Analiza exclusivamente una corrida nueva de per_pedestrian_abe.sh; no escribe en outputs/ped ni en presentación.

Uso: MPLCONFIGDIR=/tmp/tp5-matplotlib .venv/bin/python scripts/graph_gen/per_pedestrian_abe.py CARPETA
Los mínimos se eligen por ECM de evento, con interacción entre los peatones, para cada métrica por separado.
"""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from per_pedestrian import CALIBS, CALIB_SHORT, COMMA, METRICS, Grid, check_diagonal, fig_two_vs_four, num

LAYERS = {"A": (110, "t_a; ℓ"), "B": (90, "t_a; k"), "E": (72, "a; b")}
COLORS = {"A": "#0072B2", "B": "#E69F00", "E": "#009E73"}
COMMON = ["--data", "data", "--model", "sfm", "--integrator", "beeman", "--dt-div", "64",
          "--v0-frames", "5", "--delta-a", "0.1", "--rho", "0.9", "--trim", "on",
          "--trim-deg", "45", "--trim-persist", "5", "--trim-half", "2", "--trim-target", "common",
          "--trim-shared", "on", "--trim-shared-x", "1.5"]


def parameters(grid, indices):
    return [float(v) for i in indices for v in grid.pairs[i]]


def pair_text(values):
    return f"({num(values[0], '{:g}')}; {num(values[1], '{:g}')})"


def validate(folder, grids):
    evidence = {}
    for layer, grid in grids.items():
        n = LAYERS[layer][0]
        path = folder / f"grid_ped_{layer}.txt"
        rows = sum(1 for line in path.read_text().splitlines() if line and not line.startswith("#"))
        if rows != 19 * n * n or len(grid.pairs) != n or list(grid.events) != list(range(1, 20)):
            raise ValueError(f"{layer}: cantidad de combinaciones o eventos incorrecta")
        diagonal = check_diagonal(grid, folder / f"grid_{layer}.txt")
        if diagonal is None or diagonal > 1e-6:
            raise ValueError(f"{layer}: la diagonal no reproduce la grilla compartida: {diagonal}")
        for metric in METRICS:
            if not np.isfinite(grid.err[metric]).all():
                raise ValueError(f"{layer}/{metric}: errores no finitos")
            _, errors = grid.calibrate(metric)
            if np.any(errors["ind4"] > errors["ind2"] + 1e-12):
                raise ValueError("El mínimo con 4 parámetros supera al de 2 parámetros")
            if np.any(errors["ind2"] > errors["pob2"] + 1e-12):
                raise ValueError("El mínimo individual supera al poblacional compartido")
            if errors["pob4"].mean() > errors["pob2"].mean() + 1e-12:
                raise ValueError("El mínimo poblacional de 4 parámetros supera al de 2")
        evidence[layer] = {"eventos": 19, "pares": n, "corridas_por_peaton": rows, "diferencia_diagonal": diagonal}
    return evidence


def verify_runs(folder, grids, results):
    """Repite los cuatro óptimos en el evento de mayor ganancia, por capa y métrica (24 corridas)."""
    checks = []
    for layer, grid in grids.items():
        for metric, col in (("ecm1", 2), ("ecm2", 4)):
            indices, errors = results[layer][metric]
            k = int(np.argmax(errors["ind2"] - errors["ind4"]))
            event = int(grid.events[k])
            for calib in CALIBS:
                p = parameters(grid, indices[calib][k])
                out = folder / "verificacion" / layer / metric / calib
                args = ["java", "-cp", str(folder / "tp5.jar"), "ar.edu.itba.sds.tp5.analysis.AnalysisMain",
                        "run", "--event", str(event), "--layer", layer, "--p1", str(p[0]), "--p2", str(p[1]),
                        "--p1-ped2", str(p[2]), "--p2-ped2", str(p[3]), "--out", str(out)] + COMMON
                subprocess.run(args, check=True, stdout=subprocess.DEVNULL)
                row = next(l.split() for l in (out / "ecm.txt").read_text().splitlines() if l.startswith("E "))
                observed, expected = float(row[col]), float(errors[calib][k])
                if abs(observed - expected) > 1e-6:
                    raise ValueError(f"Óptimo no reproducible: {layer}/{metric}/{calib}: {observed} vs {expected}")
                checks.append({"capa": layer, "metrica": metric, "calibracion": calib, "evento": event,
                               "esperado": expected, "observado": observed})
    return checks


def write_tables(folder, grids, results, evidence):
    lines = ["# Calibración compartida y por peatón: A, B y E", "",
             "Experimento nuevo: todas las grillas y la línea base se calcularon de nuevo. No se reutilizan resultados anteriores.", "",
             "SFM, Beeman, Δt = Δt_exp/64, v inicial = ajuste lineal de 5 cuadros (no rapidez deseada), δ_a = 0,1 m, "
             "ρ = 0,9 m para A/B; recorte D(45°), persistencia 5, semiventana 2, target común y tramo compartido X = 1,5 m. "
             "En E, a es longitud del centro a la punta y b es semiancho/radio trasero; cada peatón ve el huevo real del otro.", "",
             "Grillas: A, t_a = 0,5…5 cada 0,5 y ℓ = 0…2,5 cada 0,25 (110 pares); "
             "B, igual t_a y k = 0…4 cada 0,5 (90 pares); E, a = 0,5…6 cada 0,5 y b = 0,25…0,5 cada 0,05 (72 pares).", "",
             "- pob. 2p: un par para ambos peatones y todos los eventos.",
             "- pob. 4p: un par por lado, mantenido en todos los eventos.",
             "- ind. 2p: un par por evento, compartido por los peatones.",
             "- ind. 4p: dos pares por evento, uno por peatón.", "",
             "Se minimiza el ECM promedio de los dos peatones, simulados juntos, dentro de la grilla. "
             "ECM1 excluyente y ECM2 se optimizan por separado: sus barras no necesariamente usan los mismos parámetros. "
             "Los empates se resuelven por orden creciente de los parámetros. Son errores de entrenamiento, no de validación. "
             "Las barras de error son ±s/√19, no intervalos del 95%; los mínimos en el borde no garantizan un óptimo fuera de la grilla.", "",
             "## Promedios de los 19 eventos (m²)", "",
             "| Capa | Métrica | pob. 2p | pob. 4p | ind. 2p | ind. 4p | Mejora pob. 4p vs 2p | Mejora ind. 4p vs 2p |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    records = []
    for layer, grid in grids.items():
        for metric, (name, _, _) in METRICS.items():
            indices, errors = results[layer][metric]
            means = {c: float(errors[c].mean()) for c in CALIBS}
            gains = [100 * (1 - means[s + "4"] / means[s + "2"]) for s in ("pob", "ind")]
            lines.append(f"| {layer} | {name} | " + " | ".join(num(means[c], "{:.4f}") for c in CALIBS)
                         + " | " + " | ".join(num(g, "{:.1f}") + "%" for g in gains) + " |")
            for calib in CALIBS:
                for k, event in enumerate(grid.events):
                    i, j = indices[calib][k]
                    records.append([layer, metric, calib, int(event), *parameters(grid, (i, j)),
                                    float(errors[calib][k]), bool(grid.contact[k, i, j]), float(grid.dmin[k, i, j]),
                                    bool(grid.on_edge(i) or grid.on_edge(j))])
    lines += ["", "## Parámetros poblacionales óptimos", "",
              "| Capa | Métrica | Parámetros | Par compartido (pob. 2p) | Izquierdo (pob. 4p) | Derecho (pob. 4p) |",
              "|---|---|---|---|---|---|"]
    for layer, grid in grids.items():
        for metric, (name, _, _) in METRICS.items():
            indices, _ = results[layer][metric]
            common = parameters(grid, indices["pob2"][0])
            separate = parameters(grid, indices["pob4"][0])
            lines.append(f"| {layer} | {name} | {LAYERS[layer][1]} | {pair_text(common)} | "
                         f"{pair_text(separate)} | {pair_text(separate[2:])} |")
    lines += ["", "## Contactos y límites de la grilla", "",
              "Cada celda muestra eventos con contacto / eventos con algún parámetro en el borde de la grilla. "
              "Contacto significa solape de los discos físicos de los peatones, no de sus huevos de elusión.", "",
              "| Capa | Métrica | pob. 2p | pob. 4p | ind. 2p | ind. 4p |", "|---|---|---:|---:|---:|---:|"]
    for layer, grid in grids.items():
        for metric, (name, _, _) in METRICS.items():
            indices, _ = results[layer][metric]
            cells = []
            for calib in CALIBS:
                ij = indices[calib]
                contacts = sum(int(grid.contact[k, i, j]) for k, (i, j) in enumerate(ij))
                edges = sum(grid.on_edge(i) or grid.on_edge(j) for i, j in ij)
                cells.append(f"{contacts} / {edges}")
            lines.append(f"| {layer} | {name} | " + " | ".join(cells) + " |")
    lines += ["", "## Resultados por evento", "",
              "Todos los pares óptimos, ECM, contactos, distancia mínima y condición de borde están en `optimos.csv`.", "",
              "## Verificación", "",
              "Grillas completas sin faltantes; diagonal idéntica a la grilla compartida (tolerancia 10⁻⁶); "
              "mínimos con 4 parámetros no superiores a los de 2. Se repitieron 24 corridas de óptimos "
              "con el motor copiado en esta carpeta y reprodujeron los ECM. Detalles en `verificacion.json`.", "",
              "Comandos exactos: `comandos.txt`. Copia del motor: `tp5.jar`; hash: `motor.sha256`."]
    (folder / "resumen.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (folder / "optimos.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["capa", "metrica", "calibracion", "evento", "p1_izq", "p2_izq", "p1_der", "p2_der",
                         "ecm", "contacto", "d_min", "borde"])
        writer.writerows(records)


def summary_figure(grids, results, path):
    fig, axes = plt.subplots(1, 2, figsize=(17, 6.2), constrained_layout=True)
    for ax, (metric, (name, _, _)) in zip(axes, METRICS.items()):
        top = 0
        for s, layer in enumerate(grids):
            errors = results[layer][metric][1]
            means = np.array([errors[c].mean() for c in CALIBS])
            sem = np.array([errors[c].std(ddof=1) / np.sqrt(len(grids[layer].events)) for c in CALIBS])
            pos = np.arange(4) + (s - 1) * 0.25
            ax.bar(pos, means, 0.235, color=COLORS[layer], label=f"capa {layer}", zorder=2)
            ax.errorbar(pos, means, sem, fmt="none", ecolor="#252525", capsize=3, lw=1.2, zorder=3)
            top = max(top, float(max(means + sem)))
            for x, y, se in zip(pos, means, sem):
                ax.annotate(num(y), (x, y + se), xytext=(0, 6 + 12 * (s % 2)), textcoords="offset points",
                            ha="center", fontsize=10)
        ax.set_xticks(np.arange(4), [CALIB_SHORT[c] for c in CALIBS])
        ax.set_ylabel(f"⟨{name}⟩ (m²)")
        ax.yaxis.set_major_formatter(COMMA)
        ax.set_title(name)
        ax.set_ylim(0, top * 1.3)
        ax.grid(axis="y", color="#e6e5e0")
        ax.set_axisbelow(True)
    axes[0].legend(frameon=False)
    fig.savefig(path.with_suffix(".png"), dpi=160, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Uso: per_pedestrian_abe.py CARPETA_DEL_EXPERIMENTO_NUEVO")
    folder = Path(sys.argv[1])
    grids = {layer: Grid(folder / f"grid_ped_{layer}.txt") for layer in LAYERS}
    evidence = validate(folder, grids)
    results = {layer: {metric: grid.calibrate(metric) for metric in METRICS} for layer, grid in grids.items()}
    checks = verify_runs(folder, grids, results)
    (folder / "verificacion.json").write_text(json.dumps({"grillas": evidence, "corridas": checks}, indent=2) + "\n")
    write_tables(folder, grids, results, evidence)
    figs = folder / "figs"
    figs.mkdir(exist_ok=True)
    summary_figure(grids, results, figs / "resumen_ABE")
    for scope in ("pob", "ind"):
        for metric in METRICS:
            fig_two_vs_four(grids, results, scope, metric, figs / f"comparacion_{scope}_{metric}.png")
    manifest = {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in folder.glob("grid*.txt")}
    (folder / "grillas.sha256.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Verificados {sum(v['corridas_por_peaton'] for v in evidence.values())} casos y {len(checks)} repeticiones.")
    print(f"Resultados: {folder / 'resumen.md'} | gráficos: {figs}")


if __name__ == "__main__":
    main()
