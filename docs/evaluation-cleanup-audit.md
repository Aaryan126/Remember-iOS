# Cleanup audit and evaluation findings — 24 September 2026

## Status and scope

The user authorized the recommended evaluation batches A–C after the initial low-risk cleanup. **Both cleanups are complete.** A–C removed 84 exact targets totaling **2.783 GiB**; optional batch D (the FP32 package) was retained. See [the high-level summary](evaluation-cleanup-summary.md) for a short account of deletions and failed experiments.

Deleted **1.106 GiB (1132.07 MiB)** across 65 directory/file targets: Xcode intermediates/caches, Python bytecode caches, OS metadata, and the root `.venv`. No tracked file was a deletion target. App file hashes and the complete versionable working-file status matched before and after deletion. No Git state was changed. The dedicated matcher environment outside this repository was not touched.

The directory measured approximately **6.76 GiB** after cleanup. Sizes are allocated-file estimates, not a guarantee of physical free-space gain on a filesystem with clones or snapshots.

## Completed recommended batches

Keep compact reports for **all** outcomes, including failures and mixed results. Retain raw evaluation evidence where it supports the current app or a useful future direction. Retire redundant recordings, intermediate predictions and duplicate assets first. A successful technical run does not automatically mean a successful model.

| Batch | Reviewed removal | Allocated size | Consequence |
| --- | --- | ---: | --- |
| A | Superseded search recordings and test bundles | 774.93 MiB | Retain final source-matched tests, traces and recording; lose detailed recordings/attachments for earlier trials. |
| B | Older research outputs and intermediate benchmark archives | 1181.42 MiB | Retain reports, protocols, fixtures, aggregate results and selected final raw results; full historical audits using removed inputs will no longer run. |
| C | 14 identical model packages in retired projects/snapshots | 892.99 MiB | Retain source snapshots and production/latest-deployment models; archived projects require their model to be restored before rebuilding. |
| D | Unshipped experimental FP32 model package | 127.41 MiB | Current app stays on FP16; repeating FP32 experiments would require re-export from the original checkpoint. |

**Deleted A–C: 2.783 GiB. Retained D: 127.41 MiB.** Combined with the earlier cache cleanup, approximately **3.89 GiB** of allocated files were removed. Targets do not overlap. Exact paths are listed below; phone backups, production model assets, final retained test evidence and surrounding evaluation directories were preserved.

Batch D was not included in the recommendation that the user approved. The FP32 package remains available: it was a useful precision diagnostic, not simply a failed model.

## What was tried and what happened

