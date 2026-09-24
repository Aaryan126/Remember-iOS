# Checkpoint-1 resume and safety

Only checkpoint 1 is authorized to run now. Stop after its report; checkpoint 2
requires a separate user review. All commands run from the repository root.
Use `python3 -B` to avoid bytecode caches. Never perform Git writes.

## Authoring / review

Read CONTRACT.md, FORMAT.md and PLAN.md. Author files are `authored/development.json`
and `authored/evaluation.json`. Snapshot before review or substantive fixes:

```sh
python3 -B scripts/provenance-first/checkpoint.py snapshot
python3 -B scripts/provenance-first/checkpoint.py validate
python3 -B -m unittest discover -s scripts/provenance-first -p 'test_*.py'
```

Keep original review artifacts; final `reviews/development.json` and
`reviews/evaluation.json` must bind the current authored-file bytes, name the actual
author/reviewer, and have no unresolved errors. Preserve correction rationale and
re-review changed substantive labels. Root adjudication must not see predictions.

## Freeze and resumable compilation

```sh
python3 -B scripts/provenance-first/checkpoint.py resources
python3 -B scripts/provenance-first/checkpoint.py freeze
python3 -B scripts/provenance-first/checkpoint.py run --max-libraries 1
python3 -B scripts/provenance-first/checkpoint.py pause
python3 -B scripts/provenance-first/checkpoint.py resume
python3 -B scripts/provenance-first/checkpoint.py verify
```

The first one-library run exercises pause/resume. Compare its receipt bytes/hash
and mtime before/after resume. Frozen fixture, code, and review hashes cannot silently
change. A compiler receipt is not a native ledger receipt. Source-only traces omit
gold and dependency graphs; future consumers must use `observed_packet` to restrict
every query to its actual observed prefix. Full traces are replay inputs, not prompts.

## Native replay

The isolated app has bundle ID `SimpleStudio.Remember.ProvenanceFirstProbe`.
Prepared project: `runs/checkpoint1/ledger/project/ProvenanceFirstProbe.xcodeproj`.
Build artifacts and logs: `runs/checkpoint1/ledger/`. Its sources are hash-bound
links to current production files and the unchanged existing replay harness.
No production app entry point, model assets, credentials or personal vault is used.

Use only the registered simulator `C530FCC2-DD67-4115-97D9-C4E34807EC57` (iOS 27
iPhone 17 simulator, **not the physical phone**). Local GRDB is reused from the
existing safeguards experiment. No dependency or simulator runtime downloads.
Prepare/build commands and any failures are recorded in the checkpoint report.

Launch with the compiled `runs/checkpoint1/input.json`, output directed to
`runs/checkpoint1/output`, and `--max-runs 1 --invariants` for the first native unit.
If Desktop access requires a private copy, stage only this fictional generated JSON
under this app's `Documents/ProvenanceFirst/`; verify identical bytes. Resume with
identical input/build/output and without the run limit or invariant rerun. Existing
receipts must remain unchanged. Preserve failed attempts; never count them complete.

The coordinator stages only fictional JSON and records launch commands and logs:

```sh
python3 -B scripts/provenance-first/native_probe.py --max-runs 1 --invariants
python3 -B scripts/provenance-first/native_probe.py
```

Do not launch the app through a second command while this coordinator holds its
worker lock. It checks resource growth during replay and requests a library-boundary
pause on interruption; incomplete attempts remain uncounted.

`checkpoint.py pause` writes both compiler and native pause markers. Native replay
finishes its current library, closes SQLite, publishes a receipt and exits. The
coordinator must check build/native processes and save active agent work before
confirming safe to close. `status` deliberately never infers global safety merely
because the compiler lock is free. Resume moves pause markers aside under the
compiler lock after hash verification; native restart is a separate explicit action.

```sh
python3 -B scripts/provenance-first/checkpoint.py verify-native
python3 -B scripts/provenance-first/checkpoint.py resources
```

The native verifier checks every receipt, ledger hash, prefix/restart count,
production/harness/dependency binding, and invariant receipt. It does not measure
semantic quality. Do not run checkpoint-2 models to fill in that missing claim.

## Resource limits

At most 4 GiB new artifacts and at least 10 GiB free, including the registered
simulator's growth. `resources.json` records the starting point; resource checks use
both allocated files and conservative free-space change. If a cap is reached, stop
and report; no automatic cleanup, budget extension or repository changes.
