import unittest
from audit_stage5 import counts,brute_threshold,gold


class IndependentAuditTests(unittest.TestCase):
    def test_undefined_precision_stays_undefined(self):
        rows=[{"library":"one","relation":"same","probabilities":[.2,.3,.5]}]
        result=counts(rows,.9)
        self.assertIsNone(result["precision"]);self.assertEqual(result["fn"],1)

    def test_audit_threshold_ignores_ambiguous_labels_and_groups_ties(self):
        rows=[{"library":"one","relation":"same","probabilities":[.9,.05,.05]} for _ in range(30)]
        rows += [{"library":"one","relation":"uncertain","probabilities":[.99,.005,.005]} for _ in range(8)]
        rows += [{"library":"one","relation":"unrelated","probabilities":[.8,.1,.1]}]
        best=brute_threshold(rows)
        self.assertEqual(best,(1.0,1.0,.9))

    def test_no_test_gold_without_selected_run(self):
        with self.assertRaisesRegex(ValueError,"selected run"):gold("test")


if __name__=="__main__":unittest.main()
