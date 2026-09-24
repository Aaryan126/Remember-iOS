# Stage 2 complete — no-go for the local grouping reviewers

16 September 2026. **The bounded comparison is complete; neither local reviewer
nor any tested D3/reviewer combination passes the frozen safety gate.** Keep the
current organizer unchanged. The newer phone setup can run this task, but that
does not make its judgments reliable enough for automatic placement or separation.

Work is checkpointed and stopped for review. The phone probe has exited; it is
safe to disconnect or close the laptop. No production, personal-library, cloud,
paid-API, training, threshold or Git-state changes occurred.

## What finished

- Same exposed C5/C6 diagnostic: eight fictional families, 112 distinct visible
  inputs expanding to 160 scored packets per reviewer. Existing labels were
  reviewed by agents, not independent humans. This is **not new held-out data**.
- Two frozen reviewers: unchanged C7 and one boundary-focused prompt; identical
  structured schema, fresh sessions, greedy decoding, 600 output tokens, no tools,
  truncation, prompt tuning, repaired answers or retries. The original installed
  probe and its input/model/build hashes were preserved.
- All 56 fresh phone pair controls completed. Production FP16 and the separate
  FP32 evaluation export agree on every acceptance decision, and their expanded
  predictions exactly match the historical seed-29 control on this corpus.
- 224 scheduled primary slots: **223 returned responses and one preserved
  unknown-execution transport error** (`c7-004`). All eight scheduled repeats
  returned. That is 231 returned Stage 2 responses, not 320 independent calls.
- 232 Stage 2 reservations plus two earlier generation attempts = **234/256** of
  the approved cap. The interrupted request was never retried. This continuation
  added 223 requests, with no further transport/native failure.
- Fifteen derived prediction variants, 2,400 scored packet outcomes. FP32/FP16
  policies and veto/confirmation policies produce identical predictions here;
  those duplicate results are not independent evidence.

The [original protocol](../quality/PROTOCOL.md) and
[approved continuation](PROTOCOL.md) remain separate. The only execution amendment
is the explicit host-side transport-error disposition. No fabricated native answer
was inserted. Its corresponding context packet stays in every relevant error,
recall and correctness denominator.

## Main results: context-rich view

80 packets: 32 true continuations/shared-project relationships, 32 separate
relationships and 16 unresolved relationships. Errors are not abstentions.

| Candidate | Correct same / 32 | Correct separate / 32 | Wrongly says separate / 32 same | Unsupported decision / 16 uncertain | Errors / 80 |
|---|---:|---:|---:|---:|---:|
| Historical simple classifier | 24 | 0 | 0 | 5 | 0 |
| Fresh D3 FP16 pair control | 25 | 0 | 0 | 5 | 0 |
| C7 local reviewer | 10 | 26 | 19 | 15 | 10 |
| Boundary local reviewer | 12 | 27 | 15 | 15 | 11 |
| D3 + C7 confirmation/veto | 9 | 26 | 19 | 15 | 10 |
| D3 + boundary confirmation/veto | 9 | 27 | 15 | 13 | 11 |

D3's zero explicit separations is **by design**: this pair control emits only
same-project or abstain, not a separate-project verdict. Abstaining on a truly
separate case is not credited as a correct explicit separation. D3 nevertheless
incorrectly accepts 22/32 separate pairs in this deliberately difficult slice;
the reviewers' valid answers incorrectly accept 0/32, but introduce many false
separations and errors instead. Zero observed false acceptance is not perfect
safety, nor does it compensate for those other harms.

| Candidate | Same precision | Same recall | Separation precision | Separation recall | Correct / 80 |
|---|---:|---:|---:|---:|---:|
| Historical simple classifier | 47.1% | 75.0% | — | 0.0% | 35 |
| Fresh D3 FP16 pair control | 48.1% | 78.1% | — | 0.0% | 36 |
| C7 local reviewer | 90.9% | 31.3% | 44.1% | 81.3% | 36 |
| Boundary local reviewer | 75.0% | 37.5% | 50.9% | 84.4% | 39 |
| D3 + C7 confirmation/veto | 90.0% | 28.1% | 44.1% | 81.3% | 35 |
| D3 + boundary confirmation/veto | 81.8% | 28.1% | 50.9% | 84.4% | 38 |

