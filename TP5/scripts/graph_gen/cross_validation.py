#!/usr/bin/env python3
"""Tarea 9: validación cruzada de D8 sobre las grillas del piloto, sin volver a simular.

14 eventos de entrenamiento y 5 de validación al azar, con semilla fija y las mismas particiones para todas las capas.
La zona exploratoria de F se informa aparte: se eligió después de ver los 19 eventos, así que su validación no es limpia.
Uso: python scripts/graph_gen/cross_validation.py [carpeta del piloto]
"""
import sys
from collections import Counter
from pathlib import Path

import numpy as np

SEED = 20261116
N_PARTITIONS = 5000  # 11/11: 1000 no pasaba el control de convergencia con el recorte
N_EVENTS = 19
N_TRAIN = 14
METRICS = {"ecm1_excl": 3, "ecm1_relleno": 4, "ecm2": 5}


def error_matrix(rows, column):
    """Devuelve los pares y una matriz (par, evento) con el error de cada par en cada evento."""
    pairs = sorted({(r[0], r[1]) for r in rows})
    events = sorted({int(r[2]) for r in rows})
    index = {p: k for k, p in enumerate(pairs)}
    matrix = np.full((len(pairs), len(events)), np.nan)
    for r in rows:
        matrix[index[(r[0], r[1])], events.index(int(r[2]))] = r[column]
    if np.isnan(matrix).any():
        raise ValueError("La grilla no tiene todos los pares en todos los eventos")
    return pairs, matrix


def partitions(n_partitions=N_PARTITIONS, n_events=N_EVENTS, n_train=N_TRAIN, seed=SEED):
    """Matriz booleana (partición, evento): True = entrenamiento."""
    rng = np.random.default_rng(seed)
    out = np.zeros((n_partitions, n_events), dtype=bool)
    for k in range(n_partitions):
        out[k, rng.permutation(n_events)[:n_train]] = True
    return out


def evaluate(matrix, parts):
    """Calibra en entrenamiento y mide en validación, partición por partición."""
    train_error = np.zeros(len(parts))
    validation_error = np.zeros(len(parts))
    chosen = np.zeros(len(parts), dtype=int)
    for k, train in enumerate(parts):
        means = matrix[:, train].mean(axis=1)
        chosen[k] = int(np.argmin(means))
        train_error[k] = means[chosen[k]]
        validation_error[k] = matrix[chosen[k], ~train].mean()
    return train_error, validation_error, chosen


def evaluate_on_all(matrix):
    """Control de la sección 7: con entrenamiento = validación = todos, tiene que dar el error de (b)."""
    train = np.ones(matrix.shape[1], dtype=bool)
    means = matrix[:, train].mean(axis=1)
    chosen = int(np.argmin(means))
    return chosen, float(matrix[chosen, train].mean())


def report(name, rows, parts, results):
    from pilot_analysis import surface
    grid = np.array(rows, dtype=float)
    for metric, column in METRICS.items():
        pairs, matrix = error_matrix(rows, column)
        train, val, chosen = evaluate(matrix, parts)
        full, on_all = evaluate_on_all(matrix)
        expected = surface(grid, column)[2].min()      # el error de (b), por otro camino
        same = int((chosen == full).sum())
        common = Counter(chosen.tolist()).most_common(3)
        tops = ", ".join(f"({pairs[k][0]:g}; {pairs[k][1]:g}) {n}" for k, n in common)
        print(f"{name} | {metric} | par 19 eventos ({pairs[full][0]:g}; {pairs[full][1]:g}) E={matrix[full].mean():.4f} | "
              f"entren. {train.mean():.4f} | valid. {val.mean():.4f} +- {val.std(ddof=1):.4f} | coincide {same}/{len(parts)} | mas elegidos: {tops}")
        # Controles de la sección 7: la media de validación con N/5 y N/2 particiones cambia menos de 1% contra N
        n = len(val)
        marks = (n // 5, n // 2, n)
        conv = {m: val[:m].mean() for m in marks}
        changes = [abs(conv[m] - conv[n]) / conv[n] * 100 for m in marks[:2]]
        first_1000 = int((chosen[:1000] == full).sum()) if n >= 1000 else same
        print(f"    controles: media valid. {marks[0]}/{marks[1]}/{marks[2]} = {conv[marks[0]]:.4f} {conv[marks[1]]:.4f} {conv[marks[2]]:.4f} "
              f"(cambio contra {n}: {changes[0]:.2f}%, {changes[1]:.2f}%; pasa <1%: {max(changes) < 1}) | coincide en las primeras 1000: {first_1000}/1000 | "
              f"entren.<=valid.: {train.mean() <= val.mean()} | entren.=valid. da E(19): {abs(on_all - expected) < 1e-12}")
        results[(name, metric)] = val


def main():
    pilot = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/pilot")
    parts = partitions()
    from pilot_analysis import load_grid
    results = {}
    print(f"semilla {SEED}, {N_PARTITIONS} particiones, {N_TRAIN} entrenamiento y {N_EVENTS - N_TRAIN} validacion, las mismas para todas las capas")
    print("\n===== Grilla OFICIAL (F con desempate metrico) =====")
    for name in "ABF":
        report(name, load_grid(pilot / f"grid_{name}.txt"), parts, results)
    print("\n===== Zona EXPLORATORIA de F (elegida post-hoc: su validacion NO es limpia) =====")
    report("F*", load_grid(pilot / "exploratoria" / "F_amplia.txt"), parts, results)
    print("\n===== Diferencias pareadas de validacion (mismas particiones): media +- desvio | particiones donde gana la primera =====")
    for metric in METRICS:
        for x, y in (("A", "B"), ("A", "F"), ("B", "F"), ("A", "F*"), ("B", "F*")):
            d = results[(x, metric)] - results[(y, metric)]
            print(f"{metric} {x}-{y}: {d.mean():+.4f} +- {d.std(ddof=1):.4f} | {int((d < 0).sum())}/{len(d)}")


if __name__ == "__main__":
    main()
