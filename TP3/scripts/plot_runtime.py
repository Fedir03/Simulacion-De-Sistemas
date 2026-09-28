"""Grafica media ± desvío muestral del tiempo de ejecución para el barrido de N."""
import argparse
import csv
import json
import shlex
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT/'generated/sweeps/runtime_tf30')
    args = parser.parse_args()
    meta = json.loads((args.data/'meta.json').read_text())
    if meta['time'] != 30 or meta['param'] != 'n':
        raise ValueError('Se requiere un barrido de N con tf = 30 s')
    with (args.data/'runs.csv').open() as source:
        runs = list(csv.DictReader(source))
    groups = {}
    for row in runs:
        if row['status'] != 'ok' or int(row['K']) != 0:
            raise ValueError('Todas las corridas deben ser exitosas y sin obstáculos')
        groups.setdefault(int(row['value']), []).append(float(row['runtime_s']))
    if any(len(values) < 10 for values in groups.values()):
        raise ValueError('Se necesitan al menos 10 realizaciones por N')
    ns = sorted(groups)
    means = [statistics.mean(groups[n]) for n in ns]
    stds = [statistics.stdev(groups[n]) for n in ns]

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 16, 'axes.spines.top': False, 'axes.spines.right': False})
    # Tamaño cercano al de la columna de la presentación (0.66 del ancho): una figura
    # más ancha se achica al insertarla y la letra queda ilegible al proyectar.
    fig, ax = plt.subplots(figsize=(7.0, 4.4), layout='constrained')
    ax.errorbar(ns, means, yerr=stds, fmt='o-', color='#3939B5',
                capsize=5, linewidth=1.8, markersize=6)
    ax.set(xlabel='N', ylabel='Tiempo de ejecución [s]', xticks=ns, ylim=(0, None))
    if len(ns) > 10:
        # Con muchos N (p. ej. saltos de 25) las etiquetas horizontales se pisan.
        ax.tick_params(axis='x', labelsize=13, labelrotation=45)
    ax.grid(alpha=.25)
    for ext in ('png', 'pdf'):
        fig.savefig(args.data/f'tiempo-ejecucion-vs-n.{ext}', dpi=220)
    plt.close(fig)
    lines = ['# Tiempo de ejecución en función de N', '',
             'Mesa sin obstáculos; tiempo absoluto final tf = 30 s, sin corte por t90. '
             '10 realizaciones por N, semillas 1–10; ejecución secuencial (--jobs 1).', '',
             'Se mide el tiempo de pared informado por el motor: inicialización del simulador '
             'y ciclo de eventos, incluida la escritura de los estados inicial y final. '
             'No incluye generación de partículas, arranque de Java ni lectura de la entrada. '
             'Registro de eventos desactivado. Los tiempos dependen del equipo y de su carga.', '',
             'Las barras son ± un desvío estándar muestral (denominador M−1), no el error de la media.', '',
             '| N | Realizaciones | Media [s] | Desvío estándar [s] |',
             '|---:|---:|---:|---:|']
    for n, mean, std in zip(ns, means, stds):
        lines.append(f'| {n} | {len(groups[n])} | {mean:.4f} | {std:.4f} |')
    lines += ['', 'Regenerar desde TP3:', '', '```bash',
              f'python3 scripts/sweep.py --name {shlex.quote(args.data.name)} --out-dir {shlex.quote(str(args.data))} '
              f'--param n --values {" ".join(map(str, ns))} --realizations 10 --seed-base 1 '
              '--time 30 --jobs 1 -- --obstacle-algorithm none',
              f'../.venv/bin/python scripts/plot_runtime.py --data {shlex.quote(str(args.data))}', '```', '',
              'Datos individuales: runs.csv. Resumen: summary.csv. Parámetros: meta.json.']
    (args.data/'README.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines[8:18]))
    print(f'Figuras: {args.data}')


if __name__ == '__main__':
    main()
