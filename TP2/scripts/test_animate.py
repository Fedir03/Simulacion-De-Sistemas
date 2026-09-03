#!/usr/bin/env python3

import math
import importlib.util
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from animate import (
    ProgressBar,
    SimulationFormatError,
    parse_cluster_members,
    parse_simulation,
    render_animation,
    select_frames,
    validate_cluster_members,
    velocity_components,
)


HEADER = (
    "model=voter N=2 L=10.0 rc=1.0 dt=0.5 v0=0.03 eta=0.5 "
    "periodic=true seedIC=1 seedLoop=2\n"
)


class AnimateParserTest(unittest.TestCase):
    def parse(self, contents: str):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "simulation.txt"
            path.write_text(contents, encoding="utf-8")
            return parse_simulation(path)

    def test_parses_valid_simulation_and_metadata(self):
        data = self.parse(
            HEADER
            + "t=0\n1 1.0 2.0 0.0\n2 3.0 4.0 1.5707963267948966\n"
            + "t=1\n1 1.1 2.0 0.1\n2 3.0 4.1 1.6\n"
        )

        self.assertEqual("voter", data.header.model)
        self.assertAlmostEqual(0.02, data.header.density)
        self.assertEqual((0, 1), tuple(frame.step for frame in data.frames))
        self.assertEqual((1, 2), tuple(p.particle_id for p in data.frames[0].particles))

    def test_velocity_components_use_v0_and_theta(self):
        data = self.parse(
            HEADER + "t=0\n1 1.0 2.0 0.0\n2 3.0 4.0 1.5707963267948966\n"
        )

        u, v = velocity_components(data.frames[0], data.header.v0)

        self.assertAlmostEqual(0.03, u[0])
        self.assertAlmostEqual(0.0, v[0])
        self.assertAlmostEqual(0.0, u[1], places=12)
        self.assertAlmostEqual(0.03, v[1])

    def test_stride_always_preserves_last_frame(self):
        blocks = "".join(
            f"t={step}\n1 1.0 2.0 0.0\n2 3.0 4.0 {math.pi}\n" for step in range(6)
        )
        data = self.parse(HEADER + blocks)

        selected = select_frames(data.frames, 4)

        self.assertEqual((0, 4, 5), tuple(frame.step for frame in selected))

    def test_rejects_missing_header_field(self):
        with self.assertRaisesRegex(SimulationFormatError, "seedLoop"):
            self.parse(HEADER.replace(" seedLoop=2", "") + "t=0\n")

    def test_rejects_incomplete_frame(self):
        with self.assertRaisesRegex(SimulationFormatError, "se esperaban 2 particulas"):
            self.parse(HEADER + "t=0\n1 1.0 2.0 0.0\n")

    def test_rejects_duplicate_time_block(self):
        block = "t=0\n1 1.0 2.0 0.0\n2 3.0 4.0 1.0\n"
        with self.assertRaisesRegex(SimulationFormatError, "duplicado"):
            self.parse(HEADER + block + block)

    def test_rejects_changed_particle_ids(self):
        with self.assertRaisesRegex(SimulationFormatError, "IDs"):
            self.parse(
                HEADER
                + "t=0\n1 1.0 2.0 0.0\n2 3.0 4.0 1.0\n"
                + "t=1\n1 1.0 2.0 0.0\n3 3.0 4.0 1.0\n"
            )

    def test_rejects_non_positive_stride(self):
        data = self.parse(
            HEADER + "t=0\n1 1.0 2.0 0.0\n2 3.0 4.0 1.0\n"
        )
        with self.assertRaisesRegex(ValueError, "positivo"):
            select_frames(data.frames, 0)

    def test_parses_cluster_members(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "members.txt"
            path.write_text("# comentario\n0 1 2\n5 2\n", encoding="utf-8")

            members = parse_cluster_members(path)

        self.assertEqual({0: {1, 2}, 5: {2}}, members)

    def test_rejects_duplicate_cluster_steps(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "members.txt"
            path.write_text("0 1\n0 2\n", encoding="utf-8")
            with self.assertRaisesRegex(SimulationFormatError, "paso 0 duplicado"):
                parse_cluster_members(path)

    def test_rejects_empty_largest_cluster(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "members.txt"
            path.write_text("0\n", encoding="utf-8")
            with self.assertRaisesRegex(SimulationFormatError, "no puede estar vacio"):
                parse_cluster_members(path)

    def test_validates_cluster_steps_and_particle_ids(self):
        data = self.parse(
            HEADER
            + "t=0\n1 1.0 2.0 0.0\n2 3.0 4.0 1.0\n"
            + "t=1\n1 1.1 2.0 0.1\n2 3.0 4.1 1.1\n"
        )

        validate_cluster_members(data.frames, {0: {1}, 1: {2}})
        with self.assertRaisesRegex(SimulationFormatError, "no contiene.*1"):
            validate_cluster_members(data.frames, {0: {1}})
        with self.assertRaisesRegex(SimulationFormatError, "ids inexistentes: 3"):
            validate_cluster_members(data.frames, {0: {1}, 1: {3}})

    def test_progress_bar_reports_frames_and_completion(self):
        output = io.StringIO()
        progress = ProgressBar(total=3, stream=output, width=10)

        progress.update(0, 3)
        progress.update(2, 3)

        rendered = output.getvalue()
        self.assertIn("1/3 cuadros", rendered)
        self.assertIn("100.0%", rendered)
        self.assertIn("3/3 cuadros", rendered)
        self.assertTrue(rendered.endswith("\n"))

    @unittest.skipUnless(
        importlib.util.find_spec("matplotlib") is not None and shutil.which("ffmpeg") is not None,
        "la prueba integral requiere Matplotlib y FFmpeg",
    )
    def test_renders_compatible_mp4(self):
        data = self.parse(
            HEADER
            + "t=0\n1 1.0 2.0 0.0\n2 3.0 4.0 1.0\n"
            + "t=1\n1 1.1 2.0 0.1\n2 3.0 4.1 1.1\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "animation.mp4"

            render_animation(
                data, output, fps=2, dpi=50, cluster_members={0: {1}, 1: {2}}
            )

            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 0)
            self.assertIn(b"ftyp", output.read_bytes()[:32])


if __name__ == "__main__":
    unittest.main()
