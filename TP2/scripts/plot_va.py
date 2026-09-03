#!/usr/bin/env python3
"""Grafica el parametro de orden v_a en funcion del tiempo para una o varias corridas.

Sirve para los dos graficos temporales del TP, porque en ambos casos se trata de
superponer curvas v_a(t) y la leyenda sale sola de las cabeceras de cada corrida:

    # misma condicion inicial, theta0 aleatorio vs. alineado
    python3 TP2/scripts/plot_va.py random.txt alineado.txt --label-by=theta0 \
        --out=TP2/presentacion/figuras/evolucion-temporal.pdf

    # una curva por eta
    python3 TP2/scripts/plot_va.py generated/sweep_eta/*_seed1.csv --label-by=eta \
        --out=TP2/presentacion/figuras/barrido-variable.pdf

Acepta indistintamente trayectorias .txt del motor o series .csv ya calculadas con
order_parameter.py. Sin --out abre una ventana en vez de guardar el archivo.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Sequence

from order_parameter import load_named_series, resolve_transient, tail_stats
from simulation_io import SimulationFormatError, SimulationHeader


PALETTE = ["#2a9d8f", "#e63946", "#457b9d", "#f4a261", "#8e7dbe", "#264653",
           "#e9c46a", "#d62828"]
LABEL_FIELDS = ("theta0", "eta", "model", "n", "seedIC", "file")


def label_for(header: SimulationHeader, path: Path, field: str) -> str:
    if field == "theta0":
        return header.theta0_label
    if field == "eta":
        return f"η = {header.eta:g}"
    if field == "model":
        return f"modelo {header.model}"
    if field == "n":
        return f"N = {header.n} (ρ = {header.density_label})"
    if field == "seedIC":
        return f"seedIC = {header.seed_ic}"
    return path.stem


def differing_fields(headers: Sequence[SimulationHeader]) -> list[str]:
    """Campos cuyo valor NO es el mismo en todas las corridas: son los que distinguen curvas."""
    getters = {
        "theta0": lambda h: h.theta0,
        "eta": lambda h: h.eta,
        "model": lambda h: h.model,
        "n": lambda h: h.n,
        "seedIC": lambda h: h.seed_ic,
    }
    return [field for field, getter in getters.items()
            if len({getter(h) for h in headers}) > 1]


def auto_labels(headers: Sequence[SimulationHeader], paths: Sequence[Path]) -> list[str]:
    if len(headers) == 1:
        return [f"η = {headers[0].eta:g}, {headers[0].theta0_label}"]
    fields = differing_fields(headers)
    if not fields:
        return [path.stem for path in paths]
    return [" | ".join(label_for(header, path, field) for field in fields)
            for header, path in zip(headers, paths)]


def nice_tick_steps(span: float, target_divisions: int = 6) -> tuple[float, float]:
    """Paso entre marcas con numero y entre marcas chicas, para un eje de largo `span`.

    Elige un paso "redondo" (1, 2, 2.5 o 5 por una potencia de 10) apuntando a unas
    `target_divisions` divisiones grandes, y mete 5 marcas chicas dentro de cada una.
    Para una corrida de 3000 pasos da 500 (con numero) y 100 (solo la marquita).
    """
    if span <= 0:
        return 1.0, 0.2
    raw = span / target_divisions
    magnitude = 10.0 ** math.floor(math.log10(raw))
    for multiple in (1.0, 2.0, 2.5, 5.0, 10.0):
        if raw <= multiple * magnitude:
            major = multiple * magnitude
            break
    else:
        major = 10.0 * magnitude
    return major, major / 5.0


def time_axis_label(headers: Sequence[SimulationHeader]) -> str:
    """El eje x es t = paso x Δt, en las unidades de tiempo del modelo (Δt sale de la cabecera)."""
    reference = headers[0]
    if any(h.dt != reference.dt for h in headers):
        return "Tiempo $t$ (unidades de tiempo del modelo)"
    return f"Tiempo $t$ = paso × $\\Delta t$   [unidades de tiempo del modelo, $\\Delta t$ = {reference.dt:g}]"


OBSERVABLE_LABELS = {
    "va": "Parámetro de orden $v_a$",
    "S": "Fracción en la componente gigante $S$",
}


def observable_label(observable: str) -> str:
    return OBSERVABLE_LABELS.get(observable, observable)


def parse_legend_locs(spec: str) -> list[tuple[float | None, str]]:
    """'lower right' para todos, o '1/pi:lower right,1/2pi:best' por densidad."""
    pares: list[tuple[float | None, str]] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        if ":" in token:
            densidad, _, loc = token.rpartition(":")
            pares.append((parse_density(densidad), loc.strip()))
        else:
            pares.append((None, token))
    return pares


def legend_loc_for(density: float, locs: Sequence[tuple[float | None, str]]) -> str | None:
    for d, loc in locs:
        if d is None or abs(d - density) < 1e-4:
            return loc
    return None


def parse_vlines(spec: str) -> list[tuple[float, float]]:
    """Parsea '1/pi:2000,1/2pi:4300' o '0.318:2000' en pares (densidad, tiempo).

    Sirve para marcar el inicio del estacionario cuando es distinto en cada densidad, que
    es lo que pasa con S: el agrupamiento es mas lento cuanto mas diluido el sistema.
    """
    pares: list[tuple[float, float]] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        densidad, _, tiempo = token.rpartition(":")
        pares.append((parse_density(densidad), float(tiempo)))
    return pares


def parse_density(texto: str) -> float:
    """Acepta un decimal o la forma fraccionaria: '1/pi', '1/2pi', '1/(3pi)'."""
    limpio = texto.strip().replace("(", "").replace(")", "").replace(" ", "")
    if "pi" in limpio.lower():
        numerador, _, denominador = limpio.lower().partition("/")
        factor = denominador.replace("pi", "")
        return float(numerador) / ((float(factor) if factor else 1.0) * math.pi)
    return float(limpio)


VLINE_COLORS = ["#0b6e2e", "#1f5fa8", "#b5651d", "#7b2cbf"]


def vlines_for(density: float, vlines: Sequence[tuple[float, float]]) -> list[float]:
    return [t for d, t in vlines if abs(d - density) < 1e-4]


NAMED_COLORS = {"verde": "#0b6e2e", "azul": "#1f5fa8", "rojo": "#c1121f",
                "naranja": "#b5651d", "violeta": "#7b2cbf", "gris": "#555555",
                "mostaza": "#d4a017"}


def vline_sets_for(density: float, sets) -> list[tuple[str, str, float]]:
    """Para un panel, devuelve (color, etiqueta, tiempo) de cada conjunto que le aplica."""
    aplican = []
    for color, label, pares in sets:
        for tiempo in vlines_for(density, pares):
            aplican.append((color, label, tiempo))
    return aplican


def build_vline_sets(vlines, labels, colors) -> list:
    """Empareja cada conjunto de --vlines con su etiqueta y su color.

    Sin --vlines-color el color queda en None y lo resuelve `draw_axes`, que le da el de
    la curva del mismo indice: la vertical punteada sale del color de su eta.
    """
    if not vlines:
        return []
    labels, colors = labels or [], colors or []
    resueltos = []
    for i, pares in enumerate(vlines):
        color = colors[i] if i < len(colors) else None
        resueltos.append((NAMED_COLORS.get(color.lower(), color) if color else None,
                          labels[i] if i < len(labels) else "estacionario",
                          pares))
    return resueltos


def panel_key(header: SimulationHeader, field: str) -> tuple[float, str]:
    """Devuelve (orden, titulo) del panel al que va una corrida."""
    if field == "density":
        return header.density, f"ρ = {header.density_label}  (N = {header.n}, L = {header.l:g})"
    if field == "n":
        return float(header.n), f"N = {header.n}"
    if field == "eta":
        return header.eta, f"η = {header.eta:g}"
    return 0.0, f"modelo {header.model}"


def draw_axes(ax, series, labels, transient, logy, ticker, show_ylabel: bool,
              ylabel: str, ylim: tuple[float, float] | None = None,
              vlines: Sequence[tuple[str, str, float]] = (),
              legend_loc: str | None = None) -> None:
    """Dibuja un conjunto de curvas v_a(t) sobre unos ejes ya creados."""
    headers = [header for header, _, _ in series]
    curvas: list[tuple] = []
    for index, ((header, steps, values), label) in enumerate(zip(series, labels)):
        times = [step * header.dt for step in steps]
        color = PALETTE[index % len(PALETTE)]
        linea, = ax.plot(times, values, color=color, linewidth=1.2, label=label)
        curvas.append((linea, label, color))

    if transient is not None:
        resolved_transient = resolve_transient(transient, series[0][1][-1])
        ax.axvline(resolved_transient * headers[0].dt, color="#555555", linestyle="--", alpha=0.7,
                   label="inicio del estacionario")
    verticales: list[tuple] = []
    for indice, (color, etiqueta, tiempo) in enumerate(vlines):
        # sin color explicito la vertical toma el de su curva: la leyenda queda "curva, punteada"
        if color is None:
            color = curvas[indice][2] if indice < len(curvas) else VLINE_COLORS[indice % len(VLINE_COLORS)]
        linea = ax.axvline(tiempo * headers[0].dt, color=color, linestyle="--", alpha=0.95,
                           linewidth=1.4)
        verticales.append((linea, etiqueta, color, tiempo))

    last_time = max(steps[-1] * header.dt for header, steps, _ in series)
    major_step, minor_step = nice_tick_steps(last_time)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(major_step))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(minor_step))
    ax.tick_params(axis="x", which="major", length=6)
    ax.tick_params(axis="x", which="minor", length=3)  # marca chica, sin numero

    ax.set_xlabel(time_axis_label(headers))
    if show_ylabel:
        ax.set_ylabel(ylabel)
    if ylim is not None:
        ax.set_ylim(*ylim)
    elif logy:
        # en escala log el 0 no existe: se deja que Matplotlib elija el piso segun los datos
        ax.set_yscale("log")
        ax.set_ylim(top=1.3)
    else:
        ax.set_ylim(0.0, 1.02)
    ax.set_xlim(left=0.0)
    # la grilla acompana solo a las marcas con numero: las chicas quedan como marquita
    ax.grid(alpha=0.3, which="both" if logy else "major")
    build_legend(ax, curvas, verticales, legend_loc)


def build_legend(ax, curvas, verticales, loc) -> None:
    """Un renglon por curva: "(linea) eta = x, (linea dashed) estacionario".

    Empareja por posicion: el conjunto i de --vlines corresponde a la curva i, asi la
    leyenda queda en cuatro renglones en vez de ocho. Se arma con dos columnas
    (Matplotlib las llena de arriba hacia abajo) para que la muestra dashed caiga
    despues de la coma y antes de su texto, y no amontonada con la de la curva. No se
    repite el valor de t porque se lee del eje.
    """
    extra = {}
    if len(verticales) == len(curvas) and curvas:
        handles = [linea for linea, _, _ in curvas] + [linea for linea, _, _, _ in verticales]
        labels = [f"{label}," for _, label, _ in curvas] + [etiqueta for _, etiqueta, _, _ in verticales]
        extra = {"ncols": 2, "columnspacing": 1.1, "handletextpad": 0.5}
    else:
        handles = [linea for linea, _, _ in curvas] + [linea for linea, _, _, _ in verticales]
        labels = ([label for _, label, _ in curvas]
                  + [etiqueta for _, etiqueta, _, _ in verticales])

    ubicacion, _, ancla = (loc or "best").partition("@")
    if ancla:
        # x en coordenadas de ejes, y en coordenadas de datos: arranca a esa altura
        extra |= {"bbox_to_anchor": (1.0, float(ancla)),
                  "bbox_transform": ax.get_yaxis_transform()}
    ax.legend(handles, labels, fontsize=8, loc=ubicacion.strip(), **extra)


def report_tail(series, labels, transient: str | int | None, prefix: str = "",
                observable: str = "va") -> None:
    if transient is None:
        return
    for (_, steps, values), label in zip(series, labels):
        resolved = resolve_transient(transient, steps[-1])
        mean, stdev = tail_stats(steps, values, resolved)
        print(f"{prefix}{label}: <{observable}> = {mean:.4f} +/- {stdev:.4f} (t >= {resolved})")


def plot(paths: Sequence[Path], label_by: str, transient: str | int | None, title: str | None,
         logy: bool = False, panels_by: str | None = None,
         figsize: tuple[float, float] = (9.0, 6.0), ylabel: str | None = None,
         ylim: tuple[float, float] | None = None,
         vlines=(), legend_locs=(), panel_layout: str = "row"):
    import matplotlib.pyplot as plt
    from matplotlib import ticker

    named = [load_named_series(path) for path in paths]
    series = [item[:3] for item in named]
    headers = [item[0] for item in series]
    observable = named[0][3]

    if label_by == "auto":
        labels = auto_labels(headers, paths)
    else:
        labels = [label_for(header, path, label_by) for header, path in zip(headers, paths)]

    axis_label = ylabel if ylabel is not None else observable_label(observable)

    if panels_by is None:
        fig, ax = plt.subplots(figsize=figsize)
        draw_axes(ax, series, labels, transient, logy, ticker, show_ylabel=True,
                  ylabel=axis_label, ylim=ylim,
                  vlines=[(color, label, t)
                          for color, label, pares in vlines for _, t in pares],
                  legend_loc=legend_loc_for(headers[0].density, legend_locs))
        if title is not None:
            ax.set_title(title)
        report_tail(series, labels, transient, observable=observable)
        fig.tight_layout()
        return fig

    groups: dict[tuple[float, str], list[int]] = {}
    for index, header in enumerate(headers):
        groups.setdefault(panel_key(header, panels_by), []).append(index)
    ordered = sorted(groups)

    if panel_layout == "column":
        fig, axes = plt.subplots(len(ordered), 1,
                                 figsize=(figsize[0], figsize[1] * len(ordered)),
                                 sharex=True, squeeze=False)
    else:
        fig, axes = plt.subplots(1, len(ordered),
                                 figsize=(figsize[0] * len(ordered), figsize[1]),
                                 sharey=True, squeeze=False)
    for position, key in enumerate(ordered):
        indices = groups[key]
        ax = axes[position][0] if panel_layout == "column" else axes[0][position]
        panel_series = [series[i] for i in indices]
        panel_labels = [labels[i] for i in indices]
        draw_axes(ax, panel_series, panel_labels, transient, logy, ticker,
                  show_ylabel=panel_layout == "column" or position == 0,
                  ylabel=axis_label, ylim=ylim,
                  vlines=vline_sets_for(panel_series[0][0].density, vlines),
                  legend_loc=legend_loc_for(panel_series[0][0].density, legend_locs))
        ax.set_title(key[1])
        print(f"\n{key[1]}")
        report_tail(panel_series, panel_labels, transient, prefix="  ",
                    observable=observable)
    if title is not None:
        fig.suptitle(title)
    fig.tight_layout()
    return fig


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Grafica v_a(t) superponiendo una curva por corrida."
    )
    parser.add_argument("inputs", nargs="+", type=Path,
                        help="corridas .txt del motor o series .csv de order_parameter.py")
    parser.add_argument("--out", type=Path, default=None,
                        help="archivo de salida (.pdf/.png); sin este flag abre una ventana")
    parser.add_argument("--label-by", choices=LABEL_FIELDS + ("auto",), default="auto",
                        help="que campo usar para la leyenda (default: auto, los que difieren)")
    parser.add_argument("--transient", default=None,
                        help="marca el inicio del estacionario e informa <v_a> de la cola, en "
                             "pasos (500) o como porcentaje del largo de cada corrida (40%%)")
    parser.add_argument("--width", type=float, default=9.0,
                        help="ancho de la figura en pulgadas (default: 9). Subirlo estira el "
                             "eje temporal sin cambiar el rango de datos")
    parser.add_argument("--height", type=float, default=6.0,
                        help="alto de la figura en pulgadas (default: 6)")
    parser.add_argument("--panels-by", choices=("density", "n", "eta", "model"), default=None,
                        help="partir en un panel por cada valor de este campo")
    parser.add_argument("--panel-layout", choices=("row", "column"), default="row",
                        help="como acomodar los paneles de --panels-by: en fila (default) "
                             "o apilados en columna")
    parser.add_argument("--logy", action="store_true",
                        help="escala logaritmica en el eje vertical (v_a)")
    parser.add_argument("--vlines", type=parse_vlines, action="append", default=None,
                        help="lineas verticales por densidad, como '1/pi:2000,1/2pi:4300'. "
                             "La densidad acepta forma fraccionaria de pi o decimal. Se puede "
                             "repetir el flag para varios conjuntos; el conjunto i se "
                             "empareja con la curva i y toma su color")
    parser.add_argument("--vlines-label", action="append", default=None,
                        help="etiqueta de leyenda de cada --vlines, en el mismo orden")
    parser.add_argument("--legend-loc", type=parse_legend_locs, default=(),
                        help="ubicacion de la leyenda: 'lower right' para todos los paneles, "
                             "o '1/pi:lower right' para fijarla solo en una densidad. Con "
                             "'lower right@0.06' se ancla ademas a esa altura del eje y")
    parser.add_argument("--vlines-color", action="append", default=None,
                        help="color de cada --vlines: verde, azul, rojo, naranja, violeta, "
                             "gris, o un color de Matplotlib. Por defecto cada vertical "
                             "toma el color de la curva que le corresponde")
    parser.add_argument("--ylim", type=lambda v: tuple(float(x) for x in v.split(",")),
                        default=None,
                        help="rango del eje y como 'min,max' (default: 0,1.02). Sirve para hacer zoom cuando el observable se mueve poco")
    parser.add_argument("--ylabel", default=None,
                        help="etiqueta del eje y (default: segun el observable del CSV)")
    parser.add_argument("--title", default=None, help="titulo del grafico")
    parser.add_argument("--dpi", type=int, default=150, help="resolucion de salida (default: 150)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        if args.out is not None:
            import matplotlib
            matplotlib.use("Agg")  # sin ventana: solo se guarda el archivo
        fig = plot(args.inputs, args.label_by, args.transient, args.title,
                   args.logy, args.panels_by, (args.width, args.height), args.ylabel,
                   args.ylim, build_vline_sets(args.vlines, args.vlines_label,
                                    args.vlines_color), args.legend_loc, args.panel_layout)
    except (OSError, SimulationFormatError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1
    except ImportError:
        print("Error: falta Matplotlib; instalar con: python3 -m pip install -r TP2/requirements.txt")
        return 1

    if args.out is None:
        import matplotlib.pyplot as plt
        plt.show()
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.out, dpi=args.dpi)
        print(f"Grafico guardado en {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
