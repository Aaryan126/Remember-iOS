# Evaluation cleanup summary

Completed 24 September 2026 with user approval.

## What we deleted

Removed **2.783 GiB** of old evaluation artifacts, following an earlier **1.106 GiB** cache/environment cleanup: approximately **3.89 GiB total** in allocated-file sizes. Actual free-space gain can differ because of filesystem clones or snapshots.

| Removed in this batch | Approximate size |
| --- | ---: |
| Superseded search UI recordings and test bundles | 775 MiB |
| Older prediction/ablation outputs, repeated diagnostic stores, and intermediate benchmark archives | 1,181 MiB |
| 14 byte-identical model packages copied into retired projects and snapshots | 893 MiB |

The [detailed audit](evaluation-cleanup-audit.md) records all 84 deleted targets, the earlier cache deletions, model fingerprints, and study-by-study findings. The optional 127 MiB FP32 model **was kept**.

## What we learned from the failed or incomplete approaches

- **Early model conversion:** the first attempts hit tokenizer mismatch and non-finite FP16 output. A corrected later conversion succeeded; its evidence remains.
- **Standalone MiniLM and hybrid screening:** early trained candidates did not meet the quality gates. The hybrid was more promising, but not every confirmation seed passed.
- **P2 model qualification:** seed 29 is the experimental model used by the app, but the three-seed family failed qualification. Its individual success does not erase the failed family result.
- **Grouping and repair:** corroborating matches across thread members helped, but fragmentation and incorrect grouping remained. Proposed automatic repairs could reconnect fragments without reliably fixing mixed threads.
- **Local semantic/answer verification:** local reviewers failed safety or usefulness gates. Passing tiny answer-format controls did not translate into good answer verification; the subsequent development screen failed and held-out inference was not run.
- **History retrieval:** preserving and browsing earlier source revisions worked. The tested ranking/abstention filters either returned weak evidence or suppressed too many useful answers.
- **Runtime precision:** some numerical compatibility checks failed despite unchanged decisions on their controls. FP32 improved numerical agreement with extra storage and inference cost; it was not adopted into the app.
- **Search animation trials:** several layout approaches improved opening but broke closing, or caused test stalls. The final retained solution used one persistent scroll owner and scoped results-layout changes; its passing tests, traces and final recording remain.
- **Older benchmark checkpoints:** paused, resumed and pre-fix archives were superseded by final outputs. Large-library scale runs remained incomplete; final incident records were kept.

The removed files were bulky implementation evidence and redundant copies. Original compact reports preserve both failures and successes. This cleanup does not change any recorded result or promote a failed candidate.

## What we kept

- All current app code, tests, fixtures, scripts and proxy code.
- Production FP16 model, vocabulary, parameters and attribution; D3 export/parity evidence and the complete P2 validation run needed by the export workflow.
- Accepted model-conversion/phone-feasibility results, useful organization comparison results, provenance/history integrity evidence, and final benchmark archives.
- The promising cloud-review pilot, including its limitations: exploratory synthetic results, not production qualification.
- Latest passing search unit/UI results, final geometric traces and recording, and the latest signed deployment evidence.
- Every phone backup, the optional FP32 package, and compact reports documenting failed experiments.
- Git metadata and all pre-existing user source changes.

## What is no longer reproducible from the retained files

Some old full-integrity audits, intermediate replays, recordings and attachments depended on deleted files. Those particular historical commands/raw links are retired; the exact scope is in the audit. Archived projects whose duplicate model was removed need that identical package restored before rebuilding. Frozen manifests were not rewritten to conceal deletion.

## Checks after cleanup

- All 84 approved targets were absent and the optional FP32 package remained.
- SHA-256 checks confirmed **62,477 retained evaluation files** and the protected app/script/model trees stayed unchanged.
- All four saved search opening/closing trace checks passed.
- Documentation links and `git diff --check` passed.
- No app rebuild or new device tests were needed for artifact-only deletion; those were not run.
