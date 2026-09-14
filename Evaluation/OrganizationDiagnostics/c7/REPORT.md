# C7 — local semantic-verifier results

## Decision

**Complete; no-go for integration or qualification of this candidate.** Apple's local
model can recognize some explicit project boundaries that the existing matchers miss,
but this fixed-prompt verifier fails four of five prospective exploration criteria.
It rarely abstains when evidence is ambiguous, sometimes confuses shared planning
material with project identity, and produces invalid citations in eight native responses.

The combined policies improve some diagnostic counts, but none is safe enough to ship.
No production behavior, model weights, thresholds, personal memories or Git state changed.
Stop for user review; no next experiment has started.

## What ran

- Mac-only `SystemLanguageModel.default`, the on-device provider already used by the
  app's local reasoning path, but with a new isolated three-way verification task.
  This is not the app's candidate-selection prompt and is not a trained new model.
- A fresh session per input, default guardrails, greedy generation, 600-token output
  limit, no tools, cloud fallback, conversation history or external retrieval.
- The complete visible packet, without truncation: two queried sources and up to two
  additional contextual sources. Structured output: exact evidence quotes, verdict,
  and a short rationale. A decisive verdict must cite both queried sources.
- C6's 160 reviewed packets across eight fictional families; identical visible inputs
  reduce to 112 native requests. All outcomes were saved before metric calculation.
- Four cached legacy controls, local-only, always-abstain, four conflict-veto policies,
  and four confirmation policies: **2,240 derived outcomes**, not 2,240 model calls.

Veto retains the legacy prediction unless the local verifier explicitly says separate.
Confirmation accepts same-project only if both agree; explicit local separation still
overrides. Both propagate local output errors instead of silently falling back.

**These are exposed diagnostic cases, not fresh validation.** The prompt author knew
C6's failures. No prompt tuning or retries occurred after the C7 freeze. Independent
review happened in C6; it was not repeated or relabeled to favor this model. Agent
reviews and the synthetic templates can share systematic errors.

## Prospective exploration gate: failed

Contextual view, 80 packets: 32 same-project, 32 separate-project and 16 uncertain.

| Requirement | Observed local verifier | Result |
| --- | ---: | --- |
| Separation precision ≥90% | 9/14 = 64.3% | Fail |
| Separation recall ≥80% | 9/32 = 28.1% | Fail |
| Same-project recall ≥75% | 29/32 = 90.6% | Pass |
| Unsupported decisions on uncertain cases ≤10% | 15/16 = 93.8% | Fail |
| Error rate ≤5% | 6/80 = 7.5% | Fail |

These were exploratory thresholds, not production acceptance criteria. Even passing
would only justify fresh independently reviewed validation. High same-project recall
here largely comes with an excessive willingness to attach ambiguous sources.

## Pair-only results

80 packets: 23 same-project, 24 separate-project and 33 uncertain. Repeated pairs are
correlated, not independent trials. Same precision includes unsupported same-project
assertions in its denominator. Errors are separate from abstention and remain in recall
denominators; they cannot earn credit as correct uncertain answers.

| Candidate | Same precision | Same recall | Wrong same / 24 separate | Wrong separate / 23 same | Unsupported / 33 uncertain | Errors / 80 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 37.3% | 82.6% | 21 | 0 | 11 | 0 |
| Hybrid 17 | 38.2% | 91.3% | 21 | 0 | 13 | 0 |
| Hybrid 29 | 38.5% | 87.0% | 21 | 0 | 11 | 0 |
| Hybrid 41 | 37.5% | 91.3% | 22 | 0 | 13 | 0 |
| Local alone | 35.5% | 95.7% | 9 | 0 | 31 | 3 |
| Baseline + veto | 52.9% | 78.3% | 7 | 0 | 9 | 3 |
| Hybrid 17 + veto | 52.6% | 87.0% | 7 | 0 | 11 | 3 |
| Hybrid 29 + veto | 54.3% | 82.6% | 7 | 0 | 9 | 3 |
| Hybrid 41 + veto | 51.3% | 87.0% | 8 | 0 | 11 | 3 |
| Baseline + confirmation | 54.5% | 78.3% | 6 | 0 | 9 | 3 |
| Hybrid 17 + confirmation | 54.1% | 87.0% | 6 | 0 | 11 | 3 |
| Hybrid 29 + confirmation | 55.9% | 82.6% | 6 | 0 | 9 | 3 |
| Hybrid 41 + confirmation | 52.6% | 87.0% | 7 | 0 | 11 | 3 |
| Always abstain | Undefined | 0% | 0 | 0 | 0 | 0 |

