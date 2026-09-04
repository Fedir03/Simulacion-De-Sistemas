#!/usr/bin/env python3
"""Lectura del archivo de salida del motor TP2 (formato documentado en TP2/README.md).

Modulo compartido por el resto de los scripts de Paquete C: animate.py lo usa para armar
las animaciones y order_parameter.py para calcular el parametro de orden.

Dos formas de leer una corrida:

- parse_simulation(path)  -> carga todo en memoria (SimulationData). Comodo, pero una
  corrida de N=800 x 10000 pasos son 8M de particulas: usarlo solo si hace falta acceso
  aleatorio a los cuadros, como en la animacion.
- stream_simulation(path) -> (cabecera, iterador de cuadros). Lee de a un cuadro por vez,
  con las mismas validaciones. Es lo que conviene cuando alcanza con un agregado por paso
  de tiempo, como v_a(t).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, TextIO


TWO_PI = 2.0 * math.pi
TIME_MARKER = re.compile(r"t=(\d+)")
REQUIRED_HEADER_FIELDS = {
    "model", "N", "L", "rc", "dt", "v0", "eta", "periodic", "seedIC", "seedLoop"
}
RANDOM_THETA0 = "random"


class SimulationFormatError(ValueError):
    """El archivo no respeta el formato de salida del motor."""


def density_label_for(density: float, n: int | None = None,
                      l: float | None = None) -> str:
    """La densidad como texto, en forma fraccionaria de pi cuando corresponde.

    Las densidades del anuncio de la catedra son 1/pi, 1/(2pi) y 1/(3pi); escribirlas
    como 0.3183 pierde de vista que estan elegidas para dar 1, 1/2 y 1/3 vecinos
    promedio. Se detecta hasta 1/(6pi), que cubre todo lo que usamos.

    Con L fijo el N tiene que ser entero, asi que la densidad efectiva es el redondeo de
    la fraccion: con L = 10 las tres dan N = 11, 16 y 32, o sea 0.11, 0.16 y 0.32. Con n
    y l se reconoce ese caso (N es el entero mas cercano a la densidad objetivo por L^2)
    y la etiqueta sigue siendo la fraccion, que es lo que identifica a la corrida.

    La tolerancia no puede ser ajustadisima: con L=10 fijo, N se redondea al entero
    mas cercano (11, 16, 32 para 1/(3pi), 1/(2pi), 1/pi), lo que separa la densidad
    resultante de la fraccion exacta hasta ~0.004 (peor caso N=11). 1e-2 cubre eso
    con margen y sigue muy por debajo de la distancia a la fraccion vecina mas
    cercana (>0.05 en todos los casos que usamos), asi que no hay riesgo de
    confundir una densidad con la fraccion equivocada.
    """
    for k in range(1, 7):
        objetivo = 1.0 / (k * math.pi)
        redondeada = n is not None and l is not None and round(objetivo * l * l) == n
        if abs(density - objetivo) < 1e-6 or redondeada:
        if abs(density - 1.0 / (k * math.pi)) < 1e-2:
            return "1/π" if k == 1 else f"1/({k}π)"
    return f"{density:g}"


@dataclass(frozen=True)
class SimulationHeader:
    model: str
    n: int
    l: float
    rc: float
    dt: float
    v0: float
    eta: float
    periodic: bool
    seed_ic: int
    seed_loop: int
    theta0: str = RANDOM_THETA0

    @property
    def density(self) -> float:
        return self.n / (self.l * self.l)

    @property
    def density_label(self) -> str:
        return density_label_for(self.density, self.n, self.l)

    @property
    def theta0_is_random(self) -> bool:
        return self.theta0.lower() == RANDOM_THETA0

    @property
    def theta0_label(self) -> str:
        """Etiqueta lista para la leyenda de un grafico."""
        if self.theta0_is_random:
            return "θ₀ aleatorio"
        return f"θ₀ = {float(self.theta0):g} (alineado)"


@dataclass(frozen=True)
class ParticleState:
    particle_id: int
    x: float
    y: float
    theta: float


@dataclass(frozen=True)
class Frame:
    step: int
    particles: tuple[ParticleState, ...]


@dataclass(frozen=True)
class SimulationData:
    header: SimulationHeader
    frames: tuple[Frame, ...]


def _finite_float(field: str, value: str, line_number: int = 1) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise SimulationFormatError(
            f"linea {line_number}: {field} debe ser numerico, se recibio {value!r}"
        ) from exc
    if not math.isfinite(parsed):
        raise SimulationFormatError(f"linea {line_number}: {field} debe ser finito")
    return parsed


def _integer(field: str, value: str, line_number: int = 1) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise SimulationFormatError(
            f"linea {line_number}: {field} debe ser entero, se recibio {value!r}"
        ) from exc


def parse_header(line: str) -> SimulationHeader:
    fields: dict[str, str] = {}
    for token in line.lstrip("\ufeff").split():
        if "=" not in token:
            raise SimulationFormatError(f"linea 1: campo de cabecera invalido: {token!r}")
        key, value = token.split("=", 1)
        if not key or not value:
            raise SimulationFormatError(f"linea 1: campo de cabecera invalido: {token!r}")
        if key in fields:
            raise SimulationFormatError(f"linea 1: campo de cabecera duplicado: {key}")
        fields[key] = value

    missing = sorted(REQUIRED_HEADER_FIELDS - fields.keys())
    if missing:
        raise SimulationFormatError(
            "linea 1: faltan campos obligatorios: " + ", ".join(missing)
        )

    n = _integer("N", fields["N"])
    l = _finite_float("L", fields["L"])
    rc = _finite_float("rc", fields["rc"])
    dt = _finite_float("dt", fields["dt"])
    v0 = _finite_float("v0", fields["v0"])
    eta = _finite_float("eta", fields["eta"])
    if n <= 0:
        raise SimulationFormatError("linea 1: N debe ser positivo")
    if l <= 0 or rc < 0 or dt <= 0 or v0 <= 0 or eta < 0:
        raise SimulationFormatError(
            "linea 1: se requiere L>0, rc>=0, dt>0, v0>0 y eta>=0"
        )

    periodic_text = fields["periodic"].lower()
    if periodic_text not in {"true", "false"}:
        raise SimulationFormatError("linea 1: periodic debe ser true o false")

    # theta0 es opcional: las corridas anteriores al flag --theta0 no lo traen y son
    # siempre de angulos aleatorios.
    theta0 = fields.get("theta0", RANDOM_THETA0)
    if theta0.lower() != RANDOM_THETA0:
        _finite_float("theta0", theta0)

    return SimulationHeader(
        model=fields["model"],
        n=n,
        l=l,
        rc=rc,
        dt=dt,
        v0=v0,
        eta=eta,
        periodic=periodic_text == "true",
        seed_ic=_integer("seedIC", fields["seedIC"]),
        seed_loop=_integer("seedLoop", fields["seedLoop"]),
        theta0=theta0,
    )


class _LineReader:
    """Lector con una linea de pushback, para poder mirar el marcador de tiempo siguiente."""

    def __init__(self, stream: TextIO, first_line_number: int):
        self._stream = stream
        self._number = first_line_number
        self._pending: tuple[int, str] | None = None

    def next_line(self) -> tuple[int, str] | None:
        if self._pending is not None:
            item, self._pending = self._pending, None
            return item
        raw = self._stream.readline()
        if raw == "":
            return None
        self._number += 1
        return self._number, raw.rstrip("\n").rstrip("\r")


def stream_simulation(path: str | Path) -> tuple[SimulationHeader, Iterator[Frame]]:
    """Devuelve la cabecera y un iterador perezoso de cuadros.

    El archivo queda abierto hasta que el iterador se agota (o se cierra); consumirlo
    entero, idealmente dentro de un for.
    """
    input_path = Path(path)
    stream = input_path.open("r", encoding="utf-8-sig")
    try:
        first_line = stream.readline()
        if first_line == "":
            raise SimulationFormatError(f"{input_path}: el archivo esta vacio")
        if not first_line.strip():
            raise SimulationFormatError("linea 1: se esperaba la cabecera")
        header = parse_header(first_line)
    except UnicodeDecodeError as exc:
        stream.close()
        raise SimulationFormatError(
            f"{input_path}: el archivo no es texto UTF-8 valido"
        ) from exc
    except BaseException:
        stream.close()
        raise

    return header, _iter_frames(stream, header)


def _iter_frames(stream: TextIO, header: SimulationHeader) -> Iterator[Frame]:
    reader = _LineReader(stream, first_line_number=1)
    expected_ids: tuple[int, ...] | None = None
    seen_steps: set[int] = set()
    last_step: int | None = None
    emitted = 0

    try:
        while True:
            item = reader.next_line()
            if item is None:
                break
            marker_line, text = item
            if not text.strip():
                continue

            marker = TIME_MARKER.fullmatch(text.strip())
            if marker is None:
                raise SimulationFormatError(
                    f"linea {marker_line}: se esperaba un marcador t=<entero>"
                )
            step = int(marker.group(1))
            if step in seen_steps:
                raise SimulationFormatError(f"linea {marker_line}: bloque t={step} duplicado")
            if last_step is not None and step <= last_step:
                raise SimulationFormatError(
                    f"linea {marker_line}: los tiempos deben estar en orden creciente"
                )
            seen_steps.add(step)

            particles: list[ParticleState] = []
            ids_in_frame: set[int] = set()
            for particle_number in range(header.n):
                particle_item = reader.next_line()
                if particle_item is None or TIME_MARKER.fullmatch(particle_item[1].strip()):
                    raise SimulationFormatError(
                        f"bloque t={step}: se esperaban {header.n} particulas y se encontraron "
                        f"{particle_number}"
                    )
                line_number, particle_text = particle_item
                parts = particle_text.split()
                if len(parts) != 4:
                    raise SimulationFormatError(
                        f"linea {line_number}: se esperaba 'id x y theta'"
                    )
                particle_id = _integer("id", parts[0], line_number)
                if particle_id in ids_in_frame:
                    raise SimulationFormatError(
                        f"linea {line_number}: id de particula duplicado: {particle_id}"
                    )
                ids_in_frame.add(particle_id)
                particles.append(ParticleState(
                    particle_id=particle_id,
                    x=_finite_float("x", parts[1], line_number),
                    y=_finite_float("y", parts[2], line_number),
                    theta=_finite_float("theta", parts[3], line_number),
                ))

            current_ids = tuple(p.particle_id for p in particles)
            if expected_ids is None:
                expected_ids = current_ids
            elif current_ids != expected_ids:
                raise SimulationFormatError(
                    f"bloque t={step}: los IDs o su orden no coinciden con el primer bloque"
                )

            last_step = step
            emitted += 1
            yield Frame(step=step, particles=tuple(particles))

        if emitted == 0:
            raise SimulationFormatError("el archivo no contiene bloques de tiempo")
    except UnicodeDecodeError as exc:
        raise SimulationFormatError("el archivo no es texto UTF-8 valido") from exc
    finally:
        stream.close()


def parse_simulation(path: str | Path) -> SimulationData:
    """Carga la corrida completa en memoria."""
    header, frames = stream_simulation(path)
    return SimulationData(header=header, frames=tuple(frames))
