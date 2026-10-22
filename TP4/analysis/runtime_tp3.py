"""Análisis de la medición de tiempos de ejecución del TP3 (2.1.b, D7 y D12).

Lee <input>/runs.csv (lo escribe RuntimeBenchmark del TP3) sin modificarlo y escribe en <out>:
  resumen_mediana.csv  por N: corridas, mediana, p25, p75, mínimo, máximo, media y desvío (n-1)
  perturbadas.csv      corridas marcadas con el criterio de abajo
  sensibilidad.csv     mediana por N con todas las corridas y sin las marcadas
y la figura de tiempo vs N (mediana con barra p25-p75) en presentacion/figuras/.

Criterio de perturbada (fijado a posteriori, D12): eventos dentro de ±1 % de la mediana de eventos de su N
y tiempo más de 8 % por encima de la mediana de tiempo de su N. Mismos eventos = misma simulación, así que
el tiempo extra es de la máquina, no del motor.

Uso (desde TP4/):
    .venv/Scripts/python analysis/runtime_tp3.py [--input outputs/runtime_tp3] [--out DIR] [--fig BASE]
        [--expect "300:6,200:10,100:6,100:5"] [--scale loglog|semilogy|linear] [--label TEXTO]
Sin --out, la salida va a <input>_analisis/ (runtime_tp3_b -> runtime_tp3_b_analisis/).
"""
import argparse
import csv
import re
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
LOCAL = timezone(timedelta(hours=-3), 'ART')  # Argentina, sin horario de verano
EVENTS_TOL, RUNTIME_EXCESS = 0.01, 0.08
# Leyenda de la serie TP3: la figura combinada TP3+TP4 tiene que reutilizar estas etiquetas y LEGEND_STYLE.
# Adentro de los ejes, arriba a la izquierda: la curva sube hacia la derecha y esa esquina queda libre.
# Con el recuadro por defecto de matplotlib, como las leyendas de las figuras del TP3 (plot_dcm.py, plot_fu.py).
SERIES_LABELS = {'': 'TP3', '-b': 'TP3 (réplica)'}  # por sufijo de la carpeta de entrada
LEGEND_STYLE = {'loc': 'upper left', 'frameon': True}


def quartiles(values):
    # 'inclusive' = interpolación lineal entre los puntos ordenados (mismo método que numpy.percentile por defecto)
    p25, p50, p75 = statistics.quantiles(values, n=4, method='inclusive')
    return p25, p50, p75


def local_time(stamp):
    stamp = re.sub(r'(\.\d{6})\d*', r'\1', stamp.replace('Z', '+00:00'))
    return datetime.fromisoformat(stamp).astimezone(LOCAL).strftime('%H:%M:%S')


def read_runs(path):
    with open(path, newline='', encoding='utf-8') as source:
        rows = list(csv.DictReader(source))
    for row in rows:
        row['n'], row['seed'] = int(row['n']), int(row['seed'])
        row['runtime_s'], row['events'] = float(row['runtime_s']), int(row['events'])
    return rows


def write_csv(path, header, rows, comment=None):
    with open(path, 'w', newline='', encoding='utf-8') as target:
        if comment:
            target.write(f'# {comment}\n')
        writer = csv.writer(target, lineterminator='\n')
        writer.writerow(header)
        writer.writerows(rows)


