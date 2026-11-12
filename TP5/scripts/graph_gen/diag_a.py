#!/usr/bin/env python3
"""Diagnóstico del error de A(3; 0,5), con B(3,5; 1) de referencia. Solo lee corridas ya hechas; no toca el motor.

Recorte vigente: D(45°), persistencia 5, opción 1, compuerta de tramo compartido X = 1,5 m (post-hoc). ρ = 0,9,
Δt = Δt_exp/64, salida cada Δt_exp/4. ECM 1 = variante excluyente.
Entradas:
- corridas oficiales (outputs/pilot/sensitivity_rho/{A_3_0.5,B_3.5_1}/rho_0.9, outputs/baseline);
- datos recortados (outputs/recorte);
- corridas de prueba de v_0 y trazas de RunTrace en outputs/pilot/diagnostico_A/corridas (las arma scripts/sim_gen/diag_a.sh).
Salida: outputs/pilot/diagnostico_A/diagnostico_A.md y figs/.
Uso, desde TP5/: py scripts/graph_gen/diag_a.py [carpeta de corridas] [carpeta de salida] (lo llama scripts/sim_gen/diag_a.sh)
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from pilot_analysis import load_grid  # noqa: E402
from presentation_figures import COLORS, INK, MUTED, style  # noqa: E402  (también fija los rcParams de letra grande)

OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("outputs/pilot/diagnostico_A")
RUNS = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "corridas"
FIGS = OUT / "figs"
OFFICIAL = {"A": Path("outputs/pilot/sensitivity_rho/A_3_0.5/rho_0.9"), "B": Path("outputs/pilot/sensitivity_rho/B_3.5_1/rho_0.9"),
            "base": Path("outputs/baseline")}
GRID = {"A": (Path("outputs/pilot/grid_A.txt"), 3.0, 0.5), "B": (Path("outputs/pilot/grid_B.txt"), 3.5, 1.0)}
TRIM = Path("outputs/recorte")
TAU, R, RHO, SIDE_EPS = 0.5, 0.25, 0.9, 0.05
EVENTS = range(1, 20)
LBL = {"A": "A(3; 0,5)", "B": "B(3,5; 1)", "base": "sin capa"}


def c(v, d=4):
    return "—" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.{d}f}".replace(".", ",")


def pct(v, d=1):
    return c(v, d) + "%"


# ---------------------------------------------------------------- lectura
def read_ecm(folder):
    """ecm.txt: por peatón {(ev, ped): dict} y por evento {ev: dict}."""
    ped, ev = {}, {}
    for line in (Path(folder) / "ecm.txt").read_text(encoding="utf-8").splitlines():
        p = line.split()
        if not p or line.startswith("#"):
            continue
        if p[0] == "E":
            ev[int(p[1])] = dict(ecm1=float(p[2]), ecm2=float(p[4]), dmin=float(p[5]), tmin=float(p[6]), contact=p[7] == "true",
                                 dmin_exp=float(p[8]), tmin_exp=float(p[9]))
        else:
            ped[(int(p[0]), int(p[1]))] = dict(id=int(p[2]), ecm1=float(p[3]), ecm2=float(p[5]), n1=int(p[6]), n2=int(p[7]))
    return ped, ev


def read_rows(folder, e):
    return np.genfromtxt(Path(folder) / f"evento_{e:02d}.txt", comments="#")


def read_real():
    """Trayectorias completas por (evento, peatón) y datos de la ventana por (evento, peatón)."""
    tr = defaultdict(list)
    with open(TRIM / "trayectorias_recortadas.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            tr[(int(r["evento"]), int(r["peaton"]))].append((int(r["frame"]), float(r["x"]), float(r["y"]), r["en_recorte"] == "1"))
    traj = {k: np.array(sorted(v)) for k, v in tr.items()}
    info = {}
    with open(TRIM / "recorte_eventos.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            info[(int(r["evento"]), int(r["peaton"]))] = dict(
                dt=float(r["dt_exp"]), f0=int(r["frame_ini_rec"]), f1=int(r["frame_fin_rec"]), fmin=int(r["frame_min"]),
                tx=float(r["target_x_rec"]), ty=float(r["target_y_rec"]), vd=float(r["vd_rec"]), v0x=float(r["v0x_rec"]), v0y=float(r["v0y_rec"]))
    return traj, info


def read_trace(path):
    """Primera activación de cada agente en la traza de RunTrace: {agente: (t, d_min predicho, s_c)}."""
    first = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        p = line.split()
        if p and p[0] == "S" and p[3] == "on" and int(p[2]) not in first:
            first[int(p[2])] = (float(p[1]), float(p[5]), float(p[6]))
    return first


TRAJ, INFO = read_real()
DIR = {1: 1.0, 2: -1.0}     # sentido de avance sobre x: el peatón 1 sale de la izquierda


def real_window(e, p):
    """Frames de la ventana del peatón: (t, x, y, rapidez), con rapidez por diferencia centrada de ±2 frames y tiempos reales."""
    a, i = TRAJ[(e, p)], INFO[(e, p)]
    fr, x, y = a[:, 0], a[:, 1], a[:, 2]
    n = len(fr)
    sp = np.empty(n)
    for k in range(n):
        lo, hi = max(0, k - 2), min(n - 1, k + 2)
        sp[k] = np.hypot(x[hi] - x[lo], y[hi] - y[lo]) / ((fr[hi] - fr[lo]) * i["dt"])
    m = (fr >= i["f0"]) & (fr <= i["f1"])
    return (fr[m] - i["f0"]) * i["dt"], x[m], y[m], sp[m], fr[m]


def smoothed_window(e, p):
    """Posiciones de la ventana con media móvil centrada de 5 frames (±2) sobre la trayectoria completa."""
    a, i = TRAJ[(e, p)], INFO[(e, p)]
    fr = a[:, 0]
    xs = np.array([a[max(0, k - 2):k + 3, 1].mean() for k in range(len(fr))])
    ys = np.array([a[max(0, k - 2):k + 3, 2].mean() for k in range(len(fr))])
    m = (fr >= i["f0"]) & (fr <= i["f1"])
    return xs[m], ys[m], fr[m]


def sim_at(rows, p, frames, f0):
    """Posición y rapidez simuladas del agente p (1 o 2) en los frames dados (fila = 4 por intervalo)."""
    idx = ((frames - f0) * 4).astype(int)
    idx = idx[idx < len(rows)]
    cx, cy = 1 + 4 * (p - 1), 2 + 4 * (p - 1)
    return rows[idx, cx], rows[idx, cy], np.hypot(rows[idx, cx + 2], rows[idx, cy + 2])


def length(x, y):
    ok = ~np.isnan(x)
    return float(np.sum(np.hypot(np.diff(x[ok]), np.diff(y[ok]))))


# ---------------------------------------------------------------- 1. descomposición
def decomposition(md):
    md.append("## 1. Descomposición del error\n")
    md.append("ECM 1 excl. y ECM 2 en m², ρ = 0,9, Δt = Δt_exp/64. Aporte = ECM 1 del evento / suma de los 19 ECM 1 del mismo par "
              "(= su parte del poblacional). Corrimiento = t(mínimo simulado) − t(mínimo real), en s, con t = 0 al inicio de la ventana.\n")
    md.append("⚠️ **Descomposición aproximada, no partición exacta.** \"Forma\" = ECM 2 y \"timing\" = ECM 1 − ECM 2. ECM 2 compara cada "
              "punto real con el punto más cercano de la trayectoria simulada, así que absorbe parte del avance (un atraso a lo largo de una "
              "recta casi no cuesta ECM 2) y no separa del todo el avance del desvío lateral. Además, ECM 1 excl. promedia sobre N1 "
              "instantes y ECM 2 sobre N2 (difieren si el peatón llega antes al target, D13).\n")
    res = {}
    for L in ("A", "B"):
        ped, ev = read_ecm(OFFICIAL[L])
        g, p1, p2 = GRID[L]
        rows = load_grid(g)
        rows = rows[(rows[:, 0] == p1) & (rows[:, 1] == p2)]
        assert abs(rows[:, 3].mean() - np.mean([ev[e]["ecm1"] for e in EVENTS])) < 1e-6, f"{L}: la corrida no coincide con la grilla"
        tot = sum(ev[e]["ecm1"] for e in EVENTS)
        lag = {e: ev[e]["tmin"] - ev[e]["tmin_exp"] for e in EVENTS}
        res[L] = dict(ped=ped, ev=ev, tot=tot, lag=lag)
    md.append(f"Poblacional: {LBL['A']} ECM 1 excl. {c(res['A']['tot'] / 19)}, ECM 2 {c(np.mean([res['A']['ev'][e]['ecm2'] for e in EVENTS]))}; "
              f"{LBL['B']} ECM 1 excl. {c(res['B']['tot'] / 19)}, ECM 2 {c(np.mean([res['B']['ev'][e]['ecm2'] for e in EVENTS]))} "
              "(coinciden con grid_A.txt y grid_B.txt).\n")

    md.append("### 1a. Por evento, ordenado por aporte al ECM 1 excl. poblacional de A\n")
    md.append("| evento | A: ECM 1 | A: aporte | A: acumulado | A: ECM 2 (forma) | A: timing | A: timing / ECM 1 | A: corrimiento | "
              "B: ECM 1 | B: aporte | B: ECM 2 (forma) | B: timing / ECM 1 | B: corrimiento |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    order = sorted(EVENTS, key=lambda e: -res["A"]["ev"][e]["ecm1"])
    acc = 0
    for e in order:
        a, b = res["A"]["ev"][e], res["B"]["ev"][e]
        acc += a["ecm1"] / res["A"]["tot"] * 100
        md.append(f"| {e} | {c(a['ecm1'])} | {pct(a['ecm1'] / res['A']['tot'] * 100)} | {pct(acc)} | {c(a['ecm2'])} | {c(a['ecm1'] - a['ecm2'])} | "
                  f"{pct((a['ecm1'] - a['ecm2']) / a['ecm1'] * 100)} | {c(res['A']['lag'][e], 2)} | {c(b['ecm1'])} | "
                  f"{pct(b['ecm1'] / res['B']['tot'] * 100)} | {c(b['ecm2'])} | {pct((b['ecm1'] - b['ecm2']) / b['ecm1'] * 100)} | {c(res['B']['lag'][e], 2)} |")
    md.append("")
    for L in ("A", "B"):
        ev, tot = res[L]["ev"], res[L]["tot"]
        o = sorted(EVENTS, key=lambda e: -ev[e]["ecm1"])
        cum = np.cumsum([ev[e]["ecm1"] for e in o]) / tot
        n50, n80 = int(np.searchsorted(cum, 0.5) + 1), int(np.searchsorted(cum, 0.8) + 1)
        e1 = np.array([ev[e]["ecm1"] for e in EVENTS])
        e2 = np.array([ev[e]["ecm2"] for e in EVENTS])
        lag = np.array([res[L]["lag"][e] for e in EVENTS])
        res[L].update(n50=n50, n80=n80, o=o)
        md.append(f"- **{LBL[L]}:** {n50} eventos explican el 50% del ECM 1 excl. poblacional ({', '.join(map(str, o[:n50]))}) y {n80} el 80% "
                  f"(base: suma de los 19). Forma (ECM 2) = {pct(e2.sum() / e1.sum() * 100)} del ECM 1 poblacional y timing = "
                  f"{pct(100 - e2.sum() / e1.sum() * 100)} (aproximado). Corrimiento: mediana {c(float(np.median(lag)), 2)} s, tarde en "
                  f"{int((lag > 0).sum())}/19. Correlación corrimiento–ECM 1 por evento (n = 19): Pearson {c(np.corrcoef(lag, e1)[0, 1], 2)}, "
                  f"Spearman {c(spearman(lag, e1), 2)}; con |corrimiento|: Pearson {c(np.corrcoef(np.abs(lag), e1)[0, 1], 2)}, "
                  f"Spearman {c(spearman(np.abs(lag), e1), 2)}.")
    md.append("")

    md.append("### 1b. Por peatón (A y B), ordenado por ECM 1 excl. de A\n")
    md.append("| evento | peatón (ID) | A: ECM 1 | A: ECM 2 | A: aporte al poblacional | B: ECM 1 | B: ECM 2 |")
    md.append("|---|---|---|---|---|---|---|")
    keys = sorted(res["A"]["ped"], key=lambda k: -res["A"]["ped"][k]["ecm1"])
    for k in keys:
        a, b = res["A"]["ped"][k], res["B"]["ped"][k]
        side = "izq." if k[1] == 1 else "der."
        md.append(f"| {k[0]} | {k[1]} {side} ({a['id']}) | {c(a['ecm1'])} | {c(a['ecm2'])} | {pct(a['ecm1'] / 2 / res['A']['tot'] * 100)} | "
                  f"{c(b['ecm1'])} | {c(b['ecm2'])} |")
    md.append("\nAporte del peatón = ECM 1 del peatón / 2 / suma de los 19 ECM 1 de evento (el evento promedia sus dos peatones).\n")
    for L in ("A", "B"):
        ped, tot = res[L]["ped"], res[L]["tot"]
        right = sum(ped[(e, 2)]["ecm1"] for e in EVENTS) / 2 / tot * 100
        top = sorted(ped, key=lambda k: -ped[k]["ecm1"])
        n_top = next(n for n in range(1, 39) if any(k[1] == 1 for k in top[:n])) - 1
        md.append(f"- {LBL[L]}: los 19 peatones **derechos** (salen de x ≈ 8 m hacia −x) aportan {pct(right)} del ECM 1 excl. poblacional y los "
                  f"izquierdos {pct(100 - right)} (base: suma de los 19 eventos). Los {n_top} peatones con más ECM 1 son todos derechos.")
    md.append("")
    fig_decomposition(res)
    return res


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def fig_decomposition(res):
    ev, o = res["A"]["ev"], res["A"]["o"]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = np.arange(19)
    f = np.array([ev[e]["ecm2"] for e in o])
    t = np.array([ev[e]["ecm1"] - ev[e]["ecm2"] for e in o])
    ax.bar(x, f, color=COLORS["A"], label="forma ≈ ECM 2")
    ax.bar(x, t, bottom=f, color="#56B4E9", label="timing ≈ ECM 1 − ECM 2")
    ax.plot(x, [res["B"]["ev"][e]["ecm1"] for e in o], ls="none", marker="s", ms=9, color=COLORS["B"], label="ECM 1 de B(3,5; 1)")
    ax.set_xticks(x, [str(e) for e in o])
    ax.set_xlabel("evento (ordenado por ECM 1 de A)")
    ax.set_ylabel("ECM 1 excl. de A(3; 0,5) (m²)")
    style(ax, "y")
    ax.set_xticks(x, [str(e) for e in o])
    ax.legend(loc="upper right", frameon=True, framealpha=0.95)
    save(fig, "descomposicion_A.png")


# ---------------------------------------------------------------- 2. retraso de fase
def contact_before_min(rows, tmin_exp):
    t = rows[:, 0]
    d = np.hypot(rows[:, 1] - rows[:, 5], rows[:, 2] - rows[:, 6])
    m = (t < tmin_exp) & ~np.isnan(d)
    return bool(np.any(d[m] < 2 * R))


def phase(md, res):
    md.append("## 2. Retraso de fase\n")
    runs = {"A": OFFICIAL["A"], "base": OFFICIAL["base"]}
    _, base_ev = read_ecm(OFFICIAL["base"])
    tmin_exp = {e: base_ev[e]["tmin_exp"] for e in EVENTS}
    contact = {e: contact_before_min(read_rows(OFFICIAL["base"], e), tmin_exp[e]) for e in EVENTS}
    free = [e for e in EVENTS if not contact[e]]

    # 2a: rapidez simulada − real contra el tiempo
    grid = np.round(np.arange(0, 3.0 + 1e-9, 1 / 15.0192), 6)
    curves = {}
    for L, folder in runs.items():
        for subset_name, subset in (("19", list(EVENTS)), ("libres", free)):
            diffs = []
            for e in subset:
                rows = read_rows(folder, e)
                for p in (1, 2):
                    t, x, y, sp, fr = real_window(e, p)
                    _, _, ssp = sim_at(rows, p, fr, INFO[(e, p)]["f0"])
                    k = min(len(ssp), int(np.sum(t <= tmin_exp[e] + 1e-9)))
                    d = np.full(len(grid), np.nan)
                    tt = t[:k]
                    for j, g in enumerate(grid):
                        hit = np.where(np.abs(tt - g) < 0.5 / 15.0192)[0]
                        if len(hit):
                            d[j] = ssp[hit[0]] - sp[hit[0]]
                    diffs.append(d)
            curves[(L, subset_name)] = np.array(diffs)
    md.append("### 2a. Rapidez simulada − real, desde el inicio de la ventana hasta el mínimo real\n")
    md.append("Rapidez real: diferencia centrada de ±2 frames con tiempos reales (la del recorte). Rapidez simulada: |v| de la fila del frame. "
              "Mediana entre peatones; cada peatón entra solo hasta el mínimo real de su evento. Δt = Δt_exp/64.\n")
    md.append(f"Línea base: eventos **sin contacto antes del mínimo real** (distancia simulada < 2R = 0,5 m antes de t_min real): "
              f"{', '.join(map(str, free)) or 'ninguno'} ({len(free)}/19). Con contacto antes del mínimo: "
              f"{', '.join(str(e) for e in EVENTS if contact[e])}.\n")
    md.append("| t (s) | A(3; 0,5), 19 eventos: mediana (m/s) | [p25; p75] | n | sin capa, 19 eventos: mediana | sin capa, sin contacto previo: mediana | n |")
    md.append("|---|---|---|---|---|---|---|")
    for tq in (0, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3):
        j = int(np.argmin(np.abs(grid - tq)))
        a = curves[("A", "19")][:, j]
        b19 = curves[("base", "19")][:, j]
        bf = curves[("base", "libres")][:, j]
        ok = ~np.isnan(a)
        q = np.nanpercentile(a, [25, 75]) if ok.any() else (np.nan, np.nan)
        md.append(f"| {c(tq, 2)} | {c(float(np.nanmedian(a)), 3)} | [{c(q[0], 3)}; {c(q[1], 3)}] | {int(ok.sum())} | {c(float(np.nanmedian(b19)), 3)} | "
                  f"{c(float(np.nanmedian(bf)), 3) if len(free) else '—'} | {int((~np.isnan(bf)).sum()) if len(free) else 0} |")
    md.append("")
    fig_speed(grid, curves, free)

    # 2b: avance perdido, relajación, v_d y longitud por peatón
    md.append("### 2b. Avance en x en el instante del mínimo real: relajación de v_0, v_d y longitud del recorrido\n")
    md.append("Δs = (x_sim − x_real)·sentido de avance en t_min real (negativo = el simulado va atrás), en m. Relajación a mano, sin tocar τ "
              "(peatón libre, τ = 0,5 s): x(t) = x_0 + v_d e_tx t + (v_0x − v_d e_tx)·τ·(1 − e^(−t/τ)). Contra un avance a v_d constante, el "
              "simulado libre pierde P_relaj = (v_d e_tx − v_0x)·sentido·τ·(1 − e^(−t/τ)). El real también arranca con v_0 y puede ir más "
              "rápido o más lento que v_d: G_real = avance real − v_d e_tx·sentido·t. Para el peatón libre vale exactamente "
              "**Δs_libre = −P_relaj − G_real**: el atraso se reparte entre la relajación y lo que el real le saca a v_d. La capa agrega "
              "Δs_A − Δs_sin capa. Rapidez real media = longitud suavizada (media móvil de 5 frames) / tiempo, antes y después del mínimo real. "
              "Desvío = longitud − avance en x hasta t_min real (lo que se camina de más fuera del eje); la real va suavizada, porque el ruido "
              "de seguimiento (σ ≈ 1 cm) alarga la cruda.\n")
    md.append("| evento | peatón | v_d (m/s) | v_0x·sentido (m/s) | t_min real (s) | rapidez real antes / después del mínimo (m/s) | Δs A (m) | "
              "Δs sin capa (m) | Δs libre predicho (m) | P_relaj (m) | G_real (m) | desvío A / sin capa / real (m) |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    rows_out = []
    for e in EVENTS:
        rA, rB = read_rows(OFFICIAL["A"], e), read_rows(OFFICIAL["base"], e)
        for p in (1, 2):
            i = INFO[(e, p)]
            t, x, y, sp, fr = real_window(e, p)
            xs, ys, _ = smoothed_window(e, p)
            k = int(np.sum(t <= tmin_exp[e] + 1e-9))      # frames hasta el mínimo real, inclusive
            km = k - 1
            s = DIR[p]
            sxA = sim_at(rA, p, fr, i["f0"])[0]
            sxB = sim_at(rB, p, fr, i["f0"])[0]
            ds_A, ds_B = (sxA[km] - x[km]) * s, (sxB[km] - x[km]) * s
            ex = (i["tx"] - x[0]) / np.hypot(i["tx"] - x[0], i["ty"] - y[0])
            tm = t[km]
            relax = (i["vd"] * ex - i["v0x"]) * s * TAU * (1 - np.exp(-tm / TAU))
            gain = (x[km] - x[0]) * s - i["vd"] * ex * s * tm
            row_end = int((fr[km] - i["f0"]) * 4)
            cx = 1 + 4 * (p - 1)
            det = {}
            for name, rr in (("A", rA), ("base", rB)):
                det[name] = length(rr[:row_end + 1, cx], rr[:row_end + 1, cx + 1]) - (rr[row_end, cx] - rr[0, cx]) * s
            det["real"] = length(xs[:k], ys[:k]) - (xs[km] - xs[0]) * s
            v_before = length(xs[:k], ys[:k]) / tm
            v_after = length(xs[km:], ys[km:]) / (t[-1] - tm) if t[-1] > tm else np.nan
            rows_out.append(dict(e=e, p=p, vd=i["vd"], dsA=ds_A, dsB=ds_B, pred=-relax - gain, relax=relax, gain=gain,
                                 detA=det["A"], detB=det["base"], detR=det["real"], vb=v_before, va=v_after, tm=tm))
            md.append(f"| {e} | {p} | {c(i['vd'], 3)} | {c(i['v0x'] * s, 3)} | {c(tm, 2)} | {c(v_before, 3)} / {c(v_after, 3)} | {c(ds_A, 3)} | "
                      f"{c(ds_B, 3)} | {c(-relax - gain, 3)} | {c(relax, 3)} | {c(gain, 3)} | {c(det['A'], 3)} / {c(det['base'], 3)} / {c(det['real'], 3)} |")
    md.append("")
    R_ = {k: np.array([r[k] for r in rows_out]) for k in rows_out[0]}
    left, right = R_["p"] == 1, R_["p"] == 2

    def med(v, m=None, d=3):
        v = v if m is None else v[m]
        return f"{c(float(np.median(v)), d)} [{c(float(np.percentile(v, 25)), d)}; {c(float(np.percentile(v, 75)), d)}]"

    md.append("Resumen por peatón (mediana [p25; p75]; 19 izquierdos y 19 derechos):\n")
    md.append("| magnitud | izquierdos | derechos | los 38 |")
    md.append("|---|---|---|---|")
    for name, key in (("Δs A (m)", "dsA"), ("Δs sin capa (m)", "dsB"), ("P_relaj (m)", "relax"), ("G_real (m)", "gain"),
                      ("rapidez real antes del mínimo − v_d (m/s)", None), ("rapidez real después del mínimo − v_d (m/s)", "after"),
                      ("desvío A − desvío sin capa (m)", "detAB"), ("desvío A − desvío real (m)", "detAR")):
        v = {None: R_["vb"] - R_["vd"], "after": R_["va"] - R_["vd"], "detAB": R_["detA"] - R_["detB"], "detAR": R_["detA"] - R_["detR"]}.get(key)
        v = R_[key] if v is None else v
        md.append(f"| {name} | {med(v, left)} | {med(v, right)} | {med(v)} |")
    md.append("")
    md.append(f"Control: Δs sin capa contra Δs libre predicho, Pearson {c(np.corrcoef(R_['dsB'], R_['pred'])[0, 1], 3)}, mediana de la diferencia "
              f"{c(float(np.median(R_['dsB'] - R_['pred'])), 3)} m (n = 38; difieren solo donde hubo contacto antes del mínimo).\n")

    # por evento: el mínimo llega tarde si la suma de los atrasos de los dos se cierra a v_d1 + v_d2
    md.append("Por evento, en tiempo: atraso equivalente = −(Δs_1 + Δs_2)/(v_d1 + v_d2), la demora con que se cierra la brecha que falta. "
              "Se reparte igual que Δs: relajación (P_relaj) + lo que el real le saca a v_d (G_real) + capa (Δs_A − Δs_sin capa).\n")
    md.append("| evento | corrimiento A (s) | atraso equivalente A (s) | por relajación (s) | por G_real (s) | por la capa (s) |")
    md.append("|---|---|---|---|---|---|")
    ev_rows = []
    for e in EVENTS:
        m = R_["e"] == e
        vd = R_["vd"][m].sum()
        eq, rl, gn, ly = -R_["dsA"][m].sum() / vd, R_["relax"][m].sum() / vd, R_["gain"][m].sum() / vd, -(R_["dsA"][m] - R_["dsB"][m]).sum() / vd
        ev_rows.append((res["A"]["lag"][e], eq, rl, gn, ly))
        md.append(f"| {e} | {c(res['A']['lag'][e], 2)} | {c(eq, 2)} | {c(rl, 2)} | {c(gn, 2)} | {c(ly, 2)} |")
    ev_rows = np.array(ev_rows)
    md.append(f"| **mediana** | {c(float(np.median(ev_rows[:, 0])), 2)} | {c(float(np.median(ev_rows[:, 1])), 2)} | {c(float(np.median(ev_rows[:, 2])), 2)} | "
              f"{c(float(np.median(ev_rows[:, 3])), 2)} | {c(float(np.median(ev_rows[:, 4])), 2)} |")
    md.append(f"| **suma de los 19** | {c(float(ev_rows[:, 0].sum()), 2)} | {c(float(ev_rows[:, 1].sum()), 2)} | {c(float(ev_rows[:, 2].sum()), 2)} | "
              f"{c(float(ev_rows[:, 3].sum()), 2)} | {c(float(ev_rows[:, 4].sum()), 2)} |\n")
    md.append(f"Correlación por evento entre el corrimiento y el atraso equivalente: Pearson {c(np.corrcoef(ev_rows[:, 0], ev_rows[:, 1])[0, 1], 2)} (n = 19). "
              f"Base de los repartos: la suma de los 19 atrasos equivalentes ({c(float(ev_rows[:, 1].sum()), 2)} s): relajación "
              f"{pct(ev_rows[:, 2].sum() / ev_rows[:, 1].sum() * 100)}, G_real {pct(ev_rows[:, 3].sum() / ev_rows[:, 1].sum() * 100)}, capa "
              f"{pct(ev_rows[:, 4].sum() / ev_rows[:, 1].sum() * 100)}.\n")
    fig_relax(R_, res["A"]["lag"])
    speed_series(tmin_exp)
    return R_, tmin_exp, contact, ev_rows


def fig_speed(grid, curves, free):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    a = curves[("A", "19")]
    ax.fill_between(grid, np.nanpercentile(a, 25, axis=0), np.nanpercentile(a, 75, axis=0), color=COLORS["A"], alpha=0.18, lw=0)
    ax.plot(grid, np.nanmedian(a, axis=0), color=COLORS["A"], lw=2.5, label="A(3; 0,5), 19 eventos")
    ax.plot(grid, np.nanmedian(curves[("base", "19")], axis=0), color=COLORS["base"], lw=2, ls="--", label="sin capa, 19 eventos")
    if free:
        ax.plot(grid, np.nanmedian(curves[("base", "libres")], axis=0), color=INK, lw=2, ls=":",
                label=f"sin capa, sin contacto previo ({len(free)})")
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xlim(0, 3)
    ax.set_xlabel("tiempo desde el inicio de la ventana (s)")
    ax.set_ylabel("rapidez sim. − real (m/s)")
    style(ax)
    ax.legend(loc="upper right", frameon=True, framealpha=0.95)
    save(fig, "fase_rapidez.png")


def fig_relax(R_, lag):
    """Por evento: corrimiento del mínimo contra el atraso equivalente y sus tres partes (s)."""
    ev = np.array(list(EVENTS))
    parts = {k: np.array([sign * R_[k][R_["e"] == e].sum() / R_["vd"][R_["e"] == e].sum() for e in ev]) for k, sign in (("relax", 1), ("gain", 1))}
    parts["capa"] = np.array([-(R_["dsA"] - R_["dsB"])[R_["e"] == e].sum() / R_["vd"][R_["e"] == e].sum() for e in ev])
    fig, ax = plt.subplots(figsize=(12, 5.5))
    w = 0.27
    ax.bar(ev - w, parts["relax"], w, color="#56B4E9", label="relajación de v_0")
    ax.bar(ev, parts["gain"], w, color=COLORS["B"], label="el real supera a v_d")
    ax.bar(ev + w, parts["capa"], w, color=COLORS["F"], label="capa A")
    ax.plot(ev, [lag[e] for e in ev], ls="none", marker="D", ms=9, color=INK, label="corrimiento del mínimo")
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xticks(ev, [str(e) for e in ev])
    ax.set_xlabel("evento")
    ax.set_ylabel("atraso (s)")
    ax.set_ylim(-0.35, 1.0)
    style(ax, "y")
    ax.set_xticks(ev, [str(e) for e in ev])
    ax.legend(loc="upper left", ncol=2, frameon=True, framealpha=0.95, fontsize=14)
    save(fig, "atraso_por_evento.png")


def speed_series(tmin_exp):
    """CSV y figura de rapidez real y simulada de A por evento y peatón, desde el inicio de la ventana hasta el mínimo real."""
    lines = ["evento,peaton,t,rapidez_real,rapidez_A,rapidez_sin_capa"]
    fig, axes = plt.subplots(4, 5, figsize=(20, 14), sharex=True, sharey=True)
    for ax, e in zip(axes.flat, EVENTS):
        rA, rB = read_rows(OFFICIAL["A"], e), read_rows(OFFICIAL["base"], e)
        for p, ls in ((1, "-"), (2, "--")):
            t, _, _, sp, fr = real_window(e, p)
            k = int(np.sum(t <= tmin_exp[e] + 1e-9))
            sa, sb = sim_at(rA, p, fr, INFO[(e, p)]["f0"])[2], sim_at(rB, p, fr, INFO[(e, p)]["f0"])[2]
            for j in range(k):
                lines.append(f"{e},{p},{t[j]:.4f},{sp[j]:.4f},{sa[j]:.4f},{sb[j]:.4f}")
            ax.plot(t[:k], sp[:k], ls, color=COLORS["exp"], lw=1.8, label="real" if p == 1 else None)
            ax.plot(t[:k], sa[:k], ls, color=COLORS["A"], lw=1.8, label="A(3; 0,5)" if p == 1 else None)
        ax.text(0.04, 0.93, f"evento {e}", transform=ax.transAxes, va="top", fontsize=15)
        style(ax)
    axes.flat[-1].axis("off")
    for ax in axes[-1]:
        ax.set_xlabel("t (s)")
    for ax in axes[:, 0]:
        ax.set_ylabel("rapidez (m/s)")
    h, l = axes.flat[0].get_legend_handles_labels()
    axes.flat[-1].legend(h + [plt.Line2D([], [], color=MUTED, ls="-"), plt.Line2D([], [], color=MUTED, ls="--")],
                         l + ["peatón izquierdo", "peatón derecho"], loc="center", frameon=True, fontsize=16)
    fig.tight_layout()
    save(fig, "rapidez_por_evento.png")
    (OUT / "rapidez_series.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def v0_tests(md, res):
    md.append("### 2c. Pruebas de la velocidad inicial (solo como prueba, no como cambio)\n")
    md.append("Las cuatro con A(3; 0,5), ρ = 0,9, Δt = Δt_exp/64 y el recorte vigente. \"Primer cuadro\" = `--v0-frames 2`: la pendiente de dos "
              "frames es la diferencia entre el primer y el segundo frame de la ventana, sin ajuste. v_d·e_target y v_d·dirección ajustada salen de "
              "`diagnostics/V0Probe` (no va al ZIP); con `--mode fit` reproduce byte a byte la corrida oficial. Cambio con base en el ajuste de 5 cuadros (D12).\n")
    variants = [("ajuste de 5 cuadros (D12, oficial)", OFFICIAL["A"]), ("primer cuadro, sin ajuste", RUNS / "A_primer_cuadro"),
                ("v_0 = v_d·e_target", RUNS / "A_vd_target"), ("v_0 = v_d·dirección ajustada", RUNS / "A_vd_fitdir")]
    md.append("| v_0 | ECM 1 excl. | cambio | ECM 2 | cambio | corrimiento: mediana (s) | tarde (de 19) | |corrimiento| medio (s) | eventos con contacto |")
    md.append("|---|---|---|---|---|---|---|---|---|")
    base = None
    out = {}
    for name, folder in variants:
        _, ev = read_ecm(folder)
        e1 = np.mean([ev[e]["ecm1"] for e in EVENTS])
        e2 = np.mean([ev[e]["ecm2"] for e in EVENTS])
        lag = np.array([ev[e]["tmin"] - ev[e]["tmin_exp"] for e in EVENTS])
        if base is None:
            base = (e1, e2)
        out[name] = (e1, e2, ev)
        md.append(f"| {name} | {c(e1)} | {pct((e1 / base[0] - 1) * 100)} | {c(e2)} | {pct((e2 / base[1] - 1) * 100)} | {c(float(np.median(lag)), 2)} | "
                  f"{int((lag > 0).sum())} | {c(float(np.abs(lag).mean()), 2)} | {sum(ev[e]['contact'] for e in EVENTS)} |")
    md.append("")
    # Hasta cuándo influye v_0: |rapidez(ajuste) − rapidez(v_d e_target)| < 5% de v_d de ahí en adelante
    tcut, theory, offset = [], [], []
    for e in EVENTS:
        r0, r1 = read_rows(OFFICIAL["A"], e), read_rows(RUNS / "A_vd_target", e)
        n = min(len(r0), len(r1))
        _, ev0 = read_ecm(OFFICIAL["A"])
        for p in (1, 2):
            i = INFO[(e, p)]
            cx = 1 + 4 * (p - 1)
            dv = np.hypot(r0[:n, cx + 2] - r1[:n, cx + 2], r0[:n, cx + 3] - r1[:n, cx + 3])
            below = np.where(dv < 0.05 * i["vd"])[0]
            tcut.append(r0[below[0], 0] if len(below) else np.nan)
            ex, ey = i["tx"] - r0[0, cx], i["ty"] - r0[0, cx + 1]
            nrm = np.hypot(ex, ey)
            gap = np.hypot(i["vd"] * ex / nrm - i["v0x"], i["vd"] * ey / nrm - i["v0y"])
            theory.append(TAU * np.log(gap / (0.05 * i["vd"])) if gap > 0.05 * i["vd"] else 0.0)
            rm = int(round(ev0[e]["tmin_exp"] / (i["dt"] / 4)))
            offset.append((r1[rm, cx] - r0[rm, cx]) * DIR[p])
    tcut, theory, offset = np.array(tcut), np.array(theory), np.array(offset)
    md.append(f"Hasta cuándo influye la velocidad inicial en la **velocidad**: primer instante en que |v(ajuste) − v(v_d·e_target)| < 5% de v_d "
              f"(vectorial, A(3; 0,5)). Mediana {c(float(np.nanmedian(tcut)), 2)} s, rango {c(float(np.nanmin(tcut)), 2)} a {c(float(np.nanmax(tcut)), 2)} s "
              f"(38 peatones). Esperado para el peatón libre, τ·ln(|v_d e_t − v_0|/(0,05 v_d)): mediana {c(float(np.median(theory)), 2)} s, rango "
              f"{c(float(theory.min()), 2)} a {c(float(theory.max()), 2)} s. En la **posición** la influencia no se borra: queda el avance "
              f"(v_d e_t − v_0)·τ de la relajación. En t_min real, x(v_d·e_target) − x(ajuste) en el sentido de avance vale mediana "
              f"{c(float(np.median(offset)), 3)} m, rango {c(float(offset.min()), 3)} a {c(float(offset.max()), 3)} m.\n")
    out["_tcut"] = float(np.nanmedian(tcut))
    return out


# ---------------------------------------------------------------- 3. regla de lado
def side_of(xi, yi, xj, yj, s):
    """+1 si el otro queda a la izquierda del peatón (pasa por su derecha), −1 si queda a su derecha. s = sentido de avance en x."""
    return 1 if (yj - yi) * s > 0 else -1


def sides(md, res):
    md.append("## 3. Regla de lado\n")
    band_y = np.concatenate([TRAJ[k][TRAJ[k][:, 3] == 1, 2] for k in TRAJ])
    ylo, yhi = float(band_y.min()), float(band_y.max())
    md.append("Lado = de qué lado pasa cada peatón respecto del otro, en el sentido de su avance sobre x: **der.** = el otro le queda a la izquierda "
              "(pasa por su derecha). Real: en el frame del mínimo real. Simulado: en la fila del mínimo simulado de A(3; 0,5). Regla actual: el "
              "lado que eligió la capa en la primera activación de cada peatón (RunTrace: s_c = e_t^⊥·(r + w t*); s_c < 0 o |s_c| ≤ 0,05 m "
              "esquiva a la derecha). En un cruce de dos, si un peatón pasa por su derecha el otro también, así que el lado es uno por evento.\n")
    md.append(f"Alternativas sin parámetros nuevos, evaluadas en la primera activación con la y del peatón en el cruce predicho, y_c = y + v_d e_ty t*:\n"
              f"- (a) siempre a la derecha;\n"
              f"- (b) hacia el borde más lejano de la banda y ∈ [{c(ylo, 2)}; {c(yhi, 2)}] m (y mín. y máx. de los 38 peatones dentro de sus ventanas "
              f"recortadas). ⚠️ **Post-hoc y solo diagnóstico**: los bordes salen de los mismos datos;\n"
              f"- (b') columna extra: alejarse de y = 2 m (el cruce \"por y ~ 2 m\" del LEEME), es decir, esquivar hacia +y si y_c > 2 y hacia −y si no. "
              f"Con la banda centrada en {c((ylo + yhi) / 2, 2)} m, (b) y (b') eligen casi siempre al revés: (b) va hacia el centro y (b') hacia el borde.\n")
    _, evA = read_ecm(OFFICIAL["A"])
    md.append("| evento | lado real | lado simulado A | regla A: peatón 1 / 2 (s_c en m) | desempate | d_min predicho al activarse (m) | "
              "(a) | (b) peatón 1 / 2 | (b') peatón 1 / 2 | regla B: peatón 1 / 2 | lado simulado B | A: ECM 1 excl. |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    name = {1: "der.", -1: "izq."}
    hits = defaultdict(int)
    wrong = []
    ties, frontal, all_ties, all_frontal, uncoord = [], [], [], [], []
    sc_wrong = {}
    for e in EVENTS:
        i1, i2 = INFO[(e, 1)], INFO[(e, 2)]
        a1, a2 = TRAJ[(e, 1)], TRAJ[(e, 2)]
        k1 = np.where(a1[:, 0] == i1["fmin"])[0][0]
        k2 = np.where(a2[:, 0] == i1["fmin"])[0][0]
        real = side_of(a1[k1, 1], a1[k1, 2], a2[k2, 1], a2[k2, 2], 1)
        sim_side = {}
        for L in ("A", "B"):
            rows = read_rows(OFFICIAL[L], e)
            _, ev = read_ecm(OFFICIAL[L])
            r = int(round(ev[e]["tmin"] / (i1["dt"] / 4)))
            sim_side[L] = side_of(rows[r, 1], rows[r, 2], rows[r, 5], rows[r, 6], 1)
        rule, rule_b, alt_b, alt_b2, scs, dmins = {}, {}, {}, {}, {}, {}
        for L, store in (("a", rule), ("b", rule_b)):
            tr = read_trace(RUNS / "traza" / f"{L}_{e}.txt")
            rows = read_rows(OFFICIAL["A" if L == "a" else "B"], e)
            for p in (1, 2):
                if p not in tr:
                    store[p] = 0
                    continue
                t_on, dmin, sc = tr[p]
                store[p] = 1 if (abs(sc) <= SIDE_EPS or sc < 0) else -1
                if L == "a":
                    scs[p], dmins[p] = sc, dmin
                    i = INFO[(e, p)]
                    rr = int(round(t_on / (i["dt"] / 4)))
                    cx = 1 + 4 * (p - 1)
                    xi, yi = rows[rr, cx], rows[rr, cx + 1]
                    ex, ey = i["tx"] - xi, i["ty"] - yi
                    nrm = np.hypot(ex, ey)
                    # t* de la predicción, despejado de la traza no está; se usa el de la línea S (columna 4)
                    tstar = first_tstar(RUNS / "traza" / f"a_{e}.txt", p)
                    yc = yi + i["vd"] * ey / nrm * tstar
                    s = DIR[p]
                    # derecha del peatón: −y si avanza a +x, +y si avanza a −x
                    space_right = (yc - ylo) if s > 0 else (yhi - yc)
                    space_left = (yhi - yc) if s > 0 else (yc - ylo)
                    alt_b[p] = 1 if space_right >= space_left else -1
                    away_up = yc > 2.0
                    # ir hacia +y es la izquierda del que avanza a +x y la derecha del que avanza a −x
                    alt_b2[p] = (-1 if s > 0 else 1) if away_up else (1 if s > 0 else -1)
        for p in (1, 2):
            hits[("regla", "ped")] += rule[p] == real
            hits[("a", "ped")] += 1 == real
            hits[("b", "ped")] += alt_b[p] == real
            hits[("b2", "ped")] += alt_b2[p] == real
            hits[("reglaB", "ped")] += rule_b[p] == real
        hits[("sim", "ev")] += sim_side["A"] == real
        hits[("simB", "ev")] += sim_side["B"] == real
        hits[("a", "ev")] += 1 == real
        for key, d in (("regla", rule), ("b", alt_b), ("b2", alt_b2), ("reglaB", rule_b)):
            hits[(key, "ev")] += d[1] == real and d[2] == real
        is_tie = any(abs(scs.get(p, 1)) <= SIDE_EPS for p in (1, 2))
        is_frontal = any(dmins.get(p, 9) < 2 * R for p in (1, 2))
        all_ties += [e] if is_tie else []
        all_frontal += [e] if is_frontal else []
        uncoord += [e] if rule[1] != rule[2] else []
        if sim_side["A"] != real:
            wrong.append(e)
            sc_wrong[e] = (scs, dmins)
            ties += [e] if is_tie else []
            frontal += [e] if is_frontal else []
        md.append(f"| {e} | {name[real]} | {name[sim_side['A']]}{' ⚠️' if sim_side['A'] != real else ''} | "
                  f"{name.get(rule[1], '—')} ({c(scs.get(1), 3)}) / {name.get(rule[2], '—')} ({c(scs.get(2), 3)}) | {'sí' if is_tie else 'no'} | "
                  f"{c(dmins.get(1), 3)} / {c(dmins.get(2), 3)} | der. | {name[alt_b[1]]} / {name[alt_b[2]]} | {name[alt_b2[1]]} / {name[alt_b2[2]]} | "
                  f"{name.get(rule_b[1], '—')} / {name.get(rule_b[2], '—')} | {name[sim_side['B']]}{' ⚠️' if sim_side['B'] != real else ''} | {c(evA[e]['ecm1'])} |")
    md.append("")
    n_right = sum(1 for e in EVENTS if real_side(e) == 1)
    md.append(f"Lado real: der. en {n_right}/19 eventos.\n")
    md.append("| criterio | aciertos por peatón (de 38) | eventos con los dos peatones bien (de 19) |")
    md.append("|---|---|---|")
    for key, label in (("regla", "regla actual de A (primera activación)"), ("a", "(a) siempre a la derecha"), ("b", "(b) borde más lejano de la banda (post-hoc)"),
                       ("b2", "(b') alejarse de y = 2 m"), ("reglaB", "regla actual de B (primera activación)")):
        md.append(f"| {label} | {hits[(key, 'ped')]} | {hits[(key, 'ev')]} |")
    md.append(f"| lado simulado final de A | — | {hits[('sim', 'ev')]} |")
    md.append(f"| lado simulado final de B | — | {hits[('simB', 'ev')]} |\n")

    tot = res["A"]["tot"]
    sub = sum(evA[e]["ecm1"] for e in wrong)
    expected = [6, 8, 10, 12, 17]
    md.append(f"Eventos en que A cruza del lado contrario al real: **{', '.join(map(str, wrong))}** "
              f"({'coincide' if wrong == expected else 'NO coincide'} con la lista del pedido, 6, 8, 10, 12 y 17).\n")
    md.append("| evento | A: ECM 1 excl. | aporte al poblacional | s_c peatón 1 / 2 (m) | d_min predicho peatón 1 / 2 (m) |")
    md.append("|---|---|---|---|---|")
    for e in wrong:
        scs, dmins = sc_wrong[e]
        md.append(f"| {e} | {c(evA[e]['ecm1'])} | {pct(evA[e]['ecm1'] / tot * 100)} | {c(scs.get(1), 3)} / {c(scs.get(2), 3)} | "
                  f"{c(dmins.get(1), 3)} / {c(dmins.get(2), 3)} |")
    others = [e for e in EVENTS if e not in wrong]
    md.append(f"\n- Juntos aportan {pct(sub / tot * 100)} del ECM 1 excl. poblacional de A (base: suma de los 19). ECM 1 medio de esos "
              f"{len(wrong)} eventos: {c(sub / len(wrong))}; de los otros {len(others)}: {c(np.mean([evA[e]['ecm1'] for e in others]))}.")
    md.append(f"- Con |s_c| ≤ 0,05 m (desempate) en algún peatón: {len(ties)} de {len(wrong)} ({', '.join(map(str, ties)) or 'ninguno'}).")
    md.append(f"- Casi frontales (definición de la IA: d_min predicho < 2R = 0,5 m en la primera activación, choque de cuerpos sin esquive): "
              f"{len(frontal)} de {len(wrong)} ({', '.join(map(str, frontal)) or 'ninguno'}). La definición no discrimina: en los 19 eventos son "
              f"casi frontales {len(all_frontal)}/19 y tienen desempate {len(all_ties)}/19 ({', '.join(map(str, all_ties))}).")
    md.append(f"- Elección descoordinada (en la primera activación los dos peatones eligen lados distintos, así que se desvían hacia la misma y): "
              f"{', '.join(map(str, uncoord)) or 'ninguno'} ({len(uncoord)}/19).\n")
    return dict(wrong=wrong, share=sub / tot, sub=sub, hits=hits, ties=ties, uncoord=uncoord)


def first_tstar(path, agent):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        p = line.split()
        if p and p[0] == "S" and p[3] == "on" and int(p[2]) == agent:
            return float(p[4])
    return 0.0


def real_side(e):
    i1 = INFO[(e, 1)]
    a1, a2 = TRAJ[(e, 1)], TRAJ[(e, 2)]
    k1 = np.where(a1[:, 0] == i1["fmin"])[0][0]
    k2 = np.where(a2[:, 0] == i1["fmin"])[0][0]
    return side_of(a1[k1, 1], a1[k1, 2], a2[k2, 1], a2[k2, 2], 1)


def notes(md, res, R_, ev_rows, v0, sd):
    A = res["A"]
    pop = A["tot"] / 19
    ecm2_share = np.mean([A["ev"][e]["ecm2"] for e in EVENTS]) / pop * 100
    left, right = R_["p"] == 1, R_["p"] == 2
    right_share = sum(A["ped"][(e, 2)]["ecm1"] for e in EVENTS) / 2 / A["tot"] * 100
    tot_eq = ev_rows[:, 1].sum()
    names = list(v0)
    vt, vf, f1 = v0[names[2]], v0[names[3]], v0[names[1]]
    ok = [e for e in EVENTS if e not in sd["wrong"]]
    med_ok = float(np.median([A["ev"][e]["ecm2"] for e in ok]))
    side_gain = sum(A["ev"][e]["ecm2"] - med_ok for e in sd["wrong"]) / 19
    side_timing = sum(A["ev"][e]["ecm1"] - A["ev"][e]["ecm2"] for e in sd["wrong"]) / sum(A["ev"][e]["ecm1"] for e in sd["wrong"]) * 100
    h = sd["hits"]
    alts = {"(a)": h[("a", "ev")], "(b)": h[("b", "ev")], "(b')": h[("b2", "ev")]}
    better = [k for k, v in alts.items() if v > h[("regla", "ev")]]
    alt_text = ", ".join(f"{k} {v}" for k, v in alts.items())
    best_alt = (f"ninguna alternativa sin parámetros acierta más eventos que la regla actual ({h[('regla', 'ev')]}/19; {alt_text})" if not better
                else f"aciertan más eventos que la regla actual ({h[('regla', 'ev')]}/19): {', '.join(better)} ({alt_text})")
    crash = ", ".join(str(e) for e, r in zip(EVENTS, ev_rows) if r[4] < -0.05)
    tied = len(sd["ties"])
    unco = len([e for e in sd["uncoord"] if e in sd["wrong"]])
    md.append("## 4. Qué apoya o contradice cada hipótesis\n")
    md.append(f"- **El error de A es sobre todo de timing (aproximado).** Apoya: ECM 2 = {pct(ecm2_share)} del ECM 1 excl. poblacional; corrimiento y ECM 1 "
              f"por evento con Spearman {c(spearman(np.array([A['lag'][e] for e in EVENTS]), np.array([A['ev'][e]['ecm1'] for e in EVENTS])), 2)} (n = 19). "
              f"Matiz: ECM 2 absorbe parte del avance, así que el reparto es aproximado (sección 1).")
    md.append(f"- **El retraso de fase no lo origina la capa.** Apoya: la línea base tiene el mismo atraso en x que A (mediana de Δs {c(float(np.median(R_['dsB'])), 3)} "
              f"contra {c(float(np.median(R_['dsA'])), 3)} m); el desvío extra de A sobre la línea base es {c(float(np.median(R_['detA'] - R_['detB'])), 3)} m de "
              f"mediana; la capa explica {pct(ev_rows[:, 4].sum() / tot_eq * 100)} del atraso equivalente sumado (base: {c(tot_eq, 2)} s, 19 eventos; el signo negativo "
              f"viene de los eventos {crash}, donde la línea base choca y se frena). B(3,5; 1) tiene el mismo corrimiento (sección 1). No la contradice ningún dato.")
    md.append(f"- **La relajación de v_0 hacia v_d (τ = 0,5 s) explica la mayor parte del corrimiento del mínimo.** Apoya: calculada a mano explica "
              f"{pct(ev_rows[:, 2].sum() / tot_eq * 100)} del atraso equivalente sumado (mediana por evento {c(float(np.median(ev_rows[:, 2])), 2)} s contra "
              f"un corrimiento mediano de {c(float(np.median(ev_rows[:, 0])), 2)} s). Con v_0 = v_d·e_target el corrimiento mediano baja a "
              f"{c(float(np.median([vt[2][e]['tmin'] - vt[2][e]['tmin_exp'] for e in EVENTS])), 2)} s. Contradice en parte: el ECM 1 solo baja "
              f"{pct((1 - vt[0] / pop) * 100)} (v_d·e_target) o {pct((1 - vf[0] / pop) * 100)} (v_d·dirección ajustada), y el ECM 2 sube. El real también "
              f"arranca lento: el izquierdo pierde contra v_d casi lo mismo que el modelo (G_real mediana {c(float(np.median(R_['gain'][left])), 3)} m "
              f"contra P_relaj {c(float(np.median(R_['relax'][left])), 3)} m), así que la relajación \"sobra\" sobre todo en el derecho.")
    md.append(f"- **La v_d constante (rapidez media de la ventana) no sigue el perfil real.** Apoya: los derechos van más rápido que v_d antes del mínimo "
              f"(mediana +{c(float(np.median((R_['vb'] - R_['vd'])[right])), 3)} m/s) y más lento después ({c(float(np.median((R_['va'] - R_['vd'])[right])), 3)} m/s); "
              f"los izquierdos, al revés y con menos amplitud. Coincide con que los 19 derechos acumulan {pct(right_share)} del ECM 1 excl. poblacional. En el "
              f"tiempo de encuentro los dos efectos se compensan en parte (G_real explica {pct(ev_rows[:, 3].sum() / tot_eq * 100)} del atraso sumado), "
              f"pero no en el ECM 1, que es por peatón. Es una hipótesis nueva que salió del diagnóstico; no se probó con una corrida.")
    md.append(f"- **v_0 por ajuste lineal contra el primer cuadro.** Sin ajuste, el ECM 1 sube {pct((f1[0] / pop - 1) * 100)}: el ajuste no es la causa del "
              f"atraso. v_0 influye en la velocidad hasta ≈ {c(v0['_tcut'], 1)} s (mediana, sección 2c), pero el avance perdido queda para siempre en la posición.")
    md.append(f"- **Regla de lado.** Apoya que pesa: los eventos de lado contrario ({', '.join(map(str, sd['wrong']))}) aportan {pct(sd['share'] * 100)} del ECM 1 "
              f"excl. poblacional; en {tied} de ellos hay desempate y en {unco} la elección es descoordinada. Contradice que sea la causa "
              f"principal: en esos eventos el timing sigue siendo {pct(side_timing)} del ECM 1 (aproximado), y {best_alt} (sección 3).\n")
    md.append("## 5. Mejora que cabría esperar por causa (sin elegir cuál aplicar)\n")
    md.append(f"Base: ECM 1 excl. poblacional de A(3; 0,5) = {c(pop)}, ρ = 0,9, Δt = Δt_exp/64. Son cotas o estimaciones sobre la calibración "
              "actual, sin recalibrar; no se suman, porque las causas se solapan.\n")
    md.append("| causa | estimación | de dónde sale |")
    md.append("|---|---|---|")
    md.append(f"| relajación de v_0 | ECM 1 {c(vt[0])} a {c(vf[0])} ({pct((vt[0] / pop - 1) * 100)} a {pct((vf[0] / pop - 1) * 100)}); ECM 2 sube | "
              "corridas de prueba v_0 = v_d (2c), sin recalibrar |")
    md.append(f"| v_d constante contra el perfil real | sin estimación directa; cota: la parte de timing es ≈ {pct(100 - ecm2_share)} del ECM 1 y los derechos "
              f"aportan {pct(right_share)} | secciones 1 y 2b; habría que correr una prueba |")
    md.append(f"| recorrido más largo por la capa | ≈ 0: desvío extra mediano {c(float(np.median(R_['detA'] - R_['detB'])), 3)} m, "
              f"{pct(ev_rows[:, 4].sum() / tot_eq * 100)} del atraso | 2b |")
    md.append(f"| regla de lado | ≈ {c(side_gain)} de ECM 1 poblacional ({pct(side_gain / pop * 100)}), si el exceso de ECM 2 de los "
              f"{len(sd['wrong'])} eventos sobre la mediana de los otros (≈ {c(med_ok)}) desapareciera. Contraste: el mejor lado por evento entre "
              "20 monedas da 0,3972 (−7,2%, `antes_despues_d45_compuerta.md`) | sección 3 |\n")


# ---------------------------------------------------------------- salida
def save(fig, name):
    for ax in fig.axes:
        assert not ax.get_title(), f"{name}: título embebido"
    fig.savefig(FIGS / name, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    FIGS.mkdir(parents=True, exist_ok=True)
    md = ["# Diagnóstico del error de A(3; 0,5)\n",
          "Recorte vigente: D(45°), persistencia 5, opción 1, compuerta de tramo compartido X = 1,5 m (post-hoc). ρ = 0,9, Δt = Δt_exp/64, "
          "salida cada Δt_exp/4. ECM 1 = variante excluyente. Referencia: B(3,5; 1). Pares = mejores de ECM 1 excl. de la grilla oficial. "
          "Todo es de solo lectura sobre corridas existentes, salvo las pruebas de v_0 de 2c (no cambian el motor). "
          "Generado por `scripts/graph_gen/diag_a.py`.\n"]
    res = decomposition(md)
    R_, tmin_exp, contact, ev_rows = phase(md, res)
    v0 = v0_tests(md, res)
    sd = sides(md, res)
    notes(md, res, R_, ev_rows, v0, sd)
    (OUT / "diagnostico_A.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Salida: {OUT / 'diagnostico_A.md'} y {FIGS}")


if __name__ == "__main__":
    main()
