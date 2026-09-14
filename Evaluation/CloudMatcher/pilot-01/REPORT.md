# GPT-5.4 grouping pilot — final results

Completed 14 September 2026. **Strong exploratory signal; not production-qualified.**
The approved run is finished. No further paid experiment or app integration has started.

## What we tested

Can a cloud reviewer distinguish the same ongoing project from related but separate
projects, and withhold judgment when evidence is insufficient?

We reused the C6 adjudicated diagnostic: eight agent-reviewed fictional families,
160 scored packets (80 pair-only and 80 with surrounding context). Identical visible
inputs reduced this to **112 unique API calls**. This is an exposed synthetic diagnostic,
not a new holdout, a human-validated benchmark, or a representative user sample.

The model was `gpt-5.4-2026-03-05`, low reasoning effort, standard service tier, with
strict structured output and literal source quotations. It received only the queried
pair and visible sources, not gold labels, reviewer explanations, or local scores.
The earlier C7 prompt, controls, thresholds, data and validators were frozen before
inference. Invalid answers were retained as errors, not retried or relabeled.

Comparisons:

- **Simple baseline:** the existing lightweight classifier at its frozen threshold.
- **D3:** the current trained local pair scorer, using cached reference predictions.
- **GPT-5.4:** cloud judgment independently determines same/separate/abstain.
- **D3 + veto:** retain D3 unless GPT explicitly identifies separate projects.
- **D3 + confirmation:** require both D3 and GPT to assert the same project.

Both combined policies propagate GPT validation errors. They do not simulate a
production fallback policy. No app code, personal memories, or phone state changed.

## Main result: context-rich cases

These 80 packets contain 32 genuine same-project cases, 32 separate-project cases and
16 insufficient-evidence cases. Counts make the small sample size explicit.

| Candidate | Same-project precision | Same-project recall | Wrong same on 32 separate | Wrong separate on 32 same | Unsupported decisions on 16 uncertain | Errors / 80 |
|---|---:|---:|---:|---:|---:|---:|
| Simple baseline | 24/51 = 47.1% | 24/32 = 75.0% | 22 | 0 | 5 | 0 |
| D3 local pair scorer | 25/52 = 48.1% | 25/32 = 78.1% | 22 | 0 | 5 | 0 |
| GPT-5.4 | **29/31 = 93.5%** | **29/32 = 90.6%** | **2** | 2 | **0** | 1 |
| D3 + veto | 22/29 = 75.9% | 22/32 = 68.8% | 2 | 2 | 5 | 1 |
| D3 + confirmation | **22/23 = 95.7%** | 22/32 = 68.8% | **1** | 2 | **0** | 1 |

Precision means how often an asserted connection is supported by gold labels; it
penalizes assertions on insufficient-evidence inputs too. Recall means the fraction
of genuine connections found. Errors remain in recall denominators.

GPT's separation precision was **28/30 = 93.3%**, and separation recall was
**28/32 = 87.5%**. It corrected **40** D3 decisions and damaged **3** previously
correct decisions. Its exact three-way correctness was 73/80 (91.25%), versus
D3's 36/80 (45.0%). That last comparison also reflects a capability difference:
the local controls assert same or abstain, rather than explicitly asserting separate.

**These are deliberately difficult pair-level diagnostic results, not the app's
overall accuracy.** The test does not execute candidate retrieval, Core ML rounding,
C3 multi-member corroboration, chronological River updates, or automatic grouping.
Do not compare this precision directly with earlier P2 scores on a different benchmark.

## Does surrounding context matter?

The pair-only view has 23 same, 24 separate and 33 uncertain cases:

| Candidate | Same precision | Same recall | Wrong same / 24 separate | Unsupported / 33 uncertain | Errors / 80 |
|---|---:|---:|---:|---:|---:|
| Simple baseline | 37.3% | 82.6% | 21 | 11 | 0 |
| D3 | 38.5% | 87.0% | 21 | 11 | 0 |
| GPT-5.4 | 69.2% | 78.3% | 2 | 6 | 1 |
| D3 + veto | 55.2% | 69.6% | 2 | 11 | 1 |
| D3 + confirmation | 69.6% | 69.6% | 1 | 6 | 1 |

The context view is stronger, but the aggregate difference is not a clean causal
estimate: additional evidence also changes which gold decisions are possible.
The paired behavior checks provide more specific evidence. GPT passed all required
decisions in **8/8 context clarification checks**, versus **5/8 pair-only checks**.
It passed **8/8 context scope-distinction/continuation checks**, but only **5/8
shared-source bridge triples**. Context-family correctness ranged from 8/10 to 10/10.
Packets share sources and templates; they must not be treated as independent trials.

## Remaining failure modes

