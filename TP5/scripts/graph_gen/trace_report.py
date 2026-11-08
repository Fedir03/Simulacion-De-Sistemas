#!/usr/bin/env python3
"""Tareas 3 y 5: contactos del evento 2 y sus vecinos, y causa de las conmutaciones de A y B.

Usa diagnostics/RunTrace, que no va al ZIP. Si un número de acá va a la presentación, hay que avisar para incluirlo.
Uso, desde TP5/ y con target/tp5.jar compilado: python scripts/graph_gen/trace_report.py [carpeta del piloto]
"""
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

JAR = "target/tp5.jar"
MAIN = "ar.edu.itba.sds.tp5.diagnostics.RunTrace"
RHO = 0.9
NEAR_RHO = 0.05
FLIPS = []      # cambios de lado de la última traza


def trace(layer, p1, p2, event, v0_frames=5):
    text = subprocess.run(["java", "-cp", JAR, MAIN, "--event", str(event), "--layer", layer, "--p1", str(p1), "--p2", str(p2),
                           "--v0-frames", str(v0_frames)], capture_output=True, text=True, check=True).stdout
    summary, contacts, switches = "", [], []
    FLIPS.clear()
    for line in text.splitlines():
        p = line.split()
        if p[0] == "R":
            summary = line[2:]
        elif p[0] == "L":
            FLIPS.append(dict(t=float(p[1]), agent=int(p[2]), side=float(p[3]), d=float(p[4])))
        elif p[0] == "C":
            contacts.append((float(p[1]), float(p[2]), float(p[3])))
        elif p[0] == "S":
            switches.append(dict(t=float(p[1]), agent=int(p[2]), on=p[3] == "on", tstar=float(p[4]), dmin=float(p[5]),
                                 side=float(p[6]), d=float(p[7]), contact=p[8] == "true", cause=p[9]))
    return summary, contacts, switches


def side_name(side):
    if abs(side) <= 0.05:
        return "desempate: a su derecha"
    # s_c > 0: el otro queda a la derecha de i en el máximo acercamiento, y esquiva hacia el lado opuesto
    return "a su izquierda" if side > 0 else "a su derecha"


def contacts_report():
    print("===== Tarea 3: A(t_a=4; l=0,5), contactos por evento y frames de v0 =====")
    for event in (2, 9, 17):
        for frames in (3, 5, 7):
            summary, contacts, _ = trace("a", 4, 0.5, event, frames)
            detail = "; ".join(f"t={a:.3f} a {b:.3f} s, solapamiento max {o * 100:.2f} cm" for a, b, o in contacts) or "ninguno"
            print(f"evento {event}, v0 {frames} frames | {summary} | contactos: {len(contacts)} ({detail})")
    print("\n----- Evento 2: primera activacion de cada peaton y lado elegido, con s_c = e_t_perp . (r + w t*) -----")
    for frames in (3, 5, 7):
        _, _, switches = trace("a", 4, 0.5, 2, frames)
        for agent in (1, 2):
            first = next((s for s in switches if s["agent"] == agent and s["on"]), None)
            if first:
                print(f"v0 {frames} frames, peaton {agent}: t={first['t']:.3f} s_c={first['side']:+.4f} d_min_pred={first['dmin']:.3f} -> esquiva {side_name(first['side'])}")
        print(f"   conmutaciones totales: {len(switches)} | cambios de lado con la capa prendida: {len(FLIPS)}")
        for f in FLIPS:
            print(f"   peaton {f['agent']} cambia de lado en t={f['t']:.3f}, s_c={f['side']:+.4f}, distancia {f['d']:.2f} m")


def causes_row(switches):
    c = Counter()
    for s in switches:
        for part in s["cause"].split("+"):
            c[part] += 1
    return c


def oscillation_report(pilot):
    print("\n===== Tarea 5: filas con mas de 6 conmutaciones en un agente (grillas oficiales A y B) =====")
    print("capa par evento conm1/conm2 inerte contacto d_min_real | % por d_min cruza rho, t* cruza t_a, t* cruza 0, otra | mediana |d_min-rho| al conmutar | % conmutaciones con |d_min-rho|<0,05 | % en contacto")
    total = {"inerte": Counter(), "activa": Counter()}
    for name, layer in (("A", "a"), ("B", "b")):
        rows = [l.split() for l in open(pilot / f"grid_{name}.txt", encoding="utf-8") if not l.startswith("#")]
        hi = [r for r in rows if max(int(r[15]), int(r[16])) > 6]
        for r in sorted(hi, key=lambda x: -max(int(x[15]), int(x[16]))):
            p1, p2, event = float(r[0]), float(r[1]), int(r[2])
            _, _, switches = trace(layer, p1, p2, event)
            c = causes_row(switches)
            n = max(len(switches), 1)
            gaps = [abs(s["dmin"] - RHO) for s in switches if not np.isnan(s["dmin"])]
            near = sum(g < NEAR_RHO for g in gaps) / n * 100
            touching = sum(s["contact"] for s in switches) / n * 100
            inert = p2 == 0
            total["inerte" if inert else "activa"].update(c)
            other = sum(v for k, v in c.items() if k not in ("d_min_cruza_rho", "t*_cruza_t_a", "t*_cruza_0"))
            print(f"{name} ({p1:g}; {p2:g}) ev{event} {r[15]}/{r[16]} {'si' if inert else 'no'} {'si' if r[10] == 'true' else 'no'} {float(r[11]):.3f} | "
                  f"{c['d_min_cruza_rho'] / n * 100:.0f}% {c['t*_cruza_t_a'] / n * 100:.0f}% {c['t*_cruza_0'] / n * 100:.0f}% {other / n * 100:.0f}% | {np.median(gaps):.3f} | {near:.0f}% | {touching:.0f}%")
    print("\nsuma de causas:")
    for key, c in total.items():
        print(f"  capa {key}: {dict(c)}")
    print("\nResumen de conmutaciones en toda la grilla, separando pares inertes (l = 0 o k = 0):")
    for name in "AB":
        rows = np.array([[float(x) for x in l.split()[:2]] + [int(l.split()[15]), int(l.split()[16])]
                         for l in open(pilot / f"grid_{name}.txt", encoding="utf-8") if not l.startswith("#")])
        for label, mask in (("inertes", rows[:, 1] == 0), ("activos", rows[:, 1] > 0)):
            sw = rows[mask, 2:].ravel()
            print(f"  {name} {label}: media {sw.mean():.2f}, p99 {np.percentile(sw, 99):.0f}, max {sw.max():.0f}, agentes con mas de 6: {int((sw > 6).sum())}/{sw.size}")
    print("\nControl, mejores pares (todos los eventos): conmutaciones y causa")
    for line in (pilot / "mejores.txt").read_text(encoding="utf-8").splitlines():
        name, metric, p1, p2 = line.split()
        if name == "F":
            continue
        c, top, flips = Counter(), 0, 0
        for event in range(1, 20):
            _, _, switches = trace(name.lower(), p1, p2, event)
            c.update(causes_row(switches))
            flips += len(FLIPS)
            top = max(top, max(Counter(s["agent"] for s in switches).values(), default=0))
        print(f"  {name} ({p1}; {p2}) [{metric}]: {dict(c)} | max por agente {top} | cambios de lado {flips}")


def main():
    pilot = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/pilot")
    contacts_report()
    oscillation_report(pilot)


if __name__ == "__main__":
    main()
