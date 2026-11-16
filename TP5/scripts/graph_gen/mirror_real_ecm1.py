#!/usr/bin/env python3
"""ECM1 con exactamente los eventos espejados de ECM2, sin volver a detectar el lado.

MPLCONFIGDIR=/tmp/tp5-matplotlib .venv/bin/python scripts/graph_gen/mirror_real_ecm1.py
Usa los parámetros y escala del gráfico original de ECM1 (excluyendo retiros).
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

from figure_data import experimental, read_run
from mirror_real_ecm2 import COLORS, COMMON, mirror, slide_plot
from per_event import best_rows
from pilot_analysis import load_grid


def ecm1(real, run, dt_exp):
    errors, counts = [], []
    for i, track in enumerate(real):
        # El motor imprime cuatro filas por intervalo experimental.
        indices = np.rint(track[:, 0] / dt_exp).astype(int) * 4
        simulated = np.full((len(indices), 2), np.nan)
        available = indices < len(run)  # El archivo puede terminar cuando ambos se retiran.
        simulated[available] = run[indices[available], 1 + 4*i:3 + 4*i]
        valid = np.isfinite(simulated).all(axis=1)
        errors.append(float(np.sum((track[valid, 1:] - simulated[valid])**2, axis=1).mean()))
        counts.append(int(valid.sum()))
    return float(np.mean(errors)), counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("outputs/mirror_real_ecm1"))
    parser.add_argument("--ecm2-metadata", type=Path, default=Path("outputs/mirror_real_ecm2/parametros.json"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    source = json.loads(args.ecm2_metadata.read_text())
    records, summary = [], {}
    for layer in COLORS:
        fixed = source["resumen"][layer]["eventos_espejados"]
        p1, p2, rows = best_rows(load_grid(Path("outputs/pilot") / f"grid_{layer}.txt"), 3)
        folder = args.out / "datos" / layer
        subprocess.run(["java", "-cp", "target/tp5.jar", "ar.edu.itba.sds.tp5.analysis.AnalysisMain",
                        "baseline", "--layer", layer, "--p1", str(p1), "--p2", str(p2),
                        "--out", str(folder)] + COMMON, check=True)
        for row in rows:
            event = int(row[2])
            header, run = read_run(folder / f"evento_{event:02d}.txt")
            real = experimental(Path("data"), header)
            dt = float(header["dt_exp"])
            original, counts = ecm1(real, run, dt)
            np.testing.assert_allclose(original, row[3], atol=2e-6, rtol=0)
            np.testing.assert_array_equal(counts, row[6:8])
            used = [mirror(t) for t in real] if event in fixed else real
            corrected, corrected_counts = ecm1(used, run, dt)
            assert counts == corrected_counts
            if event not in fixed:
                assert original == corrected
            else:
                for i, track in enumerate(used, 1):
                    np.savetxt(folder / f"real_espejada_{event:02d}_peaton{i}.txt", track,
                               header="t x y", fmt="%.12f")
            records.append(dict(evento=event, capa=layer, p1=float(p1), p2=float(p2),
                                espejada=event in fixed, ecm1_original=original, ecm1_corregido=corrected,
                                N1_1=counts[0], N1_2=counts[1]))
        at = [r for r in records if r["capa"] == layer]
        assert [r["evento"] for r in at if r["espejada"]] == fixed
        summary[layer] = {"parametros": [float(p1), float(p2)], "eventos_espejados": fixed,
                          "ecm1_original": float(np.mean([r["ecm1_original"] for r in at])),
                          "ecm1_corregido": float(np.mean([r["ecm1_corregido"] for r in at]))}
    with (args.out / "comparacion.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    metadata = {"eventos_fijos_desde": str(args.ecm2_metadata),
                "fuente_sha256": hashlib.sha256(args.ecm2_metadata.read_bytes()).hexdigest(),
                "espejo": source["espejo"], "metrica": "ECM1 excluyendo retiros; mismos instantes y N1 que original",
                "calibracion": "óptimos poblacionales originales de ECM1, sin recalibrar",
                "resumen": summary}
    (args.out / "parametros.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    slide_plot(records, args.out, metric="ecm1")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
