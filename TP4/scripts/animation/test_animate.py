import tempfile
import unittest
from pathlib import Path

from animate import read_simulation


class ReadSimulationTest(unittest.TestCase):
    def read(self, body, *, obstacles=True):
        header = '# format=tp4-billiard-v1 N=2 dt=1e-5 dt2=0.04 tf=0.04 R=0.51 r=0.0175\n'
        if obstacles:
            header += '# obstacle -0.25 0 0.0175\n# obstacle 0.25 0 0.0175\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'dynamic.txt'
            path.write_text(header + body, encoding='utf-8')
            return read_simulation(path)

    @staticmethod
    def trajectory(used=1):
        return ('t=0 Nu=0\n2 0.1 0 0 1 0\n1 0 0 1 0 0\n'
                f't=0.04 Nu={used}\n1 0.04 0 1 0 {used}\n2 0.1 0.04 0 1 0\n'
                f'# fin estado=completa t=0.04 Nu={used}\n')

    def test_obstacles_and_sorted_ids(self):
        data = self.read(self.trajectory())
        self.assertEqual(len(data.obstacles), 2)
        self.assertEqual(data.positions.shape, (2, 2, 2))
        self.assertEqual(data.positions[0, 0].tolist(), [0, 0])
        self.assertEqual(data.used.sum(axis=1).tolist(), [0, 1])

    def test_no_obstacles(self):
        data = self.read(self.trajectory(0), obstacles=False)
        self.assertEqual(data.obstacles, [])
        self.assertFalse(data.used.any())

    def test_incomplete_frame(self):
        with self.assertRaisesRegex(ValueError, 'ids únicos'):
            self.read(self.trajectory().replace('2 0.1 0.04 0 1 0\n', ''))

    def test_counter_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'Nu no coincide'):
            self.read(self.trajectory().replace('t=0.04 Nu=1', 't=0.04 Nu=0'))

    def test_used_without_obstacles(self):
        with self.assertRaisesRegex(ValueError, 'sin obstáculos'):
            self.read(self.trajectory(), obstacles=False)

    def test_missing_footer(self):
        with self.assertRaisesRegex(ValueError, 'pie de finalización'):
            self.read(self.trajectory().split('# fin')[0])


if __name__ == '__main__':
    unittest.main()
