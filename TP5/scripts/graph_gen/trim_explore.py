#!/usr/bin/env python3
"""Exploración del recorte al tramo frontal (Fase 1). No toca el motor: solo lee los datos de la cátedra.

Criterios (ver DEFINICIONES.md, sección "Recorte al tramo frontal"):
  A(θ)  frames comunes en que los dos peatones van a ≤ θ del eje x en sentidos opuestos; bloque que contiene el mínimo.
  B(θ)  por peatón, del primer al último frame en que cumple; la simulación usa la intersección con la ventana común.
  C(L)  por peatón, |x − x_c| ≤ L, con x_c la x media de los dos en el frame de distancia mínima.
  D(θ)  A(θ) cerrando interrupciones de menos de 5 frames (persistencia).
"none" reproduce lo actual (D3, D12): ventana común, target y v_d de la trayectoria completa.

Uso: py scripts/graph_gen/trim_explore.py [carpeta de datos] [carpeta de salida]
"""
import math
import re
import sys
from pathlib import Path

import numpy as np

DT_DEFAULT = 1 / 15.0192
V0_FRAMES = 5
HALF = 2          # suavizado del rumbo: diferencia centrada de ±2 frames
PERSIST = 5       # D: interrupciones más cortas se cierran
MIN_FRAMES = 30
BEFORE_MIN = 4.5  # s antes del mínimo (t_a máximo útil de los mejores pares)
AFTER_MIN = 2.0   # s después del mínimo (4τ)
LAT_D = 5.0       # m: zona de interacción para el desvío lateral


# ---------------------------------------------------------------- datos
def load(data_dir):
    data_dir = Path(data_dir)
    rows, fps = {}, None
    for line in (data_dir / "elusion_1_contra_1.txt").read_text(encoding="latin1").splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            m = re.search(r"framerate:\s*([0-9.]+)", s)
            if m:
                fps = float(m.group(1))
            continue
        i, f, x, y, _ = s.split()
        rows.setdefault(int(i), {})[int(f)] = (float(x), float(y))
    dt = 1 / fps if fps else DT_DEFAULT
    events = []
    pat = re.compile(r"prueba\s+(\d+):\s+sale izquierda\s+(\S+),\s+sale derecha\s+(\S+),\s+cuadros\s+(\d+)-(\d+),\s+distancia minima\s+([0-9.]+)")
    for line in (data_dir / "LEEME_elusion1contra1.txt").read_text(encoding="latin1").splitlines():
        m = pat.search(line)
        if not m:
            continue
        n, a, b, f0, f1, dmin = m.groups()
        peds = []
        for pid in (a, b):
            pid = 1000 if pid == "V?" else int(pid)
            fr = sorted(f for f in rows[pid] if int(f0) <= f <= int(f1))
            arr = np.array([(f, *rows[pid][f]) for f in fr])
            peds.append({"id": pid, "f": arr[:, 0].astype(int), "x": arr[:, 1], "y": arr[:, 2]})
        events.append({"n": int(n), "peds": peds, "leeme_dmin": float(dmin)})
    return events, dt


def common_frames(peds):
    return np.intersect1d(peds[0]["f"], peds[1]["f"])


def pos(p, frame):
    k = np.searchsorted(p["f"], frame)
    return np.array([p["x"][k], p["y"][k]])


def min_distance(peds, frames):
    d = [np.hypot(*(pos(peds[0], f) - pos(peds[1], f))) for f in frames]
    k = int(np.argmin(d))
    return frames[k], d[k]


# ---------------------------------------------------------------- rumbo
def heading(p, dt, half=HALF):
    """Ángulo (°) entre la velocidad y el sentido de avance sobre x (0 = de frente, 180 = hacia atrás)."""
    n = len(p["f"])
    sense = 1.0 if p["sense"] > 0 else -1.0
    out = np.empty(n)
    for k in range(n):
        a, b = max(0, k - half), min(n - 1, k + half)
        dtt = (p["f"][b] - p["f"][a]) * dt
        vx, vy = (p["x"][b] - p["x"][a]) / dtt, (p["y"][b] - p["y"][a]) / dtt
        out[k] = math.degrees(math.atan2(abs(vy), sense * vx))
    return out


