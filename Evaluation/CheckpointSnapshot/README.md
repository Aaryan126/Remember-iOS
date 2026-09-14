# Preparation checkpoint — 2026-09-13

P2 is complete and not qualified. No new diagnostic, training, app integration or phone test is started by this checkpoint. **Stop for the user to make their own Git checkpoint and confirm before proceeding.** Repository rules prohibit agents from changing Git state.

## What is saved

- Source code, tests, fictional inputs, labels, split definitions, reviews, protocols, model version manifest and existing small checkpoint reports remain versionable.
- [Final P2 results](../MatcherValidation/P2_REPORT.md) summarize the completed evaluation without retrospectively changing its gates.
- [The generated snapshot](2026-09-13.json) contains selected receipt/file hashes, exact P2 metrics, and compact inventories of excluded raw directories. It does not contain model weights, device identifiers, console output, absolute machine paths or raw predictions.
- [Next plan](NEXT_PLAN.md) specifies the two future diagnostic checkpoints and their stop conditions.
- [Validation record](VALIDATION.md) lists completed checks and their limitations.

Raw runs, local environment discovery, setup attempts, weights, logs, Xcode test output and database sidecars are ignored in place. Nothing was deleted. The P0/P1 preparation and review records under `MatcherValidation/runs/` are deliberately **not** excluded. Adding ignore rules does not remove already tracked files.

## Restore requirements — a commit is not a complete backup

The snapshot is an inventory, **not a backup**. A fresh checkout alone cannot verify or resume the previous experiments. Before deleting local data or moving computers, the user must separately back up:

1. Every directory listed in `rawDirectories` in the snapshot, plus `Evaluation/MatcherFeasibility/environment.json`. Preserve their original repository-relative locations, including failed attempts.
2. The existing `RememberMatcherFeasibility/v1` workspace under the user's Library Application Support. This contains model/tokenizer assets, converted models, neural exports, cached tensors, recovery states and the Python environment. Its full contents are not copied or hashed by this compact snapshot. Original completion receipts bind the relevant external artifacts; those verifiers remain authoritative.
3. Any local secrets/configuration needed for unrelated app workflows, through a private backup, never through Git. No secrets are required for the new offline diagnostic.

The pinned base model and tokenizer versions/hashes are in `../MatcherFeasibility/model-manifest.json`; dependencies are in `../MatcherFeasibility/environment.lock.txt`. Rebuilding the environment may be necessary on another Mac. Existing experiment scripts also encode local paths and platform assumptions: restore requirements are documented, not a claim of portable one-command replay. Re-training missing weights is a new run, not restoration of the original result.

Directory fingerprints hash sorted records `[relativePath, byteLength, SHA256]`, compact JSON plus newline per record, excluding only worker locks, `.DS_Store` and Python bytecode directories. They detect changed, added or missing evidence; they do not reconstruct files. No timestamps are used. Keep original completion receipts with the backups for per-file and external-model verification.

## Commands

From the repository root, using Python 3.9 or newer:

```sh
python3 -m unittest discover -s scripts -p test_evaluation_snapshot.py -v
python3 scripts/evaluation_snapshot.py verify
```

`verify` is read-only and fails if excluded artifacts are absent or different. It checks the saved local inventory and metrics, not scientific validity or model weights. `publish` creates a snapshot only when absent; it never overwrites a differing snapshot. Preserve this dated record and investigate mismatches instead of regenerating historical evidence.

The original P0/P1/P2 and screening verification commands remain in their respective resume documents. Do not run training or `prepare` to repair a verification failure. No phone is needed for this checkpoint or the next two diagnostic checkpoints.
