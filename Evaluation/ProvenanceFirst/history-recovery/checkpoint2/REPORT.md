# History-aware recovery: relevance and abstention

Status: **complete; stopped for user review. No candidate qualified.** No production
change or promotion is authorized. History coverage is promising; these particular
score/margin filters are not a usable answer-support policy.

## What this checkpoint tests

The product objective remains: **Save anything. Recover the right context. See how
your projects developed—with evidence.** Checkpoint 1 proved that a version-aware
index can expose retained current, archived and superseded evidence. This checkpoint
tests whether a small, existing local retrieval stack can select the evidence that
actually answers a question and return nothing when the answer is absent.

This is global evidence search with explicit current/include-history scope. It is
not automatic project attachment, outside-River suggestions, a generated-answer
test, or a measurement of the whole shipped app. Production D3 is unchanged.

## Dataset and frozen method

- 24 fictional libraries, 12 development and 12 evaluation, independently
  agent-authored and cross-reviewed before ranking. Not human-validated real data.
- 12 events and four questions per library: one current, one historical, one
  overlapping-topic and one unanswerable question. Each split has 36 answerable
  and 12 unanswerable questions; each answerable question has one labelled
  source/revision evidence target. Six historical targets per split are archived
  sources and six are superseded revisions.
- Candidates come from checkpoint 1's native ledger projection at each question's
  event boundary. Scoring sees question text, explicit scope and source-only text,
  not answerability, expected evidence, task mode, ideal assignments or future data.
- A = current-only production lexical scorer, positive scores, up to three results.
  B0 = the same scorer with explicit history scope; this is an untuned control.
  B = history-aware lexical with abstention. C = the same candidates scored using
  35% lexical coverage + 65% positive Apple sentence-embedding cosine, with
  abstention. No neural project matcher, training, cloud API or new model download.
- B/C each use exactly 48 development settings: eight minimum scores, three
  top-to-second margins, and a one/three-result limit. Development selection was
  sealed before held-out inference/metric evaluation. No held-out reselection.
- Quotes, source/revision IDs, version/snapshot IDs and retained-text locators must
  remain intact. Correctness requires the labelled supporting quote within the
  returned chunk, not merely a matching source ID. Repeated chunks of one
  source/revision are collapsed before applying the margin.

The existing explicit-English Mac embedding probe passed six neutral controls,
each repeated twice, with zero measured repeat delta. Only its sentence channel
enters C. This is current-runtime compatibility, not historical parity, iPhone
qualification, or proof of semantic quality.

See [frozen protocol](PROTOCOL.md), [selection](selection.json), and
[test commands/results](python-tests.json).

## Development finding — no candidate qualified

Across all 48 settings per family, none reached 90% returned-evidence precision,
let alone all the predeclared gates. Adding history without abstention (B0)
recovered 35/36 answerable targets versus A's 23/36, including 12/12 historical
targets versus 0/12. But it still returned something for all 12 unanswerable
questions and included many non-answering sources.

The frozen fallback is diagnostic-only, not a winner: B and C both use minimum
score 0.50, margin 0.10 and at most one result. On development, B returned seven
correct of ten results (70% precision, 7/36 recall); C returned six correct of
eight (75% precision, 6/36 recall). Both lost too much useful evidence and still
returned non-answering sources for some unanswerable questions.

## Held-out results — frozen settings, no reselection

Each row covers the same 48 questions in 12 evaluation libraries. “Unknown returns”
means an unanswerable question received at least one result; lower is better.

| Variant | Supporting results / all results (precision) | Answerable recovery | Historical recovery | Unknown returns |
| --- | --- | --- | --- | --- |
| A: current lexical reference | 23/144 (16.0%) | 23/36 (63.9%) | 0/12 (0%) | 12/12 (100%) |
| B0: history-aware lexical, no abstention | 35/144 (24.3%) | 35/36 (97.2%) | 12/12 (100%) | 12/12 (100%) |
| B: lexical + strict filter, diagnostic only | 5/5 (100%) | 5/36 (13.9%) | 1/12 (8.3%) | 0/12 (0%) |
| C: lexical + local sentence embeddings + strict filter, diagnostic only | 3/3 (100%) | 3/36 (8.3%) | 0/12 (0%) | 0/12 (0%) |

B0 gains **33.3 percentage points of recovery** over A, entirely from the 12
historical targets. Both recover 12/12 current and 11/12 overlapping-topic targets.
That supports the value of exposing retained history; it does not solve answer
support or uncertainty.

The apparent 100% precision of B/C is **not a win**. B returns only five results
across five libraries; C returns only three across two. B suppresses 31 of 36
available answers; C suppresses 33. Both fail the support, recall-gain, current,
overlap, historical and coverage gates. They were already nonqualified on
development and cannot be promoted based on a few correct evaluation returns.

A/B0 return three results on every question. B returns nothing on 43/48 questions;
C returns nothing on 45/48. This is the practical user-experience trade-off: broad
search finds useful history but includes non-answering context; these strict
filters make useful history disappear. Adding this particular semantic blend
did not resolve it. This is not a general claim that all embeddings are harmful.