def y_dominates(p, dt, half=HALF):
    n = len(p["f"])
    out = np.zeros(n, bool)
    for k in range(n):
        a, b = max(0, k - half), min(n - 1, k + half)
        out[k] = abs(p["y"][b] - p["y"][a]) > abs(p["x"][b] - p["x"][a])
    return out


# ---------------------------------------------------------------- criterios
def block_containing(frames, ok, frame):
    """Bloque contiguo (en la lista de frames disponibles) de ok que contiene frame; si no cumple, el más largo."""
    if not ok.any():
        return None, False
    idx = int(np.searchsorted(frames, frame))
    inside = idx < len(frames) and frames[idx] == frame and ok[idx]
    if inside:
        a = idx
        while a > 0 and ok[a - 1]:
            a -= 1
        b = idx
        while b < len(ok) - 1 and ok[b + 1]:
            b += 1
        return (frames[a], frames[b]), True
    best, k = None, 0
    while k < len(ok):
        if ok[k]:
            j = k
            while j < len(ok) - 1 and ok[j + 1]:
                j += 1
            if best is None or j - k > best[1] - best[0]:
                best = (k, j)
            k = j + 1
        else:
            k += 1
    return (frames[best[0]], frames[best[1]]), False


def close_gaps(ok, persist):
    """Cierra corridas de False más cortas que persist entre dos True."""
    ok = ok.copy()
    k, n = 0, len(ok)
    while k < n:
        if not ok[k]:
            j = k
            while j < n and not ok[j]:
                j += 1
            if k > 0 and j < n and j - k < persist:
                ok[k:j] = True
            k = j
        else:
            k += 1
    return ok


def trim(ev, dt, crit, param, half=HALF):
    """Devuelve dict con tramos por peatón (frame inicial, final) y ventana de simulación común (s, e)."""
    peds = ev["peds"]
    cf = common_frames(peds)
    m_frame, _ = min_distance(peds, cf)
    res = {"min_frame": m_frame, "min_inside": True, "empty": False}
    if crit == "none":
        res["ped"] = [(p["f"][0], p["f"][-1]) for p in peds]
        res["sim"] = (cf[0], cf[-1])
        return res
    if crit in ("A", "D"):
        h = [heading(p, dt, half) for p in peds]
        ok = np.array([h[0][np.searchsorted(peds[0]["f"], f)] <= param and h[1][np.searchsorted(peds[1]["f"], f)] <= param for f in cf])
        if crit == "D":
            ok = close_gaps(ok, PERSIST)
        blk, inside = block_containing(cf, ok, m_frame)
        if blk is None:
            res["empty"] = True
            return res
        res["min_inside"] = inside
        res["ped"] = [blk, blk]
        res["sim"] = blk
        return res
    ranges = []
    if crit == "B":
        for p in peds:
            ok = heading(p, dt, half) <= param
            if not ok.any():
                res["empty"] = True
                return res
            w = np.flatnonzero(ok)
            ranges.append((p["f"][w[0]], p["f"][w[-1]]))
    elif crit == "C":
        xc = 0.5 * (pos(peds[0], m_frame)[0] + pos(peds[1], m_frame)[0])
        for p in peds:
            ok = np.abs(p["x"] - xc) <= param
            blk, inside = block_containing(p["f"], ok, m_frame)
            if blk is None:
                res["empty"] = True
                return res
            ranges.append(blk)
    s = max(ranges[0][0], ranges[1][0])
    e = min(ranges[0][1], ranges[1][1])
    sel = cf[(cf >= s) & (cf <= e)]
    if len(sel) < 2:
        res["empty"] = True
        return res
    res["ped"] = ranges
    res["sim"] = (sel[0], sel[-1])
    res["min_inside"] = sel[0] <= m_frame <= sel[-1]
    return res


# ---------------------------------------------------------------- magnitudes derivadas
def sub(p, a, b):
    k = (p["f"] >= a) & (p["f"] <= b)
    return p["f"][k], p["x"][k], p["y"][k]


