#!/usr/bin/env python3
"""Genera F7: rapidez media <v>(t) (v = |v|) para identificar el estacionario de f(v) (2.3, N = 100, sin obstáculos).

Para cada realización se promedia |v| sobre sus N partículas en cada salida (múltiplos de dt2, sin interpolar); la curva
es la media entre realizaciones y la banda, ±σ muestral entre realizaciones (D10).
"""

from __future__ import annotations

import argparse
import statistics
from pathlib import Path

from observables import configure_matplotlib
from speed_distribution import load_runs


TP4_DIR = Path(__file__).resolve().parents[2]
DT2 = 0.04  # D3


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=TP4_DIR / "outputs" / "2.3")
    parser.add_argument("--output", type=Path, default=TP4_DIR / "presentacion" / "figuras" / "F7-v-media-vs-t.pdf")
    parser.add_argument("--t-max", type=float, default=30.0, help="tiempo máximo mostrado (s)")
    parser.add_argument("--t-est", type=float, default=0.75, help="inicio del estacionario elegido a ojo (D15)")
    args = parser.parse_args()

    times = [round(k * DT2, 2) for k in range(int(round(args.t_max / DT2)) + 1)]
    try:
        runs = load_runs(args.input, set(times))
    except ValueError as error:
        parser.error(str(error))

    means, sigmas = [], []
    for t in times:
        per_run = [statistics.fmean(next(v for time, v in frames.items() if abs(time - t) < 1e-6)) for frames in runs]
        means.append(statistics.fmean(per_run))
        sigmas.append(statistics.stdev(per_run))

    plt = configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.0, 4.4), layout="constrained")
    ax.fill_between(times, [m - s for m, s in zip(means, sigmas)], [m + s for m, s in zip(means, sigmas)],
                    color="#0072B2", alpha=0.2, linewidth=0)
    ax.plot(times, means, color="#0072B2", linewidth=2)
    # t_est se marca con una línea vertical (DEFINICIONES.md §5)
    ax.axvline(args.t_est, color="#555555", linestyle="--", linewidth=1.2)
    ax.text(args.t_est, 0.98, r" $t_{est}$", transform=ax.get_xaxis_transform(), ha="left", va="top",
            fontsize=18, color="#555555")
    ax.set_xlim(0, args.t_max)
    ax.set_xlabel(r"$t$ (s)")
    ax.set_ylabel(r"$\langle v \rangle$ (m/s)")
    ax.grid(alpha=0.22)

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"CreationDate": None})
    plt.close(fig)
    print(f"F7 generada: {output} ({len(runs)} realizaciones, {len(times)} salidas hasta t = {args.t_max:g} s)")
    for t in (0, 0.2, 0.4, 0.6, 1, 2, 5, 10, 20, 30):
        if t <= args.t_max:
            k = round(t / DT2)
            print(f"  t = {times[k]:5.2f} s   <v> = {means[k]:.4f} ± {sigmas[k]:.4f} m/s")


if __name__ == "__main__":
    main()
