"""Pruebas de los auxiliares de las figuras."""
import unittest

import numpy as np

from figure_data import closest_approach, common_times, deviation_degrees, marks


class FigureDataTest(unittest.TestCase):
    def test_deviation_is_positive_to_the_walkers_right(self):
        # Va por +x: su derecha es −y
        self.assertAlmostEqual(deviation_degrees(1, 0, np.cos(np.radians(-10)), np.sin(np.radians(-10))), 10)
        self.assertAlmostEqual(deviation_degrees(1, 0, np.cos(np.radians(10)), np.sin(np.radians(10))), -10)
        # Va por +y: su derecha es +x
        self.assertGreater(deviation_degrees(0, 1, 0.1, 1), 0)

    def test_marks_are_the_samples_nearest_to_each_half_second(self):
        t = np.arange(0, 1.2, 0.0166)
        idx = marks(t)
        self.assertEqual(len(idx), 3)
        np.testing.assert_allclose(t[idx], [0, 0.5, 1.0], atol=0.01)

    def test_closest_approach_ignores_retired_rows(self):
        a = np.array([[0, 0], [1, 0], [np.nan, np.nan]])
        b = np.array([[3, 0], [1.5, 0], [0, 0]])
        k, d = closest_approach(None, a, b)
        self.assertEqual(k, 1)
        self.assertAlmostEqual(d[1], 0.5)

    def test_common_times_skip_gaps(self):
        a = np.array([[0, 0, 0], [0.1, 1, 0], [0.2, 2, 0]])
        b = np.array([[0, 5, 0], [0.2, 3, 0]])
        t, pa, pb = common_times(a, b)
        np.testing.assert_allclose(t, [0, 0.2])
        np.testing.assert_allclose(pa[:, 0], [0, 2])


if __name__ == "__main__":
    unittest.main()
