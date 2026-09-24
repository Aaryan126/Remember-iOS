# History recovery checkpoint 2 — frozen before ranking

Approved by user: “carrry on sorry”, following the completed checkpoint-1 report.
Run the bounded Mac-only relevance/abstention experiment, then STOP for review.
No production changes, personal-vault access, training, model downloads, paid API,
device deployment, automatic organization or Git writes. Preserve checkpoint 1.
Continue the 18 GiB conservative growth guard using the original baseline and
10 GiB free reserve. Do not clean or reset accounting automatically.

## Inputs and boundary

Use the frozen 12 development / 12 evaluation libraries from checkpoint 1. Scorers
receive source-only question text and explicit current/includeHistory scope, plus
the native source-text candidates at that question's ledger prefix. No task mode,
answerability, expected evidence, project names, ideal placements or future sources
enter scoring. Evaluation labels are opened for metrics only AFTER a development
selection artifact is frozen. They were previously visible to author/review and
coverage verification staff, not used for ranking selection.

Every candidate retains the native quote, version/snapshot ID and citation locator.
Score chunks, then collapse each source/revision to its highest-scoring chunk.
Returned identities are unique source/revision pairs. Ties follow descending source
capture sequence (the fictional captures have increasing creation times), then
chunk ordinal and stable candidate ID. Scores within 0.0001 are ties, matching the
existing native lexical helper. There is no generated answer.

## Fixed comparisons

- **A:** current-source lexical reference; production lexicalCoverage scorer,
  positive scores only, up to three identities, no learned threshold. It deliberately
  cannot recover archived/superseded targets. It shares checkpoint-1 source-only
  chunks, not generated summaries; this is a controlled reference, not the full app.
- **B0:** scope-aware lexical retrieval with the same positive-score/top-three
  rule. Diagnostic isolation of coverage, not a separately tuned candidate.
- **B:** scope-aware lexical retrieval with development-selected abstention.
- **C:** same scope-aware candidates; fixed 0.35 lexical + 0.65 positive sentence
  cosine from the existing English Apple embedding probe. Cosine is clamped to [0,1];
  do NOT reuse thresholds calibrated for cloud embedding vectors. Same development
  grid as B. No contextual/neural project-membership score and no new weights.

One finite grid per B/C: min score in [0, .20, .35, .50, .65, .80, .90, .95];
minimum top-to-second identity margin in [0, .05, .10]; max results in [1, 3].
Exactly 48 configurations per available family. Require positive scores as well as
min score. A missing runner-up has score zero. An unmet margin abstains for the
whole query. Otherwise return at most max-results identities exceeding min score.
Empty lists are valid. Do not tune per question, mode, domain, or evaluation split.

## Runtime qualification

Hash-bind existing Mac lexical and English dual-embedding binaries, build/source
receipts, current OS and model space. Before fixture inference, use six neutral
English controls (not benchmark text) through the same passage/query encoding path.
Require finite nonzero 512-dimensional channels, expected equal model spaces,
norm within 0.001 of one, repeated-output delta <=1e-5 and self cosine >=0.99999.
Only the sentence channel participates in C. This qualifies current-run vector
compatibility, NOT historical numerical parity, semantic quality or iPhone/Core ML.
If controls fail/unavailable, mark C unsupported and complete A/B without substitution.
If space/shape changes during caching, stop rather than mix spaces or hide fallback.

## Selection and go/no-go gates

Compute metrics on top-three maximum returned distinct source/revision identities.
Expected-evidence sets supply correctness: a returned source/revision must also
contain an expected supporting quote in the returned chunk (identity alone is not
enough). Nonrelevant returns on unanswerable
questions are errors. Missing slots are not correct. Report pooled precision,
library-macro recall on answerable questions, mode recalls, correct-hit coverage,
returned-list sizes, unanswerable false-return rate and exact numerators.

For a recovery candidate to qualify, ALL must hold on development, then evaluation:

1. Pooled returned-evidence precision >=90%, at least 20 returns across >=8 libraries.
2. Answerable library-macro recall gain >=10 percentage points over A (no rounding).
3. Current and overlap macro recalls each >=A; historical macro recall >=50%.
4. Correct-hit coverage on answerable questions >=2/3 and >=A.
5. At most 10% of unanswerable questions receive any result (<=1/12 per split).
6. All citation, version, scope/prefix, input-binding and replay integrity checks pass.

Choose per family from qualifying development configurations: highest answerable
macro recall, then precision, then fewer unanswerable false returns, then lower
max-results, higher min-score, higher margin. Choose the overall winner by the same
order; exact family tie prefers lexical B. If a family has no qualifier, freeze a
NONQUALIFIED diagnostic setting ordered by precision, macro recall, false returns,
and the same parameter simplicity tie-breaks. Zero returns have undefined precision
and rank below settings with measured precision. Never promote the diagnostic.
Evaluate A, B0 and frozen B/C settings once; no evaluation-time reselection.

The original outside-River >=90% precision/+10-point recovery requirements remain
unchanged. This global-search dataset supplies no selected River, so this experiment
does NOT measure that gate or qualify River-specific suggestions. The general
recovery gates above are necessary evidence for a later scoped integration decision,
not a substitute claim. Do not compare these numbers directly with prior routed-River
or project-attachment studies, and do not call agent-reviewed fiction real-user accuracy.

## Persistence and stop

Hash-bound immutable caches per text, score tables per library and prediction/metric
receipts. Pause at a text/library boundary; stop worker; resume verifies and skips
completed units. Prove one-unit reuse before bulk work. Freeze protocol/code and
inputs before dev ranking; freeze selection before evaluation inference or labels.
No automatic follow-up search, retraining, relaxed gate or app integration if failed.
Expected work: 8–14 active hours initially; update estimates as work progresses.
