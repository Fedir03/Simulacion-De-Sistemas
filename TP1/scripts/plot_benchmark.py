#!/usr/bin/env python3
"""
Grafica cualquier CSV generado por benchmark-m o benchmark-n — pensado para
usar EN VIVO durante la demo: corré el benchmark que pida el profesor, después
apuntá este script al CSV resultante.

Uso:
    python plot_benchmark.py archivo1.csv [archivo2.csv ...] [--out=grafico.png] [--linear]

- Podés pasar 1 o varios CSV juntos (se superponen en el mismo gráfico —
  útil para comparar dos corridas, ej. dos N distintos, o pared vs periódico).
- Detecta solo por las columnas si es un CSV de benchmark-m (tiene "method")
  o de benchmark-n (tiene "N","L","M") — no hace falta indicarlo a mano.
- Sin --out, abre una ventana en vez de guardar un archivo.
- --linear desactiva la escala logarítmica (por si un profesor la pide en
  escala lineal para algún caso puntual).

Ejemplos:
    python plot_benchmark.py bench_m_300.csv
    python plot_benchmark.py bench_n_libre_custom.csv bench_n_fija_custom.csv
"""
import sys
import pandas as pd
import matplotlib.pyplot as plt


def is_benchmark_m(df):
    return "method" in df.columns


def plot_benchmark_m(paths, log_scale, out):
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ["#2a9d8f", "#e63946", "#457b9d", "#f4a261"]

    for i, path in enumerate(paths):
        df = pd.read_csv(path)
        color = colors[i % len(colors)]
        n = df["N"].iloc[0]
        brute = df[df["method"] == "brute"]
        cim = df[df["method"] == "cim"].sort_values("M")

        if not brute.empty:
            ax.axhline(brute["meanMs"].iloc[0], color=color, linestyle=":", alpha=0.5,
                       label=f"Fuerza bruta N={n} ({brute['meanMs'].iloc[0]:.3f} ms)")
        ax.errorbar(cim["M"], cim["meanMs"], yerr=cim["stdDevMs"], fmt="o-",
                    color=color, capsize=3, label=f"CIM N={n} ({path})")

    ax.set_xlabel("M (celdas por lado de la grilla)")
    ax.set_ylabel("Tiempo (ms)")
    if log_scale:
        ax.set_yscale("log")
    ax.set_title("Tiempo de ejecución vs M — Fuerza Bruta vs Cell Index Method")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    return fig


def plot_benchmark_n(paths, log_scale, out):
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ["#2a9d8f", "#e63946", "#457b9d", "#f4a261"]

    for i, path in enumerate(paths):
        df = pd.read_csv(path).sort_values("N")
        color = colors[i % len(colors)]
        ax.errorbar(df["N"], df["meanMs"], yerr=df["stdDevMs"], fmt="o-",
                    color=color, capsize=3, label=path)

    ax.set_xlabel("N (cantidad de partículas)")
    ax.set_ylabel("Tiempo (ms)")
    if log_scale:
        ax.set_xscale("log")
        ax.set_yscale("log")
    ax.set_title("Tiempo de ejecución vs N — Cell Index Method")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    return fig


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    out = None
    log_scale = True
    paths = []
    for arg in args:
        if arg.startswith("--out="):
            out = arg.split("=", 1)[1]
        elif arg == "--linear":
            log_scale = False
        elif arg.startswith("--"):
            sys.exit(f"Opción desconocida: {arg}\n{__doc__}")
        else:
            paths.append(arg)

    if not paths:
        sys.exit(__doc__)

    first_df = pd.read_csv(paths[0])
    if is_benchmark_m(first_df):
        fig = plot_benchmark_m(paths, log_scale, out)
    else:
        fig = plot_benchmark_n(paths, log_scale, out)

    if out:
        fig.savefig(out, dpi=200)
        print(f"Guardado: {out}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