| Study | Finding to preserve | Retention decision |
| --- | --- | --- |
| [Early MiniLM conversion](../Evaluation/MatcherFeasibility/checkpoints/stage-3.md) | Attempt 01 had empty-pair tokenizer mismatch; attempt 02 had non-finite FP16 output. Attempt 03 succeeded after tokenizer correction and a finite additive mask. | Deleted attempts 01/02; retained accepted attempt 03 and checkpoint reports. |
| [Phone feasibility](../Evaluation/MatcherFeasibility/checkpoints/stage-4.md) | Accepted stage-4 attempt 02 passed 416 original-output parity cases; measured p95 ten-pair latency 85.3 ms at 256 tokens and 257.9 ms at 512 tokens. These are probe feasibility results, not current-app accuracy. | Retain accepted raw device run and report. |
| [Early specialist training](../Evaluation/MatcherFeasibility/checkpoints/stage-5.md) | Nine candidates; none met 95% development precision with at least 30 accepted known pairs. Highest-precision diagnostic was 94.12% precision / 19.59% recall, below the frozen baseline. Test evaluation was skipped. | Retain summary/audit reports and fixtures; remove bulky per-candidate evaluation outputs. |
| [Matcher screening](../Evaluation/MatcherScreening/checkpoints/stage-2.md) | Standalone MiniLM failed all confirmation seeds. Hybrid seed 29 passed but seeds 17/41 failed the permitted precision-drop gate; neither family qualified across all seeds. Development was reused, so attractive confirmation figures are not fresh held-out evidence. | Remove specified prediction/ablation/diagnostic directories; retain screen selection, confirmation results, summaries, completion/audit receipts and reports. |
| [P2 validation](../Evaluation/MatcherValidation/P2_REPORT.md) | Seed 29 reached 95.79% pair precision / 58.39% library-macro recall; seeds 17/41 failed precision, so the all-seeds family failed qualification. Seed 29 was later integrated experimentally; do not rewrite that as a qualified production result. | Keep **all** `MatcherValidation/runs/validation-02`, releases, reports and export dependencies for now. |
| [C2 organization policy](../Evaluation/OrganizationDiagnostics/c2/REPORT.md) | Corroborated attachment reduced wrong attachments but increased fragmentation. Ledger execution and semantic grouping quality are different checks. | Retain traces, metrics, neural caches, inputs and receipts. Removed only bulky fictional ledger replay stores in `ledger/results`. |
| [C3 matched-policy comparison](../Evaluation/OrganizationDiagnostics/c3/REPORT.md) | Hybrid benefit survived matched corroboration controls. Seed 29 final grouping precision/recall was 75.2%/34.5%, versus baseline 69.4%/24.5%; wrong attachment counts were 54 versus 55 out of 360. Absolute grouping quality remained weak. | Keep online trajectories, metrics and report; retire repeated fixed-state counterfactual outputs. |
| [C4 repair proposals](../Evaluation/OrganizationDiagnostics/c4/REPORT.md) | Useful fragment reconnection did not reliably repair mixed threads. Simulated gold-assisted acceptance is not proposal correctness. No automatic repair shipped. | Keep `c4/REPORT.md`, `summary.json`, `complete.json`, inputs and scripts; retire per-context proposals/metrics. |
| [C5/C6 boundary preparation and stress test](../Evaluation/OrganizationDiagnostics/c6/REPORT.md) | C5 prepared material rather than measuring accuracy. C6 found false same-project judgments on explicit boundaries; the rule prototype abstained on all natural-prose packets. No integration candidate emerged. | Keep the small datasets, reviews and results: the cloud pilot reuses these controls. |
| [C7 local semantic verifier](../Evaluation/OrganizationDiagnostics/c7/REPORT.md) | Failed four of five exploratory gates, including ambiguity handling and errors. No integration. Read its runtime [erratum](../Evaluation/OrganizationDiagnostics/c7/ERRATA.md) alongside the report. | Keep compact result/raw evidence; only a few MiB, useful counterexample to the cloud pilot. |
| [Cloud reviewer pilot](../Evaluation/CloudMatcher/pilot-01/REPORT.md) | Context-rich diagnostic: 93.5% same-project precision / 90.6% recall; D3+confirmation 95.7% precision / 68.8% recall. Exposed synthetic pair-level data, not production grouping validation. | Keep the entire ~4 MiB pilot and its C6/C7 comparison material. Promising future direction, not shipped behavior. |
| [Original organization benchmark](evaluations/2026-09-10-organization-benchmark.md) | Final core run completed 144 scenarios. Earlier paused/resumed/pre-checkpoint-fix archives are partial or superseded. Media extraction completion did not prove transcript accuracy; larger scale runs did not complete. | Keep final core archive/score, decisions/media/public archives, scale terminal archive/log and all small scores; remove only listed intermediate archives. |
| [Provenance foundation](../Evaluation/ProvenanceFirst/REPORT.md) | Ledger integrity and replay checks passed. This established history preservation, not better grouping or answer relevance. | Keep checkpoint-1 data, fixture reviews and successful integrity evidence. |
| [Runtime qualification](../Evaluation/ProvenanceFirst/checkpoint2/runtime-qualification/REPORT.md) | 6/88 scores exceeded the numerical tolerance despite 0/264 changed threshold decisions. Numerical qualification remained failed. | Keep small control results and selection; do not equate unchanged decisions with numerical identity. |
| [Provenance A/B/C comparison](../Evaluation/ProvenanceFirst/checkpoint2/comparison/REPORT.md) | Neither B nor C qualified. Evidence recall improved from 47.22% to 56.94% while outside-suggestion precision stayed very poor; history integrity passed separately. | Keep scored comparison results, fixtures and aggregate/native-verification receipts. Retire only repeated fictional simulator output stores under `runs/current-runtime-comparison/output`. |
| [History recovery](../Evaluation/ProvenanceFirst/history-recovery/REPORT.md) | Version-aware coverage/integrity passed. [Ranking checkpoint](../Evaluation/ProvenanceFirst/history-recovery/checkpoint2/REPORT.md): no candidate qualified; restrictive filters lost too much coverage. | Keep compact results and successful coverage evidence. The failed ranking run is small enough to keep in this batch. |
| [Local answer support](../Evaluation/ProvenanceFirst/answer-support/REPORT.md) | Original answer-form technical control failed. [Format v2](../Evaluation/ProvenanceFirst/answer-support-format-v2/REPORT.md) passed 8/8 small technical controls, but this was not benchmark quality. [Stage B](../Evaluation/ProvenanceFirst/answer-support-screen/REPORT.md) then failed: 9/25 accepted-answer precision, 9/32 end-to-end correct, 3/32 unsupported assertions; held-out inference was not run. | Preserve failure summaries and compact raw outputs. Do not retain only the successful format controls and omit the later semantic failure. These are not proposed for blanket removal. |
| [iOS 27 reviewer screen](../Evaluation/iOS27/quality-continuation/REPORT.md) | Tested C7/boundary reviewers and combined policies failed the safety gate; no reviewer/veto/split path shipped. | Keep reports and compact challenge results; no blanket iOS27 deletion. |
| [FP32 conversion](../Evaluation/iOS27/precision/REPORT.md) | Closer original-PyTorch numerical agreement, unchanged 16 reference decisions, roughly double storage and 2.36× phone warm inference time. Current production remains FP16. | FP32 package, conversion/reference results and export script retained; optional deletion was not executed. |
| [Search UI iterations](../Evaluation/ProvenanceFirst/search-handoff/OPENING-FOLLOWUP.md) | Transparent backing/direct attachment/invisible retained layout could fix opening while regressing closing. Geometry/compositing trials failed opening; competing scroll hosts also stalled tests. Final solution used one persistent scroll owner plus a transaction scoped to results presence; final targeted unit/UI and geometric checks passed. | Keep final passing artifacts listed below and failed-trial report; remove earlier recordings and selected old result bundles. |

