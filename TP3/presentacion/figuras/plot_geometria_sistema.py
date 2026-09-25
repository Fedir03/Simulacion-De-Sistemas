"""Esquema estático del sistema (Geometría del Sistema, diapositiva 12).

No depende de una corrida real del motor -- es una ilustración fija con
posiciones/obstaculos generados a mano (semilla fija) solo para mostrar la
geometría del dominio con L, W, d, r y R_k marcados sobre el dibujo, como
pide la corrección real de TP2 (D9/D11: "L y r sobre el esquema").

Uso:
    python3 plot_geometria_sistema.py

Regenera figuras/geometria-sistema.png en este mismo directorio.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
from pathlib import Path

# Mismos colores que TPFresca / TPUsada / TPObstaculo / TPNavGray / TPBlue
# en template_presentacion_tp3.tex -- si se cambia la paleta allá, cambiar
# acá también.
COLOR_FRESCA = "#2E5FD0"
COLOR_USADA = "#C0392B"
COLOR_OBSTACULO = "#BFBFBF"
COLOR_GRIS = "#4D4D4D"
COLOR_BORDE = "#050505"

FONT_SIZE = 15  # grande a propósito: la figura se inserta angosta (ver
                # nota de tamaño de fuente en figuras/README.md).

L, W, d = 1.20, 0.68, 0.20
r = 0.0175

rng = np.random.default_rng(7)

fig, ax = plt.subplots(figsize=(7.3, 3.65), dpi=200)
ax.set_xlim(-0.40, L + 0.36)
ax.set_ylim(-0.30, W + 0.22)
ax.set_aspect("equal")
ax.axis("off")

# ---------- dominio ----------
# Lados largos (y=0, y=W) completos. Los cortos (x=0, x=L) con un hueco
# exactamente donde va el arco, para que el punteado rojo se vea sobre
# blanco y no salpicado sobre el negro del marco.
ax.plot([0, L], [0, 0], color=COLOR_BORDE, linewidth=1.6)
ax.plot([0, L], [W, W], color=COLOR_BORDE, linewidth=1.6)
for x_pared in (0.0, L):
    ax.plot([x_pared, x_pared], [0, W / 2 - d / 2], color=COLOR_BORDE, linewidth=1.6)
    ax.plot([x_pared, x_pared], [W / 2 + d / 2, W], color=COLOR_BORDE, linewidth=1.6)

# ---------- arcos (línea punteada sobre la pared, no un bloque sólido) ----------
for x_arco in (0.0, L):
    ax.plot([x_arco, x_arco], [W / 2 - d / 2, W / 2 + d / 2],
             color=COLOR_USADA, linewidth=2.2, linestyle=(0, (1.6, 1.6)),
             solid_capstyle="butt", zorder=2)

# "d" con flecha doble y tick punteado hacia el arco izquierdo
d_x = -0.10
ax.annotate("", xy=(d_x, W / 2 - d / 2), xytext=(d_x, W / 2 + d / 2),
            arrowprops=dict(arrowstyle="<->", color=COLOR_GRIS, lw=1.1))
ax.plot([d_x - 0.015, d_x + 0.015], [W / 2 - d / 2, W / 2 - d / 2], color=COLOR_GRIS, lw=1.1)
ax.plot([d_x - 0.015, d_x + 0.015], [W / 2 + d / 2, W / 2 + d / 2], color=COLOR_GRIS, lw=1.1)
ax.text(d_x - 0.05, W / 2, "$d$", ha="right", va="center", fontsize=FONT_SIZE, color=COLOR_GRIS)

# Marca del arco: dos líneas punteadas HORIZONTALES hacia afuera de cada
# pared (no diagonales), una en el extremo inferior y otra en el
# superior de la altura del arco. La palabra "arco" se escribe una sola
# vez, del lado izquierdo, para no competir por espacio con la flecha de
# W del lado derecho.
TICK_LEN = 0.07
for x_pared, signo in ((0.0, -1), (L, 1)):
    x_tick = x_pared + signo * TICK_LEN
    ax.plot([x_pared, x_tick], [W / 2 + d / 2, W / 2 + d / 2],
             color=COLOR_USADA, lw=1.0, linestyle=(0, (1.4, 1.4)))
    ax.plot([x_pared, x_tick], [W / 2 - d / 2, W / 2 - d / 2],
             color=COLOR_USADA, lw=1.0, linestyle=(0, (1.4, 1.4)))

ax.text(-TICK_LEN-0.03, W / 2 + d / 2 + 0.03, "arco", ha="center", va="bottom",
        fontsize=FONT_SIZE, color=COLOR_USADA)

# "W" con flecha doble a la derecha del dominio
w_x = L + 0.20
ax.annotate("", xy=(w_x, 0), xytext=(w_x, W),
            arrowprops=dict(arrowstyle="<->", color=COLOR_GRIS, lw=1.1))
ax.text(w_x + 0.05, W / 2, "$W$", ha="left", va="center", fontsize=FONT_SIZE, color=COLOR_GRIS)

# "L" con flecha doble debajo del dominio
l_y = -0.18
ax.annotate("", xy=(0, l_y), xytext=(L, l_y),
            arrowprops=dict(arrowstyle="<->", color=COLOR_GRIS, lw=1.1))
ax.text(L / 2, l_y - 0.06, "$L$", ha="center", va="top", fontsize=FONT_SIZE, color=COLOR_GRIS)

# ---------- obstáculos ----------
obstaculos = [
    (0.62, 0.42, 0.115),   # grande, central
    (0.24, 0.53, 0.055),
    (0.30, 0.16, 0.055),
    (0.92, 0.38, 0.045),   # marcado con R_k
]
for (ox, oy, orad) in obstaculos:
    ax.add_patch(Circle((ox, oy), orad, facecolor=COLOR_OBSTACULO,
                          edgecolor=COLOR_GRIS, linewidth=0.9, zorder=2))

# radio marcado sobre el obstáculo grande (sin texto -- ya son R_k y r
# los que llevan etiqueta). Punteado, igual estilo que R_k, r y d.
ox, oy, orad = obstaculos[0]
ang = np.deg2rad(48)
ax.annotate("", xy=(ox + orad * np.cos(ang), oy + orad * np.sin(ang)),
            xytext=(ox, oy),
            arrowprops=dict(arrowstyle="-", color=COLOR_BORDE, lw=1.1,
                             linestyle=(0, (1.2, 1.2))))

# R_k marcado sobre el obstáculo chico de la derecha -- tick VERTICAL
# (centro -> borde superior) para que quede en la misma dirección que el
# texto, pegado justo arriba (antes el tick apuntaba a la derecha y el
# texto se dibujaba arriba: dos direcciones distintas, por eso se veía
# "lejos").
ox, oy, orad = obstaculos[3]
ax.plot([ox, ox], [oy, oy + orad], color=COLOR_GRIS, lw=0.8, linestyle=(0, (1.5, 1.5)))
ax.text(ox, oy + orad + 0.02, "$R_k$", ha="center", va="bottom",
        fontsize=FONT_SIZE, color=COLOR_BORDE)

# ---------- partículas ----------
# Separación mínima grande a propósito: tiene que quedar lugar para la
# flecha de velocidad de cada partícula sin pisar a la vecina (ver más
# abajo, ARROW_REACH).
n_particulas = 22
n_usadas = 5
MIN_SEP = 0.10
puntos = []
intentos = 0
while len(puntos) < n_particulas and intentos < 20000:
    intentos += 1
    px = rng.uniform(0.05, L - 0.05)
    py = rng.uniform(0.05, W - 0.05)
    ok = all((px - ox) ** 2 + (py - oy) ** 2 > (orad + 0.045) ** 2 for ox, oy, orad in obstaculos)
    ok = ok and all((px - qx) ** 2 + (py - qy) ** 2 > MIN_SEP ** 2 for qx, qy in puntos)
    # despejar zonas con texto que no son partículas/obstáculos: la
    # esquina superior izquierda (etiqueta "arco", afuera del dominio
    # pero pegada a la pared) y el entorno de la etiqueta "R_k".
    ok = ok and not (px < 0.11 and py > W / 2 + d / 2 - 0.03)
    ok = ok and (px - 0.92) ** 2 + (py - 0.47) ** 2 > 0.115 ** 2
    if ok:
        puntos.append((px, py))

P_RADIO = 0.024  # radio de dibujo de cada partícula (no a escala con r real:
                  # r=0.0175m sería ilegible a este tamaño de figura).

usada_idx = set(rng.choice(len(puntos), size=n_usadas, replace=False).tolist())

# Partícula elegida para marcar r: la más cercana a una zona despejada,
# fija por índice (no aleatoria) para que el layout sea reproducible.
# Se prefiere una partícula fresca (azul) -- r es una propiedad de TODAS
# las partículas, marcarla sobre una usada (roja) podría sugerir lo
# contrario.
objetivo = np.array([0.30, 0.50 * W])
candidatas = [i for i in range(len(puntos)) if i not in usada_idx]
idx_radio = min(candidatas, key=lambda i: np.hypot(puntos[i][0] - objetivo[0],
                                                     puntos[i][1] - objetivo[1]))

# Alcance de la flecha de velocidad, medido desde el CENTRO de la
# partícula. Tiene que ser menor que MIN_SEP - P_RADIO para que la punta
# de la flecha nunca llegue a pisar el círculo de una partícula vecina.
ARROW_REACH = 0.065
assert ARROW_REACH + P_RADIO < MIN_SEP, "la flecha puede pisar a la vecina más cercana"


def choca(px, py, ang, alcance, propio_idx):
    """True si la flecha de (px,py) en dirección ang pisa otra partícula u obstáculo."""
    for t in (0.6, 1.0):
        tx = px + t * alcance * np.cos(ang)
        ty = py + t * alcance * np.sin(ang)
        for j, (qx, qy) in enumerate(puntos):
            if j == propio_idx:
                continue
            if (tx - qx) ** 2 + (ty - qy) ** 2 < (P_RADIO * 1.35) ** 2:
                return True
        for (ox, oy, orad) in obstaculos:
            if (tx - ox) ** 2 + (ty - oy) ** 2 < (orad + 0.01) ** 2:
                return True
    return False


for i, (px, py) in enumerate(puntos):
    color = COLOR_USADA if i in usada_idx else COLOR_FRESCA
    ax.add_patch(Circle((px, py), P_RADIO, facecolor=color, edgecolor="black",
                          linewidth=0.5, zorder=3))
    ang = rng.uniform(0, 2 * np.pi)
    for _ in range(40):
        if not choca(px, py, ang, ARROW_REACH, i):
            break
        ang = rng.uniform(0, 2 * np.pi)
    ax.annotate("", xy=(px + ARROW_REACH * np.cos(ang), py + ARROW_REACH * np.sin(ang)),
                xytext=(px + P_RADIO * np.cos(ang), py + P_RADIO * np.sin(ang)),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.1,
                                 mutation_scale=9), zorder=3)

# NUEVO: r marcado sobre esa partícula, mismo estilo que R_k sobre el
# obstáculo chico (tick punteado desde el centro + etiqueta pegada al
# borde) -- esto era lo que faltaba en la imagen anterior.
px, py = puntos[idx_radio]
ax.plot([px, px - P_RADIO], [py, py], color=COLOR_BORDE, lw=1.1,
        linestyle=(0, (1.2, 1.2)), zorder=4)
ax.text(px - P_RADIO - 0.018, py, "$r$", ha="right", va="center",
        fontsize=FONT_SIZE, color=COLOR_BORDE, zorder=4)

fig.tight_layout(pad=0.3)
out_path = Path(__file__).parent / "geometria-sistema.png"
fig.savefig(out_path, dpi=200)
print(f"Guardado: {out_path}")
