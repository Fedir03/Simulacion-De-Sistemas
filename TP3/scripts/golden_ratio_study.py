"""Configuraciones áureas y corridas del JAR existente, sin cambiar el motor."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess

import numpy as np
from check_map import analyze
from simulation_io import parse_simulation
from sweep import parse_result, summarize, write_csv, RUN_FIELDS, SUMMARY_FIELDS

ROOT = Path(__file__).resolve().parents[1]
PHI = (1 + math.sqrt(5)) / 2
L, W, R, D = 1.2, .68, .0175, .20


def fingerprint():
    paths = sorted((ROOT / 'src').rglob('*')) + [ROOT / 'pom.xml', ROOT / 'target/tp3.jar']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths if p.is_file()}


def chamber(particles, end):
    # Cámara superior detrás del tabique; excluye la boca a la derecha.
    x, y = particles[:, 1], particles[:, 2]
    boundary = W / PHI + (W / 2 - W / PHI) * (x - R) / (end - R)
    return (x <= end) & (y > boundary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'generated/golden_ratio')
    parser.add_argument('--realizations', type=int, default=10)
    parser.add_argument('--seed-base', type=int, default=1)
    parser.add_argument('--time', type=float, default=100)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if args.realizations < 2 or args.jobs < 1 or not math.isfinite(args.time) or args.time <= 0:
        parser.error('realizations >= 2, jobs >= 1, time finito y positivo')
    before = fingerprint()
    out = args.out.resolve()
    maps = ROOT / 'configs/golden_ratio'
    for p in (out, maps, out / 'initial', out / 'trajectories', out / 'logs'):
        p.mkdir(parents=True, exist_ok=True)
    java = ['java', '-Xmx256m', '-jar', str(ROOT / 'target/tp3.jar')]
    commands = []

    def run(options, log):
        cmd = [str(x) for x in java + options]
        commands.append(cmd)
        with (out / 'logs' / log).open('w') as stream:
            subprocess.run(cmd, stdout=stream, stderr=subprocess.STDOUT, check=True)

    configs = []
    for power in (1, 2, 3):
        gap = D / PHI ** power
        end = L - gap
        start, finish = np.array([R, W / PHI]), np.array([end, W / 2])
        # Discos sin solapamiento; huecos menores que el diámetro de partícula.
        count = math.floor(np.linalg.norm(finish - start) / (2 * R * 1.05)) + 1
        points = np.linspace(start, finish, count)
        tag = f'camara_phi{power}'
        path = maps / f'{tag}.txt'
        path.write_text(f'# phi={PHI:.16f}; boca=d/phi^{power}={gap:.12f} m\n'
                        '# Tabique desde (r,W/phi) hasta (L-boca,W/2); R=r.\n'
                        + ''.join(f'{x:.12f} {y:.12f} {R:.12f}\n' for x, y in points))
        configs.append(dict(tag=tag, path=str(path), end=end, gap=gap, power=power))
    funnel = maps / 'embudo_phi.txt'
    run(['generate', '--seed', str(args.seed_base), '--obstacle-algorithm', 'funnel',
         '--obstacle-funnel-length', str((L / 2) / PHI), '--obstacles-out', funnel,
         '--out', out / 'initial/embudo_generacion.txt'], 'embudo_generacion.log')
    configs += [dict(tag='embudo_phi', path=str(funnel)), dict(tag='mesa_vacia', path=None)]
    for c in configs:
        initial = out / 'initial' / f'{c["tag"]}_check.txt'
        options = ['--obstacles', c['path']] if c['path'] else ['--obstacle-algorithm', 'none']
        run(['generate', '--seed', str(args.seed_base), *options, '--out', initial], f'{c["tag"]}_check.log')
        data = parse_simulation(initial)
        check = analyze(data, R, .0005)
        if check['trapped'] or not (check['left_open'] and check['right_open']):
            raise RuntimeError(f'Mapa inválido: {c["tag"]}: {check["trapped"]}')
        c.update(K=len(data.obstacles), accessible_area_m2=float(check['area']),
                 components=int(check['components']), trapped_components=len(check['trapped']))
        print(f'{c["tag"]}: K={c["K"]}, sin cámaras cerradas sin arco', flush=True)

    def simulate(task):
        c, seed = task
        tag = f'{c["tag"]}_{seed}'
        initial = out / 'initial' / f'{tag}.txt'
        trajectory = out / 'trajectories' / f'{tag}.txt'
        options = ['--obstacles', c['path']] if c['path'] else ['--obstacle-algorithm', 'none']
        row = dict(param='config', value=c['tag'], seed=seed, K=c['K'])
        try:
            run(['generate', '--seed', str(seed), *options, '--out', initial], f'{tag}_generate.log')
            run(['simulate', '--input', initial, '--time', str(args.time), '--dt', '.5',
                 '--out', trajectory], f'{tag}_simulate.log')
            row.update(status='ok', **parse_result(trajectory))
            print(f'{tag}: t90={row["t90"]:.3f} s', flush=True)
        except subprocess.CalledProcessError as error:
            row.update(status='failed', error=str(error))
            print(f'{tag}: FALLÓ; consultar logs', flush=True)
        return row

    seeds = list(range(args.seed_base, args.seed_base + args.realizations))
    with ThreadPoolExecutor(args.jobs) as pool:
        rows = list(pool.map(simulate, [(c, s) for c in configs for s in seeds]))
    summary = summarize(rows)
    write_csv(out / 'runs.csv', RUN_FIELDS, rows)
    write_csv(out / 'summary.csv', SUMMARY_FIELDS, summary)
    if fingerprint() != before:
        raise RuntimeError('Cambió un archivo del motor durante el estudio')
    (out / 'metadata.json').write_text(json.dumps(dict(phi=PHI, configurations=configs,
        seeds=seeds, N=100, time_s=args.time, dt_s=.5, grid_step_m=.0005,
        commands=commands, engine_sha256_before=before, engine_sha256_after=fingerprint(),
        engine_unchanged=True), indent=2))
    plot_and_report(out, configs, rows, summary, args)


def plot_and_report(out, configs, rows, summary, args):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    def save(fig, name):
        fig.tight_layout()
        for ext in ('png', 'pdf'):
            fig.savefig(out / f'{name}.{ext}', dpi=180)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, s in enumerate(summary):
        values = [r['t90'] for r in rows if r['value'] == s['value'] and r['status'] == 'ok'
                  and math.isfinite(r['t90'])]
        ax.scatter([i] * len(values), values, alpha=.4, s=22)
        ax.errorbar(i, s['t90_mean'], yerr=s['t90_std'], fmt='ko', capsize=6)
        ax.annotate(f'{s["reached_t90"]}/{args.realizations}', (i, s['t90_mean']),
                    xytext=(12, 10), textcoords='offset points')
    ax.set(xticks=range(len(configs)), xticklabels=[c['tag'] for c in configs],
           ylabel='t90 [s]', title='Media ± desvío muestral; puntos: semillas individuales')
    ax.grid(axis='y', alpha=.2)
    save(fig, 't90_comparacion')

    fig, axes = plt.subplots(3, 2, figsize=(12, 10))
    for ax, c in zip(axes.flat, configs):
        data = parse_simulation(out / 'initial' / f'{c["tag"]}_check.txt')
        if 'end' in c:
            ax.fill([R, c['end'], c['end'], R], [W / PHI, W / 2, W, W],
                    color='#fef3c7', label='Cámara propuesta')
        for x, y, radius in data.obstacles:
            ax.add_patch(Circle((x, y), radius, color='#475569'))
        for x in (0, L):
            ax.plot([x, x], [(W-D)/2, (W+D)/2], color='#16a34a', lw=5, clip_on=False)
        ax.set(xlim=(0, L), ylim=(0, W), xlabel='x [m]', ylabel='y [m]',
               title=f'{c["tag"]} · K={c["K"]}')
        ax.set_aspect('equal')
    axes.flat[-1].set_visible(False)
    save(fig, 'configuraciones')

    separation = []
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    for ax, c in zip(axes, configs[:3]):
        curves = []
        for row in rows:
            if row['value'] != c['tag'] or row['status'] != 'ok':
                continue
            data = parse_simulation(out / 'trajectories' / f'{c["tag"]}_{row["seed"]}.txt')
            values, entries, exits = [], set(), set()
            for frame in data.frames:
                particles = np.array([p[:4] for p in frame.particles])
                inside = chamber(particles, c['end'])
                used = np.array([p[4][0] == 1 for p in frame.particles])
                values.append([inside[used].mean() if used.any() else np.nan,
                               inside[~used].mean() if (~used).any() else np.nan])
                # Observación discreta: salida después de haber sido vista usada dentro.
                current = set(particles[inside & used, 0].astype(int))
                exits.update(entries - current)
                entries.update(current)
            curves.append(values)
            idx = min(range(len(data.frames)), key=lambda i: abs(data.frames[i].time-row['t90'])) if math.isfinite(row['t90']) else -1
            separation.append(dict(config=c['tag'], seed=row['seed'],
                sample_time=data.frames[idx].time, used_in_chamber_fraction=values[idx][0],
                fresh_in_chamber_fraction=values[idx][1],
                used_seen_in_chamber=len(entries), used_seen_leaving_chamber=len(exits)))
        if curves:
            a = np.array(curves)
            for j, label in enumerate(('Usadas', 'Frescas')):
                valid = np.isfinite(a[:, :, j])
                mean = np.divide(np.nansum(a[:, :, j], axis=0), valid.sum(axis=0),
                                 out=np.full(a.shape[1], np.nan), where=valid.sum(axis=0)>0)
                ax.plot([f.time for f in data.frames], mean, label=label)
        ax.set(title=c['tag'], xlabel='Tiempo [s]', ylim=(0, 1))
        ax.grid(alpha=.2)
        ax.legend()
    axes[0].set_ylabel('Fracción de cada estado dentro de la cámara')
    save(fig, 'separacion')
    if separation:
        write_csv(out / 'separation.csv', list(separation[0]), separation)
    best = min((s for s in summary if s['reached_t90'] == args.realizations),
               key=lambda s: s['t90_mean'], default=None)
    lines = ['# Estudio de obstáculos con proporción áurea', '',
        f'φ = {PHI:.12f}. {args.realizations} semillas por configuración, N=100, tf={args.time:g} s.',
        'Motor, fuentes Java, tests, pom.xml y JAR sin cambios: hashes antes/después en metadata.json.', '',
        '| Configuración | t90 medio [s] | σ [s] | Alcanzan t90 | Fallas |',
        '|---|---:|---:|---:|---:|']
    for s in summary:
        lines.append(f'| {s["value"]} | {s["t90_mean"]:.3f} | {s["t90_std"]:.3f} | {s["reached_t90"]}/{args.realizations} | {s["failed"]} |')
    lines += ['', f'Menor promedio observado entre configuraciones completas: **{best["value"]}**.' if best else 'Ninguna configuración completó t90 en todas las semillas.', '',
        'Las medias excluyen t90 no alcanzados; no reemplazamos censura por tf. σ es dispersión entre semillas, no error estándar.',
        'Se usan las mismas semillas; las posiciones iniciales cambian con los obstáculos por el rechazo geométrico.', '',
        '## Geometría y alcance',
        'Tres tabiques de discos R=r desde (r,W/φ) hasta (L−d/φᵖ,W/2), p=1,2,3. '
        'La cámara superior se comunica junto al arco derecho. Los huecos del tabique no admiten una partícula. '
        'El embudo de referencia usa largo L/(2φ). Todos los mapas pasan la validación del motor '
        'y una comprobación conexa de paso 0,5 mm sin regiones aisladas sin arco (aproximación de grilla).',
        'La inicialización original es uniforme: hay partículas frescas dentro de la cámara desde t=0. '
        'La geometría no distingue colores; las cámaras son accesibles en ambos sentidos. '
        'Una separación permanente selectiva no está garantizada por este modelo elástico.', '',
        '## Comprobación de separación',
        'separacion.png muestra P(cámara|usada) y P(cámara|fresca), promediadas entre semillas con denominador no nulo. '
        'separation.csv guarda estas fracciones en la muestra más próxima a t90 (paso 0,5 s) '
        'y salidas observadas después de haber visto una partícula usada en la cámara. '
        'Este último conteo es un límite inferior: puede perder visitas entre muestras; no prueba retención continua.']
    for c in configs[:3]:
        group = [r for r in separation if r['config'] == c['tag']]
        if group:
            lines.append(f'- {c["tag"]}: promedio de {statistics.fmean(r["used_seen_leaving_chamber"] for r in group):.1f} partículas usadas por corrida observadas saliendo de la cámara.')
    lines += ['', '## Reproducir', '```bash',
        f'../.venv/bin/python scripts/golden_ratio_study.py --realizations {args.realizations} --seed-base {args.seed_base} --time {args.time:g} --jobs {args.jobs}',
        '```', '', 'Configuraciones: configs/golden_ratio/. Datos crudos, logs, comandos y figuras PNG/PDF en esta carpeta.']
    (out / 'RESULTADOS.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines[:15]), flush=True)


if __name__ == '__main__':
    main()