## Evidence and assets to retain

- Entire `Remember/` tree, including the production FP16 package, vocabulary, parameter JSON, attribution, tests and fixtures. No source-code removal is part of this cleanup.
- `Evaluation/AppMatcher/`: export inputs, conversion and native-parity records.
- `Evaluation/MatcherValidation/runs/validation-02/`, `MatcherValidation/releases/`, `MatcherFeasibility/model-manifest.json`, environment lock and accepted stage-3/stage-4 runs. Export reads `hybrid-29.json`, `tfidf.json`, `evaluation/seed-17.json`, corresponding saved embeddings and release inputs. External trained weights, base-model assets and the dedicated venv live under `~/Library/Application Support/RememberMatcherFeasibility/v1`; they were not deleted or audited for cleanup here.
- All `scripts/` source files: these occupy only a few MiB and share helpers across experiments. Deleting old-looking script directories wholesale risks breaking the D3 export or current test/deployment wrappers.
- All small report/protocol/summary/score/selection/review/fixture files outside the exact candidate targets. Keep original reports in place as well as this index.
- `Evaluation/CloudMatcher/`, C6/C7 comparison data, C2 traces/metrics, C3 online/metrics, provenance checkpoint-1/history coverage evidence, and scored checkpoint-2 comparison results.
- Latest search unit result `search-handoff/1790249130721671000.xcresult` (6/6) and UI result `1790249157837450000.xcresult` (11/11); also retained preceding successful closing results `1790246282358974000`, `1790246321537451000`, and scrolled-regression result `1790249006959958000`.
- Search `opening-final-top` and `opening-final-scrolled` traces/events, all current frame-review images, and `opening-final-regression.mp4`. The final video is approximately 208 MiB and intentionally retained.
- Entire latest `Evaluation/ProvenanceFirst/runs/search-opening-deployment/`: source-matched signed build/project, installation and physical-smoke receipts, preservation receipts and pre/post phone backups.
- All other phone `backup-*` and `post-install-*` directories. They are recovery data, not disposable test fixtures. No proposed target contains one.
- Final organization `core-complete-2026-09-11.json.gz` and its score, `decisions-2026-09-10.json.gz`, media-reference/media-extracted/public archives, `scale-terminal-2026-09-11.json.gz`, scale console log and incident documentation.

