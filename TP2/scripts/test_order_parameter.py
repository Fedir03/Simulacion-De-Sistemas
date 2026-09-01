#!/usr/bin/env python3

import math
import tempfile
import unittest
from pathlib import Path

from order_parameter import (
    load_named_series,
    resolve_transient,
    load_series,
    read_series_csv,
    mean_and_stdev,
    read_va_csv,
    tail_stats,
    tail_values,
    va,
    va_series,
    write_va_csv,
)
from simulation_io import (
    Frame,
    ParticleState,
    SimulationFormatError,
    parse_simulation,
    stream_simulation,
)


HEADER = (
    "model=standard N=4 L=10.0 rc=1.0 dt=0.5 v0=0.03 eta=0.5 "
    "periodic=true seedIC=1 seedLoop=2 theta0=random\n"
)


def frame_of(*thetas: float) -> Frame:
    return Frame(
        step=0,
        particles=tuple(
            ParticleState(particle_id=i + 1, x=0.0, y=0.0, theta=theta)
            for i, theta in enumerate(thetas)
        ),
    )


class OrderParameterTest(unittest.TestCase):

    def test_all_aligned_gives_one(self):
        self.assertAlmostEqual(1.0, va(frame_of(0.7, 0.7, 0.7, 0.7)))

    def test_opposite_pairs_cancel_to_zero(self):
        self.assertAlmostEqual(0.0, va(frame_of(0.0, math.pi, math.pi / 2, 3 * math.pi / 2)))

    def test_is_invariant_under_a_global_rotation(self):
        thetas = (0.1, 1.3, 2.9, 4.4)
        rotated = tuple(theta + 1.234 for theta in thetas)
        self.assertAlmostEqual(va(frame_of(*thetas)), va(frame_of(*rotated)))

    def test_half_aligned_half_opposite_matches_closed_form(self):
        # tres particulas a 0 y una a pi: |3 - 1| / 4
        self.assertAlmostEqual(0.5, va(frame_of(0.0, 0.0, 0.0, math.pi)))

    def test_angles_are_taken_modulo_two_pi(self):
        self.assertAlmostEqual(1.0, va(frame_of(0.0, 2 * math.pi, 4 * math.pi, -2 * math.pi)))


