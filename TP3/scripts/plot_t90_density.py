"""Compara t90 con la fracción de área ocupada por obstáculos usando resultados existentes."""
import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIES = {
    'central_column': 'Columna recta',
    'curved_column': 'Columna convexa',
    'concave_column': 'Columna cóncava',
    'concave_uniform_column': 'Columna cóncava uniforme',
    'funnel_min_radius': 'Embudo de radio mínimo (5 realiz.)',
    'golden_ratio': 'Cámaras áureas',
}
SAVED = {
    'central.txt': 'Disco central R = 0,08 m',
    'central_R0.32.txt': 'Disco central R = 0,32 m',
    'central_cuenco_Rf0.30.txt': 'Disco central + cuenco',
    'central_embudo_a0.05.txt': 'Disco central + embudo',
    'central_palos_Rp0.02.txt': 'Disco central + palos',
    'funnel.txt': 'Embudo recto',
    'semicircle_70.txt': 'Semicírculo libre unilateral',
}


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def point(row, path, label, source, length, width):
    obstacles = []
    if path:
        path = Path(path)
        if not path.is_absolute():
            path = ROOT / path
        for line in path.read_text().splitlines():
            line = line.split('#')[0].strip()
            if line:
                x, y, radius = map(float, line.split())
                if radius <= 0 or not all(map(math.isfinite, (x, y, radius))):
                    raise ValueError(f'Obstáculo inválido en {path}')
                obstacles.append((x, y, radius))
    area = sum(math.pi * r*r for _, _, r in obstacles)
    if not 0 <= area < length * width:
        raise ValueError(f'Área inválida en {path}')
    if int(row['failed']) or int(row['reached_t90']) != int(row['realizations']):
        raise ValueError(f'Resultados incompletos: {source}, {row["value"]}')
    mean, std = float(row['t90_mean']), float(row['t90_std'])
    if not all(map(math.isfinite, (mean, std))):
        raise ValueError(f't90 inválido: {source}')
    return dict(configuration=label, value=row['value'], K=len(obstacles),
                occupied_area_m2=area, density_percent=100*area/(length*width),
                t90_mean=mean, t90_std=std, realizations=int(row['realizations']),
                source=str(source.relative_to(ROOT)), map=str(path) if path else '')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'generated/t90_density')
    parser.add_argument('--only-sweeps', action='store_true',
                        help='Mostrar solo columnas y embudos con barridos de densidad')
    args = parser.parse_args()
    # Dimensiones verificadas en las cabeceras de las condiciones iniciales.
    length, width = 1.2, .68
    points = []
    baseline = None
    for study, label in STUDIES.items():
        folder = ROOT/'generated'/study
        metadata = json.loads((folder/'metadata.json').read_text())
        configs = metadata['configurations']
        for row in read_csv(folder/'summary.csv'):
            if row['param'] == 'width_m':
                matches = [c for c in configs if math.isclose(c['width'], float(row['value']))]
            elif row['param'] == 'angle_deg':
                matches = [c for c in configs if c['angle'] == float(row['value'])]
            elif row['param'] == 'config':
                matches = [c for c in configs if c['tag'] == row['value']]
            else:
                matches = [c for c in configs if c['tag'] == 'mesa_vacia']
            if len(matches) != 1:
                raise ValueError(f'No se puede identificar el mapa: {folder}, {row}')
            config = matches[0]
            name = 'Embudo áureo' if config['tag'] == 'embudo_phi' else label
            p = point(row, config.get('path', config.get('map')), name,
                      folder/'summary.csv', length, width)
            if p['K'] == 0:
                if study == 'central_column':
                    baseline = dict(p, configuration='Mesa vacía')
                continue
            if p['K'] != config['K']:
                raise ValueError(f'El mapa cambió: {config["tag"]}')
            points.append(p)
    source = ROOT/'generated/sweeps/configs_t90_20260918/summary.csv'
    for row in read_csv(source):
        points.append(point(row, row['value'], SAVED[Path(row['value']).name], source, length, width))
    if baseline is None:
        raise ValueError('Falta la referencia de mesa vacía')
    if args.only_sweeps:
        points = [p for p in points if p['configuration'] in list(STUDIES.values())[:5]]

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.size': 13, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, ax = plt.subplots(figsize=(13.8, 7.5))
    labels = list(dict.fromkeys(p['configuration'] for p in points))
    colors = plt.colormaps['viridis'](np.linspace(.05, .9, len(labels)))
    markers = ['o', 's', '^', 'D', 'v', 'P', 'X', '*', 'h', '<', '>', 'p', '8', 'd']
    for i, label in enumerate(labels):
        group = sorted((p for p in points if p['configuration'] == label), key=lambda p:p['density_percent'])
        # Líneas solo para barridos geométricos de una misma familia.
        line = '-' if label in list(STUDIES.values())[:5] else 'none'
        ax.errorbar([p['density_percent'] for p in group], [p['t90_mean'] for p in group],
                    yerr=[p['t90_std'] for p in group], label=label,
                    color=colors[i], marker=markers[i], linestyle=line,
                    markersize=6.5, linewidth=1.5, elinewidth=1, capsize=3, alpha=.9)
    if not args.only_sweeps:
        mean, std = baseline['t90_mean'], baseline['t90_std']
        ax.axhspan(mean-std, mean+std, color='.4', alpha=.10)
        ax.axhline(mean, color='.4', linestyle='--', linewidth=1.3)
        ax.errorbar([0], [mean], yerr=[std], color='.3', marker='o', capsize=4,
                    label='Mesa vacía (media ± σ)')
    ax.set(xlabel=r'Área ocupada por obstáculos, $\phi = \sum_k \pi R_k^2/(LW)$ [%]',
           ylabel=r'$\langle t_{90}\rangle$ [s]', xlim=(-1, None))
    ax.grid(alpha=.2)
    ax.legend(loc='center left', bbox_to_anchor=(1.02, .5), frameon=False, fontsize=11.5)
    fig.tight_layout()
    args.out.mkdir(parents=True, exist_ok=True)
    for ext in ('png', 'pdf'):
        fig.savefig(args.out/f't90-vs-densidad.{ext}', dpi=220)
    plt.close(fig)
    with (args.out/'datos.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(points[0]))
        writer.writeheader()
        writer.writerows(points if args.only_sweeps else [baseline, *points])
    (args.out/'README.md').write_text(
        '# t90 según densidad de obstáculos\n\n'
        'Densidad: φ = Σ π R_k² / (L W), con L = 1,2 m y W = 0,68 m. '
        'Es fracción de área física ocupada, no cantidad de obstáculos por m² ni área inaccesible '
        'a los centros de las partículas. Se calcula de los mapas guardados.\n\n'
        'Puntos: media; barras: ± un desvío estándar muestral (no error de la media). '
        '10 realizaciones por mapa, salvo embudos de radio mínimo: 5. '
        'Todos los puntos incluidos alcanzaron t90 en todas sus realizaciones. '
        + ('' if args.only_sweeps else 'La banda gris corresponde a la mesa vacía de 10 realizaciones. ')
        +
        'Las líneas unen puntos de un mismo barrido, sin representar un ajuste. '
        'Los cambios de densidad también cambian la geometría: no aíslan un efecto causal.\n\n'
        + ('Se incluyen solo los cinco barridos de columnas y embudos que varían la densidad. '
           if args.only_sweeps else
           'Se incluyen los siete summary.csv disponibles; la mesa vacía repetida se muestra una sola vez. ')
        +
        'No se usan medias redondeadas de GUIA.md. Fuentes y mapas por punto en datos.csv.\n\n'
        f'Regenerar desde TP3: `../.venv/bin/python scripts/plot_t90_density.py'
        f'{" --only-sweeps" if args.only_sweeps else ""} --out {args.out}`.\n')
    print(f'{len(points)} configuraciones'
          f'{"" if args.only_sweeps else " + mesa vacía"}. Salida: {args.out}')


if __name__ == '__main__':
    main()