def path_length(f, x, y):
    return float(np.sum(np.hypot(np.diff(x), np.diff(y))))


def mean_speed(f, x, y, dt):
    return path_length(f, x, y) / ((f[-1] - f[0]) * dt)


def fitted_v0(p, start, dt, count=V0_FRAMES):
    k = int(np.searchsorted(p["f"], start))
    f, x, y = p["f"][k:k + count], p["x"][k:k + count], p["y"][k:k + count]
    t = (f - start) * dt
    t = t - t.mean()
    return np.array([np.dot(t, x - x.mean()), np.dot(t, y - y.mean())]) / np.dot(t, t)


def axis_angle(vec, sense):
    """Ángulo (°) entre un vector y el sentido de avance sobre x."""
    return math.degrees(math.atan2(abs(vec[1]), sense * vec[0]))


def etarget_angles(p, sim, target, dt):
    """Ángulo de e_target (posición experimental → target) con el eje x: en t_0 y máximo en el primer segundo."""
    f, x, y = sub(p, *sim)
    k1 = f <= sim[0] + round(1 / dt)
    angs = [axis_angle(np.array(target) - np.array([x[k], y[k]]), p["sense"]) for k in np.flatnonzero(k1)]
    return angs[0], max(angs)


def lateral_reference(ev, dt):
    """Por peatón, en la zona de interacción (frames comunes alrededor del mínimo con distancia ≤ LAT_D):
    frame del desvío lateral máximo contra la recta entre los extremos de la zona, inicio del esquive
    (último frame antes del máximo con |desvío| ≤ 20% del máximo) y frame de rumbo máximo."""
    peds = ev["peds"]
    cf = common_frames(peds)
    m_frame, _ = min_distance(peds, cf)
    d = np.array([np.hypot(*(pos(peds[0], f) - pos(peds[1], f))) for f in cf])
    (a, b), _ = block_containing(cf, d <= LAT_D, m_frame)
    out = []
    for p in peds:
        f, x, y = sub(p, a, b)
        p0, p1 = np.array([x[0], y[0]]), np.array([x[-1], y[-1]])
        u = (p1 - p0) / np.linalg.norm(p1 - p0)
        dev = np.abs((x - p0[0]) * (-u[1]) + (y - p0[1]) * u[0])
        k = int(np.argmax(dev))
        j = k
        while j > 0 and dev[j] > 0.2 * dev[k]:
            j -= 1
        h = heading(p, dt)[(p["f"] >= a) & (p["f"] <= b)]
        out.append({"lat_frame": int(f[k]), "lat_m": float(dev[k]), "onset_frame": int(f[j]),
                    "peak_frame": int(f[int(np.argmax(h))]), "peak_deg": float(np.max(h)), "zone": (int(a), int(b))})
    return out


