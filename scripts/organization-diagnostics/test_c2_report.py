"""Aggregate metrics distinguish pooled evidence from equal-stream averages."""
import unittest

from c2_report import order_sensitivity, summarize


class ReportTests(unittest.TestCase):
    def test_order_comparison_ignores_thread_id_permutations(self):
        def trace(order, groups):
            return {"story": "s", "order": order, "events": [{"expectedState": {
                key: {"memberships": value, "archived": False} for key, value in groups.items()}}]}
        first = trace("chronological", {"a": ["one"], "b": ["one"], "c": ["two"]})
        second = trace("shuffle-1", {"a": ["x"], "b": ["x"], "c": ["y"]})
        third = trace("shuffle-2", {"a": ["x"], "b": ["y"], "c": ["y"]})
        result = order_sensitivity([first, second, third])
        self.assertEqual(result["comparisons"][0]["activePairDisagreement"]["value"], 0)
        self.assertAlmostEqual(result["macroPairDisagreement"]["value"], 4/9)

    def test_pooled_rates_and_macro_are_distinct_with_undefined_precision(self):
        def row(tp, fp, fn, precision):
            return {"counts": {"correctionErrorsBefore": 3, "correctionErrorsAfter": 1},
                    "rates": {"falseAttachments": {"numerator": fp, "denominator": tp+fp+fn}},
                    "macroPrefix": {"precision": {"value": precision}},
                    "final": {"pairs": {"truePositive": tp, "falsePositive": fp, "falseNegative": fn,
                                         "trueNegative": 0, "knownPairs": tp+fp+fn,
                                         "precision": {"value": precision}, "recall": {"value": tp/(tp+fn)}},
                              "structure": {"fragmentedProjects": {"value": 1}, "mixedClusters": {"value": 0}}}}
        result = summarize([row(1, 1, 0, 0.5), row(0, 0, 8, None)])
        self.assertEqual(result["rates"]["falseAttachments"]["value"], 0.1)
        self.assertEqual(result["finalMacro"]["precision"]["value"], 0.5)
        self.assertEqual(result["finalMacro"]["precision"]["denominator"], 1)
        self.assertEqual(result["finalPairsPooled"]["recall"]["value"], 1/9)
        self.assertEqual(result["correctionErrorChange"], -4)


if __name__ == "__main__":
    unittest.main()
