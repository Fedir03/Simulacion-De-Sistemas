#!/usr/bin/env python3
"""¿Hay una regla que corte solo los eventos 3 y 6 del recorte D(45°)? Discriminadores sin simular, más el ajuste
manual de esos dos eventos para mostrar cómo quedarían.

Lee el recorte vigente que exporta el motor (`java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain trim-export` → outputs/recorte/*.csv).
Discriminadores, por peatón, sobre su tramo en la ventana D(45°) [s, e]:
  (a) sobrepaso en x más allá de la x inicial del otro (m; negativo si no la alcanza);
  (b) ángulo de la cuerda inicio→fin del tramo con el eje x (°);
  (c) ángulo de e_target con el eje x en el frame de distancia mínima real y máximo en el primer segundo (°);
  (d) excursión lateral de la cola: |y_fin − y(f*)|, f* = primer frame en que pasa la x inicial del otro (m).
Margen claro (DEFINICIONES 8b): 3 y 6 son los dos primeros a nivel evento y el hueco entre el menor de ellos y el mayor
de los otros 17 es ≥ 25% de ese mayor; en (c) además tiene que superar el cambio que produce el suavizado (±1 contra ±2).
Uso: py scripts/graph_gen/trim_discriminators.py > outputs/recorte/discriminadores.md
"""
import copy
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "animation"))
import trim_check as tc  # noqa: E402
import trim_explore as te  # noqa: E402

TARGETS = (3, 6)
SENSE = (1, -1)
NAMES = ("izq.", "der.")
REL_MARGIN = 0.25


def c(v, d=2):
    return f"{v:.{d}f}".replace(".", ",")


def window_frames(p, s, e):
    k = (p["f"] >= s) & (p["f"] <= e)
    return p["f"][k], p["x"][k], p["y"][k]


def angle_first_second(p, sense, s, e, target, dt):
    f, x, y = window_frames(p, s, min(e, s + round(1 / dt)))
    return max(abs(tc.axis_angle(target[0] - xi, target[1] - yi, sense)) for xi, yi in zip(x, y))


def angle_at(p, sense, frame, target):
    q = tc.pos(p, frame)
    return abs(tc.axis_angle(target[0] - q[0], target[1] - q[1], sense))


def discriminators(ev, s=None, e=None, targets=None):
    s = ev["rec"][0] if s is None else s
    e = ev["rec"][1] if e is None else e
    dt = ev["dt"]
    out = []
    for i, p in enumerate(ev["peds"]):
        o = ev["peds"][1 - i]
        x0_other = tc.pos(o, s)[0]
        f, x, y = window_frames(p, s, e)
        target = (x[-1], y[-1]) if targets is None else targets[i]
        overshoot = (x.max() - x0_other) if i == 0 else (x0_other - x.min())
        chord = abs(tc.axis_angle(x[-1] - x[0], y[-1] - y[0], SENSE[i]))
        passed = np.flatnonzero(x >= x0_other) if i == 0 else np.flatnonzero(x <= x0_other)
        tail = abs(y[-1] - y[passed[0]]) if len(passed) else 0.0
        out.append({"a": overshoot, "b": chord, "c_min": angle_at(p, SENSE[i], ev["min"], target),
                    "c_1s": angle_first_second(p, SENSE[i], s, e, target, dt), "d": tail, "passes": bool(len(passed))})
    return out


def smoothing_noise(events):
    """Cambio de (c) por evento entre el rumbo con ±2 y con ±1 frames (ventana D(45°) del script de exploración, que
    coincide frame a frame con la del motor con ±2)."""
    raw, dt = te.load(Path("data"))
    for r in raw:
        r["peds"][0]["sense"], r["peds"][1]["sense"] = 1, -1
    noise = {}
    for r in raw:
        n = r["n"]
        w2 = te.trim(r, dt, "D", 45, half=2)["sim"]
        w1 = te.trim(r, dt, "D", 45, half=1)["sim"]
        assert tuple(int(v) for v in w2) == events[n]["rec"], f"evento {n}: la ventana del script no coincide con la del motor"
        d2 = discriminators(events[n], int(w2[0]), int(w2[1]))
        d1 = discriminators(events[n], int(w1[0]), int(w1[1]))
        noise[n] = {k: max(abs(d1[i][k] - d2[i][k]) for i in (0, 1)) for k in ("c_min", "c_1s")}
    return noise


def separation(values, noise=None):
    """values: {evento: valor a nivel evento}. Devuelve el texto de la conclusión y si separa con margen claro."""
    order = sorted(values, key=values.get, reverse=True)
    top_two = set(order[:2]) == set(TARGETS)
    low = min(values[n] for n in TARGETS)
    others = max(values[n] for n in values if n not in TARGETS)
    gap = low - others
    rel = gap / others if others > 0 else float("inf")
    clear = top_two and rel >= REL_MARGIN and (noise is None or gap > noise)
    text = (f"3 y 6 son los dos primeros: {'sí' if top_two else 'no'} (orden: {', '.join(str(n) for n in order[:5])}, ...). "
            f"Menor de 3 y 6 = {c(low)}; mayor de los otros 17 = {c(others)} (evento {max((n for n in values if n not in TARGETS), key=values.get)}); "
            f"hueco = {c(gap)} ({c(100 * rel, 0)}% del mayor de los otros)"
            + (f"; ruido del suavizado = {c(noise)}" if noise is not None else "")
            + f". **{'Separa con margen claro' if clear else 'No separa con margen claro'}.**")
    return text, clear


