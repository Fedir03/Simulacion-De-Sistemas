"""Desplazamiento cuadrático medio y coeficiente de difusión (diapositivas 30 y 31).

DCM de una realización (semilla 101), promediado sobre las N partículas (frescas y
usadas): z(t) = < |r_i(t) - r_i(0)|^2 >_i, en los estados que escribe el motor cada
10 eventos (posiciones exactas en cada t_e, sin interpolar).
Ajuste lineal por el origen, z = c t, minimizando E(c) = sum_k (z_k - c t_k)^2:
c = sum(z_k t_k) / sum(t_k^2) y D = c / 2. Solo se ajusta 0 < t <= T_AJUSTE: más
tarde el confinamiento en la mesa satura z (mesa vacía: (L^2 + W^2)/6 ~ 0.32 m^2).

<t90> y su desvío salen de los barridos arq_* (semillas 101-150).

Uso, desde la raíz del repositorio:
    for c in vacia central_R0.32 central_embudo_a0.05 galton_s0.10 cuenco_fino_R0.34; do
        map="--obstacles TP3/configs/$c.txt"; [ $c = vacia ] && map="--obstacle-algorithm none"
        java -jar TP3/target/tp3.jar generate --seed 101 $map --out TP3/generated/dcm/ic_$c.txt
        java -jar TP3/target/tp3.jar simulate --input TP3/generated/dcm/ic_$c.txt --time 10 \\
            --every 10 --events-out none --out TP3/generated/dcm/sim_$c.txt
    done
    python3 TP3/presentacion/figuras/plot_dcm.py

Regenera dcm-ajuste.pdf y d-vs-t90.pdf en este directorio e imprime D de cada configuración.
"""

import csv
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FormatStrFormatter, NullFormatter
from pathlib import Path

HERE = Path(__file__).parent
TP3 = HERE.parents[1]
sys.path.insert(0, str(TP3 / "scripts"))
from simulation_io import parse_simulation  # noqa: E402

plt.rcParams.update({"font.size": 14})

T_AJUSTE = 1.0   # [s] fin de la ventana de ajuste
T_GRAFICO = 3.0  # [s] hasta dónde se dibuja z(t) en dcm-ajuste
COLOR_ELEGIDA = "#3939B5"  # TPBlue
COLOR_REF = "#4D4D4D"

# (archivo de simulación, barrido con <t90>, etiqueta)
CONFIGS = [
    ("vacia", "arq_vacia", "Mesa vacía"),
    ("central_R0.32", "arq_central_R0.32", "Disco solo"),
    ("central_embudo_a0.05", "arq_central_embudo_a0.05", "Embudo"),
    ("galton_s0.10", "arq_galton_s0.10", "Galton"),
    ("cuenco_fino_R0.34", "arq_cuenco_fino_R0.34", "Cuenco"),
]


def dcm(sim):
    data = parse_simulation(sim)
    inicio = {p[0]: (p[1], p[2]) for p in data.frames[0].particles}
    t, z = [], []
    for frame in data.frames:
        t.append(frame.time)
        z.append(sum((p[1] - inicio[p[0]][0]) ** 2 + (p[2] - inicio[p[0]][1]) ** 2
                     for p in frame.particles) / len(frame.particles))
    return t, z


def ajuste(t, z):
    ventana = [(tk, zk) for tk, zk in zip(t, z) if 0 < tk <= T_AJUSTE]
    return sum(tk * zk for tk, zk in ventana) / sum(tk * tk for tk, _ in ventana)


def t90(barrido):
    with open(TP3 / "generated" / "sweeps" / barrido / "summary.csv", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    return float(row["t90_mean"]), float(row["t90_std"])


def main():
    curvas = {}
    for nombre, barrido, etiqueta in CONFIGS:
        t, z = dcm(TP3 / "generated" / "dcm" / f"sim_{nombre}.txt")
        c = ajuste(t, z)
        curvas[nombre] = (t, z, c, *t90(barrido), etiqueta)
        print(f"{etiqueta:12s} c = {c:.5f} m²/s  D = {c / 2:.5f} m²/s  <t90> = {curvas[nombre][3]:.2f} s")

    # z(t) y ajuste: mesa vacía y configuración elegida.
    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=200)
    for nombre, color in (("vacia", COLOR_REF), ("cuenco_fino_R0.34", COLOR_ELEGIDA)):
        t, z, c, _, _, etiqueta = curvas[nombre]
        pares = [(tk, zk) for tk, zk in zip(t, z) if tk <= T_GRAFICO]
        ax.plot(*zip(*pares), color=color, linewidth=1.6, label=etiqueta)
        ax.plot([0, T_AJUSTE], [0, c * T_AJUSTE], color=color, linestyle="--", linewidth=1.4)
    ax.axvspan(0, T_AJUSTE, color="0.5", alpha=0.12, lw=0)
    ax.set_xlabel(r"$t$ [s]")
    ax.set_ylabel(r"DCM [m$^2$]")
    ax.set_xlim(0, T_GRAFICO)
    ax.set_ylim(0, None)
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=12)
    fig.tight_layout(pad=0.3)
    fig.savefig(HERE / "dcm-ajuste.pdf")
    plt.close(fig)

    # D vs <t90>, barras solo en <t90>.
    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=200)
    for nombre, _, _ in CONFIGS:
        _, _, c, media, desvio, etiqueta = curvas[nombre]
        color = COLOR_ELEGIDA if nombre.startswith("cuenco") else COLOR_REF
        ax.errorbar(media, c / 2, xerr=desvio, fmt="o", color=color, capsize=4, markersize=7)
        # "Disco solo" y "Embudo" caen casi en el mismo punto: una etiqueta abajo y otra arriba.
        # "Mesa vacía" va abajo a la izquierda para no chocar con el borde superior.
        dx, dy, ha = {"Disco solo": (6, -18, "left"), "Mesa vacía": (-6, -18, "right")}.get(etiqueta, (6, 6, "left"))
        ax.annotate(etiqueta, (media, c / 2), textcoords="offset points", xytext=(dx, dy), ha=ha, fontsize=12)
    ax.set_xlabel(r"$\langle t_{90} \rangle$ [s]")
    ax.set_ylabel(r"$D$ [m$^2$/s]")
    # Escala log: con eje lineal hasta 0.05 (mesa vacía) los otros cuatro puntos quedan
    # apretados entre 0.01 y 0.02.
    ax.set_yscale("log")
    ax.set_ylim(0.01, 0.06)
    ax.yaxis.set_major_locator(FixedLocator([0.01, 0.015, 0.02, 0.03, 0.04, 0.05]))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%g"))  # "%.2f" redondearía 0.015
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(alpha=0.3)
    fig.tight_layout(pad=0.3)
    fig.savefig(HERE / "d-vs-t90.pdf")
    plt.close(fig)
    print(f"Guardado: {HERE / 'dcm-ajuste.pdf'}, {HERE / 'd-vs-t90.pdf'}")


if __name__ == "__main__":
    main()
