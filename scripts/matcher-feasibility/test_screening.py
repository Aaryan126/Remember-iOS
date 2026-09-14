import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from screening_common import (stage_guard,load_split,validate_fold,space_ok,GIB,roll_recovery,
                              save,read,sha,lock,locations)
from screening_config import folds,trials
from screening_ablation import fit_vocabulary,policy_metrics,diagnostic_curve,PROFILES
from screening_review import sample_cases,publish_context,import_reviews
from screening_sanity import sanity_inputs
from stage2_metrics import select_threshold
from audit_stage5 import brute_threshold


class ScreeningTests(unittest.TestCase):
    def test_stage2_is_blocked(self):
        stage_guard("audit")
        with self.assertRaisesRegex(ValueError,"not authorized"): stage_guard("screen")

    def test_test_access_rejected_before_read(self):
        with patch("screening_common.read") as reader:
            with self.assertRaisesRegex(ValueError,"heldout"): load_split("test")
            reader.assert_not_called()

    def test_outer_and_inner_groups(self):
        outer=[]
        for fold in folds()["folds"]:
            validate_fold(fold);outer+=fold["evaluation"]
            inner=fold["hybridInnerValidation"]
            self.assertEqual(sorted(sum(inner,[])),sorted(fold["fit"]))
            self.assertTrue(all(len(v)==3 for v in inner))
        self.assertEqual(sorted(outer),[f"mf{i:02}" for i in range(1,19)])

    def test_fold_leakage_rejected(self):
        fold=folds()["folds"][0];fold["fit"][0]=fold["evaluation"][0]
        with self.assertRaisesRegex(ValueError,"leakage"):validate_fold(fold)

    def test_exact_profile_count_and_no_execution(self):
        config=trials()
        self.assertEqual(len(config["configurations"]),12)
        self.assertFalse(config["authorizedToExecute"])
        self.assertEqual(set(PROFILES),{"embeddings","lexical","all_six","without_numbers"})

    def test_vocabulary_cannot_see_calibration_or_evaluation(self):
        libs=[{"id":"fit","items":[{"id":"a","text":"blue bridge"}]},
              {"id":"eval","items":[{"id":"b","text":"unseenleakword"}]}]
        vectorizer,record=fit_vocabulary(libs,["fit"])
        self.assertNotIn("unseenleakword",record["vocabulary"])
        self.assertEqual(record["fitSourceIDs"],["a"])
        self.assertEqual(vectorizer.transform(["unseenleakword"]).nnz,0)

    def test_space_reserve_and_budget(self):
        self.assertTrue(space_ok(12*GIB,GIB,GIB))
        self.assertFalse(space_ok(10*GIB,GIB,1))
        self.assertFalse(space_ok(20*GIB,4*GIB,1))

    def test_unscoped_run_rejected(self):
        with self.assertRaises(ValueError):locations("/tmp/audit-attempt-01")

    def test_exclusive_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            handle=lock(Path(folder))
            try:
                with self.assertRaises(BlockingIOError):lock(Path(folder))
            finally:handle.close()

    def make_recovery(self,root):
        external=root/"external";rows=[]
        for i in range(4):
            p=external/"recovery/sanity"/f"step-{i}.pt.gz"
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(bytes([i]))
            rows.append({"stamp":i,"file":str(p.relative_to(external)),"SHA256":sha(p),"bytes":1})
        return external,rows

    def test_rotation_preserves_last_two_and_receipts(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);external,rows=self.make_recovery(root)
            roll_recovery(root/"run",external,rows)
            self.assertEqual(len(list(external.rglob("*.pt.gz"))),2)
            self.assertEqual(len(list((root/"run/retention").glob("*.json"))),2)
            roll_recovery(root/"run",external,rows)

    def test_rotation_rejects_corrupt_latest(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);external,rows=self.make_recovery(root)
            rows[-1]["SHA256"]="wrong"
            with self.assertRaisesRegex(ValueError,"corrupted"):roll_recovery(root/"run",external,rows)
            self.assertEqual(len(list(external.rglob("*.pt.gz"))),4)

    def test_rotation_rejects_outside_target(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);external,rows=self.make_recovery(root)
            rows[0]["file"]="../old-feasibility.pt.gz"
            with self.assertRaisesRegex(ValueError,"unsafe"):roll_recovery(root/"run",external,rows)

    def test_review_sample_size_unique_and_balanced(self):
        cases=sample_cases()
        self.assertEqual(len({r["id"] for r in cases}),60)
        self.assertEqual([sum(r["library"]==f"mf{i}" for r in cases) for i in range(19,25)],[10]*6)

    def test_context_requires_pair_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);save(root/"review/selection.json",{"cases":[{"id":"a--b"}]})
            with self.assertRaisesRegex(ValueError,"pair-only"):publish_context(root)

    def test_review_rejects_missing_note(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);save(root/"review/selection.json",{"cases":[{"id":"a--b"}]})
            save(root/"input.json",{"phase":"pair","reviewer":"executing_agent","records":[{"id":"a--b","note":"short"}]})
            with self.assertRaisesRegex(ValueError,"evidence"):import_reviews(root,root/"input.json")

    def test_sanity_known_labels_balanced(self):
        examples=sanity_inputs()
        self.assertEqual(len(examples),12)
        self.assertEqual([sum(r["relation"]==label for r in examples) for label in ("same","related","unrelated")],[4,4,4])

    def test_threshold_ties_and_uncertain_do_not_qualify(self):
        rows=[{"library":"a","relation":"same","probabilities":[.9,.05,.05]} for _ in range(29)]
        rows += [{"library":"a","relation":"uncertain","probabilities":[.99,.005,.005]}]*20
        self.assertIsNone(select_threshold(rows))
        rows.append({"library":"a","relation":"same","probabilities":[.9,.05,.05]})
        self.assertEqual(select_threshold(rows)["threshold"],brute_threshold(rows)[2])

    def test_pool_keeps_separately_calibrated_decisions(self):
        rows=[{"library":"a","relation":"same","probabilities":[.8,.1,.1],"accepted":True},
              {"library":"b","relation":"same","probabilities":[.9,.05,.05],"accepted":False},
              {"library":"b","relation":"unrelated","probabilities":[.99,.005,.005],"accepted":True},
              {"library":"a","relation":"uncertain","probabilities":[.8,.1,.1],"accepted":True}]
        result=policy_metrics(rows)
        self.assertEqual((result["tp"],result["fp"],result["macroLibraryRecall"]),(1,1,.5))
        self.assertEqual(result["acceptedUncertainPairs"],1)

    def test_abstention_has_undefined_precision(self):
        rows=[{"library":"a","relation":"same","probabilities":[.9,.05,.05],"accepted":False}]
        self.assertIsNone(policy_metrics(rows)["precision"])
        self.assertEqual(diagnostic_curve(rows)["averagePrecision"],1)


if __name__=="__main__":unittest.main()
