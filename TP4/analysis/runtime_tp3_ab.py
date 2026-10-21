"""Comparación de las tandas A y B de la medición de tiempos del TP3 (D12).

Lee <a>/runs.csv y <b>/runs.csv sin modificarlos y escribe <out>/comparacion_A_B.csv con, por N:
mediana de A y de B, diferencia porcentual de B respecto de A, p25-p75 de cada una, el cociente B/A de la
misma semilla (mediana, mínimo y máximo) y si los eventos coinciden semilla a semilla. Imprime si cada
diferencia de medianas queda dentro o fuera de la tolerancia (5 %, la regla de la tanda B).

Uso (desde TP4/):
    .venv/Scripts/python analysis/runtime_tp3_ab.py [--a outputs/runtime_tp3] [--b outputs/runtime_tp3_b]
        [--out outputs/runtime_tp3_ab] [--tol 0.05]
"""
import argparse
import statistics
import sys
from pathlib import Path

from runtime_tp3 import MODULE, quartiles, read_runs, write_csv


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--a', type=Path, default=MODULE / 'outputs' / 'runtime_tp3', help='carpeta de la tanda A')
    parser.add_argument('--b', type=Path, default=MODULE / 'outputs' / 'runtime_tp3_b', help='carpeta de la tanda B')
    parser.add_argument('--out', type=Path, default=MODULE / 'outputs' / 'runtime_tp3_ab')
    parser.add_argument('--tol', type=float, default=0.05, help='tolerancia relativa entre medianas')
    args = parser.parse_args(argv)

    a_dir, b_dir, out = args.a.resolve(), args.b.resolve(), args.out.resolve()
    if out in (a_dir, b_dir):
        parser.error('la salida no puede ser una carpeta de entrada')
    runs_a = {(r['n'], r['seed']): r for r in read_runs(a_dir / 'runs.csv')}
    runs_b = {(r['n'], r['seed']): r for r in read_runs(b_dir / 'runs.csv')}
    if runs_a.keys() != runs_b.keys():
        sys.exit(f'A y B no tienen los mismos pares (N, semilla): solo A {sorted(runs_a.keys() - runs_b.keys())}, '
                 f'solo B {sorted(runs_b.keys() - runs_a.keys())}')

    rows = []
    for n in sorted({n for n, _ in runs_a}):
        keys = sorted(k for k in runs_a if k[0] == n)
        a = [runs_a[k]['runtime_s'] for k in keys]
        b = [runs_b[k]['runtime_s'] for k in keys]
        ratios = [tb / ta for ta, tb in zip(a, b)]
        a25, a50, a75 = quartiles(a)
        b25, b50, b75 = quartiles(b)
        diff = b50 / a50 - 1
        same_events = all(runs_a[k]['events'] == runs_b[k]['events'] for k in keys)
        rows.append([n, len(keys), a50, b50, round(100 * diff, 3), a25, a75, b25, b75,
                     statistics.median(ratios), min(ratios), max(ratios), same_events, abs(diff) <= args.tol])

    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / 'comparacion_A_B.csv',
              ['n', 'semillas', 'mediana_A_s', 'mediana_B_s', 'dif_pct', 'p25_A_s', 'p75_A_s', 'p25_B_s', 'p75_B_s',
               'cociente_BA_mediana', 'cociente_BA_min', 'cociente_BA_max', 'eventos_iguales', f'dentro_{args.tol:.0%}'],
              rows,
              comment=f'A: {a_dir / "runs.csv"}; B: {b_dir / "runs.csv"}; dif_pct = 100 (mediana_B / mediana_A - 1); '
                      f'percentiles: statistics.quantiles(method="inclusive"); cociente B/A por semilla')

    print(f'{"N":>4} {"mediana A [s]":>14} {"mediana B [s]":>14} {"dif %":>7} {"p25-p75 A [s]":>20} {"p25-p75 B [s]":>20}'
          f' {"B/A med (min-max)":>24}  eventos')
    for n, k, a50, b50, diff, a25, a75, b25, b75, rmed, rmin, rmax, same, inside in rows:
        print(f'{n:>4} {a50:>14.4f} {b50:>14.4f} {diff:>+7.2f} {f"{a25:.4f}-{a75:.4f}":>20} {f"{b25:.4f}-{b75:.4f}":>20}'
              f' {f"{rmed:.4f} ({rmin:.4f}-{rmax:.4f})":>24}  {"iguales" if same else "DISTINTOS"}'
              f'  {"dentro" if inside else "FUERA"} del {args.tol:.0%}')
    print(f'\nSalida: {out / "comparacion_A_B.csv"}')


if __name__ == '__main__':
    main()