def figure(summary, base, scale, label):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FixedLocator, NullFormatter, NullLocator
    plt.rcParams.update({'font.size': 14, 'axes.spines.top': False, 'axes.spines.right': False,
                         'svg.fonttype': 'none', 'pdf.fonttype': 42})
    ns = [s['n'] for s in summary]
    med = [s['median'] for s in summary]
    low = [s['median'] - s['p25'] for s in summary]
    high = [s['p75'] - s['median'] for s in summary]
    # Tamaño de la columna de la diapositiva (0.66 del ancho), como en TP3.
    fig, ax = plt.subplots(figsize=(7.0, 4.4), layout='constrained')
    ax.errorbar(ns, med, yerr=[low, high], fmt='o-', color='#3939B5', ecolor='#3939B5',
                capsize=4, linewidth=2, markersize=7, label=label)
    if scale in ('loglog', 'semilogy'):
        ax.set_yscale('log')
    if scale == 'loglog':
        ax.set_xscale('log')
        ax.xaxis.set_major_locator(FixedLocator(ns))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_xticklabels([str(n) for n in ns])
    else:
        ax.set_xticks(ns)
    ax.set(xlabel='N', ylabel='tiempo (s)')
    ax.grid(alpha=.25, which='major')
    ax.legend(**LEGEND_STYLE)
    base.parent.mkdir(parents=True, exist_ok=True)
    for ext in ('pdf', 'png'):
        # metadata fija: la misma entrada da el mismo PDF
        fig.savefig(base.with_suffix(f'.{ext}'), dpi=220, metadata={'CreationDate': None} if ext == 'pdf' else None)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--input', type=Path, default=MODULE / 'outputs' / 'runtime_tp3', help='carpeta con runs.csv')
    parser.add_argument('--out', type=Path, help='carpeta de salida (por defecto <input>_analisis)')
    parser.add_argument('--fig', type=Path, help='ruta de la figura sin extensión')
    parser.add_argument('--expect', help='perturbadas esperadas, "N:semilla,..."; si difieren, termina con error')
    parser.add_argument('--runs-per-n', type=int, default=10)
    parser.add_argument('--scale', choices=('loglog', 'semilogy', 'linear'), default='loglog')
    parser.add_argument('--label', help='etiqueta de la leyenda (por defecto según SERIES_LABELS)')
    args = parser.parse_args(argv)

    source = args.input.resolve()
    out = (args.out or source.with_name(source.name + '_analisis')).resolve()
    if out == source:
        parser.error('la salida no puede ser la carpeta de entrada')
    suffix = source.name.removeprefix('runtime_tp3').replace('_', '-')
    fig = args.fig or MODULE / 'presentacion' / 'figuras' / f'F4-tp3-tiempo-vs-n{suffix}'

    rows = read_runs(source / 'runs.csv')
    by_n = {}
    for row in rows:
        by_n.setdefault(row['n'], []).append(row)
    for n, group in sorted(by_n.items()):
        seeds = sorted(r['seed'] for r in group)
        if len(group) != args.runs_per_n or len(set(seeds)) != len(seeds):
            sys.exit(f'N={n}: se esperaban {args.runs_per_n} corridas con semillas distintas y hay {len(group)}')

    summary, flagged = [], []
    for n, group in sorted(by_n.items()):
        times = [r['runtime_s'] for r in group]
        p25, med, p75 = quartiles(times)
        med_events = statistics.median(r['events'] for r in group)
        summary.append({'n': n, 'runs': len(times), 'median': med, 'p25': p25, 'p75': p75, 'min': min(times),
                        'max': max(times), 'mean': statistics.fmean(times), 'std': statistics.stdev(times)})
        for r in sorted(group, key=lambda r: r['seed']):
            d_events = (r['events'] - med_events) / med_events
            d_time = r['runtime_s'] / med - 1
            if abs(d_events) <= EVENTS_TOL and d_time > RUNTIME_EXCESS:
                flagged.append((n, r['seed'], r['runtime_s'], r['events'], d_time, d_events, r['finished_at'], local_time(r['finished_at'])))

    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / 'resumen_mediana.csv',
              ['n', 'corridas', 'mediana_s', 'p25_s', 'p75_s', 'min_s', 'max_s', 'media_s', 'desvio_s'],
              [[s['n'], s['runs'], s['median'], s['p25'], s['p75'], s['min'], s['max'], s['mean'], s['std']] for s in summary],
              comment=f'fuente: {source / "runs.csv"}; percentiles: statistics.quantiles(method="inclusive"); desvío con n-1')
    write_csv(out / 'perturbadas.csv',
              ['n', 'semilla', 'runtime_s', 'eventos', 'exceso_tiempo_pct', 'dif_eventos_pct', 'finished_at_utc', 'hora_local'],
              [[n, s, t, e, round(100 * dt, 2), round(100 * de, 3), utc, loc] for n, s, t, e, dt, de, utc, loc in flagged],
              comment=f'criterio (a posteriori): |eventos - mediana_eventos(N)| <= {EVENTS_TOL:.0%} y tiempo > mediana_tiempo(N) + {RUNTIME_EXCESS:.0%}; hora local UTC-3')

    marked = {(n, s) for n, s, *_ in flagged}
    sensitivity = []
    for s in summary:
        clean = [r['runtime_s'] for r in by_n[s['n']] if (s['n'], r['seed']) not in marked]
        clean_median = statistics.median(clean)
        sensitivity.append([s['n'], s['median'], clean_median, len(clean), round(100 * (clean_median / s['median'] - 1), 3)])
    write_csv(out / 'sensibilidad.csv', ['n', 'mediana_todas_s', 'mediana_sin_marcadas_s', 'corridas_sin_marcadas', 'dif_pct'], sensitivity)
    figure(summary, fig, args.scale, args.label or SERIES_LABELS.get(suffix, 'TP3'))

    print('Perturbadas (N, semilla, exceso de tiempo, hora local):')
    for n, s, t, e, dt, de, utc, loc in flagged:
        print(f'  ({n}, {s})  {t:.4f} s  +{100 * dt:.1f} %  eventos {100 * de:+.2f} %  {loc}')
    print(f'\n{"N":>4} {"mediana todas [s]":>18} {"sin marcadas [s]":>17} {"dif %":>7}')
    for n, all_med, clean_med, k, diff in sensitivity:
        print(f'{n:>4} {all_med:>18.4f} {clean_med:>17.4f} {diff:>7.2f}   ({k} corridas)')
    print(f'\nSalidas: {out}\nFigura: {fig}.pdf / .png ({args.scale})')
    if args.expect:
        expected = {tuple(int(x) for x in pair.split(':')) for pair in args.expect.split(',')}
        if expected != marked:
            sys.exit(f'Las perturbadas no coinciden con --expect: sobran {sorted(marked - expected)}, faltan {sorted(expected - marked)}')
        print('Perturbadas = --expect')


if __name__ == '__main__':
    main()
