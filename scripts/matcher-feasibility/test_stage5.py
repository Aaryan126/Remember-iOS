import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

from stage5_common import save_state,load_state,sha,authorize_test,save,paths
from stage5_data import order_for,class_weights,pair_inputs,batch_inputs,inputs_for
from stage5_evaluate import candidate_rank,quality_gates,paired_bootstrap
from stage5_train import rng_state,restore_rng,cpu_tree,apply_retention


class Stage5Tests(unittest.TestCase):
    def test_order_complete_reproducible_and_seed_epoch_specific(self):
        first=order_for(17,0,80)
        self.assertEqual(first,order_for(17,0,80))
        self.assertEqual(sorted(first),list(range(80)))
        self.assertNotEqual(first,order_for(29,0,80));self.assertNotEqual(first,order_for(17,1,80))

    def test_inverse_frequency_weights(self):
        self.assertEqual(class_weights([0,0,1,2]),[2/3,4/3,4/3])
        with self.assertRaises(Exception):class_weights([0,1])

    def test_test_split_sealed_without_selection(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            with self.assertRaisesRegex(ValueError,"sealed"):inputs_for("test",root)
            save(root/"selection.json",{"status":"no_qualifying_development_candidate","threshold":None})
            with self.assertRaisesRegex(ValueError,"qualifying"):authorize_test(root)

    def test_test_split_rejects_changed_winner(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);weights=root/"model";weights.write_bytes(b"changed")
            save(root/"selection.json",{"status":"selected","threshold":.8,"weights":str(weights),"weightsSHA256":"wrong"})
            with self.assertRaisesRegex(ValueError,"weights changed"):authorize_test(root)

    def test_checkpoint_round_trip_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/"checkpoint.pt.gz"
            value={"tensor":torch.arange(4),"position":{"epoch":1,"nextOffset":32},"rng":random.getstate()}
            save_state(path,value);digest=sha(path);actual=load_state(path,digest)
            self.assertTrue(torch.equal(actual["tensor"],value["tensor"]))
            self.assertEqual(actual["position"],value["position"]);self.assertEqual(actual["rng"],value["rng"])
            with self.assertRaises(Exception):save_state(path,value)
            with self.assertRaisesRegex(ValueError,"hash mismatch"):load_state(path,"wrong")

    def test_accumulated_weighted_loss_has_same_gradient(self):
        torch.manual_seed(17)
        x=torch.randn(7,4);y=torch.tensor([0,0,1,2,1,0,2]);weights=torch.tensor([.5,2.,1.])
        original=torch.nn.Linear(4,3);second=torch.nn.Linear(4,3);second.load_state_dict(original.state_dict())
        torch.nn.functional.cross_entropy(original(x),y,weight=weights).backward()
        denominator=(weights[y]*.5).sum()
        for start in range(0,7,3):
            loss=(torch.nn.functional.cross_entropy(second(x[start:start+3]),y[start:start+3],weight=weights,reduction="none")*.5).sum()/denominator
            loss.backward()
        for first,other in zip(original.parameters(),second.parameters()):self.assertTrue(torch.allclose(first.grad,other.grad,atol=1e-7))

    def test_dynamic_padding_preserves_input_and_order(self):
        tokens={"input_ids":torch.ones((4,512),dtype=torch.long),"attention_mask":torch.zeros((4,512),dtype=torch.long),
                "token_type_ids":torch.zeros((4,512),dtype=torch.long)}
        tokens["attention_mask"][0,:33]=1;tokens["attention_mask"][2,:120]=1
        value=batch_inputs(tokens,[2,0],"cpu")
        self.assertEqual(value["input_ids"].shape,(2,128));self.assertEqual(value["attention_mask"].sum(-1).tolist(),[120,33])

    def test_pairs_do_not_cross_libraries_or_include_metadata(self):
        doc={"libraries":[{"id":"a","items":[{"id":"a1","text":"first"},{"id":"a2","text":"second"}]},
                          {"id":"b","items":[{"id":"b1","text":"third"}]}]}
        self.assertEqual(len(pair_inputs(doc)),1)
        self.assertEqual(pair_inputs(doc)[0]["texts"],["first","second"])

    def test_candidate_tie_break(self):
        def row(seed,epoch):return {"seed":seed,"epoch":epoch,"selection":{"threshold":.9,"metrics":{"macroLibraryRecall":.5,"precision":.96}}}
        self.assertGreater(candidate_rank(row(17,1)),candidate_rank(row(29,1)))
        self.assertGreater(candidate_rank(row(41,1)),candidate_rank(row(17,2)))

    def test_quality_undefined_baseline_precision_never_passes(self):
        n={"allPairs":{"precision":.97,"acceptedKnownPairs":40,"macroLibraryRecall":.6,"missingPredictionPairs":0}}
        b={"allPairs":{"precision":None,"macroLibraryRecall":.3,"missingPredictionPairs":0}}
        gates=quality_gates(n,b,{"atLeastOneRecallAt10":.99})
        self.assertFalse(gates["precisionDrop"]);self.assertTrue(gates["macroRecallImprovement"])
        b["allPairs"]["precision"]=.98
        self.assertTrue(quality_gates(n,b,{"atLeastOneRecallAt10":.99})["precisionDrop"])
        b["allPairs"]["macroLibraryRecall"] = .55
        self.assertTrue(quality_gates(n,b,{"atLeastOneRecallAt10":.99})["macroRecallImprovement"])
        b["allPairs"]["precision"] = .981
        self.assertFalse(quality_gates(n,b,{"atLeastOneRecallAt10":.99})["precisionDrop"])

    def test_paired_library_bootstrap(self):
        a={"perLibrary":{"one":{"tp":4,"fp":0,"fn":1,"recall":.8},"two":{"tp":3,"fp":0,"fn":2,"recall":.6}}}
        result=paired_bootstrap(a,a,count=50)
        self.assertEqual(result["intervals"]["macroRecallDifference"]["lower"],0)
        self.assertEqual(result["intervals"]["precisionDifference"]["upper"],0)

    def test_reject_unscoped_run(self):
        with self.assertRaises(Exception):paths("/tmp/stage-5-attempt-01")

    def test_optimizer_and_dropout_rng_resume_matches_uninterrupted_step(self):
        torch.manual_seed(17)
        x=torch.randn(4,3); y=torch.tensor([0,1,0,1])
        def model():return torch.nn.Sequential(torch.nn.Linear(3,2),torch.nn.Dropout(.2))
        first=model(); optimizer=torch.optim.AdamW(first.parameters(),lr=.001)
        def step(network,opt):
            opt.zero_grad();torch.nn.functional.cross_entropy(network(x),y).backward();opt.step()
        step(first,optimizer)
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/"recovery.pt.gz"
            save_state(file,{"model":cpu_tree(first.state_dict()),"optimizer":cpu_tree(optimizer.state_dict()),"rng":rng_state()})
            step(first,optimizer)
            restored=model();restored_optimizer=torch.optim.AdamW(restored.parameters(),lr=.001)
            saved=load_state(file,sha(file));restored.load_state_dict(saved["model"]);restored_optimizer.load_state_dict(saved["optimizer"]);restore_rng(saved["rng"])
            step(restored,restored_optimizer)
            for a,b in zip(first.parameters(),restored.parameters()):self.assertTrue(torch.equal(a,b))

    def test_retention_needs_explicit_policy_and_keeps_latest_two(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder)/"run";external=Path(folder)/"external"
            for index in range(4):
                file=external/"recovery/seed-17"/f"state-{index}.pt.gz";file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(bytes([index]))
                save(run/"recovery/seed-17"/f"{index}.json",{"globalStep":index,"savedAtNS":index,"file":str(file.relative_to(external)),"SHA256":sha(file),"bytes":1})
            self.assertEqual(apply_retention(run,external,17),0)
            save(run/"control/retention-policy.json",{"policy":"latest-two","explicitUserAuthorization":"test only: authorized isolated temporary fixture cleanup"})
            self.assertEqual(apply_retention(run,external,17),2)
            self.assertEqual(len(list((external/"recovery/seed-17").glob("*.pt.gz"))),2)
            self.assertEqual(len(list((run/"recovery/seed-17").glob("*.json"))),4)
            self.assertEqual(apply_retention(run,external,17),0)


if __name__=="__main__":unittest.main()
