"""Barrido reproducible de inclinación del embudo con todos los radios iguales a r.

Ejecutar desde cualquier directorio con el entorno de TP3. Requiere tp3.jar compilado.
Guarda mapas, condiciones iniciales, resultados, figuras y videos por eventos.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

from simulation_io import parse_simulation
from sweep import parse_result, summarize, write_csv, RUN_FIELDS, SUMMARY_FIELDS
from check_map import analyze

MODULE = Path(__file__).resolve().parents[1]
RADIUS = 0.0175


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=MODULE / 'generated/funnel_min_radius')
    parser.add_argument('--angles', type=float, nargs='+', default=[25, 35, 45, 55, 65, 75])
    parser.add_argument('--realizations', type=int, default=5)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if args.realizations < 2 or args.jobs < 1:
        parser.error('Se necesitan al menos dos realizaciones y un proceso')
    if any(not 0 < a < 90 or 0.24 / math.tan(math.radians(a)) > 0.6 for a in args.angles):
        parser.error('El ángulo debe ser mayor o igual a atan(0.24/0.6) y menor que 90 grados')
    out = args.out.resolve()
    for folder in ('maps', 'initial', 'results', 'trajectories', 'animations', 'logs'):
        (out / folder).mkdir(parents=True, exist_ok=True)
    java = ['java', '-jar', str(MODULE / 'target/tp3.jar')]
    commands = []

    def run(command, log):
        commands.append([str(x) for x in command])
        with (out / 'logs' / log).open('w') as stream:
            subprocess.run([str(x) for x in command], stdout=stream, stderr=subprocess.STDOUT, check=True)

    configs = []
    for angle in args.angles:
        tag = f'embudo_{angle:g}deg'
        length = 0.24 / math.tan(math.radians(angle))
        initial = out / 'initial' / f'{tag}_seed1.txt'
        config = out / 'maps' / f'{tag}.txt'
        run(java + ['generate', '--seed', '1', '--obstacle-algorithm', 'funnel',
                    '--obstacle-funnel-length', str(length), '--obstacle-max-radius', str(RADIUS),
                    '--obstacles-out', config, '--out', initial], f'{tag}_map.log')
        data = parse_simulation(initial)
        assert data.obstacles and all(o[2] == RADIUS for o in data.obstacles)
        check = analyze(data, RADIUS, 0.0005)
        assert not check['trapped'] and check['left_open'] and check['right_open'], (tag, check['trapped'])
        configs.append(dict(tag=tag, angle=angle, length=length, K=len(data.obstacles),
                            accessible_area_m2=float(check['area']), map=str(config)))
        print(f'{tag}: K={len(data.obstacles)}, R={RADIUS}, ambos arcos accesibles', flush=True)
    configs.append(dict(tag='mesa_vacia', angle=None, length=None, K=0, map=None))
    (out / 'metadata.json').write_text(json.dumps(dict(radius_m=RADIUS, N=100, time_s=100,
        seeds=list(range(1, args.realizations + 1)), angle_definition='respecto del eje horizontal',
        map_check_grid_m=0.0005, animation_every_events=100, configurations=configs), indent=2))

    def simulate(task):
        config, seed = task
        tag = config['tag']
        initial = out / 'initial' / f'{tag}_seed{seed}.txt'
        gen = ['--obstacles', config['map']] if config['map'] else ['--obstacle-algorithm', 'none']
        run(java + ['generate', '--seed', str(seed), *gen, '--out', initial], f'{tag}_{seed}_generate.log')
        result = out / 'results' / f'{tag}_seed{seed}.txt'
        run(java + ['simulate', '--input', initial, '--time', '100', '--every', str(2**31-1),
                    '--out', result], f'{tag}_{seed}_simulate.log')
        row = dict(param='angle_deg' if config['angle'] is not None else '',
                   value=config['angle'] if config['angle'] is not None else '',
                   seed=seed, status='ok', K=config['K'], **parse_result(result))
        print(f'{tag}, seed={seed}: t90={row["t90"]:.3f} s', flush=True)
        return row

    with ThreadPoolExecutor(args.jobs) as pool:
        rows = list(pool.map(simulate, [(c, s) for c in configs for s in range(1, args.realizations + 1)]))
    summary = summarize(rows)
    write_csv(out / 'runs.csv', RUN_FIELDS, rows)
    write_csv(out / 'summary.csv', SUMMARY_FIELDS, summary)

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    fig, ax = plt.subplots(figsize=(8, 5))
    points = [s for s in summary if s['param']]
    baseline = next(s for s in summary if not s['param'])
    ax.errorbar([s['value'] for s in points], [s['t90_mean'] for s in points],
                yerr=[s['t90_std'] for s in points], fmt='o', capsize=5,
                label=f'Embudos: media ± desvío ({args.realizations} semillas)')
    for s in points:
        individual = [r['t90'] for r in rows if r['value'] == s['value'] and math.isfinite(r['t90'])]
        ax.scatter([s['value']] * len(individual), individual, s=20, color='#2563eb', alpha=.35)
        ax.annotate(f'K={next(c["K"] for c in configs if c["angle"] == s["value"])}\n'
                    f'{s["reached_t90"]}/{s["realizations"]} alcanzan t90',
                    (s['value'], s['t90_mean'] + s['t90_std']), xytext=(0, 7),
                    textcoords='offset points', ha='center', fontsize=8)
    mean, std = baseline['t90_mean'], baseline['t90_std']
    ax.axhline(mean, color='0.35', ls='--', label='Mesa vacía: media ± desvío')
    ax.axhspan(mean - std, mean + std, color='0.5', alpha=.15)
    ax.set(xlabel='Inclinación nominal respecto del eje horizontal [°]', ylabel='t90 [s]',
           title='Embudos hacia ambos arcos · radio fijo R = r = 0,0175 m', xticks=args.angles)
    ax.margins(x=.12, y=.25)
    ax.grid(alpha=.2)
    ax.legend(fontsize=9)
    fig.tight_layout()
    for suffix in ('png', 'pdf'):
        fig.savefig(out / f't90_vs_inclinacion.{suffix}', dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(math.ceil(len(args.angles)/2), 2, figsize=(12, 4*math.ceil(len(args.angles)/2)), squeeze=False)
    for ax, c in zip(axes.flat, configs[:-1]):
        data = parse_simulation(out / 'initial' / f'{c["tag"]}_seed1.txt')
        for x, y, radius in data.obstacles:
            ax.add_patch(Circle((x, y), radius, color='#475569'))
        for x in (0, 1.2):
            ax.plot([x, x], [.24, .44], color='#16a34a', lw=5, clip_on=False)
        for x in (0, 1.2):
            direction = 1 if x == 0 else -1
            for y, end in ((.44, .68), (.24, 0)):
                ax.plot([x, x + direction*c['length']], [y, end], '--', color='#e8790b', lw=1)
        ax.set(xlim=(0, 1.2), ylim=(0, .68), title=f'{c["angle"]:g}° · K={c["K"]} · a={c["length"]:.3f} m', xlabel='x [m]', ylabel='y [m]')
        ax.set_aspect('equal')
    for ax in list(axes.flat)[len(args.angles):]:
        ax.set_visible(False)
    fig.tight_layout()
    fig.savefig(out / 'mapas.png', dpi=160)
    plt.close(fig)

    videos = []
    for c in configs:
        group = [r for r in rows if r['value'] == (c['angle'] if c['angle'] is not None else '')]
        finite = [r for r in group if math.isfinite(r['t90'])]
        median = statistics.median(r['t90'] for r in finite) if finite else 100
        representative = min(finite or group, key=lambda r: abs(r['t90']-median) if math.isfinite(r['t90']) else math.inf)
        seed, t90 = representative['seed'], representative['t90']
        duration = min(100, t90 + .01) if math.isfinite(t90) else 100
        tag = c['tag']
        trajectory = out / 'trajectories' / f'{tag}_seed{seed}.txt'
        run(java + ['simulate', '--input', out / 'initial' / f'{tag}_seed{seed}.txt',
                    '--time', str(duration), '--every', '100', '--out', trajectory], f'{tag}_animation_sim.log')
        video = out / 'animations' / f'{tag}.mp4'
        run([sys.executable, MODULE / 'scripts/animate.py', trajectory, '--out', video,
             '--fps', '30', '--dpi', '80'], f'{tag}_render.log')
        probe = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=nb_frames,width,height,duration', '-of', 'json', str(video)], text=True)
        stream = json.loads(probe)['streams'][0]
        frames = len(parse_simulation(trajectory).frames)
        assert int(stream['nb_frames']) == frames
        videos.append(dict(tag=tag, seed=seed, t90=t90, saved_frames=frames, **stream))
        (out / 'videos.json').write_text(json.dumps(videos, indent=2))
        print(f'Video listo: {video.name} ({frames} frames, seed={seed})', flush=True)
    (out / 'commands.json').write_text(json.dumps(commands, indent=2))
    print(f'Resultados completos: {out}', flush=True)


if __name__ == '__main__':
    main()
