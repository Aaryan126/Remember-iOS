import unittest

from stage5_diagnostics import coverage_diagnostic


def row(relation, probabilities):
    return {"library": "example", "relation": relation, "probabilities": probabilities}


class DevelopmentDiagnosticsTests(unittest.TestCase):
    def test_ambiguous_pairs_do_not_satisfy_minimum_coverage(self):
        rows = [row("same", [.9, .05, .05]) for _ in range(29)]
        rows += [row("uncertain", [.99, .005, .005]) for _ in range(20)]
        self.assertIsNone(coverage_diagnostic(rows))

    def test_precision_ceiling_is_diagnostic_not_a_qualifying_threshold(self):
        rows = [row("same", [.9, .05, .05]) for _ in range(28)]
        rows += [row("related", [.9, .05, .05]) for _ in range(2)]
        result = coverage_diagnostic(rows)
        self.assertEqual(result["metrics"]["acceptedKnownPairs"], 30)
        self.assertAlmostEqual(result["metrics"]["precision"], 28 / 30)
        self.assertIn("NOT an approved operating point", result["purpose"])

    def test_same_probability_must_also_be_the_winning_class(self):
        rows = [row("same", [.3, .6, .1]) for _ in range(40)]
        self.assertIsNone(coverage_diagnostic(rows))

    def test_tied_scores_are_never_split_to_inflate_precision(self):
        rows = [row("same", [.9, .05, .05]) for _ in range(30)]
        rows += [row("unrelated", [.9, .05, .05]) for _ in range(10)]
        result = coverage_diagnostic(rows)
        self.assertEqual(result["threshold"], .9)
        self.assertEqual(result["metrics"]["precision"], .75)
        self.assertEqual(result["metrics"]["acceptedKnownPairs"], 40)


if __name__ == "__main__":
    unittest.main()
