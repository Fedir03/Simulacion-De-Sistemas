#!/usr/bin/env python3
"""Pruebas de las partes de los graficadores que no requieren Matplotlib."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import plot_va
import plot_va_vs_eta
import plot_va_vs_s
from plot_va import (
    auto_labels,
    differing_fields,
    nice_tick_steps,
    panel_key,
    report_tail,
    time_axis_label,
)
from plot_va_vs_eta import differing_field, group_key
from plot_va_vs_s import steady_values
from simulation_io import SimulationHeader


def header(**overrides) -> SimulationHeader:
    base = dict(model="standard", n=400, l=10.0, rc=1.0, dt=1.0, v0=0.03, eta=1.0,
                periodic=True, seed_ic=1, seed_loop=1, theta0="random")
    base.update(overrides)
    return SimulationHeader(**base)


class TickStepTest(unittest.TestCase):

    def test_three_thousand_steps_gives_500_and_100(self):
        self.assertEqual((500.0, 100.0), nice_tick_steps(3000))

    def test_steps_scale_with_the_span(self):
        self.assertEqual((50.0, 10.0), nice_tick_steps(200))
        self.assertEqual((1000.0, 200.0), nice_tick_steps(5000))

    def test_degenerate_span_does_not_crash(self):
        major, minor = nice_tick_steps(0)
        self.assertGreater(major, 0)
        self.assertGreater(minor, 0)


class TimeAxisLabelTest(unittest.TestCase):

    def test_states_the_time_unit_when_dt_is_shared(self):
        label = time_axis_label([header(), header(eta=2.0)])
        self.assertIn("Delta t$ = 1", label)

    def test_falls_back_when_dt_differs(self):
        label = time_axis_label([header(dt=1.0), header(dt=0.5)])
        self.assertNotIn("= 1]", label)


class PlotVaLabelTest(unittest.TestCase):

    def test_detects_the_field_that_differs(self):
        headers = [header(theta0="random"), header(theta0="0.0")]
        self.assertEqual(["theta0"], differing_fields(headers))

    def test_labels_a_single_run_with_its_parameters(self):
        import pathlib
        label, = auto_labels([header(eta=2.5)], [pathlib.Path("a.csv")])

        self.assertIn("η = 2.5", label)
        self.assertIn("aleatorio", label)

    def test_auto_labels_mention_the_differing_field(self):
        import pathlib
        headers = [header(eta=1.0), header(eta=3.0)]
        paths = [pathlib.Path("a.csv"), pathlib.Path("b.csv")]

        labels = auto_labels(headers, paths)

        self.assertIn("η = 1", labels[0])
        self.assertIn("η = 3", labels[1])


class PanelTest(unittest.TestCase):

    def test_panels_by_density_sort_by_density(self):
        keys = [panel_key(header(n=800), "density"), panel_key(header(n=200), "density")]
        self.assertEqual([2.0, 8.0], sorted(order for order, _ in keys))

    def test_panel_title_states_n_and_l(self):
        _, title = panel_key(header(n=200, l=10.0), "density")
        self.assertIn("ρ = 2", title)
        self.assertIn("N = 200", title)


class GroupingTest(unittest.TestCase):

    def test_groups_by_density_and_sorts_by_it(self):
        order, label = group_key(header(n=800, l=10.0), "density")
        self.assertAlmostEqual(8.0, order)
        self.assertIn("ρ = 8", label)
        self.assertIn("N = 800", label)

    def test_group_by_n_reports_the_box_side(self):
        _, label = group_key(header(n=4000, l=31.6227766), "n")
        self.assertIn("N = 4000", label)
        self.assertIn("L = 31.6228", label)

    def test_model_is_the_first_field_considered(self):
        headers = [header(model="standard", n=200), header(model="voter", n=400)]
        self.assertEqual("model", differing_field(headers))

    def test_combined_group_by_joins_order_and_label(self):
        order, label = group_key(header(model="voter", n=800, l=10.0), "density,model")
        self.assertEqual((8.0, 0.0), order)
        self.assertIn("ρ = 8", label)
        self.assertIn("modelo voter", label)

    def test_combined_group_by_gives_a_distinct_key_per_model_at_the_same_density(self):
        standard = group_key(header(model="standard", n=200), "density,model")
        voter = group_key(header(model="voter", n=200), "density,model")

        self.assertNotEqual(standard, voter)
        self.assertEqual(standard[0], voter[0])

    def test_density_wins_when_the_model_is_shared(self):
        headers = [header(n=200), header(n=800)]
        self.assertEqual("density", differing_field(headers))

    def test_same_density_different_size_groups_by_n(self):
        headers = [header(n=200, l=10.0), header(n=800, l=20.0)]  # ambas rho = 2
        self.assertEqual("n", differing_field(headers))


SERIES_HEADER = (
    "model=standard N=4 L=10.0 rc=1.0 dt=0.5 v0=0.03 eta=0.5 "
    "periodic=true seedIC=1 seedLoop=2 theta0=random"
)


def write_series_csv(directory: Path, name: str, steps, values, column: str = "va") -> Path:
    path = directory / name
    lines = [f"# {SERIES_HEADER}", f"t,{column}"]
    lines += [f"{step},{value}" for step, value in zip(steps, values)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


class TransientArgparseTest(unittest.TestCase):
    """Los 3 graficadores aceptan --transient tanto en pasos absolutos como en porcentaje."""

    def test_plot_va_accepts_percentage(self):
        args = plot_va.build_argument_parser().parse_args(["dummy.csv", "--transient=40%"])
        self.assertEqual("40%", args.transient)

    def test_plot_va_still_accepts_absolute_steps(self):
        args = plot_va.build_argument_parser().parse_args(["dummy.csv", "--transient=500"])
        self.assertEqual("500", args.transient)

    def test_plot_va_vs_eta_accepts_percentage(self):
        args = plot_va_vs_eta.build_argument_parser().parse_args(["dummy.csv", "--transient=40%"])
        self.assertEqual("40%", args.transient)

    def test_plot_va_vs_s_accepts_percentage(self):
        args = plot_va_vs_s.build_argument_parser().parse_args(["dummy.csv", "--transient=40%"])
        self.assertEqual("40%", args.transient)

    def test_plot_va_vs_s_still_accepts_absolute_steps(self):
        args = plot_va_vs_s.build_argument_parser().parse_args(["dummy.csv", "--transient=500"])
        self.assertEqual("500", args.transient)


class TransientEquivalenceTest(unittest.TestCase):
    """Un porcentaje y su paso absoluto equivalente dan el mismo resultado en los 3 graficadores."""

    STEPS = [0, 10, 20, 30, 40]
    VALUES = [1.0, 1.0, 0.5, 0.5, 0.5]

    def test_plot_va_report_tail_percentage_matches_absolute(self):
        series = [(None, self.STEPS, self.VALUES)]
        labels = ["corrida"]

        with_percentage = io.StringIO()
        with redirect_stdout(with_percentage):
            report_tail(series, labels, "50%")

        with_absolute = io.StringIO()
        with redirect_stdout(with_absolute):
            report_tail(series, labels, 20)

        self.assertEqual(with_absolute.getvalue(), with_percentage.getvalue())
        self.assertIn("t >= 20", with_percentage.getvalue())

    def test_plot_va_vs_s_steady_mean_percentage_matches_absolute(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            write_series_csv(temp_path, "va.csv", self.STEPS, self.VALUES)

            with_percentage = steady_values(temp_path, "va.csv", "50%")
            with_absolute = steady_values(temp_path, "va.csv", 20)

            self.assertEqual(with_absolute, with_percentage)
            self.assertEqual([0.5, 0.5, 0.5], with_percentage)

    def test_plot_va_vs_eta_collect_percentage_matches_absolute(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            write_series_csv(temp_path, "va.csv", self.STEPS, self.VALUES)
            runs_csv = temp_path / "runs.csv"
            runs_csv.write_text("eta,va_csv\n0.5,va.csv\n", encoding="utf-8")

            curves_percentage, _, _ = plot_va_vs_eta.collect([runs_csv], "50%", "auto")
            curves_absolute, _, _ = plot_va_vs_eta.collect([runs_csv], 20, "auto")

            self.assertEqual(curves_absolute, curves_percentage)


if __name__ == "__main__":
    unittest.main()