Machine-readable counts, per-library outcomes and gate flags: [results.json](results.json).

## How to read the metrics

**Precision** is labelled supporting evidence divided by all returned evidence.
**Recall** is the library-balanced fraction of answerable targets recovered;
because this dataset is balanced with one target per question, it also equals
correct hits out of 36. **False-return rate** is the fraction of the 12 unanswerable
questions receiving any result. Missing result slots are not counted as correct.

The reference often fills three result slots, while each answerable question has
only one labelled target. Consequently, an always-three-results policy has a
maximum pooled precision of 36/144 = 25% on this particular benchmark, even if
every answer appears somewhere in its list. This does not mean the app is only
25% accurate. It explains why we report recovery, abstention and list lengths
alongside precision and require useful coverage before a restrictive filter can
qualify. The thresholds were not relaxed after observing this trade-off.

## What the errors mean

A development example asks: “Which tool number is mentioned in the loose crack
memo?” The returned memo explicitly says that no tool number was spoken. Another
asks for a millimeters-per-pulse calibration, while the returned source says the
poured volume was not recorded, so that calibration cannot be established.

Both are topically related, honestly quoted sources, but neither supplies the
requested answer. The frozen contract counts these returns as abstention errors;
this is **not** evidence of hallucinated text. In a browsing UI those sources might
still be useful if labelled as explaining a missing fact. A future product contract
should distinguish related context, positive answer support and explicit evidence
that a fact is unknown. We do not relabel these cases or recompute easier success
metrics after seeing the results.

Strict margins have a different failure mode: several legitimate, related sources
can score similarly, so rejecting every close race also hides valid evidence.
The development numbering-notebook example additionally shows lexical overlap
ranking a glossary/caption above the actual revised numeric range. Retaining a
source is necessary; topical similarity alone does not establish answer support.

## Limits and review boundary

This is a small, consumed, agent-reviewed English stress set with short extracted
text and a single target per answerable question. It does not measure broad
real-user accuracy, multilingual quality, original media playback, long-document
retrieval, multi-source synthesis, scale, phone latency or production storage.
Future tuned models need fresh evaluation data. The original outside-River gates
remain unmeasured here and cannot be claimed as passed.

## Verification and saved checkpoint

- 196 Python tests passed across the seven existing/new suites; the 31 ranking
  tests were also rerun successfully after inference started. Exact commands and
  outputs are in [python-tests.json](python-tests.json).
- 317 benchmark text embeddings saved (160 development, 157 evaluation), 24 library
  score tables, 96 development configurations, sealed selection and held-out
  predictions/results. Native probes were reused; no new model build was required.
- Independent audit of all 192 family/question combinations and 296 returned
  citations passed: source/revision, native quote, locator, snapshot/version and
  explicit scope/event boundary were preserved. Independently counted outcomes
  agree with the reported metrics.
- Metric replay from saved scores produced identical result/prediction bytes and
  preserved modification times. Frozen code/runtime/input bindings and all 2,779
  protected earlier files passed verification. See [audit](final-verification.json).
- Saved-unit pause/resume passed, preserving the initial catalogue and embedding
  by both hash and modification time. See [pause proof](pause-proof.json).
- No app changes, phone use, personal-vault access, model training/download, paid
  API calls or Git mutations. Workers stop at checkpoint completion; resource
  accounting retains the original baseline, 18 GiB cap and 10 GiB free reserve.

Verification commands actually run:

```sh
python3 -B scripts/provenance-first/history-ranking/qa/verify_checkpoint.py
python3 -B scripts/provenance-first/history-ranking/rk_runner.py verify
python3 -B scripts/provenance-first/history/control.py verify
python3 -B -m unittest discover -s scripts/provenance-first/history-ranking -p 'test_*.py'
git diff --check
```

## Recommendation and position in the larger plan

1. **Keep production unchanged.** History-index correctness/coverage (checkpoint 1)
   is complete. Relevance/abstention comparison (checkpoint 2) is complete with a
   no-go result. Conditional phone/app integration (checkpoint 3) is not started.
2. **Retain the version-aware index as the useful foundation.** B0's recovery gain
   merits preserving it, but not presenting its search results as verified answers
   or automatically reorganizing projects.
3. **Next decision: define the evidence/answer boundary before another model sweep.**
   Specify separate states for a related source, a source that supports the requested
   fact, and a source explaining that the fact is missing. Then design one bounded
   answer-support/uncertainty experiment using the cached retrieval stage and fresh
   evaluation examples. A query–passage verifier is a candidate to test, not an
   established solution. Do not assume a larger model or another similarity
   threshold will fix this. Do not start training, RL or a broad grid search yet.

Planning that narrow follow-up should take roughly 1–2 active hours; its execution
and device requirements need a separate estimate once the contract and candidate
are chosen. The earlier 6–12-hour integration estimate was conditional on passing
quality gates and is not an approved next step here.

**Stopped for user review.** No app integration, phone deployment, new experiment,
relabelling or threshold search follows automatically. All results are saved.