Same/separation precision counts unsupported assertions on unresolved cases as
incorrect. A dash means the system made no such predictions, not 100% precision.

The boundary combination fixes 27 previously incorrect context decisions but
damages **25 previously correct decisions**, a net gain of only two. The C7
combination fixes 26 and damages 27. Boundary alone fixes 30 and damages 27.
These changes do not support a safe replacement for D3. In particular, higher
same-project precision comes partly from recognizing far fewer true continuations.

These numbers evaluate **pair judgments**, not the shipped organizer's complete
retrieval, corroboration, single-qualifying-thread rule, chronology or manual-placement
protections. Do not describe 48.1% as Remember's overall grouping accuracy. The
exposed, correlated challenge corpus intentionally concentrates on hard scope,
shared-planning and reference cases; it is not a representative personal library.

## Frozen gate: all candidates fail

The boundary reviewer has the highest standalone contextual correctness in this
screen, but passes only two of seven requirements:

| Requirement | Boundary reviewer | Result |
|---|---:|---|
| Same precision >=95% | 12/16 = 75.0% | Fail |
| Same recall >=75% | 12/32 = 37.5% | Fail |
| Separation precision >=90% | 27/53 = 50.9% | Fail |
| Separation recall >=80% | 27/32 = 84.4% | Pass |
| Unsupported uncertain decisions <=10% | 15/16 = 93.8% | Fail |
| Errors <=5% | 11/80 = 13.8% | Fail |
| More fixes than damages | 30 versus 27 | Pass |

The boundary/D3 combinations also fail five of seven requirements. C7 and its
combinations pass only separation recall. No FP32 combination changes this result.
The gate only licenses a proposal for fresh validation—not deployment—even if passed.

## What this means in practice

There is a narrow useful capability: both standalone reviewers get all eight
joint explicit-scope-versus-continuation contrasts right, in both views. They can
distinguish an explicitly separate commission from an explicitly continuing task.

But both get **0/8 complete bridge triples** and **0/8 complete before/after reference
groups** right in the context view. Neither produces a valid abstention on any of
the 112 unique primary inputs. Their confident boundary decisions do not reliably
track which projects the queried sources actually share.

Three concrete boundary-reviewer examples, with IDs pointing to saved evidence:

1. **Useful separation** — `boundary-039`: one source commissions a harbour
   oral-history programme; another explicitly commissions a different weather
   bulletin with its own approval. The reviewer correctly says separate projects.
2. **Harmful false separation** — `boundary-067`: an otter-census source and a
   volunteer rota which explicitly includes that census share the census project.
   The rota also includes a reedbed survey. The reviewer focuses on the two grants
   and incorrectly says the queried sources are separate. Their shared work is lost.
3. **Confident guess on ambiguity** — `boundary-095`: a voice memo says “that
   harbour segment” was approved, without identifying which of two programmes.
   The reviewer asserts separation instead of acknowledging the unresolved reference.

All three have valid exact quotations. **This is not merely a citation-formatting
problem.** Automatically vetoing D3 with these answers would fragment valid threads;
silently repairing quotations would not fix the underlying semantic mistakes.

## Pair-only view, labels and repeatability

80 packets: 23 same, 24 separate and 33 unresolved, under adjudicated labels.

| Candidate | Same recall | Wrong separate / 23 same | Unsupported / 33 uncertain | Errors / 80 | Correct / 80 |
|---|---:|---:|---:|---:|---:|
| Fresh D3 FP16 pair control | 20/23 = 87.0% | 0 | 11 | 0 | 42 |
| C7 local reviewer | 14/23 = 60.9% | 8 | 29 | 6 | 37 |
| Boundary local reviewer | 12/23 = 52.2% | 10 | 31 | 4 | 35 |
| D3 + C7 confirmation/veto | 12/23 = 52.2% | 8 | 23 | 6 | 41 |
| D3 + boundary confirmation/veto | 10/23 = 43.5% | 10 | 21 | 4 | 43 |