def table(events, key, unit, noise_key=None, noise=None):
    rows = []
    for n, ev in events.items():
        for i, d in enumerate(discriminators(ev)):
            rows.append((d[key], n, i, d))
    rows.sort(key=lambda r: r[0], reverse=True)
    per_event = {}
    for v, n, i, _ in rows:
        per_event[n] = max(per_event.get(n, -math.inf), v)
    noise_val = max(noise[n][noise_key] for n in noise if n not in TARGETS) if noise_key else None
    text, clear = separation(per_event, noise_val)
    print(text)
    print()
    print(f"| # | evento | peatón | valor ({unit}) |" + (" pasa la x inicial del otro |" if key == "d" else ""))
    print("|---|---|---|---|" + ("---|" if key == "d" else ""))
    for k, (v, n, i, d) in enumerate(rows, 1):
        mark = " ⚠️" if n in TARGETS else ""
        extra = f" {'sí' if d['passes'] else 'no pasa'} |" if key == "d" else ""
        print(f"| {k} | **{n}**{mark} | {NAMES[i]} | {c(v)} |{extra}" if n in TARGETS else f"| {k} | {n} | {NAMES[i]} | {c(v)} |{extra}")
    return clear


def manual_cut(events, out):
    print("\n## Ajuste manual de los eventos 3 y 6 (corte en la x inicial del derecho)")
    print("La ventana común termina en el último frame común anterior a aquel en que el izquierdo pasa la x inicial del "
          "derecho. Target = última posición en esa ventana; v_d = rapidez media en ella (como en la opción 1).\n")
    print("| evento | versión | ventana (frames) | frames comunes | antes del mínimo (s) | después (s) | e_target 1.er s izq. / der. (°) | "
          "e_target en el mínimo izq. / der. (°) | target izq. | target der. | v_d izq. / der. (m/s) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    out.mkdir(parents=True, exist_ok=True)
    for n in TARGETS:
        ev = events[n]
        s, e = ev["rec"]
        left, right = ev["peds"]
        x0r = tc.pos(right, s)[0]
        common = sorted(set(left["f"]) & set(right["f"]))
        common = [f for f in common if s <= f <= e]
        cross = next(f for f in common if tc.pos(left, f)[0] > x0r)
        e_new = max(f for f in common if f < cross)
        for label, (lo, hi) in (("D(45°)", (s, e)), ("ajuste manual", (s, e_new))):
            dt = ev["dt"]
            targets, vds, frames = [], [], []
            for p in ev["peds"]:
                f, x, y = window_frames(p, lo, hi)
                targets.append((x[-1], y[-1]))
                vds.append(float(np.sum(np.hypot(np.diff(x), np.diff(y)))) / ((f[-1] - f[0]) * dt))
                frames.append(len(f))
            d = discriminators(ev, lo, hi, targets)
            before, after = (ev["min"] - lo) * dt, (hi - ev["min"]) * dt
            flag = " ⚠️ < 2 s" if after < 2 else ""
            print(f"| {n} | {label} | {lo}–{hi} | {len([f for f in common if lo <= f <= hi])} | {c(before)} | {c(after)}{flag} | "
                  f"{c(d[0]['c_1s'], 1)} / {c(d[1]['c_1s'], 1)} | {c(d[0]['c_min'], 1)} / {c(d[1]['c_min'], 1)} | "
                  f"({c(targets[0][0])}; {c(targets[0][1])}) | ({c(targets[1][0])}; {c(targets[1][1])}) | {c(vds[0])} / {c(vds[1])} |")
            if label == "ajuste manual":
                mod = copy.deepcopy(ev)
                mod["rec"] = (lo, hi)
                mod["label"] = "recorte=ajuste manual"
                for i, p in enumerate(mod["peds"]):
                    p["target_rec"], p["vd_rec"], p["frames_rec"] = targets[i], vds[i], frames[i]
                tc.draw(mod, n, out, video=True)
        print(f"|  | frames quitados | {e - e_new} |  |  |  |  |  |  |  |  |")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    events = tc.load(Path("outputs/recorte"))
    label = next(iter(events.values()))["label"]
    print("# ¿Qué separa a los eventos 3 y 6 del resto? (recorte vigente, sin simular)")
    print(f"Recorte: `{label}` (del motor, `trim-export`). Valores por peatón sobre su tramo en la ventana D(45°); a nivel evento, "
          f"el máximo de los dos peatones. Margen claro: 3 y 6 primeros y hueco ≥ {int(REL_MARGIN * 100)}% del mayor de los otros 17 "
          "(en (c), además, mayor que el cambio por suavizado ±1 contra ±2 frames). ⚠️ = eventos 3 y 6.\n")
    noise = smoothing_noise(events)
    verdict = {}
    for key, title, unit, nk in (("a", "(a) Sobrepaso en x más allá de la x inicial del otro", "m", None),
                                 ("b", "(b) Ángulo de la cuerda inicio→fin del tramo con el eje x", "°", None),
                                 ("c_min", "(c) Ángulo de e_target con el eje x en el frame de distancia mínima", "°", "c_min"),
                                 ("c_1s", "(c) Ángulo de e_target con el eje x, máximo en el primer segundo", "°", "c_1s"),
                                 ("d", "(d) Excursión lateral de la cola, |y_fin − y(f*)|", "m", None)):
        print(f"\n## {title}")
        verdict[title] = table(events, key, unit, nk, noise)
    print("\n## Conclusión")
    good = [t for t, ok in verdict.items() if ok]
    print("Separan con margen claro: " + ("; ".join(good) if good else "**ninguno**") + ".")
    manual_cut(events, Path("outputs/recorte/ajuste_manual"))


if __name__ == "__main__":
    main()