Local separation precision is 14/14 on this view, but recall is only 14/24. This does
not establish perfect safety: it is a small, exposed, repeated-pair sample, and the
contextual view introduces false conflicts. The lower false-attachment counts are
real diagnostic gains, not sufficient overall reliability.

For example, among the baseline's 21 false same-project pair assertions, confirmation
turns 14 into correct separations and one into abstention; six remain wrong. None of
those 21 is merely hidden by an error. This separates genuine corrected decisions from
the other failure types rather than counting all missing attachments as improvements.

## Contextual results

The legacy controls still ignore extra context. The local verifier uses it. Do not
interpret a difference between view-level percentages alone as causal context benefit:
the reference labels differ between views. The paired examples below show actual
context-induced changes for the same queried pair.

| Candidate | Same precision | Same recall | Wrong same / 32 separate | Wrong separate / 32 same | Unsupported / 16 uncertain | Errors / 80 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 47.1% | 75.0% | 22 | 0 | 5 | 0 |
| Hybrid 17 | 49.1% | 84.4% | 22 | 0 | 6 | 0 |
| Hybrid 29 | 48.1% | 78.1% | 22 | 0 | 5 | 0 |
| Hybrid 41 | 48.2% | 84.4% | 23 | 0 | 6 | 0 |
| Local alone | 49.2% | 90.6% | 18 | 2 | 15 | 6 |
| Baseline + veto | 56.1% | 71.9% | 14 | 2 | 7 | 6 |
| Hybrid 17 + veto | 57.8% | 81.3% | 14 | 2 | 8 | 6 |
| Hybrid 29 + veto | 57.1% | 75.0% | 14 | 2 | 7 | 6 |
| Hybrid 41 + veto | 56.5% | 81.3% | 15 | 2 | 8 | 6 |
| Baseline + confirmation | 57.5% | 71.9% | 13 | 2 | 7 | 6 |
| Hybrid 17 + confirmation | 59.1% | 81.3% | 13 | 2 | 8 | 6 |
| Hybrid 29 + confirmation | 58.5% | 75.0% | 13 | 2 | 7 | 6 |
| Hybrid 41 + confirmation | 57.8% | 81.3% | 14 | 2 | 8 | 6 |
| Always abstain | Undefined | 0% | 0 | 0 | 0 | 0 |

The combination is not a free safety improvement: it introduces two false separations,
raises unsupported decisions on uncertain contextual cases compared with the legacy
controls, and inherits evidence errors. No seed is selected as a production winner.

## Mechanisms illustrated by the fictional Marble Desk family

1. **A genuine gain:** the database-migration note and a separately scoped security
   incident are correctly judged separate (`qb957718c29ac1fdb632a58af`). The migration
   rollback/retry is correctly judged a continuation (`q37c475a4972a0e261da5898b`). C6's
   legacy scorers got the former wrong and abstained on the latter.
2. **A bridge-induced regression:** adding an operations diary that coordinates both
   jobs changes the first judgment to same-project (`q8d2d71faf9f8834f76a9bc8f`), despite
   the source pair still describing distinct undertakings. Sharing a planning note
   must not merge the projects. The model provides real quotes but the inference is wrong.
3. **Guessing an unresolved reference:** “the fix worked after the restart” is attached
   to a project before the note identifies which job it concerns. In the complete
   benchmark the local verifier makes 46 unsupported decisive assertions across 49
   uncertain packets, and abstains only twice across all 160 packets.
4. **Identifier distraction:** it links the migration with a lobby carpet replacement
   sharing purchase reference MD-11 (`qda18e417e684b4acab6c12c0`), despite explicit text
   saying the flooring purchase is not the database engagement.
5. **Evidence failure:** in `q907056227666d5f8b8c8bcd0`, clarification text is attributed
   to the security-incident source instead of its actual source. The result is recorded
   as an error, not repaired or counted as a valid uncertain answer.

These are illustrative examples, not a blind independent explanation-quality audit.
Exact-substring validation does not establish that a quote supports the verdict.

## Cross-checks and limitations

