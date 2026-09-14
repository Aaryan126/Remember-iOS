# Isolated production ledger replay

This harness compiles unchanged production `MemoryStore`, `ProvenanceSnapshot`, correction APIs, and their dependency sources into a separate simulator app. It never opens `MemoryStore.live()`, initializes the normal app, invokes a model, reads originals, or accesses a personal vault. Source text is fictional fixture evidence. No production project edits are required.

The JSON input is schema version 1 with `runs: [{id, events: [...]}]`. Commands are `capture`, `revise`, `correct`, `archive`, and `restore`; every command includes a complete independent `expectedState` mapping source IDs to `memberships`, `archived`, `textSHA256`, and zero-based `revision`. Captures include `{id,text,modality}` under `source`. Other commands use `target`; revisions also use `text`; captures optionally and corrections always use nonempty `assignments`. Text hashes use exact UTF-8. Revisions fail if production `NoteDocument` normalization changes those bytes.

Source `localc01` and singleton thread `t:c01` map to the same deterministic UUID because production creates a source-UUID singleton. Other runtime thread IDs are independently hashed. Each run creates its own UUID-named attempt directory and SQLite store. No semantic gold or scorer runs inside this harness.

Fixture modality names `note`, `voice`, and `file` map to production `text`, `audio`, and `pdf`; production modality names are also accepted. This adapter stores the supplied fictional extracted text and does not open or extract media files.

Each policy prefix checks assignments, archive state, text bytes, revision count/chain, pinned corrections, visible/active projections, materialized SQLite memory fields, immutable ledger history, unique ordered events, and valid references. On completion it closes/reopens the SQLite pool and checks reconstruction, then replays every historical prefix against its saved oracle. Date comparisons allow SQLite's millisecond serialization precision; other memory fields compare exactly. Captures may generate capture plus placement ledger events within a single policy prefix. Policies cannot emit merge/split actions.

`--invariants` additionally runs separate explicitly commanded merge/undo, split/undo, split proposal immutability, stale decision rejection, archive/restore, idempotency, SQLite append-only trigger, unrelated correction preservation, and restart checks. These fixtures do not contribute semantic grouping scores.

## Prepare and coordinate a single worker

Run preparation only after the root coordinator confirms resource availability. Preparation does not build or start a simulator. It rejects existing output paths, binds production files by symlink, hashes source/dependency bindings, and requires an already cached local GRDB package. Do not edit source bindings between preparation and build; regenerate in a new directory if any bound source changes.

```sh
python3 scripts/organization-diagnostics/ledger/prepare_project.py \
  --output Evaluation/OrganizationDiagnostics/runs/c2-01/ledger/project \
  --grdb-package /private/tmp/RememberProvenance/SourcePackages/checkouts/GRDB.swift
```

The coordinator must enforce the checkpoint's combined 4 GiB new-write cap and 10 GiB free-space floor, including build/simulator writes outside this directory. Anticipated ledger artifacts are below 300 MiB for 288 runs; build/runtime costs must be measured. Existing simulator runtime must already be installed. No download, phone, automatic cleanup, Git action, or new model is authorized by this helper.

Build only after coordination, supplying the approved simulator UUID:

```sh
xcodebuild -project Evaluation/OrganizationDiagnostics/runs/c2-01/ledger/project/OrganizationLedgerProbe.xcodeproj \
  -scheme OrganizationLedgerProbe -configuration Debug -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,id=APPROVED_SIMULATOR_UUID' \
  -derivedDataPath Evaluation/OrganizationDiagnostics/runs/c2-01/ledger/build \
  -disableAutomaticPackageResolution -skipPackageUpdates -jobs 1 \
  CODE_SIGNING_ALLOWED=NO COMPILER_INDEX_STORE_ENABLE=NO build
```

Install only the isolated app with bundle ID `SimpleStudio.Remember.OrganizationLedgerProbe`. Obtain its own data container with `xcrun simctl get_app_container APPROVED_SIMULATOR_UUID SimpleStudio.Remember.OrganizationLedgerProbe data` and copy the fictional input JSON into `Documents/OrganizationDiagnostics/` beneath that container. Preserve its exact bytes and compare its hash to the source. This avoids macOS Desktop privacy prompts when the simulator app opens a host-authored file. Include this temporary input copy in storage accounting.

Launch with `--input ABSOLUTE_PRIVATE_TRACE_JSON --output ABSOLUTE_RECEIPT_DIRECTORY --invariants`; output must be beneath `Evaluation/OrganizationDiagnostics/runs/`. The harness also accepts input beneath that workspace if host permissions already allow it. Add `--max-runs 1` for an interruption/recovery exercise. The app exits when finished; `status.json` is the authoritative completion/paused result and failures also print `LEDGER_REPLAY_FAILED`. The tiny fixture from `smoke_fixture.py` contains two independent six-prefix runs; smoke artifacts are separate from policy results.

## Pause and resume

Each run is a bounded unit. Either launch with `--max-runs N` or create `pause.request` in the output directory. The app completes the current run, closes its SQLite pool, atomically publishes its receipt, writes paused status, and exits before the next unit. Resume uses exactly the same input/output/bindings and omits the run limit; the coordinator must move the pause marker aside first if one exists. A receipt is published only after ledger evidence is durable and the pool closes. Resume validates command, batch, binding, and saved ledger hashes before skipping a completed run. Incomplete attempts remain for inspection and are retried in a fresh directory. There is no automatic cleanup. `status.json` is marked complete only after all runs have valid receipts.

Database reconstruction is verified while running; resumed receipts verify the saved JSON ledger hash. Preserved SQLite files are evidence, not trusted resume inputs. A process interruption before receipt publication never counts that run complete.

Validation without builds: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/organization-diagnostics/ledger -p 'test_*.py'`.
