# C6 — independent semantic review and bounded frozen-model scoring

Approved after C5. Mac-only experiment; stop after results for review. No training,
threshold fitting, new model downloads, app/ledger mutation, phone use or Git changes.
Keep all prior evidence and the cumulative 4 GiB cap / 10 GiB free-space reserve.

## Reference review before scoring

Two separate agents independently review source-only inputs using C6_REVIEW_CONTRACT.md,
without author labels, model outputs or one another's decisions. Pair-only work is
validated and sealed before each agent sees context. Deduplicate only identical ordered
sources and query endpoints, ignoring queryID/view: 160 packets reduce to 112 unique
contexts (56 pair then 56 additional context). Map decisions back to every original ID.
Agents must use each packet in isolation, not other packets' content. This is procedural
blindness in a shared environment; agents may share systematic model-family errors.

Root reviews every disagreement between reviewers or with original labels against its
exact visible packet. Preserve first judgments and write explicit adjudication and
amendments. No original labels are overwritten. Freeze adjudicated references before
model execution. Reference agents are annotators, **not an on-device model candidate**.

## Candidate inventory and rules

- Frozen simple baseline and hybrid seeds 17/29/41: existing P2 transforms, weights,
  tokenization, symmetric-direction averaging, eligibility and C2 thresholds unchanged.
  Score only the queried source pair. Map passing scores to `same_project`, otherwise
  `abstain`; never interpret a failed attachment threshold as `separate_projects`.
- `scope-rules`: an independently implemented, corpus-blind controlled-English verifier.
  It requires explicit project-name/membership bindings and explicit same/separate
  relations; no inferred transitivity. Its exact source and independent fixture tests
  must be frozen before seeing C5 packets or reference reviews. Natural prose may not
  satisfy this restricted grammar, so zero coverage is an admissible negative result.
  This is a non-neural feasibility control, not a general language reasoner.
- Four corresponding conflict-gated candidates: a scope-rule `separate_projects`
  result overrides the legacy output; otherwise keep the unchanged legacy prediction.
  A scope-rule `same_project` does not force a new attachment. Nine candidates total.

All candidates consume the same released packets; legacy models ignore extra context.
Native pair inputs are ordered by text hash for deterministic caching. Neural pair
token budget remains 512 with original longest-first truncation, two directions,
microbatches <=8. Rule inputs use the complete <=4 visible source texts, no truncation.
No prompts, retrieval or model inventory are tuned after predictions or scores appear.

Legacy evidence quotes are the two evaluated source texts, automatically attached as
input provenance—not generated explanations or semantic justification. Rule evidence
comes from its bound spans. Validate exact source visibility and quote spans under the
C5 schema. A valid quote does not prove the verdict is correct.

## Execution and integrity

Freeze protocol, review contract/receipts, code/tests, input bytes, adjudicated reference
and all inherited model bindings before inference. Use existing English embedding probe
and pinned feasibility environment; stage all new logs under C6, never C2 artifacts.
Build only a current-query pair cache from source-only inputs; no gold/rationale features.
Persist each text embedding and every bounded neural batch result as checksum units.
Before accepting each seed's new scores, reproduce the 16 existing C2/P2 reference pairs
with feature tolerance 1e-12 and neural/hybrid tolerance 1e-5, including threshold decisions.
This reference parity is numerical regression, not fresh test accuracy.

Freeze all 9 × 160 predictions before opening adjudicated labels in the scoring stage.
Fail on missing/nonfinite inference, malformed outputs or missing prediction IDs—do not
turn runtime failures into apparently correct abstentions. Single shared worker lock;
signals or pause requests stop at short boundaries. Resume verifies hashes, skips saved
units and reloads the current model only when needed. Exercise real saved stop/resume
without modifying the first embedding's hash or timestamp. Recompute features/assembled
predictions and metrics for replay verification; do not rerun inference merely to resume.

## Interpretation and review stop

Use C5's three-way metric adapter: conflict precision/recall, coverage, unsupported
decisive assertions on uncertainty, false conflicts on same-project pairs, grouped by
view/family/partition/behavior, plus joint contrast outcomes. Add same-project precision
and recall from the same counts. Undefined precision stays null for always-abstain
conflict outputs. Report original-label versus adjudicated-label differences separately.
Do not claim no-conflict controls failed a learned conflict task they were never trained
to perform; measure their false same-project assertions on explicit separations too.

The author saw all original labels; only four families are in the diagnostic partition.
Views, repeated pairs and template variants are correlated. No production qualification,
statistical safety guarantee, real-user acceptance or phone-performance claim follows.
No simulated acceptance or clustering execution occurs here. Save all errors and results,
report what improved or failed, then stop before another experiment or integration.
Initial estimate 4–8 active hours; update from actual review/inference progress.