The older search-handoff report includes appended historical “not installed yet” sections. The later opening follow-up and [24 September deployment report](../Evaluation/ProvenanceFirst/search-opening-deployment/REPORT.md) establish the latest recorded state. No new build or phone installation was performed for this cleanup.

## Effect on historical reproduction

The app runtime does not read the deleted evaluation paths. Deletion retired historical replay/audit inputs and old project resources. **Full historical verification is no longer available for commands requiring these deleted paths.** This includes old screening/stage-3 failure/stage-5 audits, C2 ledger-store verification, C3 fixed-state replay, C4 per-context replay, provenance comparison store verification, checkpoint inventory audits, and older UI runs. Selected final results and their reports remain.

The exact allowlist was rechecked before deletion, including size comparison within the proposal's rounding interval and fresh model-package hashes. Original summaries and frozen manifests were left unchanged. Historical raw links matching the A–C inventory below are now retired; their absence is intentional, not evidence of a new evaluation failure. This document records the retention change rather than modifying historical hashes or claiming old verification still passes. A future fresh evaluation is distinct from reproducing a historical run, especially across Apple model/runtime changes.

All 14 deleted duplicate packages were compared again against the production package using SHA-256 for every package file, not just file size. Every package matched. Their surrounding source snapshots remain. These retired projects need an identical model package supplied again before rebuilding. The production and latest-deployment models were excluded.

## Validation of the initial cache cleanup

- Read-only process inspection before deletion: no xcodebuild, Swift frontend, clang build, or root-venv process was detected. Xcode itself was open.
- Deletion allowlist checked against `git --no-optional-locks ls-files -z`: no tracked deletion targets.
- SHA-256 comparison of app-tree file contents before/after cleanup: identical (excluding intentionally removed OS/cache metadata).
- `git --no-optional-locks status --porcelain=v1 -uall` before/after cleanup: identical. The new audit document is the only subsequently added source document.
- All 65 deletion targets absent immediately afterward.
- Proposed evaluation targets checked for existence, nonoverlap, separation from protected retained paths and absence of phone backup targets.
- Production model and retained D3 checkpoint/parameter reference files present.
- Python AST parsing of `server/openai_proxy.py` and `scripts/app-matcher/export_d3.py`: passed without executing either program or creating bytecode.
- The four following saved-trace checks passed after cleanup. These recheck retained historical traces, not newly recorded device behavior:

```sh
python3 -B scripts/provenance-first/search-handoff/verify-opening.py Evaluation/ProvenanceFirst/runs/search-handoff/opening-final-top-trace.jsonl
python3 -B scripts/provenance-first/search-handoff/verify-motion.py Evaluation/ProvenanceFirst/runs/search-handoff/opening-final-top-events.json
python3 -B scripts/provenance-first/search-handoff/verify-opening.py Evaluation/ProvenanceFirst/runs/search-handoff/opening-final-scrolled-trace.jsonl
python3 -B scripts/provenance-first/search-handoff/verify-motion.py Evaluation/ProvenanceFirst/runs/search-handoff/opening-final-scrolled-events.json
```

No new app build, XCTest suite, training, inference, cloud request, historical full-integrity verification or model export was run. No secrets were read into this report. Git state and phone data were untouched.

## Validation of the approved evaluation cleanup

- Deleted all **84** exact A–C targets; retained the D package. No target was tracked, contained Git data, or contained a phone-backup directory.
- No active compiler/build process was detected before execution.
- Reverified all 14 duplicate model packages against production using SHA-256.
- Hashed **62,477 retained evaluation files** before and after deletion: every file remained present and identical, including phone backups and retained test evidence.
- App, scripts, proxy, D3 export evidence/P2 run, cloud pilot, latest deployment and FP32 package content hashes matched before/after.
- Complete versionable working-file status matched immediately before/after deletion; documentation was updated afterward.
- The four saved-trace checks listed above were rerun after evaluation deletion and passed.
- No app rebuild or new XCTest run was performed; no production source changed.