The original labels differ from adjudicated labels in one pair-only case. Original
and adjudicated results are both saved in `summary.json`. The contextual scores,
gates and no-go conclusion are unchanged. With original labels D3 gets 43/80 pair
cases correct instead of 42; the listed reviewer correctness counts do not change.

Primary unique-input failures: C7 has 12 ungrounded-quotation outputs plus the one
transport error; boundary has nine ungrounded-quotation outputs and four missing
queried-source citations. Deduplication expansion changes packet-level counts.

Seven of eight repeat comparisons have valid matching evidence/verdict predictions.
The remaining C7 comparison repeats an invalid-quotation failure; it earns no valid
agreement credit. Rationale wording is not part of this prediction-agreement check.
This tiny repeat sample is not a reliability guarantee.

Median successful generation response time: **C7 3.70 s**, **boundary 4.22 s**;
maxima 12.67 s and 7.91 s respectively. These exclude process-launch overhead and
include responses later rejected by citation validation. They are not cold-model
load benchmarks. The continuation launch span was approximately 19.1 minutes,
including its pause/resume check.

The historical Mac C7 result and this phone result use the same prompt/schema but
different platform/runtime/model conditions. The new result is much more willing
to assert separation. This is not a controlled OS-only A/B test, so do not attribute
the change solely to iOS 27 or claim a general improvement/regression in Apple's model.

## Recommendation and larger-plan status

1. **Close this bounded local-reviewer screen as no-go.** Do not add either reviewer
   to automatic placement or introduce an automatic split/veto path. Do not start
   another training sweep or tune prompts on these exposed examples.
2. **Keep the current free-tier organizer and its safeguards unchanged.** FP32 has
   not improved these decisions; its separate numerical benefits/costs and the
   failed historical FP16 parity gate remain open qualification concerns, not
   erased by this quality screen.
3. **Before another model experiment, review the relation contract and error cases.**
   Shared planning documents need project-overlap semantics without merging all
   projects they mention; unresolved references need genuine abstention. Both
   reviewers already received those instructions and still failed. A further
   experiment should have a materially different, testable mechanism, not simply
   another wording change. A bounded offline design/error review is the next useful
   step; it needs no phone or paid API and should produce a go/no-go plan first.
4. Any later candidate must first pass a comparable frozen screen, then fresh
   family-separated validation and chronological River replay before suggestions-
   first integration is considered. Existing Pro API evidence remains separate;
   this test does not change the production free tier or establish cloud results.

The larger plan's two approved stages have now yielded readiness evidence and a
completed quality decision. This does **not** mean the entire project is qualified
for release: full organizer/UI coverage, representative validation and original
numerical compatibility remain separate work. No next experiment has started.

## Evidence and checks

- `python3 -B -m unittest discover -s scripts/ios27-quality-continuation -p 'test_*.py'`:
  11 passed, including the transport-error denominator, no-retry handling and full
  synthetic evaluator smoke. All nine iOS 27 runner suites: **75 tests passed**.
- `freeze`, bounded `run`, `pause`, expected paused exit 75, then `resume`: completed
  223 new units. First saved unit's hash/mtime unchanged; original checkpoint unchanged.
- `evaluate` run twice: identical saved predictions/metrics, all ten reviewer/policy
  gates false. A separate recount checked **90 metric scopes** across both label sets
  and all 15 variants. All native outputs replay from checksummed raw evidence.
- `verify`: passed. Final scoped device-process inspection: no probe running;
  `status` after pause reports `safeToClose: true`. No process termination needed.

See `summary.json`, `predictions/`, `audit.json`, `complete.json`, `resume-proof.json`,
`validation/`, `disposition.json`, and `process-closure.json`. Detailed family and
joint-contrast metrics are retained in the JSON; no independent-sample confidence
claim is made from these eight exposed template families.

Continuation code lives in `scripts/ios27-quality-continuation/`; the original
runner, protocol, report, checkpoint and all prior raw evidence remain unchanged.
