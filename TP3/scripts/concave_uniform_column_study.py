"""Columna cóncava )( más uniforme: cintura ancha y curvatura suave."""
import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from scipy import ndimage
from check_map import analyze
from golden_ratio_study import fingerprint
from simulation_io import parse_simulation
from sweep import parse_result, summarize, write_csv, RUN_FIELDS, SUMMARY_FIELDS

ROOT = Path(__file__).resolve().parents[1]
L, W, R = 1.2, .68, .0175
DX = .0351


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--columns', nargs='+', type=int, default=[1, 2, 4, 6, 8, 10, 12, 16, 20])
    parser.add_argument('--realizations', type=int, default=10)
    parser.add_argument('--seed-base', type=int, default=1)
    parser.add_argument('--time', type=float, default=100)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--out', type=Path, default=ROOT / 'generated/concave_uniform_column')
    args = parser.parse_args()
    if args.realizations < 2 or args.jobs < 1 or not math.isfinite(args.time) or args.time <= 0:
        parser.error('Se requiere realizations >= 2, jobs >= 1 y time finito positivo')
    if any(c < 1 or (c-1)*DX+2*R >= L-4*R for c in args.columns):
        parser.error('Cantidad de columnas incompatible con la mesa')
    before = fingerprint()
    out = args.out.resolve()
    maps = ROOT / 'configs/concave_uniform_column'
    for folder in (maps, out, out/'initial', out/'results', out/'logs'):
        folder.mkdir(parents=True, exist_ok=True)
    commands = []

    def run(options, log):
        cmd = [str(x) for x in ['java', '-Xmx256m', '-jar', ROOT/'target/tp3.jar', *options]]
        commands.append(cmd)
        with (out/'logs'/log).open('w') as stream:
            subprocess.run(cmd, stdout=stream, stderr=subprocess.STDOUT, check=True)

    configs = [dict(tag='mesa_vacia', columns=0, width=0., K=0, path=None)]
    for count in sorted(set(args.columns)):
        tag = f'uniforme_{count:02d}'
        ys = np.linspace(R+1e-9, W-R-1e-9, 19)
        path = maps/f'{tag}.txt'
        width = (count-1)*DX + 2*R
        points = []
        a, b = (width-2*R)/2, (ys[-1]-ys[0])/2
        for y in ys:
            # Cintura = 60 % del ancho máximo; el resto aporta la curvatura.
            half = a * (0.60 + 0.40 * (1-math.sqrt(max(0., 1-((y-W/2)/b)**2))))
            number = math.floor(2*half/DX+1e-9)+1
            xs = L/2 + np.linspace(-half, half, number) if number > 1 else [L/2]
            points.extend((x, y) for x in xs)
        path.write_text(f'# Dos caras concavas )( uniformes: ancho máximo exterior={width:.9f} m; R=r={R} m\n'
                        '# Cintura central = 60% del ancho máximo; interior relleno.\n'
                        f'# a={a:.12f}; b={b:.12f}; 19 filas horizontales\n'
                        + ''.join(f'{x:.12f} {y:.12f} {R:.12f}\n' for x, y in points))
        configs.append(dict(tag=tag, columns=count, width=width, K=len(points),
                            ellipse_a_m=a, ellipse_b_m=b, path=str(path)))

    for c in configs:
        options = ['--obstacles', c['path']] if c['path'] else ['--obstacle-algorithm', 'none']
        initial = out/'initial'/f'{c["tag"]}_check.txt'
        run(['generate', '--seed', args.seed_base, *options, '--out', initial], f'{c["tag"]}_check.log')
        data = parse_simulation(initial)
        check = analyze(data, R, .0005)
        c['infill_disks'] = 0
        # Un centro accesible admite también un disco fijo de radio R=r.
        # Cubrir pequeños intersticios cerrados detectados a resolución fina.
        for attempt in range(10):
            if not check['trapped']:
                break
            if not c['path']:
                raise RuntimeError('Región aislada inesperada en mesa vacía')
            labels, _ = ndimage.label(check['free'])
            label = check['trapped'][0][0]
            indices = np.argwhere(labels == label)
            candidates = np.column_stack((check['xs'][indices[:, 0]], check['ys'][indices[:, 1]]))
            obstacles = np.array(data.obstacles)
            clearance = np.min(np.linalg.norm(candidates[:, None, :] - obstacles[None, :, :2], axis=2)
                               - obstacles[None, :, 2] - R, axis=1)
            index = int(np.argmax(clearance))
            if clearance[index] <= 1e-10:
                raise RuntimeError('No se puede rellenar el intersticio sin solapamiento')
            x, y = candidates[index]
            with Path(c['path']).open('a') as stream:
                stream.write(f'# Relleno de intersticio cerrado\n{x:.12f} {y:.12f} {R:.12f}\n')
            c['infill_disks'] += 1
            run(['generate', '--seed', args.seed_base, *options, '--out', initial], f'{c["tag"]}_infill{attempt}.log')
            data = parse_simulation(initial)
            check = analyze(data, R, .0005)
        c['K'] = len(data.obstacles)
        expected = 2 if c['columns'] else 1
        if check['components'] != expected or check['trapped'] or not (check['left_open'] and check['right_open']):
            raise RuntimeError(f'{c["tag"]}: división geométrica incorrecta')
        if not all(o[2] == R for o in data.obstacles):
            raise RuntimeError('Radio distinto del mínimo')
        c.update(components=int(check['components']), accessible_area_m2=float(check['area']))
        print(f'{c["tag"]}: ancho={c["width"]:.4f} m, K={c["K"]}, regiones={expected}', flush=True)

    def simulate(task):
        c, seed = task
        tag = f'{c["tag"]}_{seed}'
        initial, result = out/'initial'/f'{tag}.txt', out/'results'/f'{tag}.txt'
        options = ['--obstacles', c['path']] if c['path'] else ['--obstacle-algorithm', 'none']
        row = dict(param='width_m', value=c['width'], seed=seed, K=c['K'])
        try:
            run(['generate', '--seed', seed, *options, '--out', initial], f'{tag}_generate.log')
            run(['simulate', '--input', initial, '--time', args.time, '--every', 2**31-1,
                 '--out', result], f'{tag}_simulate.log')
            data = parse_simulation(result)
            first, last = data.frames[0], data.frames[-1]
            left = lambda frame: {p[0] for p in frame.particles if p[1] < L/2}
            if c['columns'] and left(first) != left(last):
                raise RuntimeError(f'{tag}: partículas cambiaron de mitad')
            row.update(status='ok', initial_left=len(left(first)), **parse_result(result))
            print(f'{tag}: t90={row["t90"]:.3f} s', flush=True)
        except subprocess.CalledProcessError as exc:
            row.update(status='failed', error=str(exc))
            print(f'{tag}: falló, consultar logs', flush=True)
        return row

    seeds = list(range(args.seed_base, args.seed_base+args.realizations))
    with ThreadPoolExecutor(args.jobs) as pool:
        rows = list(pool.map(simulate, [(c, s) for c in configs for s in seeds]))
    summary = summarize(rows)
    write_csv(out/'runs.csv', RUN_FIELDS+['initial_left'], rows)
    write_csv(out/'summary.csv', SUMMARY_FIELDS, summary)
    after = fingerprint()
    if before != after:
        raise RuntimeError('Cambió el motor durante el experimento')
    reference = ROOT/'generated/central_column'
    reference_meta = json.loads((reference/'metadata.json').read_text())
    if (reference_meta['seeds'] != seeds or reference_meta['time_s'] != args.time
            or reference_meta['engine_sha256_after'] != before):
        raise RuntimeError('La referencia recta tiene distintas semillas, tiempo o motor')
    (out/'metadata.json').write_text(json.dumps(dict(configurations=configs, seeds=seeds,
        N=100, radius_m=R, time_s=args.time, grid_step_m=.0005, commands=commands,
        geometry='Dos caras concavas )(, cintura de 60% del ancho máximo, interior relleno',
        straight_reference=str(reference),
        engine_sha256_before=before, engine_sha256_after=after, engine_unchanged=True), indent=2))
    figures(out, configs, rows, summary, args)