## Exact evaluation inventory — A–C deleted; D retained

Each A–C directory listed below and its contents were deleted. The D package is retained. This is an exact historical inventory, not a wildcard deletion command.

### A — superseded UI recordings and test bundles

| Path relative to repository root | Allocated MiB |
| --- | ---: |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790232227283887000.xcresult` | 0.13 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790232285230077000.xcresult` | 0.38 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790232387326376000.xcresult` | 0.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790232542046447000.xcresult` | 15.16 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790232797018182000.xcresult` | 0.74 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790233080712009000.xcresult` | 5.11 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790234681401842000.xcresult` | 0.36 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790234766540038000.xcresult` | 1.55 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790234887864896000.xcresult` | 0.13 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790234971555269000.xcresult` | 0.81 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790235080926176000.xcresult` | 11.02 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790235202449327000.xcresult` | 0.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790235350835092000.xcresult` | 0.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790243734478875000.xcresult` | 0.27 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790243814729764000.xcresult` | 0.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790244052571216000.xcresult` | 5.98 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790245329926370000.xcresult` | 0.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790245491410054000.xcresult` | 0.83 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790245625804634000.xcresult` | 0.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790245822707772000.xcresult` | 5.49 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790246128927448000.xcresult` | 0.59 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790247304547636000.xcresult` | 0.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790247419768138000.xcresult` | 0.83 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790247535824401000.xcresult` | 0.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790247626275646000.xcresult` | 0.82 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790247723946161000.xcresult` | 0.82 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790247811968595000.xcresult` | 0.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790247937566206000.xcresult` | 0.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790248052272201000.xcresult` | 0.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790248167945825000.xcresult` | 0.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790248274609060000.xcresult` | 0.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790248429587615000.xcresult` | 0.74 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790248547830621000.xcresult` | 39.19 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790248657119104000.xcresult` | 40.29 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790248820482468000.xcresult` | 40.73 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/1790248908493486000.xcresult` | 40.56 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/bitmap-top.mp4` | 43.12 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/edge-top.mp4` | 0.00 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/final-ui.mp4` | 7.67 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/geometry-regression.mp4` | 182.87 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/opening-scoped-removal.mp4` | 39.59 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/opening-single-scrolled.mp4` | 40.75 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/opening-stable-backing.mp4` | 44.67 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/overlay-scrolled.mp4` | 77.14 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/overlay-top-retry.mp4` | 39.91 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/overlay-top.mp4` | 0.01 |
| `Evaluation/ProvenanceFirst/runs/search-overlay/scoped-top-dark.mp4` | 20.35 |
| `Evaluation/ProvenanceFirst/runs/search-overlay/traced-baseline.mp4` | 56.84 |

### B — superseded or retired research outputs

