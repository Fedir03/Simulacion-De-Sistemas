#!/usr/bin/env python3
"""Fase 3 (sensibilidad del recorte, ρ cada 0,1, chattering) y Fase 4 (preguntas abiertas) del recorte al tramo frontal.

Lee outputs/pilot (con recorte), outputs/pilot_sin_recorte, las dos líneas base y lo que exporta
`java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain trim-export` (outputs/recorte/*.csv). Δt = Δt_exp/64. ECM 1 = variante excluyente.
Uso: py scripts/graph_gen/trim_phase4.py > outputs/pilot/fase4.md
"""
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from pilot_analysis import load_grid

CON, SIN = Path("outputs/pilot"), Path("outputs/pilot_sin_recorte")
BASE_CON, BASE_SIN = Path("outputs/baseline"), SIN / "baseline"
X = CON / "recorte_extra"
COL = {"ecm1_excl": 3, "ecm2": 5, "contact": 10, "dmin": 11, "tdmin": 12, "sw1": 15, "sw2": 16}
LABEL = {"ecm1_excl": "ECM 1 excl.", "ecm2": "ECM 2"}
VARIANTS = [("D45", "D(45°), persistencia 5 (vigente)"), ("A45", "A(45°) = persistencia 1"), ("D30", "D(30°)"), ("D60", "D(60°)"),
            ("p3", "D(45°), persistencia 3"), ("p7", "D(45°), persistencia 7"), ("own", "opción 2: target al final del tramo propio")]


def c(v, d=4):
    return f"{v:.{d}f}".replace(".", ",")


def pct(new, old):
    return f"{100 * (new / old - 1):+.1f}%".replace(".", ",")


def best_pairs(folder):
    out = {}
    for line in (folder / "mejores.txt").read_text(encoding="utf-8").splitlines():
        layer, m, p1, p2 = line.split()
        if m in LABEL:
            out[(layer, m)] = (p1, p2)
    return out