def describe(ev, dt, crit, param, half=HALF):
    peds = ev["peds"]
    cur = trim(ev, dt, "none", None)
    tr = trim(ev, dt, crit, param, half)
    row = {"event": ev["n"], "crit": crit, "param": param, "empty": tr["empty"]}
    if tr["empty"]:
        return row
    s, e = tr["sim"]
    cf = common_frames(peds)
    row["sim"] = (int(s), int(e))
    row["n_common"] = int(np.sum((cf >= s) & (cf <= e)))
    row["sim_s"] = (e - s) * dt
    m = tr["min_frame"]
    row["min_inside"] = bool(tr["min_inside"])
    row["before_s"] = (m - s) * dt
    row["after_s"] = (e - m) * dt
    lat = lateral_reference(ev, dt)
    for i, p in enumerate(peds):
        a, b = tr["ped"][i]
        f, x, y = sub(p, a, b)
        cf_, cx, cy = sub(p, *cur["ped"][i])
        tgt, tgt0 = (x[-1], y[-1]), (cx[-1], cy[-1])
        vd, vd0 = mean_speed(f, x, y, dt), mean_speed(cf_, cx, cy, dt)
        v0, v00 = fitted_v0(p, s, dt), fitted_v0(p, cur["sim"][0], dt)
        a_t0, a_1s = etarget_angles(p, (s, e), tgt, dt)
        b_t0, b_1s = etarget_angles(p, cur["sim"], tgt0, dt)
        missing = int((b - a + 1) - len(f))
        row[f"p{i}"] = {
            "id": p["id"], "frames": len(f), "len_m": path_length(f, x, y), "missing": missing,
            "target": tgt, "dtarget": math.hypot(tgt[0] - tgt0[0], tgt[1] - tgt0[1]),
            "dtx": tgt[0] - tgt0[0], "dty": tgt[1] - tgt0[1],
            "vd": vd, "vd0": vd0, "dvd_pct": 100 * (vd - vd0) / vd0,
            "dv0": float(np.linalg.norm(v0 - v00)), "dv0_deg": axis_angle(v0, p["sense"]) - axis_angle(v00, p["sense"]),
            "et_t0": a_t0, "et_1s": a_1s, "et_t0_cur": b_t0, "et_1s_cur": b_1s,
            "lat_in": s <= lat[i]["lat_frame"] <= e, "onset_in": s <= lat[i]["onset_frame"] <= e,
            "peak_in": s <= lat[i]["peak_frame"] <= e, "lat_m": lat[i]["lat_m"], "peak_deg": lat[i]["peak_deg"],
            "onset_s": (lat[i]["onset_frame"] - m) * dt, "lat_s": (lat[i]["lat_frame"] - m) * dt,
        }
    return row


CRITERIA = [("none", None), ("A", 30), ("A", 45), ("A", 60), ("B", 30), ("B", 45), ("B", 60),
            ("C", 2.0), ("C", 3.0), ("C", 4.0), ("D", 30), ("D", 45)]


def label(crit, param):
    if crit == "none":
        return "actual"
    return f"{crit}{param:g}" + ("°" if crit in "ABD" else "m")


def flags(r):
    out = []
    if r["empty"]:
        return ["SIN TRAMO"]
    if r["n_common"] < MIN_FRAMES:
        out.append(f"<{MIN_FRAMES}fr")
    if not r["min_inside"]:
        out.append("min afuera")
    if r["before_s"] < BEFORE_MIN:
        out.append("poco antes")
    if r["after_s"] < AFTER_MIN:
        out.append("poco despues")
    if not all(r[f"p{i}"][k] for i in (0, 1) for k in ("lat_in", "onset_in")):
        out.append("esquive cortado")
    if not (r["p0"]["peak_in"] and r["p1"]["peak_in"]):
        out.append("pico rumbo afuera")
    if r["p0"]["missing"] or r["p1"]["missing"]:
        out.append(f"hueco {r['p0']['missing']}/{r['p1']['missing']}")
    return out


def fmt(v, d=2):
    return f"{v:.{d}f}"