| Path relative to repository root | Allocated MiB |
| --- | ---: |
| `Evaluation/MatcherFeasibility/runs/stage-3-attempt-01` | 6.07 |
| `Evaluation/MatcherFeasibility/runs/stage-3-attempt-02` | 6.76 |
| `Evaluation/MatcherFeasibility/runs/stage-5-attempt-01/evaluations` | 47.02 |
| `Evaluation/MatcherScreening/runs/audit-attempt-01/ablations` | 27.53 |
| `Evaluation/MatcherScreening/runs/audit-attempt-01/diagnostics` | 14.54 |
| `Evaluation/MatcherScreening/runs/screen-attempt-01/predictions` | 213.75 |
| `Evaluation/Organization/results/core-checkpoint-01-2026-09-11.json.gz` | 30.57 |
| `Evaluation/Organization/results/core-departure-checkpoint-2026-09-10.json.gz` | 9.83 |
| `Evaluation/Organization/results/core-english-complete-2026-09-11.json.gz` | 33.87 |
| `Evaluation/Organization/results/core-paused-02-2026-09-10.json.gz` | 28.32 |
| `Evaluation/Organization/results/core-paused-2026-09-10.json.gz` | 20.48 |
| `Evaluation/Organization/results/core-paused-2026-09-11.json.gz` | 33.10 |
| `Evaluation/Organization/results/core-precheckpoint-fix-2026-09-10.json.gz` | 5.90 |
| `Evaluation/Organization/results/core-resumed-checkpoint-01-2026-09-10.json.gz` | 24.96 |
| `Evaluation/Organization/results/core-resumed-checkpoint-02-2026-09-10.json.gz` | 27.49 |
| `Evaluation/Organization/results/scale-checkpoint-01-2026-09-11.json.gz` | 0.96 |
| `Evaluation/Organization/results/scale-checkpoint-02-2026-09-11.json.gz` | 4.39 |
| `Evaluation/OrganizationDiagnostics/runs/c2-01/ledger/results` | 388.50 |
| `Evaluation/OrganizationDiagnostics/runs/c3-01/fixed` | 62.64 |
| `Evaluation/OrganizationDiagnostics/runs/c4-01/metrics` | 43.90 |
| `Evaluation/OrganizationDiagnostics/runs/c4-01/proposals` | 40.65 |
| `Evaluation/ProvenanceFirst/runs/current-runtime-comparison/output` | 110.17 |

### C — identical model packages in retired snapshots/projects

| Path relative to repository root | Allocated MiB |
| --- | ---: |
| `Evaluation/ProvenanceFirst/runs/search-compact/baseline/Remember/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |
| `Evaluation/ProvenanceFirst/runs/search-dismissal/baseline/Remember/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/baseline/Remember/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |
| `Evaluation/ProvenanceFirst/runs/search-handoff/project/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |
| `Evaluation/ProvenanceFirst/runs/search-handoff-deployment/project/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |
| `Evaluation/ProvenanceFirst/runs/search-handoff-deployment/uninstalled-build-1790246295454434000/project/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |
| `Evaluation/ProvenanceFirst/runs/search-motion/baseline/Remember/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |
| `Evaluation/ProvenanceFirst/runs/search-options/baseline/Remember/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |
| `Evaluation/ProvenanceFirst/runs/search-overlay/baseline/Remember/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |
| `Evaluation/ProvenanceFirst/runs/search-overlay-deployment/project/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |
| `Evaluation/ProvenanceFirst/runs/search-spacing/baseline/Remember/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |
| `Evaluation/ProvenanceFirst/runs/search-transition/baseline/Remember/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |
| `Evaluation/ProvenanceFirst/source-browser-media/baseline/Remember/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |
| `Evaluation/ProvenanceFirst/unified-search/baseline/Remember/Remember/MatcherAssets/D3Matcher.mlpackage` | 63.79 |

### D — optional unshipped FP32 experiment

| Path relative to repository root | Allocated MiB |
| --- | ---: |
| `Evaluation/iOS27/precision/export-fp32/models/D3MatcherFP32.mlpackage` | 127.41 |


## Completed low-risk deletion receipt

