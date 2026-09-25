"""Barrido de parámetros: genera y simula varias realizaciones por valor y resume t90.

Cada realización k usa --seed (seed-base + k) para las posiciones y direcciones
iniciales. Los argumentos después de `--` se pasan tal cual a `generate`, por ejemplo
`-- --obstacle-algorithm funnel` o `-- --obstacles TP3/configs/funnel.txt`.

Ejemplos, desde la raíz del repositorio:

    # 1.2: largo del embudo, 10 realizaciones por valor, tmax = 100 s.
    python3 TP3/scripts/sweep.py --name embudo --param obstacle-funnel-length \\
        --values 0.1 0.2 0.3 0.4 --realizations 10 -- --obstacle-algorithm funnel

    # 1.1: tiempo de ejecución vs N en la mesa vacía, tf = 30 s.
    python3 TP3/scripts/sweep.py --name runtime --param n --values 50 100 200 400 \\
        --realizations 10 --time 30 -- --obstacle-algorithm none

    # Una configuración fija (sin --param), por ejemplo la mesa vacía de referencia.
    python3 TP3/scripts/sweep.py --name vacia --realizations 10 -- --obstacle-algorithm none

Salidas en TP3/generated/sweeps/<name>/: runs.csv (una fila por realización),
summary.csv (una fila por valor) y meta.json (comando y parámetros).
El desvío es el muestral entre realizaciones: cada una aporta un único t90.
runtime_s es el tiempo del ciclo de eventos informado por el motor. Con varias
corridas en paralelo compiten por la CPU: para el punto 1.1 usar --jobs 1.
"""
import argparse
import csv
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
RUN_FIELDS = ['param', 'value', 'seed', 'status', 'K', 't90', 'goals', 'events', 'runtime_s', 'error']
SUMMARY_FIELDS = ['param', 'value', 'realizations', 'failed', 'reached_t90',
                  't90_mean', 't90_std', 'goals_mean', 'goals_std', 'runtime_mean_s', 'runtime_std_s', 'events_mean']
# Sin estados intermedios: la trayectoria tiene solamente el inicial y el final.
NO_FRAMES = str(2 ** 31 - 1)


def parse_result(path):
    """Lee el comentario final `# tf=... t90=... runtime=...` de una trayectoria."""
    last = None
    with open(path, encoding='utf-8') as source:
        for line in source:
            if line.startswith('# tf='):
                last = line
    if last is None:
        raise ValueError(f'{path}: falta el comentario final de resultados')
    fields = dict(token.split('=', 1) for token in last[1:].split())
    return {
        't90': float(fields['t90']), 'goals': int(fields['Ng']),
        'events': int(fields['events']), 'runtime_s': float(fields['runtime']),
    }


def count_obstacles(path):
    with open(path, encoding='utf-8') as source:
        header = dict(token.split('=', 1) for token in source.readline().split())
    return int(header['K'])


def run_one(jar, workdir, param, value, seed, sim_time, generate_args):
    tag = f'{value}_{seed}'.replace('/', '_')
    initial, trajectory = workdir / f'ic_{tag}.txt', workdir / f'sim_{tag}.txt'
    row = {'param': param or '', 'value': value if value is not None else '', 'seed': seed}
    command = ['java', '-jar', str(jar), 'generate', '--seed', str(seed), '--out', str(initial), *generate_args]
    if param:
        command += [f'--{param}', str(value)]
    generated = subprocess.run(command, capture_output=True, text=True)
    if generated.returncode != 0:
        return {**row, 'status': 'generate_failed', 'error': generated.stderr.strip()}
    simulated = subprocess.run(['java', '-jar', str(jar), 'simulate', '--input', str(initial), '--time', str(sim_time),
                                '--every', NO_FRAMES, '--events-out', 'none', '--out', str(trajectory)], capture_output=True, text=True)
    if simulated.returncode != 0:
        return {**row, 'status': 'simulate_failed', 'error': simulated.stderr.strip()}
    result = {**row, 'status': 'ok', 'K': count_obstacles(initial), **parse_result(trajectory)}
    initial.unlink()
    trajectory.unlink()
    return result


def summarize(rows):
    def mean_std(values):
        if not values:
            return math.nan, math.nan
        return statistics.fmean(values), statistics.stdev(values) if len(values) > 1 else math.nan

    groups = {}
    for row in rows:
        groups.setdefault((row['param'], row['value']), []).append(row)
    summary = []
    for (param, value), group in groups.items():
        ok = [row for row in group if row['status'] == 'ok']
        reached = [row['t90'] for row in ok if math.isfinite(row['t90'])]
        t90_mean, t90_std = mean_std(reached)
        goals_mean, goals_std = mean_std([row['goals'] for row in ok])
        runtime_mean, runtime_std = mean_std([row['runtime_s'] for row in ok])
        summary.append({
            'param': param, 'value': value, 'realizations': len(ok), 'failed': len(group) - len(ok),
            'reached_t90': len(reached), 't90_mean': t90_mean, 't90_std': t90_std,
            'goals_mean': goals_mean, 'goals_std': goals_std,
            'runtime_mean_s': runtime_mean, 'runtime_std_s': runtime_std,
            'events_mean': statistics.fmean([row['events'] for row in ok]) if ok else math.nan,
        })
    return summary