def write_table(events, dt, out):
    rows = {(c, p): [describe(ev, dt, c, p) for ev in events] for c, p in CRITERIA}
    lines = [f"# Recorte al tramo frontal: exploración. dt_exp={dt:.6f} s, rumbo ±{HALF} frames, v0 con {V0_FRAMES} frames (D12).",
             "# Δ contra lo actual (D3: ventana común; target y v_d de la trayectoria completa). Base de los %: el valor actual.",
             f"# Marcas: <{MIN_FRAMES}fr, min afuera (el frame de distancia mínima real queda fuera), poco antes (<{BEFORE_MIN} s antes del mínimo),",
             f"#   poco despues (<{AFTER_MIN} s después), esquive cortado (inicio o máximo del desvío lateral fuera de la ventana; zona d ≤ {LAT_D:g} m),",
             "#   pico rumbo afuera (frame de rumbo máximo en esa zona, fuera de la ventana), hueco izq/der (frames faltantes en el tramo).",
             "# Columnas por peatón (izq | der): frames, long (m), |Δtarget| (Δx, Δy), v_d y Δv_d %, |Δv0| (m/s), ang e_t t0 y máx 1 s (antes→después)."]
    for (c, p), rs in rows.items():
        lines.append("")
        lines.append(f"===== {label(c, p)} =====")
        lines.append("ev  sim_frames  N_com  dur_s  antes_s  despues_s | izq: fr long dtarget(dx,dy) vd dvd% dv0 et_t0 et_1s | der: ... | marcas")
        for r in rs:
            if r["empty"]:
                lines.append(f"{r['event']:2d}  SIN TRAMO")
                continue
            parts = [f"{r['event']:2d}  {r['sim'][0]}-{r['sim'][1]}  {r['n_common']:4d}  {fmt(r['sim_s'])}  {fmt(r['before_s'])}  {fmt(r['after_s'])}"]
            for i in (0, 1):
                q = r[f"p{i}"]
                parts.append(f"{q['id']}: {q['frames']} {fmt(q['len_m'])} {fmt(q['dtarget'])}({fmt(q['dtx'])},{fmt(q['dty'])}) "
                             f"{fmt(q['vd'])} {q['dvd_pct']:+.1f}% {fmt(q['dv0'])} {q['et_t0_cur']:.0f}→{q['et_t0']:.0f} {q['et_1s_cur']:.0f}→{q['et_1s']:.0f}")
            parts.append(" ".join(flags(r)))
            lines.append(" | ".join(parts))
    # Resumen por criterio
    lines.append("")
    lines.append("===== Resumen por criterio (19 eventos, 38 peatones) =====")
    lines.append("criterio  sin_tramo  <30fr  min_afuera  poco_antes  poco_desp(1/2/3 s)  esquive_cortado(peatones)  pico_afuera(peat.)  "
                 "N_com_med  N_com_min  antes/despues_med_s  et_1s_max(med/máx)  |Δv_d|%_med  |Δtarget|_med_m")
    summary = {}
    for (c, p), rs in rows.items():
        ok = [r for r in rs if not r["empty"]]
        ps = [r[f"p{i}"] for r in ok for i in (0, 1)]
        et = [q["et_1s"] for q in ps]
        s = {
            "empty": [r["event"] for r in rs if r["empty"]],
            "few": [r["event"] for r in ok if r["n_common"] < MIN_FRAMES],
            "minout": [r["event"] for r in ok if not r["min_inside"]],
            "before": [r["event"] for r in ok if r["before_s"] < BEFORE_MIN],
            "after": {t: [r["event"] for r in ok if r["after_s"] < t] for t in (1.0, 2.0, 3.0)},
            "latout": sorted({r["event"] for r in ok for i in (0, 1) if not (r[f"p{i}"]["lat_in"] and r[f"p{i}"]["onset_in"])}),
            "latout_n": sum(not (q["lat_in"] and q["onset_in"]) for q in ps),
            "before_med": float(np.median([r["before_s"] for r in ok])) if ok else 0,
            "after_med": float(np.median([r["after_s"] for r in ok])) if ok else 0,
            "peakout_n": sum(not q["peak_in"] for q in ps),
            "ncom_med": float(np.median([r["n_common"] for r in ok])) if ok else 0,
            "ncom_min": min([r["n_common"] for r in ok]) if ok else 0,
            "et_med": float(np.median(et)) if et else 0, "et_max": max(et) if et else 0,
            "dvd": float(np.median([abs(q["dvd_pct"]) for q in ps])) if ps else 0,
            "dtg": float(np.median([q["dtarget"] for q in ps])) if ps else 0,
        }
        summary[(c, p)] = s
        lines.append(f"{label(c, p):8s}  {s['empty']}  {s['few']}  {s['minout']}  {s['before']}  "
                     f"{len(s['after'][1.0])}/{len(s['after'][2.0])}/{len(s['after'][3.0])} {s['after'][2.0]}  "
                     f"{s['latout_n']} {s['latout']}  {s['peakout_n']}  {s['ncom_med']:.0f}  {s['ncom_min']}  {s['before_med']:.2f}/{s['after_med']:.2f}  "
                     f"{s['et_med']:.1f}/{s['et_max']:.1f}  {s['dvd']:.1f}  {s['dtg']:.2f}")
    (out / "tabla_recorte.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows, summary


def smoothing_sensitivity(events, dt, out):
    lines = ["# Sensibilidad al suavizado del rumbo: ventana de simulación (frames comunes) con ±1, ±2 y ±4 frames."]
    for c, p in (("A", 30), ("A", 45), ("B", 45), ("D", 45)):
        lines.append(f"== {label(c, p)} ==  ev: N(±1) N(±2) N(±4)  [inicio ±1/±2/±4]")
        for ev in events:
            vals = []
            for h in (1, 2, 4):
                r = describe(ev, dt, c, p, half=h)
                vals.append(("-", "-") if r["empty"] else (r["n_common"], r["sim"][0] - common_frames(ev["peds"])[0]))
            lines.append(f"{ev['n']:2d}: {vals[0][0]} {vals[1][0]} {vals[2][0]}  [{vals[0][1]}/{vals[1][1]}/{vals[2][1]}]")
    (out / "sensibilidad_suavizado.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def y_dominance(events, dt, out):
    """Frames (relativos al primer frame común) en que |Δy| > |Δx| con el mismo suavizado, agrupados en corridas."""
    lines = ["# Frames con movimiento dominante en y (|Δy| > |Δx|, ±2 frames). Relativos al primer frame común; m = frame del mínimo."]
    for ev in events:
        cf = common_frames(ev["peds"])
        m, _ = min_distance(ev["peds"], cf)
        parts = [f"{ev['n']:2d} (m={m - cf[0]})"]
        for q in ev["peds"]:
            yd = y_dominates(q, dt)
            runs, k = [], 0
            while k < len(yd):
                if yd[k]:
                    j = k
                    while j < len(yd) - 1 and yd[j + 1]:
                        j += 1
                    runs.append(f"{q['f'][k] - cf[0]}..{q['f'][j] - cf[0]}")
                    k = j + 1
                else:
                    k += 1
            parts.append(f"{q['id']}: {int(yd.sum())} fr [{', '.join(runs)}]")
        lines.append(" | ".join(parts))
    (out / "dominio_y.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def extremes(events, dt, out):
    """Eventos 1, 4 (huecos) y 9, 14, 17, 19 (el izquierdo termina en x ≈ 8)."""
    lines = ["# Casos particulares. Por criterio: x final del izquierdo, frames faltantes en el tramo (izq/der)."]
    for n in (1, 4, 9, 14, 17, 19):
        ev = events[n - 1]
        lines.append(f"== evento {n} (izq {ev['peds'][0]['id']}, der {ev['peds'][1]['id']}) ==")
        for c, p in CRITERIA:
            r = describe(ev, dt, c, p)
            if r["empty"]:
                lines.append(f"  {label(c, p):7s} SIN TRAMO")
                continue
            lines.append(f"  {label(c, p):7s} x_fin_izq={r['p0']['target'][0]:.2f} x_fin_der={r['p1']['target'][0]:.2f} "
                         f"hueco={r['p0']['missing']}/{r['p1']['missing']} N_com={r['n_common']} despues={r['after_s']:.2f}s")
    (out / "casos_particulares.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- figuras
def figures(events, dt, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    plt.rcParams.update({"font.size": 15, "axes.labelsize": 16, "legend.fontsize": 13, "xtick.labelsize": 12, "ytick.labelsize": 12,
                         "axes.edgecolor": "#52514e", "axes.labelcolor": "#0b0b0b", "xtick.color": "#52514e", "ytick.color": "#52514e"})
    comma = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
    colors = ("#2a78d6", "#eb6834")
    gray = "#b8b7b2"
    figs = out / "figs"
    figs.mkdir(parents=True, exist_ok=True)

    for c, p in (("A", 30), ("A", 45), ("A", 60), ("B", 45), ("C", 3.0), ("D", 45)):
        fig, axes = plt.subplots(5, 4, figsize=(18, 10.5), constrained_layout=True)
        for ax, ev in zip(axes.flat, events):
            tr = trim(ev, dt, c, p)
            for i, q in enumerate(ev["peds"]):
                ax.plot(q["x"], q["y"], color=gray, lw=1.5)
                if not tr["empty"]:
                    a, b = tr["ped"][i]
                    s, e = tr["sim"]
                    f, x, y = sub(q, a, b)
                    ax.plot(x, y, "-" if i == 0 else "--", color=colors[i], lw=2.2)
                    _, xs, ys = sub(q, s, e)
                    ax.plot(xs[0], ys[0], "o", color=colors[i], ms=7)
                    ax.plot(x[-1], y[-1], "x", color=colors[i], ms=9, mew=2)
            mp = [pos(q, tr["min_frame"]) for q in ev["peds"]]
            ax.plot([mp[0][0], mp[1][0]], [mp[0][1], mp[1][1]], ":", color="#0b0b0b", lw=1.5)
            ax.text(0.03, 0.95, f"evento {ev['n']}" + (" (sin tramo)" if tr["empty"] else ""), transform=ax.transAxes, va="top", fontsize=13)
            ax.set_xlim(-0.5, 12)
            ax.set_ylim(-0.8, 4.2)
            ax.set_aspect("equal")
            ax.xaxis.set_major_formatter(comma)
            ax.yaxis.set_major_formatter(comma)
            ax.grid(color="#e6e5e0", lw=0.8)
        ax = axes.flat[-1]
        ax.axis("off")
        ax.plot([], [], color=gray, lw=1.5, label="trayectoria completa")
        ax.plot([], [], "-", color=colors[0], lw=2.2, label="tramo, izquierdo")
        ax.plot([], [], "--", color=colors[1], lw=2.2, label="tramo, derecho")
        ax.plot([], [], "o", color="#52514e", ms=7, label="inicio de la simulación")
        ax.plot([], [], "x", color="#52514e", ms=9, mew=2, label="target")
        ax.plot([], [], ":", color="#0b0b0b", lw=1.5, label="distancia mínima real")
        ax.legend(loc="center", frameon=False, fontsize=15)
        for ax in axes[-1, :]:
            ax.set_xlabel("x (m)")
        for ax in axes[:, 0]:
            ax.set_ylabel("y (m)")
        tag = label(c, p).replace("°", "").replace(".0m", "m")
        fig.savefig(figs / f"xy_{tag}.png", dpi=110)
        plt.close(fig)

    # Rumbo contra t, con la ventana A(45°) sombreada
    fig, axes = plt.subplots(5, 4, figsize=(18, 17), constrained_layout=True, sharey=True)
    for ax, ev in zip(axes.flat, events):
        cf = common_frames(ev["peds"])
        t0 = cf[0]
        tr = trim(ev, dt, "A", 45)
        if not tr["empty"]:
            ax.axvspan((tr["sim"][0] - t0) * dt, (tr["sim"][1] - t0) * dt, color="#e6e5e0")
        for i, q in enumerate(ev["peds"]):
            ax.plot((q["f"] - t0) * dt, heading(q, dt), "-" if i == 0 else "--", color=colors[i], lw=1.8)
        for th in (30, 45, 60):
            ax.axhline(th, color="#52514e", lw=0.8, ls=":")
        ax.axvline((tr["min_frame"] - t0) * dt, color="#0b0b0b", lw=1.2)
        ax.text(0.03, 0.95, f"evento {ev['n']}", transform=ax.transAxes, va="top", fontsize=13)
        ax.set_ylim(0, 120)
        ax.xaxis.set_major_formatter(comma)
    ax = axes.flat[-1]
    ax.axis("off")
    ax.plot([], [], "-", color=colors[0], lw=1.8, label="izquierdo")
    ax.plot([], [], "--", color=colors[1], lw=1.8, label="derecho")
    ax.plot([], [], ":", color="#52514e", lw=0.8, label="θ = 30°, 45°, 60°")
    ax.plot([], [], color="#0b0b0b", lw=1.2, label="distancia mínima real")
    ax.fill_between([], [], color="#e6e5e0", label="tramo A(45°)")
    ax.legend(loc="center", frameon=False, fontsize=15)
    for ax in axes[-1, :]:
        ax.set_xlabel("t (s), 0 = primer frame común")
    for ax in axes[:, 0]:
        ax.set_ylabel("rumbo respecto de x (°)")
    fig.savefig(figs / "rumbo.png", dpi=110)
    plt.close(fig)

    # Desplazamiento acumulado en x y en y contra t
    fig, axes = plt.subplots(5, 4, figsize=(18, 17), constrained_layout=True, sharey=True)
    for ax, ev in zip(axes.flat, events):
        t0 = common_frames(ev["peds"])[0]
        tr = trim(ev, dt, "D", 45)
        if not tr["empty"]:
            ax.axvspan((tr["sim"][0] - t0) * dt, (tr["sim"][1] - t0) * dt, color="#e6e5e0")
        for i, q in enumerate(ev["peds"]):
            t = (q["f"] - t0) * dt
            ax.plot(t, np.abs(q["x"] - q["x"][0]), "-", color=colors[i], lw=1.8)
            ax.plot(t, np.abs(q["y"] - q["y"][0]), ":", color=colors[i], lw=2.2)
        ax.axvline((tr["min_frame"] - t0) * dt, color="#0b0b0b", lw=1.2)
        ax.text(0.03, 0.95, f"evento {ev['n']}", transform=ax.transAxes, va="top", fontsize=13)
        ax.xaxis.set_major_formatter(comma)
    ax = axes.flat[-1]
    ax.axis("off")
    for i, name in enumerate(("izquierdo", "derecho")):
        ax.plot([], [], "-", color=colors[i], lw=1.8, label=f"|Δx|, {name}")
        ax.plot([], [], ":", color=colors[i], lw=2.2, label=f"|Δy|, {name}")
    ax.plot([], [], color="#0b0b0b", lw=1.2, label="distancia mínima real")
    ax.fill_between([], [], color="#e6e5e0", label="tramo D(45°)")
    ax.legend(loc="center", frameon=False, fontsize=15)
    for ax in axes[-1, :]:
        ax.set_xlabel("t (s), 0 = primer frame común")
    for ax in axes[:, 0]:
        ax.set_ylabel("desplazamiento (m)")
    fig.savefig(figs / "desplazamiento.png", dpi=110)
    plt.close(fig)

    # Resumen: ángulo máximo de e_target en el primer segundo, por evento (máximo de los dos peatones)
    fig, ax = plt.subplots(figsize=(13, 6.5), constrained_layout=True)
    n = np.array([ev["n"] for ev in events])
    series = [("none", None, "actual", "#0b0b0b", "o"), ("A", 30, "A(30°)", "#2a78d6", "s"), ("A", 45, "A(45°)", "#1baf7a", "^"),
              ("B", 45, "B(45°)", "#eb6834", "D"), ("C", 3.0, "C(3 m)", "#8a5cd1", "v"), ("D", 45, "D(45°)", "#c4314b", "P")]
    for k, (c, p, name, col, mk) in enumerate(series):
        vals = []
        for ev in events:
            r = describe(ev, dt, c, p)
            vals.append(np.nan if r["empty"] else max(r["p0"]["et_1s"], r["p1"]["et_1s"]))
        ax.plot(n + (k - 2.5) * 0.12, vals, mk, color=col, ms=8, label=name, ls="none")
    ax.set_xticks(n)
    ax.set_xlabel("evento")
    ax.set_ylabel("ángulo máx. de e_target con x en el 1.er s (°)")
    ax.yaxis.set_major_formatter(comma)
    ax.grid(axis="y", color="#e6e5e0")
    ax.legend(loc="upper right", frameon=False, ncol=6, fontsize=12)
    fig.savefig(figs / "angulo_etarget.png", dpi=110)
    plt.close(fig)


def main():
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("outputs/recorte")
    out.mkdir(parents=True, exist_ok=True)
    events, dt = load(data_dir)
    for ev in events:
        ev["peds"][0]["sense"], ev["peds"][1]["sense"] = 1, -1
    write_table(events, dt, out)
    smoothing_sensitivity(events, dt, out)
    extremes(events, dt, out)
    y_dominance(events, dt, out)
    figures(events, dt, out)
    print(f"listo: {out}")


if __name__ == "__main__":
    main()