- Local joint contrasts: scope/continuation 7/8 in each view; complete bridge triples
  5/8 pair-only but 0/8 contextual; complete before/after-reference contrasts 0/8 in
  both views. Errors fail a joint test, rather than disappearing from its denominator.
- On the four-family diagnostic partition, local separation precision is 11/15 (73.3%),
  recall 11/28 (39.3%), with unsupported assertions on all 24 uncertain packets.
  This partition is also exposed diagnostic material, not new qualification data.
- All original-label and C6-adjudicated metrics are retained in [summary.json](summary.json).
  The one C6 same-to-uncertain amendment lowers correct counts by one for every
  non-abstention candidate; always-abstain gains one. No labels were changed in C7.
- Eight distinct native responses fail validation: five have an ungrounded/wrong-source
  quote and three omit a queried source from decisive evidence. Repeated input mappings
  expand these to nine error packets: three pair-only and six contextual. No process
  crashes, availability failures, timeouts, hidden retries or automatic quote fixes.
- These eight fictional families reuse templates and correlated pairs; agent labels
  are not human ground truth. Nothing here validates actual media extraction, user
  preferences, large libraries, multilingual inputs or online retrieval/context choice.

## Runtime, verification and recovery

112 native requests took a summed 302.83 seconds of measured process time: mean 2.70 s,
median 2.63 s (average of the two middle observations), nearest-rank p95 3.72 s, maximum
5.33 s. These include process launch/session/generation but exclude build and runner
bookkeeping. The first request was 4.65 s; this is **not** a controlled cold-load test.
macOS 26.2 on Apple silicon, Swift 6.3.2. No iPhone, energy, peak-memory or new-model
storage measurement was performed. The native provider exposes no pinned weight hash;
OS/toolchain, availability, executable and source hashes are recorded instead.

The isolated build/cache occupies approximately 31 MiB. The cumulative diagnostic cap
and 10 GiB free-space reserve held throughout; approximately 24 GiB remained free.

- **193 Python tests passed**, including 21 C7 tests for source-only inputs, evidence
  validation, errors, gates, metric denominators, pause/resume and saved units.
- A real one-unit stop/pause/resume preserved the first unit's SHA-256 and timestamp.
- Exact replay checked all 112 native response interpretations, 2,240 derived outcomes,
  both reference variants and the exploration gate without rerunning inference.
- Parent C6 verification passed; its evidence and earlier checkpoints remain unchanged.

Commands executed with the existing feasibility virtualenv and
`PYTHONDONTWRITEBYTECODE=1`:

```sh
python -m unittest discover -s scripts/organization-diagnostics -p test_c7.py
python scripts/organization-diagnostics/c7_run.py build
python scripts/organization-diagnostics/c7_run.py tests
python scripts/organization-diagnostics/c7_run.py freeze
python scripts/organization-diagnostics/c7_run.py predict --max-units 1
python scripts/organization-diagnostics/c7_run.py proof-before
python scripts/organization-diagnostics/c7_run.py pause
python scripts/organization-diagnostics/c7_run.py predict
python scripts/organization-diagnostics/c7_run.py predict --resume
python scripts/organization-diagnostics/c7_run.py proof-after
python scripts/organization-diagnostics/c7_run.py evaluate
python scripts/organization-diagnostics/c7_run.py audit
```

The paused predict returned the expected exit 75; the resumed predict completed. Final
publication uses `complete`, followed by `verify`. See [RESUME.md](../RESUME.md) for
the exact interpreter, completion receipt and current status. Raw evidence is under
`runs/c7-01/`; a fresh checkout without those ignored artifacts cannot replay this run.

## Recommendation

Do not add this verifier to automatic grouping or splitting. Retain the existing app
unchanged; the improved diagnostic combinations are not production-qualified either.
Do not tune another prompt on these exposed examples and call it independent progress.

Before a further model experiment, narrow the representation: distinguish a source's
references to one or more projects from the identity of the projects themselves, and
make unresolved references an explicit state. The observed bridge and ambiguity errors
are the behaviors any future classifier or extraction-based verifier must be trained
and tested to avoid. Keep embeddings as candidate retrieval, not proof of identity.

That is a design hypothesis, not an extraction approach already shown to work. A future
proposal should have fresh family-held-out examples, targeted bridge/unknown cases,
and separate semantic-versus-citation checks. This candidate has not earned a larger
training or integration effort. C7 ends at this saved checkpoint for user review.