| Deleted path relative to repository root | Category | Allocated MiB |
| --- | --- | ---: |
| `.DS_Store` | OS metadata | 0.01 |
| `output/.DS_Store` | OS metadata | 0.01 |
| `server/__pycache__` | Python bytecode cache | 0.01 |
| `.venv` | Unused root Python environment | 83.21 |
| `scripts/.DS_Store` | OS metadata | 0.01 |
| `scripts/organization-diagnostics/__pycache__` | Python bytecode cache | 0.47 |
| `scripts/matcher-validation/__pycache__` | Python bytecode cache | 0.41 |
| `scripts/__pycache__` | Python bytecode cache | 0.19 |
| `scripts/provenance-first/answer-support-screen/__pycache__` | Python bytecode cache | 0.01 |
| `scripts/provenance-first/answer-support/__pycache__` | Python bytecode cache | 0.16 |
| `scripts/provenance-first/search-spacing/__pycache__` | Python bytecode cache | 0.00 |
| `scripts/provenance-first/answer-support-format-v2/__pycache__` | Python bytecode cache | 0.04 |
| `scripts/provenance-first/__pycache__` | Python bytecode cache | 0.05 |
| `scripts/provenance-first/history-ranking/__pycache__` | Python bytecode cache | 0.06 |
| `scripts/provenance-first/search-overlay/__pycache__` | Python bytecode cache | 0.00 |
| `scripts/provenance-first/search-dismissal/__pycache__` | Python bytecode cache | 0.00 |
| `scripts/provenance-first/search-motion/__pycache__` | Python bytecode cache | 0.00 |
| `scripts/provenance-first/search-options/__pycache__` | Python bytecode cache | 0.01 |
| `scripts/provenance-first/main-app-deployment/__pycache__` | Python bytecode cache | 0.05 |
| `scripts/provenance-first/history/__pycache__` | Python bytecode cache | 0.07 |
| `scripts/provenance-first/unified-search/__pycache__` | Python bytecode cache | 0.02 |
| `scripts/provenance-first/source-browser-ui/__pycache__` | Python bytecode cache | 0.03 |
| `scripts/provenance-first/search-handoff/__pycache__` | Python bytecode cache | 0.02 |
| `scripts/matcher-feasibility/__pycache__` | Python bytecode cache | 1.17 |
| `Evaluation/.DS_Store` | OS metadata | 0.01 |
| `Evaluation/iOS27/sentence-diagnostic/build/device-build/SDKStatCaches.noindex` | Xcode cache/intermediate | 1.51 |
| `Evaluation/iOS27/sentence-diagnostic/build/device-build/CompilationCache.noindex` | Xcode cache/intermediate | 0.03 |
| `Evaluation/iOS27/generation-trace/build/device-build/SDKStatCaches.noindex` | Xcode cache/intermediate | 1.51 |
| `Evaluation/iOS27/generation-trace/build/device-build/CompilationCache.noindex` | Xcode cache/intermediate | 0.03 |
| `Evaluation/iOS27/sentence-context/build/device-build/SDKStatCaches.noindex` | Xcode cache/intermediate | 1.51 |
| `Evaluation/iOS27/sentence-context/build/device-build/CompilationCache.noindex` | Xcode cache/intermediate | 0.03 |
| `Evaluation/iOS27/sentence-controls/build/device-build/SDKStatCaches.noindex` | Xcode cache/intermediate | 1.51 |
| `Evaluation/iOS27/sentence-controls/build/device-build/CompilationCache.noindex` | Xcode cache/intermediate | 0.03 |
| `Evaluation/OrganizationDiagnostics/runs/c2-01/ledger/build/SDKStatCaches.noindex` | Xcode cache/intermediate | 1.47 |
| `Evaluation/OrganizationDiagnostics/runs/c2-01/ledger/build/CompilationCache.noindex` | Xcode cache/intermediate | 0.03 |
| `Evaluation/ProvenanceFirst/runs/answer-support/native-build/SDKStatCaches.noindex` | Xcode cache/intermediate | 1.54 |
| `Evaluation/ProvenanceFirst/runs/answer-support/native-build/CompilationCache.noindex` | Xcode cache/intermediate | 0.03 |
| `Evaluation/ProvenanceFirst/runs/search-opening-deployment/build/SDKStatCaches.noindex` | Xcode cache/intermediate | 1.51 |
| `Evaluation/ProvenanceFirst/runs/search-opening-deployment/build/SDKExplicitPrecompiledModules` | Xcode cache/intermediate | 173.63 |
| `Evaluation/ProvenanceFirst/runs/search-opening-deployment/build/ModuleCache.noindex` | Xcode cache/intermediate | 27.29 |
| `Evaluation/ProvenanceFirst/runs/search-opening-deployment/build/CompilationCache.noindex` | Xcode cache/intermediate | 0.03 |
| `Evaluation/ProvenanceFirst/runs/search-opening-deployment/build/Build/Intermediates.noindex` | Xcode cache/intermediate | 119.97 |
| `Evaluation/ProvenanceFirst/runs/search-opening-deployment/build/Build/ProfileData` | Xcode cache/intermediate | 3.48 |
| `Evaluation/ProvenanceFirst/runs/checkpoint1/ledger/build/SDKStatCaches.noindex` | Xcode cache/intermediate | 1.54 |
| `Evaluation/ProvenanceFirst/runs/checkpoint1/ledger/build/CompilationCache.noindex` | Xcode cache/intermediate | 0.03 |
| `Evaluation/ProvenanceFirst/runs/search-handoff-deployment/build/SDKStatCaches.noindex` | Xcode cache/intermediate | 1.51 |
| `Evaluation/ProvenanceFirst/runs/search-handoff-deployment/build/SDKExplicitPrecompiledModules` | Xcode cache/intermediate | 173.63 |
| `Evaluation/ProvenanceFirst/runs/search-handoff-deployment/build/ModuleCache.noindex` | Xcode cache/intermediate | 27.29 |
| `Evaluation/ProvenanceFirst/runs/search-handoff-deployment/build/CompilationCache.noindex` | Xcode cache/intermediate | 0.03 |
| `Evaluation/ProvenanceFirst/runs/search-handoff-deployment/build/Build/Intermediates.noindex` | Xcode cache/intermediate | 125.07 |
| `Evaluation/ProvenanceFirst/runs/search-handoff-deployment/build/Build/ProfileData` | Xcode cache/intermediate | 0.25 |
| `Evaluation/ProvenanceFirst/runs/main-app-deployment/build/SDKStatCaches.noindex` | Xcode cache/intermediate | 1.51 |
| `Evaluation/ProvenanceFirst/runs/main-app-deployment/build/ModuleCache.noindex` | Xcode cache/intermediate | 27.29 |
| `Evaluation/ProvenanceFirst/runs/main-app-deployment/build/CompilationCache.noindex` | Xcode cache/intermediate | 0.03 |
| `Evaluation/ProvenanceFirst/runs/main-app-deployment/build/Build/ProfileData` | Xcode cache/intermediate | 3.34 |
| `Evaluation/ProvenanceFirst/runs/search-overlay-deployment/build/SDKStatCaches.noindex` | Xcode cache/intermediate | 1.51 |
| `Evaluation/ProvenanceFirst/runs/search-overlay-deployment/build/CompilationCache.noindex` | Xcode cache/intermediate | 0.03 |
| `Evaluation/ProvenanceFirst/runs/search-overlay-deployment/build/Build/ProfileData` | Xcode cache/intermediate | 3.46 |
| `Evaluation/ProvenanceFirst/runs/unified-search/build/SDKStatCaches.noindex` | Xcode cache/intermediate | 1.54 |
| `Evaluation/ProvenanceFirst/runs/unified-search/build/SDKExplicitPrecompiledModules` | Xcode cache/intermediate | 172.23 |
| `Evaluation/ProvenanceFirst/runs/unified-search/build/ModuleCache.noindex` | Xcode cache/intermediate | 27.54 |
| `Evaluation/ProvenanceFirst/runs/unified-search/build/CompilationCache.noindex` | Xcode cache/intermediate | 0.03 |
| `Evaluation/ProvenanceFirst/runs/unified-search/build/Build/Intermediates.noindex` | Xcode cache/intermediate | 131.13 |
| `Evaluation/ProvenanceFirst/runs/unified-search/build/Build/ProfileData` | Xcode cache/intermediate | 11.91 |
| `Remember/.DS_Store` | OS metadata | 0.01 |

## Production model fingerprints retained

These fingerprints identify the package against which the duplicate proposals were checked.

| File relative to production D3Matcher.mlpackage | SHA-256 |
| --- | --- |
| `Manifest.json` | `427e6d4a0745373fba9779e53c0aa493585abfe0e4ace5cb83ca32fec35189fa` |
| `Data/com.apple.CoreML/model.mlmodel` | `ddcb20d305f4ce74eb9837ea20585906cee807273ce75a94c9b5b785a672f5e9` |
| `Data/com.apple.CoreML/weights/weight.bin` | `2c0cfb576c006959aaa28003b1cea3ca1fcd851caf9614f4f840c15c9a23e698` |
