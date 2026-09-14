import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import experiment as e
import environment as env


def fixture():
    items = [{"id": f"mf01-i{i:02}", "text": f"Example source {i} with unique content"} for i in range(1, 21)]
    library = {"id": "mf01", "split": "train", "items": items}
    ids = [i["id"] for i in items]
    groups = [{"id": name, "members": ids[start:stop], "evidence": "Visible source evidence"}
              for name, start, stop in [("a", 0, 4), ("b", 4, 8), ("c", 8, 12), ("d", 12, 16)]]
    groups[0]["members"] += [ids[16], ids[17]]
    groups[1]["members"] += [ids[16]]
    groups[2]["members"] += [ids[17]]
    label = {"id": "mf01", "groups": groups, "relatedGroupPairs": [["a", "b"]],
             "ambiguous": [{"id": i, "reason": "No identifying context"} for i in ids[18:]], "issues": []}
    return library, label


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.library, self.label = fixture()
        self.inputs = {"schemaVersion": 1, "libraries": [self.library]}
        self.labels = {"schemaVersion": 1, "libraries": [self.label]}

    def test_input_allowlist(self):
        e.validate_inputs(self.inputs, complete=False)
        self.library["items"][0]["memberships"] = ["a"]
        with self.assertRaisesRegex(ValueError, "leaked"):
            e.validate_inputs(self.inputs, complete=False)

    def test_library_metadata_forbidden(self):
        self.library["domain"] = "spoiler"
        with self.assertRaisesRegex(ValueError, "forbidden"):
            e.validate_inputs(self.inputs, complete=False)

    def test_complete_count_required(self):
        with self.assertRaisesRegex(ValueError, "split counts"):
            e.validate_inputs(self.inputs)

    def test_wrong_split_rejected(self):
        self.library["split"] = "test"
        with self.assertRaisesRegex(ValueError, "split mismatch"):
            e.validate_inputs(self.inputs, complete=False)

    def test_out_of_range_source_id_rejected(self):
        self.library["items"][0]["id"] = "mf01-i99"
        with self.assertRaisesRegex(ValueError, "i01 through i20"):
            e.validate_inputs(self.inputs, complete=False)

    def test_duplicate_source_rejected(self):
        self.library["items"][1]["text"] = self.library["items"][0]["text"].upper()
        with self.assertRaisesRegex(ValueError, "duplicate normalized"):
            e.validate_inputs(self.inputs, complete=False)

    def test_hidden_context_id_rejected(self):
        self.library["items"][0]["text"] = "Task belongs to mf01-c1"
        with self.assertRaisesRegex(ValueError, "leaked"):
            e.validate_inputs(self.inputs, complete=False)

    def test_pair_class_counts_and_no_self_pairs(self):
        rows = e.pair_rows(self.library, self.label)
        self.assertEqual(len(rows), 190)
        self.assertEqual(len({(r["first"], r["second"]) for r in rows}), 190)
        self.assertTrue(all(r["first"] < r["second"] for r in rows))
        self.assertEqual({r["relation"] for r in rows}, {"same", "related", "unrelated", "uncertain"})
        self.assertEqual(sum(r["relation"] == "uncertain" for r in rows), 37)

    def relation(self, a, b):
        return next(r["relation"] for r in e.pair_rows(self.library, self.label)
                    if r["first"] == f"mf01-i{a:02}" and r["second"] == f"mf01-i{b:02}")

    def test_same_precedes_related(self):
        self.assertEqual(self.relation(1, 17), "same")

    def test_bridge_does_not_merge_contexts(self):
        self.assertEqual(self.relation(1, 5), "related")
        self.assertEqual(self.relation(1, 9), "unrelated")
        self.assertEqual(self.relation(1, 18), "same")
        self.assertEqual(self.relation(9, 18), "same")

    def test_related_not_transitive(self):
        self.label["relatedGroupPairs"].append(["b", "c"])
        self.assertEqual(self.relation(1, 9), "unrelated")

    def test_ambiguous_excluded_even_if_other_is_bridge(self):
        self.assertEqual(self.relation(17, 19), "uncertain")

    def test_ambiguous_cannot_have_membership(self):
        self.label["groups"][0]["members"].append("mf01-i19")
        with self.assertRaisesRegex(ValueError, "ambiguous group member"):
            e.validate_labels(self.inputs, self.labels)

    def test_missing_membership_fails(self):
        self.label["groups"][0]["members"].remove("mf01-i01")
        with self.assertRaisesRegex(ValueError, "coverage"):
            e.validate_labels(self.inputs, self.labels)

    def test_unknown_related_group_fails(self):
        self.label["relatedGroupPairs"] = [["a", "unknown"]]
        with self.assertRaisesRegex(ValueError, "invalid related"):
            e.validate_labels(self.inputs, self.labels)

    def test_duplicate_related_group_fails(self):
        self.label["relatedGroupPairs"].append(["b", "a"])
        with self.assertRaisesRegex(ValueError, "duplicate related"):
            e.validate_labels(self.inputs, self.labels)

    def test_duplicate_library_labels_fails(self):
        self.labels["libraries"].append(copy.deepcopy(self.label))
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            e.validate_labels(self.inputs, self.labels)

    def test_comparison_ignores_group_names(self):
        other = copy.deepcopy(self.labels)
        for g in other["libraries"][0]["groups"]:
            g["id"] = "renamed-" + g["id"]
        other["libraries"][0]["relatedGroupPairs"] = [["renamed-a", "renamed-b"]]
        self.assertEqual(e.compare(self.inputs, self.labels, other)["disagreementPairs"], 0)

    def test_comparison_detects_relatedness_difference(self):
        other = copy.deepcopy(self.labels)
        other["libraries"][0]["relatedGroupPairs"] = []
        result = e.compare(self.inputs, self.labels, other)
        self.assertGreater(result["disagreementPairs"], 0)
        self.assertEqual(result["disagreementLibraries"], 1)

    def test_review_blindness_required(self):
        with self.assertRaisesRegex(ValueError, "not blind"):
            e.validate_review(self.inputs, self.labels)
        review = {**self.labels, "reviewer": "a", "model": "unknown", "blindToAuthorLabels": True, "blindToPredictions": True}
        e.validate_review(self.inputs, review)

    def review(self):
        return {**copy.deepcopy(self.labels), "reviewer": "a", "model": "unknown",
                "blindToAuthorLabels": True, "blindToPredictions": True}

    def test_merge_binds_latest_source_revision(self):
        original = copy.deepcopy(self.inputs)
        self.library["items"][0]["text"] += " Revised source scope."
        merged = e.merge_reviews(self.inputs, [self.review(), self.review()], [original, self.inputs])
        self.assertEqual(merged["libraries"], self.labels["libraries"])

    def test_merge_rejects_unreviewed_source_change(self):
        original = copy.deepcopy(self.inputs)
        self.library["items"][0]["text"] += " Unreviewed change."
        with self.assertRaisesRegex(ValueError, "reviewed sources differ"):
            e.merge_reviews(self.inputs, [self.review()], [original])

    def test_merge_rejects_mixed_reviewers(self):
        other = self.review()
        other["reviewer"] = "b"
        with self.assertRaisesRegex(ValueError, "different reviewers"):
            e.merge_reviews(self.inputs, [self.review(), other], [self.inputs, self.inputs])

    def test_merge_rejects_missing_input_batch(self):
        with self.assertRaisesRegex(ValueError, "count mismatch"):
            e.merge_reviews(self.inputs, [self.review()], [])

    def test_superseded_review_still_requires_valid_coverage(self):
        invalid = self.review()
        invalid["libraries"][0]["groups"][0]["members"].remove("mf01-i01")
        with self.assertRaisesRegex(ValueError, "coverage"):
            e.merge_reviews(self.inputs, [invalid, self.review()], [self.inputs, self.inputs])

    def author(self):
        memberships, ambiguous, _ = e.library_truth(self.library, self.label)
        return {"schemaVersion": 1, "libraries": [{
            **copy.deepcopy(self.library), "domain": "fictional fixture", "templateFamily": "test fixture",
            "contexts": [{"id": g["id"], "description": g["evidence"]} for g in self.label["groups"]],
            "relatedContextPairs": self.label["relatedGroupPairs"],
            "items": [{**i, "memberships": sorted(memberships[i["id"]]),
                       "ambiguous": i["id"] in ambiguous, "rationale": "Fixture evidence"}
                      for i in self.library["items"]]}]}

    def amendment(self):
        item = self.library["items"][0]
        return {"schemaVersion": 1, "items": [{"id": item["id"],
                "originalTextSHA256": hashlib.sha256(item["text"].encode()).hexdigest(),
                "text": "A clarified fictional source with a continuing project scope.", "reason": "Clarify scope"}]}

    def test_amendment_projects_without_mutating_author(self):
        author = self.author()
        before = copy.deepcopy(author)
        inputs, _ = e.project([author], complete=False, amendments=self.amendment())
        self.assertEqual(inputs["libraries"][0]["items"][0]["text"], self.amendment()["items"][0]["text"])
        self.assertEqual(author, before)

    def test_amendment_wrong_original_hash_rejected(self):
        changes = self.amendment()
        changes["items"][0]["originalTextSHA256"] = "wrong"
        with self.assertRaisesRegex(ValueError, "original hash mismatch"):
            e.project([self.author()], complete=False, amendments=changes)

    def test_duplicate_amendment_rejected(self):
        changes = self.amendment()
        changes["items"] *= 2
        with self.assertRaisesRegex(ValueError, "duplicate amended"):
            e.project([self.author()], complete=False, amendments=changes)

    def test_review_may_merge_authored_workstreams(self):
        ids = [i["id"] for i in self.library["items"]]
        self.label["groups"] = [{"id": "one-project", "members": ids, "evidence": "All workstreams share a project"}]
        self.label["ambiguous"] = []
        self.label["relatedGroupPairs"] = []
        e.validate_labels(self.inputs, self.labels)
        self.assertTrue(all(p["relation"] == "same" for p in e.pair_rows(self.library, self.label)))

    def test_atomic_save_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "artifact.json"
            e.save(path, {"value": 1})
            with self.assertRaisesRegex(ValueError, "overwrite"):
                e.save(path, {"value": 2})
            self.assertEqual(e.read(path), {"value": 1})
            self.assertEqual(len(list(Path(tmp).iterdir())), 1)

    def test_failed_serialization_does_not_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "artifact.json"
            with self.assertRaises(ValueError):
                e.save(path, {"nan": float("nan")})
            self.assertFalse(path.exists())
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_frozen_change_detected(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(e, "ROOT", Path(tmp)):
            root = Path(tmp)
            e.save(root / "inputs.json", self.inputs)
            e.save(root / "freeze.json", {"schemaVersion": 1, "stage": 1, "files": {"inputs.json": e.sha(root / "inputs.json")}})
            self.assertTrue(e.verify_freeze(root / "freeze.json")["verified"])
            (root / "inputs.json").write_text("tampered")
            with self.assertRaisesRegex(ValueError, "mismatch"):
                e.verify_freeze(root / "freeze.json")

    def test_freeze_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(e, "ROOT", Path(tmp)):
            path = Path(tmp) / "freeze.json"
            e.save(path, {"schemaVersion": 1, "stage": 1, "files": {"../secret": "hash"}})
            with self.assertRaisesRegex(ValueError, "escapes"):
                e.verify_freeze(path)

    def test_model_asset_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            asset = workspace / "models" / "fixture.json"
            e.save(asset, {"fixture": True})
            manifest = {"workspaceRelativeDirectory": "models", "assets": {
                "fixture.json": {"bytes": asset.stat().st_size, "sha256": e.sha(asset)}}}
            self.assertEqual(env.verify_assets(workspace, manifest), 1)
            manifest["assets"]["fixture.json"]["sha256"] = "bad"
            with self.assertRaisesRegex(ValueError, "asset mismatch"):
                env.verify_assets(workspace, manifest)

    def test_model_asset_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = {"workspaceRelativeDirectory": "models", "assets": {
                "../secret": {"bytes": 0, "sha256": "bad"}}}
            with self.assertRaisesRegex(ValueError, "escapes"):
                env.verify_assets(Path(tmp), manifest)

    def test_model_directory_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "escapes workspace"):
                env.verify_assets(Path(tmp), {"workspaceRelativeDirectory": "../other", "assets": {}})


if __name__ == "__main__":
    unittest.main()
