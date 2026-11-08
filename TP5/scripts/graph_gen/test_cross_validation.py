"""Pruebas de la validación cruzada con grillas sintéticas de respuesta conocida."""
import unittest

import numpy as np

from cross_validation import error_matrix, evaluate, evaluate_on_all, partitions


class CrossValidationTest(unittest.TestCase):
    def test_partitions_have_the_requested_sizes(self):
        parts = partitions(200)
        self.assertEqual(parts.shape, (200, 19))
        self.assertTrue((parts.sum(axis=1) == 14).all())

    def test_same_seed_gives_the_same_partitions(self):
        np.testing.assert_array_equal(partitions(50, seed=7), partitions(50, seed=7))
        self.assertFalse((partitions(50, seed=7) == partitions(50, seed=8)).all())

    def test_a_pair_better_in_every_event_is_always_chosen(self):
        matrix = np.array([[2.0] * 19, [1.0] * 19, [3.0] * 19])
        train, val, chosen = evaluate(matrix, partitions(100))
        self.assertTrue((chosen == 1).all())
        np.testing.assert_allclose(train, 1.0)
        np.testing.assert_allclose(val, 1.0)

    def test_validation_uses_only_the_events_left_out(self):
        # El par 0 vale 0 en los primeros 14 eventos y 10 en los últimos 5; el par 1 vale 1 siempre
        matrix = np.array([[0.0] * 14 + [10.0] * 5, [1.0] * 19])
        train_mask = np.zeros((1, 19), dtype=bool)
        train_mask[0, :14] = True
        train, val, chosen = evaluate(matrix, train_mask)
        self.assertEqual(chosen[0], 0)
        self.assertAlmostEqual(train[0], 0.0)
        self.assertAlmostEqual(val[0], 10.0)

    def test_training_on_everything_gives_the_population_optimum(self):
        matrix = np.random.default_rng(3).random((12, 19))
        chosen, error = evaluate_on_all(matrix)
        self.assertEqual(chosen, int(np.argmin(matrix.mean(axis=1))))
        self.assertAlmostEqual(error, matrix.mean(axis=1).min())

    def test_training_error_is_optimistic_on_noise(self):
        # Sin diferencia real entre pares, elegir el mínimo en entrenamiento es optimista
        rng = np.random.default_rng(5)
        matrix = rng.normal(1.0, 0.3, size=(40, 19))
        train, val, _ = evaluate(matrix, partitions(300))
        self.assertLess(train.mean(), val.mean())

    def test_matrix_is_built_from_rows(self):
        rows = [[1.0, 2.0, 1.0, 0.5], [1.0, 2.0, 2.0, 0.7], [3.0, 2.0, 1.0, 0.1], [3.0, 2.0, 2.0, 0.2]]
        pairs, matrix = error_matrix(rows, 3)
        self.assertEqual(pairs, [(1.0, 2.0), (3.0, 2.0)])
        np.testing.assert_allclose(matrix, [[0.5, 0.7], [0.1, 0.2]])

    def test_incomplete_grid_is_rejected(self):
        with self.assertRaises(ValueError):
            error_matrix([[1.0, 2.0, 1.0, 0.5], [3.0, 2.0, 2.0, 0.2]], 3)


if __name__ == "__main__":
    unittest.main()