1. **Shared sources can legitimately belong to multiple projects.** GPT incorrectly
   separated a reedbed survey from a volunteer rota covering both that survey and a
   separate otter census. A workshop schedule covering two separate repair projects
   produced the same mistake. These were two harmful overrides of correct local matches.
2. **Mentioning another project is not membership in it.** GPT incorrectly connected
   a roof restoration and an unrelated playground delivery sharing identifier NL-6,
   and a basil experiment and an unrelated van-maintenance invoice sharing BAS-2.
   The source explicitly explained the collisions, but its cross-reference was
   mistaken for evidence of belonging to the other project.
3. **Quoted evidence still needs validation.** Two unique responses contained invalid
   quotations: one in each view. The context response gave the right semantic verdict
   but used a non-contiguous quotation; it still counts as an error. This was the third
   damaged previously correct D3 decision.
4. **Some explicit separations became abstentions.** Two further identifier-collision
   cases were left unresolved rather than correctly separated.

No failed case was removed, repaired through another paid call, or tuned away in this run.

## Cost and responsiveness

| Measurement | Result |
|---|---:|
| Paid inference requests | 112 |
| Input tokens | 62,285 |
| Output tokens, including reasoning | 21,904 |
| Reasoning subset of output | 9,994 |
| Cached input tokens | 0 |
| Token-derived API cost, before tax | **US$0.4842725** |
| Approved cap | US$5.00 |
| Unknown-billing calls / retries | 0 / 0 |
| Request latency, median | 2.49 seconds |
| Request latency, 95th percentile | 4.37 seconds |

Cost uses $2.50 per million input tokens and $15 per million output tokens;
reasoning is already included in output and is not counted twice.
See [official API pricing](https://developers.openai.com/api/docs/pricing).
This is a usage-derived estimate, not an invoice reconciliation. Short fictional
requests cost less than the conservative initial estimate; these timings and costs
are not guarantees for full threads, production traffic, or an entire-library rebuild.

## Recommendation and stopping point

**The most promising balanced candidate is GPT's context-aware judgment**, while
keeping local embeddings for candidate retrieval and an offline local path. This
does not mean sending every memory to the cloud or discarding local models.

Hard confirmation increased precision to 95.7%, but found only 22 genuine connections
instead of GPT's 29. Requiring D3 approval for every suggestion therefore throws away
much of the cloud reviewer's potential improvement. Veto alone retained unsupported
local assertions when GPT appropriately abstained.

GPT passed all five pre-existing C7 exploration checks: separation precision ≥90%,
separation recall ≥80%, same recall ≥75%, unsupported uncertain decisions ≤10%, and
errors ≤5%. **This justifies fresh validation, not automatic deployment.**

Proposed next step, requiring a separate scope/budget approval:

1. Prepare fresh, independently reviewed families including ordinary captures,
   shared-source bridges, incidental cross-references and identifier collisions.
   Do not use this diagnostic as the final qualification set after tuning.
2. Evaluate the complete local-retrieval → context-review path in chronological
   River replays, including retrieval misses, revisions and import-order changes.
   Measure incorrect attachments, missed connections and harmful overrides, not
   just pair accuracy; do not assume perfect user review.
3. If that passes, consider an explicitly opted-in premium **suggestion-only** pilot,
   with validated evidence, undo, a local fallback and server-side credentials.
   Do not silently upload personal memories or automatically merge threads.

## Reproducibility and checks

The [protocol](PROTOCOL.md) and [manifest](manifest.json) bind the original sources,
settings and controls. [Summary](summary.json), `predictions/`, `units/` and
`attempts/` preserve metrics, interpreted outcomes and raw successful responses.
[Verification](verification.json) records independent confusion-count and cost checks.

Executed with the existing feasibility Python environment:

```sh
python -m unittest discover -s scripts/cloud-matcher -p 'test_*.py'
python -m unittest discover -s scripts/organization-diagnostics -p 'test_*.py'
python scripts/cloud-matcher/pilot.py proof
python scripts/cloud-matcher/pilot.py evaluate
python scripts/cloud-matcher/pilot.py predict
python scripts/cloud-matcher/pilot.py evaluate
```

- 14 new safety tests and 193 existing diagnostic tests passed.
- Ten independently reconstructed candidate/view confusion tables matched.
- Pause after the first two calls and resume preserved their hashes and timestamps.
- Completed prediction replay skipped all 112 saved inputs without additional calls.
- Evaluation replay reproduced the same summary; frozen input hashes remained intact.
- No app build or phone test was needed: the experiment changed no app code.
- Only fictional text was uploaded. `store: false` is not a zero-retention guarantee.
- Git state was not modified; all version-control actions remain with the user.