class SeriesFromFileTest(unittest.TestCase):

    def write_run(self, temp_dir: str, contents: str) -> Path:
        path = Path(temp_dir) / "corrida.txt"
        path.write_text(contents, encoding="utf-8")
        return path

    def test_series_follows_the_time_blocks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_run(
                temp_dir,
                HEADER
                + "t=0\n1 0 0 0.0\n2 0 0 0.0\n3 0 0 0.0\n4 0 0 0.0\n"
                + f"t=1\n1 0 0 0.0\n2 0 0 0.0\n3 0 0 0.0\n4 0 0 {math.pi}\n",
            )

            header, steps, values = va_series(path)

            self.assertEqual("standard", header.model)
            self.assertEqual([0, 1], steps)
            self.assertAlmostEqual(1.0, values[0])
            self.assertAlmostEqual(0.5, values[1])

    def test_streaming_and_eager_parsers_agree(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            blocks = "".join(
                f"t={step}\n1 1 1 {step * 0.1}\n2 2 2 {step * 0.2}\n"
                f"3 3 3 {step * 0.3}\n4 4 4 {step * 0.4}\n"
                for step in range(5)
            )
            path = self.write_run(temp_dir, HEADER + blocks)

            eager = parse_simulation(path)
            _, streamed = stream_simulation(path)

            self.assertEqual(list(eager.frames), list(streamed))
            self.assertEqual(
                [va(frame) for frame in eager.frames],
                va_series(path)[2],
            )

    def test_streaming_reports_incomplete_block(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_run(temp_dir, HEADER + "t=0\n1 0 0 0.0\n")

            with self.assertRaisesRegex(SimulationFormatError, "se esperaban 4 particulas"):
                va_series(path)

    def test_defaults_theta0_to_random_for_older_runs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_run(
                temp_dir,
                HEADER.replace(" theta0=random", "")
                + "t=0\n1 0 0 0.0\n2 0 0 0.0\n3 0 0 0.0\n4 0 0 0.0\n",
            )

            header, _, _ = va_series(path)

            self.assertTrue(header.theta0_is_random)

    def test_aligned_header_produces_a_readable_label(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_run(
                temp_dir,
                HEADER.replace("theta0=random", "theta0=0.0")
                + "t=0\n1 0 0 0.0\n2 0 0 0.0\n3 0 0 0.0\n4 0 0 0.0\n",
            )

            header, _, _ = va_series(path)

            self.assertFalse(header.theta0_is_random)
            self.assertIn("alineado", header.theta0_label)


class CsvRoundTripTest(unittest.TestCase):

    def test_csv_round_trip_preserves_header_and_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run = Path(temp_dir) / "corrida.txt"
            run.write_text(
                HEADER
                + "t=0\n1 0 0 0.0\n2 0 0 0.3\n3 0 0 0.6\n4 0 0 0.9\n"
                + "t=1\n1 0 0 0.1\n2 0 0 0.4\n3 0 0 0.7\n4 0 0 1.0\n",
                encoding="utf-8",
            )
            header, steps, values = va_series(run)
            csv_path = Path(temp_dir) / "va.csv"

            write_va_csv(csv_path, header, steps, values)
            reread_header, reread_steps, reread_values = read_va_csv(csv_path)

            self.assertEqual(header, reread_header)
            self.assertEqual(steps, reread_steps)
            self.assertEqual(values, reread_values)

    def test_load_series_dispatches_on_extension(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run = Path(temp_dir) / "corrida.txt"
            run.write_text(
                HEADER + "t=0\n1 0 0 0.0\n2 0 0 0.0\n3 0 0 0.0\n4 0 0 0.0\n",
                encoding="utf-8",
            )
            csv_path = Path(temp_dir) / "va.csv"
            write_va_csv(csv_path, *va_series(run))

            self.assertEqual(load_series(run)[2], load_series(csv_path)[2])

    def test_rejects_csv_without_header_line(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "va.csv"
            csv_path.write_text("t,va\n0,1.0\n", encoding="utf-8")

            with self.assertRaisesRegex(SimulationFormatError, "cabecera"):
                read_va_csv(csv_path)


class GenericSeriesTest(unittest.TestCase):
    """El mismo lector sirve para v_a y para el S que escribe el comando `clusters`."""

    def write(self, temp_dir: str, contents: str) -> Path:
        path = Path(temp_dir) / "serie.csv"
        path.write_text(contents, encoding="utf-8")
        return path

    def test_reads_a_clusters_csv_and_reports_its_column(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write(temp_dir, "# " + HEADER.strip() + "\nt,S\n0,0.25\n5,0.5\n")

            header, steps, values, column = read_series_csv(path)

            self.assertEqual("S", column)
            self.assertEqual([0, 5], steps)
            self.assertEqual([0.25, 0.5], values)
            self.assertEqual("standard", header.model)

    def test_va_csv_still_reports_its_own_column(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write(temp_dir, "# " + HEADER.strip() + "\nt,va\n0,1.0\n")

            self.assertEqual("va", read_series_csv(path)[3])

    def test_load_named_series_defaults_to_va_for_a_trajectory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "corrida.txt"
            path.write_text(
                HEADER + "t=0\n1 0 0 0.0\n2 0 0 0.0\n3 0 0 0.0\n4 0 0 0.0\n",
                encoding="utf-8")

            self.assertEqual("va", load_named_series(path)[3])

    def test_rejects_a_row_with_the_wrong_number_of_columns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write(temp_dir, "# " + HEADER.strip() + "\nt,S\n0,0.25,extra\n")

            with self.assertRaisesRegex(SimulationFormatError, "dos columnas"):
                read_series_csv(path)


class StatisticsTest(unittest.TestCase):

    def test_tail_stats_ignores_the_transient(self):
        steps = [0, 1, 2, 3]
        values = [0.9, 0.1, 0.2, 0.3]

        mean, stdev = tail_stats(steps, values, transient=1)

        self.assertAlmostEqual(0.2, mean)
        self.assertAlmostEqual(0.1, stdev)

    def test_tail_stats_with_a_single_point_has_no_spread(self):
        self.assertEqual((0.4, 0.0), tail_stats([0, 1], [0.9, 0.4], transient=1))

    def test_tail_stats_rejects_a_transient_past_the_run(self):
        with self.assertRaisesRegex(ValueError, "t >= 10"):
            tail_stats([0, 1], [0.5, 0.5], transient=10)

    def test_mean_and_stdev_over_runs(self):
        mean, stdev = mean_and_stdev([0.4, 0.5, 0.6])

        self.assertAlmostEqual(0.5, mean)
        self.assertAlmostEqual(0.1, stdev)

    def test_percentage_transient_scales_with_the_run_length(self):
        self.assertEqual(4000, resolve_transient("40%", 10000))
        self.assertEqual(1200, resolve_transient("40%", 3000))

    def test_absolute_transient_ignores_the_run_length(self):
        self.assertEqual(500, resolve_transient(500, 3000))
        self.assertEqual(500, resolve_transient("500", 10000))

    def test_rejects_an_out_of_range_percentage(self):
        with self.assertRaisesRegex(ValueError, "porcentaje"):
            resolve_transient("120%", 3000)

    def test_mean_and_stdev_with_one_run(self):
        self.assertEqual((0.7, 0.0), mean_and_stdev([0.7]))

    def test_tail_values_returns_the_raw_points_past_the_transient(self):
        steps = [0, 1, 2, 3]
        values = [0.9, 0.1, 0.2, 0.3]

        self.assertEqual([0.1, 0.2, 0.3], tail_values(steps, values, transient=1))

    def test_tail_values_rejects_a_transient_past_the_run(self):
        with self.assertRaisesRegex(ValueError, "t >= 10"):
            tail_values([0, 1], [0.5, 0.5], transient=10)

    def test_pooling_raw_points_gives_a_different_stdev_than_averaging_per_run(self):
        # Dos corridas con el mismo promedio pero mucha dispersion interna: el desvio
        # "entre promedios de corrida" da 0 (ambas corridas promedian 0.5), pero la
        # bolsa de puntos crudos de las dos corridas juntas capta la dispersion real.
        run_a = [0.0, 1.0]
        run_b = [1.0, 0.0]
        mean_a, _ = mean_and_stdev(run_a)
        mean_b, _ = mean_and_stdev(run_b)
        _, between_run_means_stdev = mean_and_stdev([mean_a, mean_b])
        pooled_mean, pooled_stdev = mean_and_stdev(run_a + run_b)

        self.assertAlmostEqual(0.0, between_run_means_stdev)
        self.assertGreater(pooled_stdev, between_run_means_stdev)
        self.assertAlmostEqual(0.5, pooled_mean)


if __name__ == "__main__":
    unittest.main()
