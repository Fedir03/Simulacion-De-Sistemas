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

from order_parameter import load_named_series, tail_stats
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
        return f"N = {header.n} (ρ = {header.density:g})"
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


def build_title(headers: Sequence[SimulationHeader], observable: str = "va") -> str:
    """Los parametros que comparten todas las corridas van al titulo, no a la leyenda."""
    reference = headers[0]
    shared = [f"Modelo {reference.model}"] if all(h.model == reference.model for h in headers) else []
    if all(h.n == reference.n and h.l == reference.l for h in headers):
        shared.append(f"N={reference.n}")
        shared.append(f"ρ={reference.density:g}")
    if all(h.eta == reference.eta for h in headers):
        shared.append(f"η={reference.eta:g}")
    nombre = "Parámetro de orden $v_a$" if observable == "va" else observable_label(observable)
    return f"{nombre} vs. tiempo" + (" — " + ", ".join(shared) if shared else "")


def panel_key(header: SimulationHeader, field: str) -> tuple[float, str]:
    """Devuelve (orden, titulo) del panel al que va una corrida."""
    if field == "density":
        return header.density, f"ρ = {header.density:g}  (N = {header.n}, L = {header.l:g})"
    if field == "n":
        return float(header.n), f"N = {header.n}"
    if field == "eta":
        return header.eta, f"η = {header.eta:g}"
    return 0.0, f"modelo {header.model}"


def draw_axes(ax, series, labels, transient, logy, ticker, show_ylabel: bool,
              ylabel: str, ylim: tuple[float, float] | None = None) -> None:
    """Dibuja un conjunto de curvas v_a(t) sobre unos ejes ya creados."""
    headers = [header for header, _, _ in series]
    for index, ((header, steps, values), label) in enumerate(zip(series, labels)):
        times = [step * header.dt for step in steps]
        ax.plot(times, values, color=PALETTE[index % len(PALETTE)], linewidth=1.2, label=label)

    if transient is not None:
        ax.axvline(transient * headers[0].dt, color="#555555", linestyle="--", alpha=0.7,
                   label=f"inicio del estacionario (t={transient})")

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
    ax.legend(fontsize=8)


def report_tail(series, labels, transient: int | None, prefix: str = "",
                observable: str = "va") -> None:
    if transient is None:
        return
    for (_, steps, values), label in zip(series, labels):
        mean, stdev = tail_stats(steps, values, transient)
        print(f"{prefix}{label}: <{observable}> = {mean:.4f} +/- {stdev:.4f} (t >= {transient})")


def plot(paths: Sequence[Path], label_by: str, transient: int | None, title: str | None,
         logy: bool = False, panels_by: str | None = None,
         figsize: tuple[float, float] = (9.0, 6.0), ylabel: str | None = None,
         ylim: tuple[float, float] | None = None):
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
                  ylabel=axis_label, ylim=ylim)
        ax.set_title(title if title is not None else build_title(headers, observable))
        report_tail(series, labels, transient, observable=observable)
        fig.tight_layout()
        return fig

    groups: dict[tuple[float, str], list[int]] = {}
    for index, header in enumerate(headers):
        groups.setdefault(panel_key(header, panels_by), []).append(index)
    ordered = sorted(groups)

    fig, axes = plt.subplots(1, len(ordered),
                             figsize=(figsize[0] * len(ordered), figsize[1]),
                             sharey=True, squeeze=False)
    for position, key in enumerate(ordered):
        indices = groups[key]
        ax = axes[0][position]
        panel_series = [series[i] for i in indices]
        panel_labels = [labels[i] for i in indices]
        draw_axes(ax, panel_series, panel_labels, transient, logy, ticker,
                  show_ylabel=position == 0, ylabel=axis_label, ylim=ylim)
        ax.set_title(key[1])
        print(f"\n{key[1]}")
        report_tail(panel_series, panel_labels, transient, prefix="  ",
                    observable=observable)
    fig.suptitle(title if title is not None else build_title(headers, observable))
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
    parser.add_argument("--transient", type=int, default=None,
                        help="marca el inicio del estacionario e informa <v_a> de la cola")
    parser.add_argument("--width", type=float, default=9.0,
                        help="ancho de la figura en pulgadas (default: 9). Subirlo estira el "
                             "eje temporal sin cambiar el rango de datos")
    parser.add_argument("--height", type=float, default=6.0,
                        help="alto de la figura en pulgadas (default: 6)")
    parser.add_argument("--panels-by", choices=("density", "n", "eta", "model"), default=None,
                        help="partir en un panel por cada valor de este campo")
    parser.add_argument("--logy", action="store_true",
                        help="escala logaritmica en el eje vertical (v_a)")
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
                   args.ylim)
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
