# Checkpoint 1 complete — representation passes; quality not yet tested

17 September 2026. **Stopped for user review. Checkpoint 2 has not started.**

The provenance-first contract is representable using the existing production
ledger: a source can belong to multiple distinct projects; unresolved/independent
sources can retain singletons; revisions preserve history; user corrections and
archive/restore remain respected. Experiment-only suggestions do not change
production membership. No app behavior or production schema was changed.

## Results

| Check | Result |
|---|---:|
| Independently agent-reviewed fictional libraries | 24: 12 development, 12 evaluation |
| Chronological events prepared and replayed | 288 |
| Evidence-recovery tasks authored/reviewed | 96; retrieval not yet run |
| Native current-prefix state checks | 288/288 passed |
| Native historical-prefix reconstruction checks | 288/288 passed |
| Database close/reopen verification | 24/24 passed |
| Additional native ledger invariant checks | 31 passed |
| Python validation, isolation, resume and tamper tests | 55 passed |
| Actual compiler and native pause/resume | Passed; first receipts unchanged |
| Semantic model quality / calibration | Not measured in this checkpoint |

Both fixture splits contain all six source modalities as fictional extracted text.
Development has 104 captures, 8 corrections, 13 revisions, 11 archives and 8 restores.
Evaluation has 97 captures, 11 corrections, 12 revisions, 13 archives and 11 restores.
Each split has 12 unanswerable queries. All 24 alternative schedules were validated
as nontrivial; alternative-order native policy evaluation belongs to checkpoint 2
and was **not** counted in these 288 chronological checks.

## What review changed

Independent review found real label/contract defects before freeze: omitted equally
valid evidence, unknown-reference versus answerable-negative confusion, a shared
return record mislabeled as a single project, and missing causal dependencies.
Authors corrected them; independent reviewers re-reviewed the changed fixtures.
One evaluation scenario resembled exposed C5/C6 material and was replaced entirely.

Original snapshots, initial failures, author change logs and review rounds remain
saved. See [adjudication](ADJUDICATION.md) and `reviews/`. This is not a claim that
initial labels were all correct or that agent consensus is human ground truth.

## Saved implementation and evidence

- Contract, format, measurement definitions and two-checkpoint plan are versioned
  in this directory. `frozen.json` binds fixtures, reviews, snapshots and runner code.
- New scripts under `scripts/provenance-first/` validate fixtures, emit label-free
  prefix packets, compile ideal membership commands, checkpoint work and verify
  native results. No model inference/training or network API code was added.
- The isolated `ProvenanceFirstProbe` compiled current production persistence code
  and reused the unchanged existing ledger/invariant harness with local GRDB.
  It used its own fictional SQLite stores on the iOS 27 simulator, not the personal
  app or physical phone. Generated projects, stores and local state are ignored by
  the experiment's `.gitignore`; they remain available locally, not deleted.
- `native-verification.json` binds 24 successful replay receipts. Input SHA256:
  `a29435f6d0c3d9aecb4ad1af85ad187ef038f4eb335fec9535c10273795b791f`.
  Native binding SHA256:
  `b919968ceed2dd90ed59762e1336cbea7eb06920654cb42a1311b3eaf1fdca5d`.
- [Pause proof](PAUSE_PROOF.md) records unchanged hashes and mtimes from actual
  one-unit stops and resumes. [Resume instructions](RESUME.md) describe verification.
- Product documentation now states the provenance-first objective while clearly
  separating shipped D3 behavior from proposed River review and future research.

## Commands actually run

```sh
python3 -B -m unittest discover -s scripts/provenance-first -p 'test_*.py'
python3 -B scripts/provenance-first/checkpoint.py validate
python3 -B scripts/provenance-first/checkpoint.py freeze
python3 -B scripts/provenance-first/checkpoint.py run --max-libraries 1
python3 -B scripts/provenance-first/checkpoint.py pause
python3 -B scripts/provenance-first/checkpoint.py resume
python3 -B scripts/provenance-first/native_probe.py --max-runs 1 --invariants
python3 -B scripts/provenance-first/native_probe.py
python3 -B scripts/provenance-first/checkpoint.py verify-native
python3 -B scripts/provenance-first/checkpoint.py verify
python3 -B scripts/provenance-first/checkpoint.py resources
git diff --check
```

All final checks passed. Signed production app tests were not run: app code was
not changed by this work. The isolated unsigned simulator build succeeded using:

```sh
xcodebuild \
  -project Evaluation/ProvenanceFirst/runs/checkpoint1/ledger/project/ProvenanceFirstProbe.xcodeproj \
  -scheme ProvenanceFirstProbe -configuration Debug -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,id=C530FCC2-DD67-4115-97D9-C4E34807EC57' \
  -derivedDataPath Evaluation/ProvenanceFirst/runs/checkpoint1/ledger/build \
  -disableAutomaticPackageResolution -skipPackageUpdates -jobs 1 \
  CODE_SIGNING_ALLOWED=NO COMPILER_INDEX_STORE_ENABLE=NO build
```

The first dependency-preparation attempt rejected an incorrect assumed GRDB folder
layout before writing a project. The adapter was corrected to the actual cached
`Sources/GRDBSQLite` layout and tested against that package; subsequent preparation
and build passed. Code review also caught and corrected dependency-label leakage,
incomplete receipt verification, resume race handling and stale invariant identity.
Those fixes were completed and tested before the final freeze and native run.

## Limits and next decision

**This passes checkpoint 1's representation gate, not a model-quality gate.** The
96 query labels have not yet been scored against retrieval, and no claim is made
that the proposed system groups better, calibrates uncertainty, or improves UX.
The fixtures are controlled, short, English, agent-authored stories with explicit
identifiers and repeated high-level scaffolds. They do not measure actual media
extraction, natural personal-vault prevalence or real-user preferences. The old D3
qualification and FP16 compatibility limitations remain open.

No further representation repair is currently required. Recommended next step is
checkpoint 2: frozen D3 versus retrieval-assisted River suggestions and the
conservative relationship policy. Estimated **10–16 active hours, Mac only**,
subject to asset/runtime preflight. Stop again after its results; integration and
phone testing need a separate decision. Do not tune on evaluation labels or treat
this small screen as release qualification.

Final resource checks remained under the 4 GiB conservative new-write cap and well
above the 10 GiB free-space reserve. Experiment files were about 254 MiB, with
approximately 2.13 GiB registered simulator growth; conservative accounting also
includes unrelated volume free-space decreases. No artifacts were removed.
The scoped worker processes have exited and the test simulator is shut down.
**Progress is saved; it is safe to close the laptop.** No Git state was changed.
