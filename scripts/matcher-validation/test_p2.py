import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

import p2_common as c
import p2_data as data
import p2_models as models
import p2_train as training


class P2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="remember-p2-test-")
        self.root = Path(self.temp.name)
        self.patches = [patch.object(c,"RUN",self.root/"run"), patch.object(c,"EXTERNAL",self.root/"external"),
                        patch.object(c,"check_space",return_value={}), patch.object(c,"requested",False),
                        patch.object(c,"log")]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def toy(self,task,pause_after=None,fingerprint="fixture"):
        import torch
        random.seed(17)
        np.random.seed(17)
        torch.manual_seed(17)
        model=torch.nn.Sequential(torch.nn.Linear(4,8),torch.nn.ReLU(),torch.nn.Dropout(.3),torch.nn.Linear(8,2))
        optimizer=torch.optim.AdamW([{"params":model.parameters(),"lr":.001,"base_lr":.001}],weight_decay=.01)
        x=torch.arange(128,dtype=torch.float32).reshape(32,4)/128
        position=training.train_loop(model,optimizer,[(i,i%2) for i in range(32)],lambda m,i,all_i:m(x[i]),
                                     task,fingerprint,17,epochs=2,batch=8,micro=4,pause_after=pause_after)
        return model,optimizer,position

    def test_cpu_pause_resume_matches_uninterrupted_training(self):
        import torch
        whole,opt_whole,state_whole=self.toy("whole")
        with self.assertRaises(c.Paused):
            self.toy("resumed",pause_after=2)
        checkpoint=c.latest_recovery("resumed")
        self.assertEqual(checkpoint["position"]["step"],2)
        resumed,opt_resumed,state_resumed=self.toy("resumed")
        self.assertEqual(state_resumed["step"],state_whole["step"])
        for a,b in zip(whole.parameters(),resumed.parameters()):
            self.assertTrue(torch.equal(a,b))
        for key,value in opt_whole.state_dict()["state"].items():
            for name,tensor in value.items():
                self.assertTrue(torch.equal(tensor,opt_resumed.state_dict()["state"][key][name]))
        self.assertEqual(len(list((c.EXTERNAL/"recovery").glob("*.pt.gz"))),2)
        self.assertGreater(len(list((c.RUN/"retention").glob("*.json"))),0)

    def test_checkpoint_fingerprint_mismatch_fails(self):
        with self.assertRaises(c.Paused):
            self.toy("bound",pause_after=1)
        with self.assertRaisesRegex(ValueError,"binding"):
            self.toy("bound",fingerprint="changed")

    def test_preexisting_pause_saves_initial_state_then_exits(self):
        with patch.object(c,"requested",True),self.assertRaises(c.Paused):
            self.toy("paused")
        self.assertEqual(c.latest_recovery("paused")["position"]["step"],0)

    def test_retention_does_not_remove_unverified_replacements(self):
        with self.assertRaises(c.Paused):
            self.toy("retention",pause_after=1)
        last=c.latest_recovery("retention")
        target=c.EXTERNAL/last["file"]
        # Corruption is confined to this test's explicitly created temporary file.
        target.write_bytes(b"invalid fixture")
        with self.assertRaises(ValueError):
            self.toy("retention")
        self.assertTrue(target.exists())

    def test_evaluation_is_blocked_before_selection(self):
        with self.assertRaisesRegex(ValueError,"evaluation forbidden"):
            c.split_data("evaluation")

    def test_unexpected_split_rejected(self):
        for split in ("test","development","../test"):
            with self.subTest(split=split),self.assertRaises(ValueError):
                c.split_data(split)

    def test_selection_cannot_have_empty_inventories(self):
        c.publish(c.RUN/"manifest.json",{})
        c.publish(c.RUN/"selection.json",{"manifestSHA256":c.digest(c.RUN/"manifest.json"),
                  "hybrids":{"17":None,"29":None,"41":None},"artifacts":{},"weights":{}})
        with self.assertRaisesRegex(ValueError,"inventory"):
            c.verify_selection()

    def test_pair_projection_contains_no_labels_or_host_tags(self):
        lib={"id":"x","threads":["secret"],"items":[{"id":"x2","text":"second","memberships":["secret"]},
                                                        {"id":"x1","text":"first","rationale":"secret"}]}
        self.assertEqual(data.pairs([lib]),[{"id":"x1--x2","library":"x","first":"x1","second":"x2","texts":["first","second"]}])

    def test_baseline_keeps_same_class_winning_constraint(self):
        model={"scalerMean":[0]*6,"scalerScale":[1]*6,"coefficients":[[0]*6]*3,"intercept":[1,2,0]}
        row={"id":"p","library":"x","split":"calibration","first":"a","second":"b","relation":"same","features":[0]*10}
        result=models.baseline_score(model,[row])[0]
        self.assertFalse(result["eligible"])
        self.assertGreater(result["score"],0)

    def test_missing_feature_is_not_imputed(self):
        row={"id":"p","library":"x","split":"calibration","first":"a","second":"b","relation":"uncertain","features":[None]+[0]*9}
        self.assertFalse(models.usable(row))
        self.assertIsNone(models.baseline_score({},[row])[0]["score"])
        self.assertIsNone(models.hybrid_score({},[row],{"p":.5})[0]["score"])

    def test_hybrid_feature_order_and_clipped_logit(self):
        matrix=models.hybrid_matrix([{"id":"p","features":list(range(10))}],{"p":1.})
        self.assertEqual(matrix.shape,(1,11))
        self.assertTrue(np.array_equal(matrix[0,:10],np.arange(10)))
        self.assertAlmostEqual(matrix[0,10],np.log((1-1e-6)/1e-6),places=8)

    def test_hybrid_rejects_missing_oof_score(self):
        with self.assertRaises(KeyError):
            models.hybrid_matrix([{"id":"p","features":[0]*10}],{})

    def test_bootstrap_preserves_paired_family_draws_and_abstention(self):
        rows=[{"id":"a","library":"x","split":"evaluation","relation":"same","score":.9},
              {"id":"b","library":"y","split":"evaluation","relation":"same","score":.8}]
        families={"x":"one","y":"two"}
        result=models.bootstrap(rows,rows,{"baseline":.5,"hybrid":.5},families,samples=20)
        self.assertEqual(result["differences"]["precision"]["percentile95"],[0.,0.])
        self.assertEqual(result["differences"]["macroRecall"]["percentile95"],[0.,0.])
        result=models.bootstrap(rows,rows,{"baseline":.5,"hybrid":None},families,samples=20)
        self.assertEqual(result["differences"]["precision"]["undefined"],20)
        self.assertEqual(result["differences"]["macroRecall"]["percentile95"],[-1.,-1.])

    def test_bootstrap_rejects_mismatched_pair_coverage(self):
        row={"id":"a","library":"x","split":"evaluation","relation":"same","score":.9}
        with self.assertRaises(ValueError):
            models.bootstrap([row],[row|{"id":"b"}],{"baseline":.5,"hybrid":.5},{"x":"one"},samples=2)

    def test_diagnostic_slices_partition_without_changing_decisions(self):
        row={"id":"p","library":"x","split":"evaluation","first":"a","second":"b","relation":"same","score":.9}
        rows=[row,row|{"id":"q","relation":"related","first":"c"}]
        features=[r|{"features":[0]*10} for r in rows]
        items={k:{"text":"one two three four five six seven eight nine ten"} for k in ("a","b","c")}
        result=models.diagnostic_slices(rows,.5,features,items)
        self.assertEqual(result["challenge"]["pairs"],1)
        self.assertEqual(result["routine"]["pairs"],1)
        self.assertEqual(result["challenge"]["metrics"]["fp"],1)
        self.assertEqual(result["routine"]["metrics"]["tp"],1)
        self.assertEqual(rows[0]["score"],.9)

    def test_space_accounting_includes_pending_writes(self):
        with patch.object(c,"logical_bytes",return_value=1),patch.object(c.shutil,"disk_usage") as disk:
            disk.return_value.free=11*c.GIB
            self.assertTrue(c.capacity(1)["withinReserve"])
            self.assertFalse(c.capacity(2*c.GIB)["withinReserve"])
            self.assertFalse(c.capacity(4*c.GIB)["withinCap"])


if __name__=="__main__":
    unittest.main()
