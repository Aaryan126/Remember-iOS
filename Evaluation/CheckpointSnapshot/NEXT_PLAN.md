# Next: diagnose River grouping before further model investment

This records the approved diagnostic-first direction. Preparation must stop for a manual user Git checkpoint. Then checkpoint 1 and checkpoint 2 each end with a separate review stop. These are diagnostic experiments, not a new qualification dataset or permission to ship a model.

## Intended behavior

A River represents a continuing project: its design, execution, results and revisions can belong together. Distinct projects remain separate even when they share a topic. Ambiguous attachments should become proposals rather than confident automatic changes. Apply this contract prospectively; preserve all previous labels, gates and reported failures.

## Checkpoint 1 — contract and prediction-blind diagnosis

Estimated 4–8 active hours, Mac only, after preparation approval.

1. Create isolated `Evaluation/OrganizationDiagnostics/` and `scripts/organization-diagnostics/` workspaces. Do not modify frozen feasibility, screening or validation sources.
2. Write operational same-project, related-but-separate, ambiguous, revision and correction rules with examples and explicit non-goals.
3. Select deterministic, distinct P2 examples: 20 false positives, 20 false negatives, 20 true positives and 20 true negatives. Preserve selection provenance; do not show predictions or the outcome stratum to reviewers. Insufficient strata must be reported, not silently resampled with duplicates.
4. Give independent review agents the approved contract and source evidence. Save pair-only judgments before contextual judgments, then adjudicate disagreements with rationale. Gold and predictions remain outside scorer inputs. These are agent reviews, not human labels or independent proof of correctness.
5. Author and review 12 fictional stories of 12 captures each. Include related distinct projects, revisions, corrections and archives. Define expected state at each prefix, plus chronological order and two dependency-valid shuffles; never let a correction precede its target.
6. Save contract, sampling manifest, reviews, adjudication, story/event fixtures, prefix gold, hashes, validation tests and resume instructions. Report whether errors indicate contract mismatch, missing context, retrieval failure or scoring failure. **Stop for user approval.**

## Checkpoint 2 — small frozen policy comparison and ledger replay

Estimated 8–16 active hours, Mac only, only after checkpoint 1 approval.

1. Implement a resumable, isolated runner that cannot touch the personal vault. Reuse cached English embeddings and frozen baseline/hybrid models; keep scorer inputs gold-free and preserve original thresholds/features. Exercise interruption/recovery before long work.
2. Compare four paths: production embedding-only reference, simple-baseline strongest-member attachment, hybrid strongest-member attachment, and hybrid attachment requiring two-of-three corroboration. Report all hybrid seeds; do not choose a winner by hiding other seeds. Precisely freeze reference behavior and small-thread fallback before scoring.
3. Share retrieval for controlled policy comparisons: top five contextual candidates plus top five lexical candidates, reciprocal-rank fusion with constant 60 and stable-ID ties. Report retrieval coverage separately from scoring. Where the production reference necessarily differs, disclose that difference rather than treating it as an isolated scorer ablation.
4. Auto-attach only when exactly one thread qualifies; multiple qualifying threads become proposals. Experimental policies must not auto-merge threads. Document the corroboration behavior when fewer than three members are available.
5. Run chronology and the two valid shuffles, scoring every prefix. Report false attachments, missed attachments, fragmentation, proposals/abstentions, order sensitivity and correction recovery, with library/story-level summaries. Keep retrieval, pair classification and whole-thread outcomes separate.
6. Replay accepted actions through the actual provenance ledger in an isolated simulator test store. Test correction, merge/split where explicitly commanded, archive and replay invariants. Semantic grouping quality and ledger correctness are separate claims.
7. Save predictions, metrics, errors, replay evidence, runtime/storage measurements and a recommendation. **Stop.** No tuning on these exposed examples may be presented as held-out improvement.

## Pause, resource and decision rules

- One worker; offline fictional inputs only. No model downloads, new training, phone access, production integration or personal-memory ingestion in either checkpoint.
- New artifacts including temporary writes: at most 4 GiB; maintain at least 10 GiB free. Preserve earlier artifacts; no automatic cleanup. The old temporary 4.5 GiB exception does not apply.
- Support `pause` and `resume` at bounded work units. Save input/model/policy hashes, completed IDs and verified output receipts; publish completion last. On pause, finish the current bounded unit, save and stop the worker, then confirm safe to close. Never assume an unacknowledged pause or laptop sleep is a verified checkpoint.
- Report progress and revised remaining time at each checkpoint and during lengthy work. Estimates depend on review and replay findings; a failed precondition means stop and explain the smallest recovery step, not expand scope automatically.
- If the contract/context explains errors, pursue retrieval and conservative attachment policy next. If scores remain the limiting factor, propose targeted data/training only after diagnostics. Any eventual integration needs a new untouched qualification set and trained-model phone measurements; these diagnostics do not replace either.

Remaining estimate after preparation: 12–24 active hours total, with a mandatory stop after the first 4–8 hours. No stage starts merely because a status check or verification command succeeds.
