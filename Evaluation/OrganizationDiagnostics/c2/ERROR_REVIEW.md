# Post-freeze error review

An independent review agent inspected the frozen C2 traces and semantic results after
prediction publication. This is a diagnostic analysis, not another blind labeling round
or human validation. No policy, threshold, label or score was changed.

## Findings

Corroboration reduces wrong attachment events for every hybrid seed:
17: 94→52; 29: 91→54; 41: 101→46 (each out of 360 eligible captures).
But missed events increase: 173→206; 177→202; 169→215 (each out of 279).
No seed provides an unambiguous precision-and-recall win.

Shared retrieval contains 861/906 same-project predecessor pairs (95.03%). Only 45
are absent. Strongest hybrids miss 585/581/549 same-project capture pairs; corroborated
hybrids miss 618/621/636. Retrieval limits therefore cannot explain most of the misses.
These are observed-prefix diagnostics, not estimates of deployment accuracy.

## Distinct failure mechanisms

1. **Direct scorer mistake.** `story-02`, chronological `e02`, `c02–c01`: a battery
   experiment explicitly says it is independent of the humidity study, but all scorers
   accept. Hybrid probabilities are 0.984914/0.990339/0.980552; baseline 0.999159.
   Singleton corroboration allows 1/1 support, so it cannot prevent this first mistake.
2. **Propagation through an already mixed thread.** Same story, `e09`, seed 17: the
   disjoint `c08–c01` pair scores only 0.442789. However, `c08–c02` (0.995574) and
   bridge `c08–c06` (0.999920) are valid supports. Joining their mixed thread still
   creates the wrong `c08–c01` relationship. A pair-level rejection is not a thread-level
   veto in the tested policy.
3. **Correction to a contaminated destination.** Same story, `e11`, seed 17: correcting
   `c04` through anchor `c02` reduces target-pair errors from 3 to 1. The destination
   remains mixed. The simulator must faithfully preserve this result; using gold to
   silently repair the whole destination would invalidate the experiment.
4. **Good candidates retrieved but scored below threshold.** `story-01`, `e16`, seed 17:
   wrong-project `c12–c02` scores 0.991028, while true-project retrieved `c01` (0.934211)
   and revised `c03` (0.972646) fall below the unchanged threshold. This is not a
   retrieval failure.
5. **Intentional abstention and structural limits.** `story-01`, `e07`, strongest seed 17:
   a bridge qualifies two independent threads. The maximum-one-attachment policy
   proposes instead of auto-merging; the new singleton misses three valid pair links.
   Repeated proposals can preserve fragmentation. This test does not simulate a user
   resolving every proposal, so missed attachments include intentionally deferred work.

Wrong-event breakdown by supporting pairs (seed order 17/29/41):

| Supporting evidence at a wrong attachment | Strongest hybrid | Corroborated hybrid |
|---|---:|---:|
| At least one known disjoint supporting pair | 51 / 54 / 53 | 38 / 40 / 35 |
| All supporting pairs known same-project | 42 / 36 / 48 | 14 / 14 / 11 |
| Uncertain support, neither category above | 1 / 1 / 0 | 0 / 0 / 0 |

Membership overlap is deliberately non-transitive: sharing with a bridge does not
make two independent projects identical. The second row includes contamination and
non-transitivity effects; it must not be called a direct pair-classifier error.

## Recommendation

First add the missing **simple-baseline corroboration control**, keeping the same
cached scores, thresholds, retrieval, stories and orders. Add a fixed-prefix audit
that compares scorers on identical thread memberships to isolate score differences
from earlier state divergence. The current experiment cannot tell us that the neural
model is necessary for the corroboration benefit.

Next, use that diagnosis to evaluate conflict-aware thread evidence and an explicit
proposal/correction recovery workflow. Do not infer permission for automatic merges,
hard-code these story phrases, or start more training from this report alone.
Any later tuning on these exposed stories is development work and requires new,
untouched qualification evidence before a shipping decision.
