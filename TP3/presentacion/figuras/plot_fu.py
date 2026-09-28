"""F_u(t) de una o más realizaciones representativas (diapositivas 17, 25 y 29).

Cada curva se lee de un registro de eventos completo (<salida>_events.txt): F_u sube
un escalón 1/N en cada choque con gol = 1. Se marca t90 de cada curva.

Realizaciones representativas: la semilla con t90 más cercano a la media y a la
mediana de su barrido (semillas 101-150).
    Mesa vacía:  semilla 141, t90 = 22.44 s  (arq_vacia: <t90> = 22.59 s)
    Cuenco:      semilla 140, t90 = 13.36 s  (cuenco_fino_radio R_f = 0.34: <t90> = 13.31 s)

Uso, desde la raíz del repositorio (ver los comandos generate/simulate en figuras/README.md):
    python3 TP3/presentacion/figuras/plot_fu.py \\
        TP3/generated/vacia_s141/full_events.txt "Mesa vacía" --out fu-temporal-vacia.pdf
    python3 TP3/presentacion/figuras/plot_fu.py \\
        TP3/generated/elegida_s140/full_events.txt "Cuenco" --out fu-temporal-cuenco.pdf
    python3 TP3/presentacion/figuras/plot_fu.py \\
        TP3/generated/elegida_s140/full_events.txt "Cuenco" \\
        TP3/generated/vacia_s141/full_events.txt "Mesa vacía" --out fu-temporal-elegida.pdf

Con una sola curva no se dibuja leyenda. --out relativo se guarda en este directorio.
"""

import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams.update({"font.size": 14})

# Series en la paleta de los barridos (TPBlue primero); la última curva es la referencia, en gris.
COLORES = ["#3939B5", "#E08E0B", "#2E8B57", "#C0392B"]
COLOR_REF = "#4D4D4D"
N = 100


def goles(events):
    tiempos = [0.0]
    with open(events, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("#") and line.split()[5] == "1":
                tiempos.append(float(line.split()[0]))
    return tiempos


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("curvas", nargs="+", help="pares: registro_de_eventos etiqueta")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if len(args.curvas) % 2:
        parser.error("las curvas van de a pares: registro_de_eventos etiqueta")
    pares = list(zip(args.curvas[::2], args.curvas[1::2]))

    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=200)
    ax.axhline(0.9, color="0.3", linestyle="--", linewidth=1.2, zorder=1)
    t_max = 0.0
    for i, (events, etiqueta) in enumerate(pares):
        tiempos = goles(events)
        fu = [k / N for k in range(len(tiempos))]
        t90 = tiempos[next(k for k, v in enumerate(fu) if v >= 0.9)]
        color = COLOR_REF if len(pares) > 1 and i == len(pares) - 1 else COLORES[i % len(COLORES)]
        ax.step(tiempos, fu, where="post", color=color, linewidth=1.8, zorder=3,
                label=rf"{etiqueta}: $t_{{90}} = {t90:.2f}$ s")
        ax.axvline(t90, color=color, linestyle=":", linewidth=1.2, zorder=2)
        t_max = max(t_max, tiempos[-1])
        print(f"{etiqueta}: t90 = {t90}, goles = {len(tiempos) - 1}")
        if len(pares) == 1:
            ax.annotate(rf"$t_{{90}} = {t90:.2f}$ s", xy=(t90, 0.9), xytext=(t90 + 0.06 * tiempos[-1], 0.55),
                        arrowprops=dict(arrowstyle="->", color="0.3"))

    ax.set_xlabel(r"$t$ [s]")
    ax.set_ylabel(r"$F_u$")
    ax.set_xlim(0, t_max * 1.05)
    ax.set_ylim(0, 1.02)
    ax.grid(alpha=0.3)
    if len(pares) > 1:
        ax.legend(loc="lower right")

    fig.tight_layout(pad=0.3)
    out = Path(args.out)
    if not out.is_absolute():
        out = Path(__file__).parent / out
    fig.savefig(out)
    print(f"Guardado: {out}")


if __name__ == "__main__":
    main()
