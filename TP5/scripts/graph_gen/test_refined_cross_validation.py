"""Controles de aislamiento del entrenamiento y de candidatos por partición."""
import unittest
import numpy as np

from refined_cross_validation import fit, select, window


class RefinedCrossValidationTest(unittest.TestCase):
    def test_validation_values_do_not_influence_selection(self):
        errors = {(1., 0.): np.array([[0., 0.], [100., 100.]]),
                  (2., 0.): np.array([[1., 1.], [0., 0.]])}
        allowed = [frozenset(errors)]
        weights = np.array([[1.], [0.]])
        self.assertEqual(select(errors, allowed, weights, 0), [(1., 0.)])
        errors[(1., 0.)][1] = 1e6
        errors[(2., 0.)][1] = -1e6
        self.assertEqual(select(errors, allowed, weights, 0), [(1., 0.)])

    def test_cached_candidates_from_other_partitions_are_not_shared(self):
        errors = {(1., 0.): np.full((2, 2), 2.), (2., 0.): np.full((2, 2), 0.)}
        allowed = [frozenset([(1., 0.)]), frozenset(errors)]
        weights = np.full((2, 2), .5)
        self.assertEqual(select(errors, allowed, weights, 0), [(1., 0.), (2., 0.)])

    def test_both_metrics_use_their_own_objective(self):
        errors = {(1., 0.): np.array([[0., 2.], [0., 2.]]),
                  (2., 0.): np.array([[1., 0.], [1., 0.]])}
        allowed, weights = [frozenset(errors)], np.full((2, 1), .5)
        self.assertEqual(select(errors, allowed, weights, 0), [(1., 0.)])
        self.assertEqual(select(errors, allowed, weights, 1), [(2., 0.)])

    def test_training_only_refinements_are_unchanged_by_heldout_values(self):
        class FakeCache:
            layer = "A"
            def __init__(self, heldout_target):
                self.target = np.array([1., heldout_target])
                self.errors = {}
            def ensure(self, pairs):
                for a, b in pairs:
                    error = (a-self.target)**2+b*b
                    self.errors[a, b] = np.column_stack([error, error])
        coarse = [(1., 0.), (3., 0.)]
        masks = np.array([[True, False], [False, True]])
        results = []
        for heldout in (3., 4.):
            cache = FakeCache(heldout); cache.ensure(coarse)
            chosen = fit(cache, coarse, masks)
            results.append([chosen[m][0] for m in (0, 1)])
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0], [(1., 0.), (1., 0.)])

    def test_refinement_respects_domain_limits(self):
        candidates = window("E", (.5, .25), 1)
        self.assertTrue(all(.5 <= a <= 6 and .25 <= b <= .5 for a, b in candidates))


if __name__ == "__main__":
    unittest.main()
