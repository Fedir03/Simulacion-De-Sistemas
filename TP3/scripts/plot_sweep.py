"""Grafica el summary.csv de uno o más barridos de sweep.py.

Eje y: ⟨t90⟩, tiempo de ejecución o goles, con barras de un desvío estándar.
Una configuración fija (barrido sin --param) puede dibujarse como referencia
horizontal: su media como recta y ±σ como banda.

Ejemplos, desde la raíz del repositorio:

    python3 TP3/scripts/plot_sweep.py TP3/generated/sweeps/embudo_largo/summary.csv \\
        --xlabel 'Largo del embudo [m]' --reference TP3/generated/sweeps/vacia/summary.csv \\
        --reference-label 'Mesa vacía' --out TP3/generated/embudo_largo.png

    python3 TP3/scripts/plot_sweep.py TP3/generated/sweeps/runtime/summary.csv --y runtime \\
        --xlabel 'N' --out TP3/generated/runtime.png

Sin título embebido: el título va en el caption del informe o en la diapositiva.
"""
import argparse
import csv
import math
import sys

COLUMNS = {
    't90': ('t90_mean', 't90_std', r'$\langle t_{90} \rangle$ [s]'),
    'runtime': ('runtime_mean_s', 'runtime_std_s', 'Tiempo de ejecución [s]'),
    'goals': ('goals_mean', 'goals_std', r'$\langle N_g(t_{max}) \rangle$'),
}


def read_summary(path):
    with open(path, newline='', encoding='utf-8') as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError(f'{path}: sin filas')
    return rows


def series(rows, y):
    mean_key, std_key, _ = COLUMNS[y]
    points = []
    for row in rows:
        mean, std = float(row[mean_key]), float(row[std_key])
        if row['value'] == '' or not math.isfinite(mean):
            continue
        points.append((float(row['value']), mean, std if math.isfinite(std) else 0.0, row))
    return sorted(points)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('summaries', nargs='+', help='summary.csv de sweep.py (uno por serie)')
    parser.add_argument('--labels', nargs='+', help='etiqueta de cada serie en la leyenda')
    parser.add_argument('--y', choices=COLUMNS, default='t90', help='magnitud graficada (t90)')
    parser.add_argument('--xlabel', required=True, help="etiqueta del eje x con unidades, ej. 'x [m]'")
    parser.add_argument('--ylabel', help='reemplaza la etiqueta del eje y')
    parser.add_argument('--reference', help='summary.csv de una configuración fija, dibujada como banda')
    parser.add_argument('--reference-label', default='Referencia')
    parser.add_argument('--logx', action='store_true')
    parser.add_argument('--logy', action='store_true')
    parser.add_argument('--out', required=True, help='figura de salida (.png, .pdf, .svg)')
    args = parser.parse_args(argv)
    if args.labels and len(args.labels) != len(args.summaries):
        parser.error('--labels necesita una etiqueta por summary')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    labeled = bool(args.labels) or bool(args.reference)
    for i, path in enumerate(args.summaries):
        points = series(read_summary(path), args.y)
        if not points:
            parser.error(f'{path}: no hay valores barridos con {args.y} finito')
        for x, _, _, row in points:
            if args.y == 't90' and int(row['reached_t90']) < int(row['realizations']):
                print(f'Aviso: {path} valor={x}: solo {row["reached_t90"]}/{row["realizations"]} '
                      f'realizaciones alcanzaron t90', file=sys.stderr)
        xs, means, stds, _ = zip(*points)
        label = args.labels[i] if args.labels else ('Configuración estudiada' if args.reference else None)
        ax.errorbar(xs, means, yerr=stds, marker='o', capsize=4, label=label)
    if args.reference:
        [row] = [row for row in read_summary(args.reference) if row['value'] == ''][:1] or [None]
        if row is None:
            parser.error(f'{args.reference}: se esperaba un barrido sin --param')
        mean_key, std_key, _ = COLUMNS[args.y]
        mean, std = float(row[mean_key]), float(row[std_key])
        ax.axhline(mean, color='0.3', ls='--', label=f'{args.reference_label} (±σ)')
        ax.axhspan(mean - std, mean + std, color='0.3', alpha=0.15, lw=0)
    ax.set_xlabel(args.xlabel)
    ax.set_ylabel(args.ylabel or COLUMNS[args.y][2])
    if args.logx:
        ax.set_xscale('log')
    if args.logy:
        ax.set_yscale('log')
    if labeled:
        ax.legend(loc='best')
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    print(f'Figura: {args.out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