def events_e(folder):
    ev = {}
    for line in (folder / "ecm.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("E "):
            p = line.split()
            ev[int(p[1])] = {"ecm1_excl": float(p[2]), "ecm2": float(p[4]), "dmin": float(p[5]), "tdmin": float(p[6]),
                             "contact": p[7] == "true", "dmin_exp": float(p[8]), "tdmin_exp": float(p[9])}
    t_end = {}
    for line in (folder / "ecm.txt").read_text(encoding="utf-8").splitlines():
        p = line.split()
        if len(p) == 12 and not line.startswith("#"):
            t_end[int(p[0])] = float(p[8])
    return ev, t_end


def grid_rows(path):
    rows = load_grid(path)
    return rows[np.argsort(rows[:, 2])]


def pair_rows(folder, layer, pair):
    rows = load_grid(folder / f"grid_{layer}.txt")
    sel = rows[(rows[:, 0] == float(pair[0])) & (rows[:, 1] == float(pair[1]))]
    return sel[np.argsort(sel[:, 2])]


def trim_sensitivity():
    print("## Sensibilidad del criterio de recorte (mejores pares de la grilla con D(45°), sin regrillar)")
    print("Base de cada cambio: el mismo par con el recorte vigente D(45°), persistencia 5. Δt = Δt_exp/64.")
    pairs = best_pairs(CON)
    ref = {}
    print("| variante | duración de la ventana (mediana, s) | línea base ECM 1 / ECM 2 | " + " | ".join(
        f"{l}({p[0]}; {p[1]}) {LABEL[m]}".replace(".", ",") for (l, m), p in sorted(pairs.items())) + " | eventos con contacto (A / B / F, pares de ECM 1) |")
    print("|---|---|---|" + "---|" * len(pairs) + "---|")
    for name, label in VARIANTS:
        folder = X / "variantes" / name
        if not (folder / "base" / "ecm.txt").exists():
            continue
        ev, t_end = events_e(folder / "base")
        cells = [label, c(float(np.median(list(t_end.values()))), 2),
                 f"{c(np.mean([e['ecm1_excl'] for e in ev.values()]))} / {c(np.mean([e['ecm2'] for e in ev.values()]))}"]
        contacts = []
        for (l, m), p in sorted(pairs.items()):
            rows = grid_rows(folder / f"{l.lower()}_{p[0]}_{p[1]}.txt")
            e = rows[:, COL[m]].mean()
            if name == "D45":
                ref[(l, m)] = e
            cells.append(f"{c(e)} ({pct(e, ref[(l, m)])})")
            if m == "ecm1_excl":
                contacts.append(str(int(rows[:, COL["contact"]].sum())))
        cells.append(" / ".join(contacts))
        print("| " + " | ".join(cells) + " |")


def rho_sweep():
    print("\n## ρ de 0,7 a 1,1 cada 0,1 (par fijo en su óptimo de ρ = 0,9; sin recalibrar)")
    print("ECM 1 excl. y ECM 2 poblacionales; contactos = eventos con solape; conmutaciones = por peatón (media / máximo de 38).")
    for tag, folder in (("con recorte", CON), ("sin recorte", SIN)):
        print(f"\n### {tag}")
        print("| capa y par | ρ | ECM 1 excl. | ECM 2 | contactos | conmutaciones media / máx. |")
        print("|---|---|---|---|---|---|")
        seen = set()
        for (l, m), p in sorted(best_pairs(folder).items()):
            if (l, p) in seen:
                continue
            seen.add((l, p))
            for rho in ("0.7", "0.8", "0.9", "1.0", "1.1"):
                f = X / "rho" / f"{'con' if folder == CON else 'sin'}_{l.lower()}_{p[0]}_{p[1]}_rho{rho}.txt"
                rows = grid_rows(f)
                sw = np.concatenate([rows[:, COL["sw1"]], rows[:, COL["sw2"]]])
                print(f"| {l}({p[0]}; {p[1]}) | {rho} | {c(rows[:, 3].mean())} | {c(rows[:, 5].mean())} | {int(rows[:, 10].sum())} | {c(sw.mean(), 1)} / {int(sw.max())} |".replace(".", ",").replace("(,", "(."))


def min_distance_and_lag():
    print("\n## Fase 4.1 y 4.2: distancia mínima y su instante, simulado contra real (mejores pares de ECM 1 excl.)")
    print("d_min entre centros (m); Δt_min = t(mín. simulado) − t(mín. real), en s, con t = 0 al inicio de la ventana de cada versión.")
    for tag, folder, base in (("con recorte", CON, BASE_CON), ("sin recorte", SIN, BASE_SIN)):
        ev, _ = events_e(base)
        pairs = best_pairs(folder)
        sims = {l: pair_rows(folder, l, pairs[(l, "ecm1_excl")]) for l in "ABF"}
        print(f"\n### {tag}: A{tuple(pairs[('A', 'ecm1_excl')])}, B{tuple(pairs[('B', 'ecm1_excl')])}, F{tuple(pairs[('F', 'ecm1_excl')])}".replace("'", ""))
        print("| evento | d_min real | d_min A / B / F | contacto A / B / F | Δt_min A / B / F |")
        print("|---|---|---|---|---|")
        for k in range(19):
            n = k + 1
            d = [sims[l][k, COL["dmin"]] for l in "ABF"]
            lag = [sims[l][k, COL["tdmin"]] - ev[n]["tdmin_exp"] for l in "ABF"]
            ct = ["sí" if sims[l][k, COL["contact"]] else "–" for l in "ABF"]
            print(f"| {n} | {c(ev[n]['dmin_exp'], 2)} | {' / '.join(c(v, 2) for v in d)} | {' / '.join(ct)} | {' / '.join(c(v, 2) for v in lag)} |")
        real = np.array([ev[n]["dmin_exp"] for n in range(1, 20)])
        print()
        for l in "ABF":
            d = sims[l][:, COL["dmin"]]
            lag = sims[l][:, COL["tdmin"]] - np.array([ev[n]["tdmin_exp"] for n in range(1, 20)])
            print(f"- {l}: d_min simulada − real: mediana {c(float(np.median(d - real)), 2)} m (media {c(float((d - real).mean()), 2)}); "
                  f"eventos que pasan más cerca que los reales {int((d < real).sum())}/19; con contacto {int(sims[l][:, COL['contact']].sum())}/19. "
                  f"Δt_min: mediana {c(float(np.median(lag)), 2)} s, media {c(float(lag.mean()), 2)} s, |Δt_min| medio {c(float(np.abs(lag).mean()), 2)} s; "
                  f"simulado después del real en {int((lag > 0).sum())}/19.")


def b_over_dodge():
    print("\n## Fase 4.3: sobre-esquive de B según ρ (con recorte; par fijo, mejor de ECM 1 excl.)")
    ev, _ = events_e(BASE_CON)
    real = np.array([ev[n]["dmin_exp"] for n in range(1, 20)])
    for tag, folder in (("con", CON), ("sin", SIN)):
        p = best_pairs(folder)[("B", "ecm1_excl")]
        evs, _ = events_e(BASE_CON if tag == "con" else BASE_SIN)
        real = np.array([evs[n]["dmin_exp"] for n in range(1, 20)])
        print(f"\n### {'con' if tag == 'con' else 'sin'} recorte, B({p[0]}; {p[1]})".replace(".", ","))
        print("| ρ | d_min simulada por evento (1 a 19) | mediana | máximo | mediana de (sim − real) | eventos a más de 0,9 m | ECM 1 excl. |")
        print("|---|---|---|---|---|---|---|")
        for rho in ("0.7", "0.8", "0.9"):
            rows = grid_rows(X / "rho" / f"{tag}_b_{p[0]}_{p[1]}_rho{rho}.txt")
            d = rows[:, COL["dmin"]]
            print(f"| {rho.replace('.', ',')} | {' '.join(c(v, 2) for v in d)} | {c(float(np.median(d)), 2)} | {c(float(d.max()), 2)} | "
                  f"{c(float(np.median(d - real)), 2)} | {int((d > 0.9).sum())} | {c(rows[:, 3].mean())} |")
        print(f"| real | {' '.join(c(v, 2) for v in real)} | {c(float(np.median(real)), 2)} | {c(float(real.max()), 2)} | – | {int((real > 0.9).sum())} | – |")


def load_tracks():
    tracks = defaultdict(dict)
    with open("outputs/recorte/trayectorias_recortadas.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            tracks[int(r["evento"])].setdefault(int(r["peaton"]) - 1, []).append((int(r["frame"]), float(r["x"]), float(r["y"]), r["en_recorte"] == "1"))
    meta = defaultdict(dict)
    with open("outputs/recorte/recorte_eventos.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            meta[int(r["evento"])][int(r["peaton"]) - 1] = r
    return {n: [np.array(tracks[n][i]) for i in (0, 1)] for n in tracks}, meta


def turning_profile():
    print("\n## Fase 4.4: perfil de giro real (datos recortados, 38 peatones)")
    print("Desvío lateral = distancia a la recta entre la posición del peatón al inicio y al final de la ventana recortada. Rumbo = ángulo con el eje x "
          "en el sentido de avance (diferencia centrada de ±2 frames), buscado solo con distancia al otro ≤ 5 m. t relativo al mínimo de distancia real (negativo = antes).")
    tracks, meta = load_tracks()
    rows = []
    for n, (a, b) in tracks.items():
        m = meta[n][0]
        dt, fmin = float(m["dt_exp"]), int(m["frame_min"])
        s, e = int(m["frame_ini_rec"]), int(m["frame_fin_rec"])
        other = {0: b, 1: a}
        for i, t in enumerate((a, b)):
            w = t[(t[:, 0] >= s) & (t[:, 0] <= e)]
            f, x, y = w[:, 0], w[:, 1], w[:, 2]
            p0, p1 = np.array([x[0], y[0]]), np.array([x[-1], y[-1]])
            u = (p1 - p0) / np.linalg.norm(p1 - p0)
            dev = np.abs((x - p0[0]) * (-u[1]) + (y - p0[1]) * u[0])
            k = int(np.argmax(dev))
            half = next(j for j in range(k + 1) if dev[j] >= 0.5 * dev[k])
            onset = k
            while onset > 0 and dev[onset] > 0.2 * dev[k]:
                onset -= 1
            sense = 1 if i == 0 else -1
            h = []
            for j in range(len(f)):
                lo, hi = max(0, j - 2), min(len(f) - 1, j + 2)
                h.append(math.degrees(math.atan2(abs(y[hi] - y[lo]), sense * (x[hi] - x[lo]))))
            h = np.array(h)
            o = other[i]
            od = {int(r[0]): (r[1], r[2]) for r in o}
            # rumbo máximo solo en la zona de interacción (distancia al otro ≤ 5 m), como en la exploración
            dist = np.array([math.hypot(x[j] - od[int(f[j])][0], y[j] - od[int(f[j])][1]) if int(f[j]) in od else np.inf for j in range(len(f))])
            kh = int(np.argmax(np.where(dist <= 5.0, h, -1)))
            dist_onset = math.hypot(x[onset] - od[int(f[onset])][0], y[onset] - od[int(f[onset])][1]) if int(f[onset]) in od else float("nan")
            rows.append({"n": n, "i": i, "lat": dev[k], "t_lat": (f[k] - fmin) * dt, "t_half": (f[half] - fmin) * dt, "t_onset": (f[onset] - fmin) * dt,
                         "d_onset": dist_onset, "h_max": h[kh], "t_h": (f[kh] - fmin) * dt, "vd": float(meta[n][i]["vd_rec"])})
    arr = lambda key: np.array([r[key] for r in rows])
    q = lambda key, d=2: f"mediana {c(float(np.nanmedian(arr(key))), d)}, rango {c(float(np.nanmin(arr(key))), d)} a {c(float(np.nanmax(arr(key))), d)}"
    print(f"- Desvío lateral máximo (m): {q('lat')}.")
    print(f"- Inicio del esquive (|desvío| pasa el 20% del máximo), t − t_min (s): {q('t_onset')}; distancia al otro en ese instante (m): {q('d_onset')}.")
    print(f"- Mitad del desvío alcanzada, t − t_min (s): {q('t_half')}. Desvío máximo, t − t_min (s): {q('t_lat')}.")
    print(f"- Rumbo máximo (°): {q('h_max', 1)}; su instante, t − t_min (s): {q('t_h')}.")
    print(f"- Duración desde el inicio hasta el máximo del desvío (s): mediana {c(float(np.median(arr('t_lat') - arr('t_onset'))), 2)}.")
    vd = arr("vd")
    print(f"- v_d recortada (38 peatones): media {c(vd.mean(), 3)} m/s, DE {c(vd.std(ddof=1), 3)}, CV {c(100 * vd.std(ddof=1) / vd.mean(), 1)}%, rango {c(vd.min(), 2)} a {c(vd.max(), 2)}.")
    per_event = [np.mean([r['vd'] for r in rows if r['n'] == n]) for n in sorted(tracks)]
    print(f"- v_d media por evento (19): DE entre eventos {c(float(np.std(per_event, ddof=1)), 3)} m/s, rango {c(min(per_event), 2)} a {c(max(per_event), 2)}.")
    print("\n| evento | peatón | desvío máx. (m) | inicio (s) | distancia al inicio (m) | mitad (s) | máximo (s) | rumbo máx. (°) | t rumbo máx. (s) | v_d (m/s) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['n']} | {'izq.' if r['i'] == 0 else 'der.'} | {c(r['lat'], 2)} | {c(r['t_onset'], 2)} | {c(r['d_onset'], 2)} | {c(r['t_half'], 2)} | "
              f"{c(r['t_lat'], 2)} | {c(r['h_max'], 1)} | {c(r['t_h'], 2)} | {c(r['vd'], 2)} |")
    return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("# Fase 3 (sensibilidades) y Fase 4 (preguntas abiertas) del recorte al tramo frontal")
    print("Δt = Δt_exp/64, salida cada Δt_exp/4. ECM 1 = variante excluyente. Recorte vigente: D(45°), persistencia 5, opción 1.\n")
    trim_sensitivity()
    rho_sweep()
    min_distance_and_lag()
    b_over_dodge()
    turning_profile()


if __name__ == "__main__":
    main()
