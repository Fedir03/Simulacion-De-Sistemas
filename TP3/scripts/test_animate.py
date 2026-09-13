"""Pruebas del formato y de los tiempos de una simulación por eventos."""
import tempfile
from pathlib import Path
import unittest

from simulation_io import parse_simulation, sample_frame

HEADER = 'format=tp3-v1 N=1 K=1 L=1.2 W=0.68 d=0.2\nobstacle 0.6 0.34 0.08\n'


def block(t, x, used=False):
    return (f't={t} events={int(t)} Ng={int(used)} Fu={float(used)}\n'
            f'1 {x} 0.2 1 0 0.0175 0.025 ' + ('255 0 0' if used else '0 0 255') + '\n')


class SimulationTests(unittest.TestCase):
    def parse(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'run.txt'
            path.write_text(text)
            return parse_simulation(path)

    def test_variable_times_and_color_at_event(self):
        data = self.parse(HEADER + block(0, 0.1) + block(2, 0.5, True) + block(3, 0.3, True))
        frame, xy = sample_frame(data, [0, 2, 3], 1)
        self.assertAlmostEqual(xy[0][0], 0.3)
        self.assertEqual(frame.goals, 0)
        self.assertEqual(sample_frame(data, [0, 2, 3], 2)[0].goals, 1)
        self.assertAlmostEqual(sample_frame(data, [0, 2, 3], 2.5)[1][0][0], 0.4)

    def test_simultaneous_events_and_final_comment(self):
        data = self.parse(HEADER + block(0, 0.1) + block(0, 0.1, True) + block(1, 0.2, True)
                          + '# tf=1 t90=NaN\n')
        self.assertEqual(sample_frame(data, [0, 0, 1], 0)[0].goals, 1)
        self.assertEqual(sample_frame(data, [0, 0, 1], 1)[1], [(0.2, 0.2)])

    def test_single_frame(self):
        data = self.parse(HEADER + block(0, 0.1))
        self.assertEqual(sample_frame(data, [0], 0)[1], [(0.1, 0.2)])

    def test_invalid_files(self):
        for text in (HEADER, HEADER + 't=0 events=0 Ng=0 Fu=0\n',
                     HEADER + block(2, 0.1) + block(1, 0.2),
                     HEADER + block(0, 'NaN'),
                     HEADER + block(0, 0.1) + block(1, 0.2).replace('1 0.2', '2 0.2')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.parse(text)


if __name__ == '__main__':
    unittest.main()
