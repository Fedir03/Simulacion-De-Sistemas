"""Rechaza resultados truncados o inconsistentes antes de generar F2/F3."""
import tempfile
import unittest
from pathlib import Path

from observables import read_run, load_study


VALID = """# format=tp4-billiard-v1 N=300 seed=1 x0=none dt=0.001 dt2=0.04 tf=0.08 R=0.51 r=0.0175 m=0.025 k=10000 v0=1
t E_tot E_cin E_el Nu
0 3.75 3.75 0 0
0.04 3.75 3.70 0.05 0
0.08 3.75 3.65 0.10 0
# fin estado=completa t=0.08 pasos=80 Nu=0 runtime_s=1
"""


class ObservablesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "observables.txt"

    def read(self, data):
        self.path.write_text(data)
        return read_run(self.path)

    def test_complete(self):
        self.assertEqual(self.read(VALID).epsilon, 0)

    def test_divergence_without_second_sample(self):
        data = VALID.split("0.04 3.75")[0] + "# fin estado=divergio t=0.02 pasos=20\n"
        self.assertEqual(self.read(data).times, [0])

    def test_truncated_or_inconsistent_results(self):
        for data in (
            VALID.split("# fin")[0],
            VALID.replace("0.04 3.75 3.70", "0.04 3.80 3.70"),
            VALID.replace("0.04 3.75 3.70 0.05 0\n", ""),
            VALID.replace("0.08 3.75 3.65 0.10 0\n", ""),
            VALID.replace("3.70", "nan"),
            VALID.replace("0.05 0", "0.05 1"),
            VALID.replace("pasos=80", "pasos=79"),
        ):
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.read(data)

    def test_different_physical_parameters(self):
        for dirname, data in (("dt-1e-3", VALID), ("dt-1e-4", VALID.replace("dt=0.001", "dt=0.0001").replace("pasos=80", "pasos=800").replace("k=10000", "k=20000"))):
            target = Path(self.temp.name) / dirname / "observables.txt"
            target.parent.mkdir()
            target.write_text(data)
        with self.assertRaisesRegex(ValueError, "no son comparables"):
            load_study(Path(self.temp.name))


if __name__ == "__main__":
    unittest.main()
