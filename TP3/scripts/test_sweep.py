import math
import tempfile
import unittest
from pathlib import Path

from sweep import parse_result, summarize


class SweepTest(unittest.TestCase):
    def test_parse_result_reads_final_comment(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'sim.txt'
            path.write_text('format=tp3-v1 N=1 K=0\nt=0.0 events=0 Ng=0 Fu=0.0\n'
                            '# tf=100.0 outputEvery=5 events=42 Ng=91 t90=12.5 runtime=0.25\n', encoding='utf-8')
            self.assertEqual(parse_result(path), {'t90': 12.5, 'goals': 91, 'events': 42, 'runtime_s': 0.25})
            path.write_text('# tf=1.0 outputEvery=1 events=0 Ng=0 t90=NaN runtime=0.1\n', encoding='utf-8')
            self.assertTrue(math.isnan(parse_result(path)['t90']))

    def test_summary_excludes_unreached_t90_and_failures(self):
        rows = [
            {'param': 'x', 'value': '1', 'status': 'ok', 't90': 10.0, 'goals': 95, 'events': 10, 'runtime_s': 1.0},
            {'param': 'x', 'value': '1', 'status': 'ok', 't90': 14.0, 'goals': 97, 'events': 20, 'runtime_s': 3.0},
            {'param': 'x', 'value': '1', 'status': 'ok', 't90': math.nan, 'goals': 80, 'events': 30, 'runtime_s': 2.0},
            {'param': 'x', 'value': '1', 'status': 'generate_failed'},
        ]
        [s] = summarize(rows)
        self.assertEqual((s['realizations'], s['failed'], s['reached_t90']), (3, 1, 2))
        self.assertAlmostEqual(s['t90_mean'], 12.0)
        self.assertAlmostEqual(s['t90_std'], math.sqrt(8.0))
        self.assertAlmostEqual(s['goals_mean'], 272 / 3)
        self.assertAlmostEqual(s['runtime_mean_s'], 2.0)


if __name__ == '__main__':
    unittest.main()