def figures(out, configs, rows, summary, args):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    def save(fig, name):
        fig.tight_layout()
        for ext in ('png', 'pdf'):
            fig.savefig(out/f'{name}.{ext}', dpi=180)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    points = summary[1:]
    ax.errorbar([s['value']*100 for s in points], [s['t90_mean'] for s in points],
                yerr=[s['t90_std'] for s in points], fmt='o-', capsize=4,
                label=f'Columna )( uniforme: media ± desvío ({args.realizations} semillas)')
    for s in points:
        values = [r['t90'] for r in rows if r['value'] == s['value'] and r['status'] == 'ok' and math.isfinite(r['t90'])]
        ax.scatter([s['value']*100]*len(values), values, s=12, alpha=.3, color='#2563eb')
        ax.annotate(f'{s["reached_t90"]}/{args.realizations}', (s['value']*100, s['t90_mean']+s['t90_std']),
                    xytext=(0, 6), textcoords='offset points', ha='center', fontsize=8)
    baseline = summary[0]
    with (ROOT/'generated/central_column/summary.csv').open() as stream:
        straight = [{k: float(v) if k in ('value', 't90_mean', 't90_std') else v
                     for k, v in row.items()} for row in csv.DictReader(stream)]
    reference_points = [s for s in straight if s['value'] > 0]
    ax.errorbar([s['value']*100 for s in reference_points], [s['t90_mean'] for s in reference_points],
                yerr=[s['t90_std'] for s in reference_points], fmt='s--', capsize=3,
                color='#d97706', label='Columna recta: media ± desvío (10 semillas)')
    mean, std = baseline['t90_mean'], baseline['t90_std']
    ax.axhline(mean, color='.4', ls='--', label='Mesa vacía: media ± desvío')
    ax.axhspan(mean-std, mean+std, color='.5', alpha=.15)
    ax.set(xlabel='Ancho máximo exterior arriba y abajo [cm]', ylabel='t90 [s]',
           title='Columna )( más uniforme frente a columna recta · R = 0,0175 m · N = 100')
    ax.margins(y=.2)
    ax.grid(alpha=.2)
    ax.legend()
    save(fig, 't90_vs_ancho')

    fig, axes = plt.subplots(math.ceil(len(configs)/3), 3, figsize=(14, 3.2*math.ceil(len(configs)/3)))
    for ax, c in zip(axes.flat, configs):
        data = parse_simulation(out/'initial'/f'{c["tag"]}_check.txt')
        for x, y, radius in data.obstacles:
            ax.add_patch(Circle((x, y), radius, color='#475569', lw=0))
        for x in (0, L):
            ax.plot([x, x], [.24, .44], color='#16a34a', lw=4, clip_on=False)
        ax.set(xlim=(0, L), ylim=(0, W), xlabel='x [m]', ylabel='y [m]',
               title=f'Ancho {100*c["width"]:.2f} cm · K={c["K"]}')
        ax.set_aspect('equal')
    for ax in list(axes.flat)[len(configs):]:
        ax.set_visible(False)
    save(fig, 'configuraciones')

    lines = ['# Columna central )( más uniforme: ancho vs t90', '',
        f'{args.realizations} semillas por configuración; N=100, tf={args.time:g} s. Radio mínimo R=r=0,0175 m.',
        'Motor y JAR sin cambios, comprobados por SHA-256 (metadata.json).', '',
        '| Ancho máximo [cm] | Índice de ancho | K | t90 medio [s] | σ [s] | Alcanzan t90 | Fallas |',
        '|---:|---:|---:|---:|---:|---:|---:|']
    for c, s in zip(configs, summary):
        lines.append(f'| {100*c["width"]:.2f} | {c["columns"]} | {c["K"]} | {s["t90_mean"]:.3f} | {s["t90_std"]:.3f} | {s["reached_t90"]}/{args.realizations} | {s["failed"]} |')
    eligible = [s for s in points if s['reached_t90'] == args.realizations]
    if eligible:
        best = min(eligible, key=lambda s: s['t90_mean'])
        lines += ['', f'Menor promedio observado entre columnas completas: ancho {100*best["value"]:.2f} cm, '
                  f't90={best["t90_mean"]:.3f} s; cambio respecto de mesa vacía: '
                  f'{100*(best["t90_mean"]/mean-1):+.1f} %. No implica un óptimo fuera de los anchos ensayados.']
    lines += ['', '## Geometría y medición',
        'Forma solicitada: )(, caras cóncavas vistas desde cada mitad libre. '
        'El máximo ancho está arriba y abajo; la cintura a la altura de los arcos de gol mide 60% del ancho máximo. '
        'La mitad del espesor sigue x=L/2 ± a[0,60+0,40(1−sqrt(1−((y−W/2)/b)²))], a=(ancho−2r)/2, b≈0,3225 m. '
        'Se discretiza en 19 filas horizontales; el interior se rellena con discos mínimos para evitar '
        'una cámara central cerrada donde pudieran nacer partículas atrapadas. '
        'Las filas demasiado angostas llevan un disco central: los bordes son una aproximación discreta de la elipse. '
        'El primer ancho (3,5 cm) degenera en la misma columna recta de un disco de espesor. '
        'La separación horizontal de centros es al menos 0,0351 m y la vertical ≈0,03583 m. '
        'Los discos no se solapan. Sus huecos, incluidos los extremos contra las paredes, '
        'no admiten partículas de diámetro 0,035 m; tampoco caben partículas en los intersticios internos. '
        'Así quedan dos regiones desconectadas, cada una con su arco. '
        'Los intersticios cerrados detectados se rellenan con discos adicionales del mismo radio mínimo. '
        'Comprobado por el validador del motor y una grilla de 0,5 mm; se verificó además que los IDs '
        'en cada mitad coinciden al inicio y al final de cada corrida.',
        'La mesa vacía (ancho cero) tiene una sola región. El paso de cero a la primera columna cambia la conectividad.',
        'Se conserva la inicialización uniforme original, sin forzar 50 partículas por lado. '
        'Las mismas semillas se usan para todos los anchos, pero el rechazo geométrico cambia las posiciones. '
        'Al ensanchar la columna disminuye el área libre y aumenta la densidad: el experimento combina ambos efectos. '
        'La comparación con la columna recta usa el mismo ancho máximo, no igual área ocupada: '
        'la columna curva ocupa menos área, por lo que no aísla exclusivamente el efecto de la curvatura. '
        'La referencia recta se reutiliza del estudio previo, verificando hashes del motor, semillas y tiempo.',
        't90 corresponde al 90 % de las 100 partículas de la mesa completa y se toma del evento exacto del motor. '
        'Las barras muestran desvío estándar muestral, no error de la media. '
        'Los t90 no alcanzados no se sustituyen por tf; se cuentan aparte. Fallas y semillas quedan en runs.csv.',
        'Esta división separa las mitades izquierda/derecha, no las partículas frescas/usadas.', '',
        '## Reproducción', '```bash',
        f'../.venv/bin/python scripts/concave_uniform_column_study.py --columns {" ".join(str(c["columns"]) for c in configs[1:])} '
        f'--realizations {args.realizations} --seed-base {args.seed_base} --time {args.time:g} --jobs {args.jobs}',
        '```', '', 'Requiere la referencia generated/central_column del estudio previo. '
        'Mapas en configs/concave_uniform_column/. Figuras PNG/PDF, CSV, condiciones iniciales, resultados y logs en esta carpeta.']
    comparisons = []
    for s in points:
        ref = next(t for t in reference_points if math.isclose(t['value'], s['value']))
        comparisons.append(dict(width_m=s['value'], curved_t90_mean=s['t90_mean'],
            curved_t90_std=s['t90_std'], straight_t90_mean=ref['t90_mean'],
            straight_t90_std=ref['t90_std'], change_percent=100*(s['t90_mean']/ref['t90_mean']-1)))
    write_csv(out/'comparison.csv', list(comparisons[0]), comparisons)
    lines += ['', '## Comparación con la columna recta', '',
              '| Ancho máximo [cm] | Curva [s] | Recta [s] | Cambio del promedio |',
              '|---:|---:|---:|---:|']
    for c in comparisons:
        lines.append(f'| {100*c["width_m"]:.2f} | {c["curved_t90_mean"]:.3f} | '
                     f'{c["straight_t90_mean"]:.3f} | {c["change_percent"]:+.1f} % |')
    (out/'RESULTADOS.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines[:20]), flush=True)


if __name__ == '__main__':
    main()
