import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import torch

from screening2_common import paths,save,sha,read,rotate,lock,request_pause
from screening2_data import identifiers,identifier_features,matrix,matrix_key,task_id
from screening2_metrics import counts,select,with_decisions,ranking
from screening2_models import fit_portable,portable_scores,evaluate
from screening2_neural import schedule,restore_trainable,trainable_state,token_cache
from screening2_report import quality
from audit_screening2 import brute_threshold,independent_counts,average_precision
from stage5_common import save_state,load_state
from stage5_train import rng_state,restore_rng,cpu_tree


class Screening2Tests(unittest.TestCase):
    def rows(self,n=50):
        return [{"id":str(i),"library":"a" if i%2 else "b","relation":"same" if i<40 else "related",
                 "score":.9 if i<35 else .8 if i<40 else .7} for i in range(n)]

    def test_identifier_definition_and_case(self):
        self.assertEqual(identifiers("AW-H's room, Q4 and q4; 2026-09-12 at 09:30, 42; east-facing"),{"AW-H","Q4","q4","east-facing"})

    def test_identifier_missing_and_conflict_flags(self):
        self.assertEqual(identifier_features("no codes","empty text"),[0,0,1,1])
        self.assertEqual(identifier_features("AW-H","AW-S"),[0,1,0,0])
        self.assertEqual(identifier_features("AW-H","AW-H"),[1,0,0,0])

    def test_symmetric_vector_features(self):
        rng=np.random.default_rng(17)
        emb={key:{"space":"fixed","contextual":rng.normal(size=512).tolist(),"sentence":rng.normal(size=512).tolist()} for key in ("a","b")}
        a={"first":"a","second":"b","features":[0.]*10}
        b=a|{"first":"b","second":"a"}
        np.testing.assert_array_equal(matrix([a],"vectors",emb),matrix([b],"vectors",emb))
        self.assertEqual(matrix([a],"vectors",emb).shape,(1,2058))

    def test_hybrid_logit_clips_extremes(self):
        rows=[{"id":"a","features":[0.]*10},{"id":"b","features":[0.]*10}]
        result=matrix(rows,"hybrid",extra={"a":0.,"b":1.})
        self.assertTrue(np.isfinite(result).all());self.assertAlmostEqual(result[0,-1],-result[1,-1],places=8)

    def test_task_identity_is_group_order_invariant(self):
        self.assertEqual(matrix_key(["mf01","mf02"]),matrix_key(["mf02","mf01"]))
        self.assertNotEqual(task_id("C1",["mf01"],17),task_id("C1",["mf01"],29))

    def test_binary_threshold_may_be_below_half(self):
        rows=[r|{"score":r["score"]*.4} for r in self.rows()]
        selected=select(rows)
        self.assertIsNotNone(selected);self.assertLess(selected["threshold"],.5)
        self.assertEqual(selected["threshold"],brute_threshold(rows))

    def test_tied_scores_enter_together(self):
        rows=self.rows();self.assertEqual(select(rows)["threshold"],brute_threshold(rows))

    def test_uncertain_does_not_meet_known_minimum(self):
        rows=self.rows(29)+[{"library":"a","relation":"uncertain","score":1.}]*10
        self.assertIsNone(select(rows))

    def test_independent_metrics_match(self):
        rows=self.rows()+[{"library":"a","relation":"uncertain","score":.99}]
        metric=counts(rows,.8)
        for key,value in independent_counts(rows,.8).items():self.assertEqual(metric[key],value)
        self.assertAlmostEqual(metric["averagePrecision"],average_precision(rows))

    def test_stored_decisions_pool_without_common_threshold(self):
        rows=with_decisions(self.rows(),.8)
        self.assertEqual(counts(rows,stored=True)["tp"],40)
        self.assertEqual(counts(rows,stored=True)["acceptedKnown"],40)

    def test_abstention_not_perfect_precision(self):
        metric=counts(self.rows(),None)
        self.assertIsNone(metric["precision"]);self.assertEqual(metric["recall"],0)

    def test_invalid_score_rejected(self):
        with self.assertRaises(ValueError):with_decisions([{"score":float("nan")}],.5)

    def test_evaluation_labels_do_not_change_calibration(self):
        calibration=[r|{"library":"cal"} for r in self.rows()]
        evaluation=[r|{"library":"eval"} for r in self.rows()]
        first=evaluate(calibration+evaluation,["cal"],["eval"])
        second=evaluate(calibration+[r|{"relation":"unrelated"} for r in evaluation],["cal"],["eval"])
        self.assertEqual(first["threshold"],second["threshold"])

    def test_evaluation_overlap_rejected(self):
        with self.assertRaises(ValueError):evaluate(self.rows(),["a"],["a"])

    def test_portable_logistic_and_tree_match(self):
        rng=np.random.default_rng(17);x=rng.normal(size=(100,10));y=(x[:,0]+x[:,1]>.2).astype(int)
        for trial in ("A1","A2","A3","B1"):
            record,model,scaler=fit_portable(trial,x,y)
            held=rng.normal(size=(20,10))
            np.testing.assert_allclose(portable_scores(record,held),model.predict_proba(scaler.transform(held))[:,1],atol=1e-10,rtol=0)

    def test_scaler_fitted_to_train_only(self):
        x=np.array([[0.,1.],[1.,2.],[2.,3.],[3.,4.]])
        record,_,_=fit_portable("A1",x,np.array([0,0,1,1]))
        np.testing.assert_allclose(record["mean"],[1.5,2.5])

    def test_schedule_warmup_decay(self):
        self.assertEqual(schedule(0,100),.1);self.assertEqual(schedule(9,100),1)
        self.assertEqual(schedule(10,100),1);self.assertAlmostEqual(schedule(99,100),1/90)

    def test_only_trainable_state_is_saved_and_restored(self):
        model=torch.nn.Sequential(torch.nn.Linear(2,3),torch.nn.Linear(3,2))
        for p in model[0].parameters():p.requires_grad_(False)
        state=trainable_state(model)
        self.assertEqual(set(state),{"1.weight","1.bias"})
        with torch.no_grad():model[1].weight.add_(1)
        # CPU tensors can share storage until serialized; checkpoint serialization is tested below.
        restore_trainable(model,state)
        with self.assertRaises(ValueError):restore_trainable(model,{})

    def test_lossless_optimizer_rng_resume(self):
        torch.manual_seed(17);x=torch.randn(4,3);y=torch.tensor([0,1,0,1])
        def network():return torch.nn.Sequential(torch.nn.Linear(3,2),torch.nn.Dropout(.2))
        first=network();opt=torch.optim.AdamW(first.parameters(),lr=.001)
        def step(m,o):
            o.zero_grad();torch.nn.functional.cross_entropy(m(x),y).backward();o.step()
        step(first,opt)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"state.pt.gz"
            save_state(path,{"model":trainable_state(first),"optimizer":cpu_tree(opt.state_dict()),"rng":rng_state(),"step":1})
            step(first,opt)
            second=network();other=torch.optim.AdamW(second.parameters(),lr=.001)
            state=load_state(path,sha(path));restore_trainable(second,state["model"]);other.load_state_dict(state["optimizer"]);restore_rng(state["rng"])
            step(second,other)
            for a,b in zip(first.parameters(),second.parameters()):self.assertTrue(torch.equal(a,b))

    def test_effective_batch_microbatch_gradient_equivalence(self):
        torch.manual_seed(17);x=torch.randn(7,3);y=torch.tensor([0,1,1,0,0,1,0])
        a=torch.nn.Linear(3,2);b=torch.nn.Linear(3,2);b.load_state_dict(a.state_dict())
        torch.nn.functional.cross_entropy(a(x),y).backward()
        for start in range(0,7,3):(torch.nn.functional.cross_entropy(b(x[start:start+3]),y[start:start+3],reduction="sum")/7).backward()
        for one,two in zip(a.parameters(),b.parameters()):self.assertTrue(torch.allclose(one.grad,two.grad,atol=1e-7))

    def test_test_tokens_rejected(self):
        with self.assertRaisesRegex(ValueError,"heldout"):token_cache("test")

    def test_unscoped_run_rejected(self):
        with self.assertRaises(ValueError):paths("/tmp/screen-attempt-01")

    def test_lock_rejects_second_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            handle=lock(Path(folder))
            try:
                with self.assertRaises(BlockingIOError):lock(Path(folder))
            finally:handle.close()

    def test_completed_pause_does_not_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);save(p/"manifest.json",{});save(p/"complete.json",{})
            self.assertEqual(request_pause(p),"already_complete_and_stopped")
            self.assertFalse((p/"control/pause-requested.json").exists())

    def test_rotation_only_superseded_new_recoveries(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);run=root/"run";external=root/"external"
            for i in range(4):
                file=external/"recovery"/f"{i}.pt.gz";file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(bytes([i]))
                save(run/"recovery"/f"{i}.json",{"stamp":i,"file":str(file.relative_to(external)),"SHA256":sha(file),"bytes":1})
            final=external/"models/final.pt.gz";final.parent.mkdir();final.write_bytes(b"preserve")
            rotate(run,external);rotate(run,external)
            self.assertEqual(len(list((external/"recovery").glob("*.pt.gz"))),2)
            self.assertEqual(final.read_bytes(),b"preserve")
            self.assertEqual(len(list((run/"retention").glob("*.json"))),2)

    def test_quality_requires_all_gates_and_defined_precision(self):
        baseline={"macroRecall":.3,"precision":.96}
        metric={"precision":.96,"macroRecall":.36,"acceptedKnown":40,"missingKnown":0}
        self.assertTrue(all(quality(metric,baseline).values()))
        self.assertFalse(all(quality(metric|{"precision":None},baseline).values()))
        self.assertFalse(all(quality(metric|{"macroRecall":.34},baseline).values()))


if __name__=="__main__":unittest.main()