def write_csv(path, fields, rows):
    with open(path, 'w', newline='', encoding='utf-8') as target:
        writer = csv.DictWriter(target, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    split = argv.index('--') if '--' in argv else len(argv)
    own, generate_args = argv[:split], argv[split + 1:]
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                     usage='%(prog)s --name NOMBRE [opciones] -- [opciones de generate]')
    parser.add_argument('--name', required=True, help='nombre del barrido (carpeta de salida)')
    parser.add_argument('--param', help='opción de generate que se barre, sin guiones (ej. obstacle-funnel-length, n)')
    parser.add_argument('--values', nargs='+', help='valores del parámetro barrido')
    parser.add_argument('--realizations', type=int, default=10, help='realizaciones por valor (10)')
    parser.add_argument('--seed-base', type=int, default=1, help='semilla de la primera realización (1)')
    parser.add_argument('--time', type=float, default=100.0, help='tiempo simulado en segundos (100)')
    parser.add_argument('--jobs', type=int, default=max(1, (os.cpu_count() or 2) - 1), help='procesos en paralelo')
    parser.add_argument('--jar', type=Path, default=MODULE / 'target' / 'tp3.jar')
    parser.add_argument('--out-dir', type=Path, help='carpeta de salida (TP3/generated/sweeps/<name>)')
    args = parser.parse_args(own)
    if bool(args.param) != bool(args.values):
        parser.error('--param y --values van juntos')
    if args.realizations < 1 or args.jobs < 1:
        parser.error('--realizations y --jobs deben ser positivos')
    if args.param and f'--{args.param}' in generate_args:
        parser.error(f'--{args.param} se barre; no repetirlo después de --')
    if any(flag in generate_args for flag in ('--seed', '--out')):
        parser.error('--seed y --out los maneja el barrido')
    if not args.jar.exists():
        parser.error(f'no existe {args.jar}; compilar con mvn -f TP3/pom.xml package')
    out_dir = args.out_dir or MODULE / 'generated' / 'sweeps' / args.name
    out_dir.mkdir(parents=True, exist_ok=True)
    values = args.values or [None]
    seeds = range(args.seed_base, args.seed_base + args.realizations)
    tasks = [(value, seed) for value in values for seed in seeds]
    started = time.time()
    rows = []
    with tempfile.TemporaryDirectory(prefix='sweep_') as tmp, ThreadPoolExecutor(args.jobs) as pool:
        futures = [pool.submit(run_one, args.jar, Path(tmp), args.param, value, seed, args.time, generate_args)
                   for value, seed in tasks]
        for done, future in enumerate(as_completed(futures), 1):
            row = future.result()
            rows.append(row)
            if row['status'] != 'ok':
                print(f'  [{row["status"]}] valor={row["value"]} seed={row["seed"]}: {row["error"]}', file=sys.stderr)
            print(f'\r{done}/{len(tasks)} corridas', end='', file=sys.stderr, flush=True)
    print(file=sys.stderr)
    order = {value: i for i, value in enumerate(values)}
    rows.sort(key=lambda row: (order[row['value'] if args.param else None], row['seed']))
    summary = summarize(rows)
    write_csv(out_dir / 'runs.csv', RUN_FIELDS, rows)
    write_csv(out_dir / 'summary.csv', SUMMARY_FIELDS, summary)
    with open(out_dir / 'meta.json', 'w', encoding='utf-8') as meta:
        json.dump({'argv': argv, 'param': args.param, 'values': args.values, 'realizations': args.realizations,
                   'seed_base': args.seed_base, 'time': args.time, 'generate_args': generate_args,
                   'elapsed_s': round(time.time() - started, 1)}, meta, indent=2, ensure_ascii=False)
    print(f'{"valor":>10} {"ok":>3} {"t90":>4} {"<t90> [s]":>10} {"σ [s]":>8} {"<Ng>":>6} {"runtime [s]":>12}')
    for s in summary:
        label = s['value'] if args.param else '-'
        print(f'{label:>10} {s["realizations"]:>3} {s["reached_t90"]:>4} {s["t90_mean"]:>10.2f} {s["t90_std"]:>8.2f} '
              f'{s["goals_mean"]:>6.1f} {s["runtime_mean_s"]:>12.3f}')
    print(f'Resultados: {out_dir}')
    failed = sum(s['failed'] for s in summary)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
