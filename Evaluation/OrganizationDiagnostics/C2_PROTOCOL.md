# Checkpoint 2 — frozen-policy chronological diagnosis

Authorized by the user's “proceed” after checkpoint 1. This protocol is prospective
until a C2 manifest is published. No training, downloads, phone use, personal vault,
or production integration. Keep checkpoint 1 and all P2 artifacts unchanged.

## Fixed comparisons

Use all 12 reviewed stories, all three released orders, and eight policy instances:
one production embedding-only **placement** reference, one six-feature simple control,
and three seeds each of strongest-member and corroborated hybrid attachment. There are
288 policy streams and 4,632 policy prefixes. Report every seed, not a chosen winner.

All models, TF–IDF vocabulary/IDF, feature definitions and thresholds come unchanged
from P2 English attempt 02. No fitting on these stories. Verify portable features and
model outputs against 16 predeclared existing P2 prediction pairs before new scoring.
The 16 cases are the first 16 IDs in the frozen seed-17 evaluation prediction order;
they are reference-output checks, not a fresh evaluation. The old final test stays closed.

- Baseline threshold: 0.9984624186401344, with original three-class argmax eligibility.
- Hybrid thresholds: seed 17 = 0.9732961945149138; 29 = 0.9804276486193665;
  41 = 0.9742345622672387. Average both MiniLM directions and apply the frozen combiner.
- Baseline/feature parity tolerance: 1e-12. Neural probability parity tolerance: 1e-5
  absolute on MPS; any changed accept/reject decision on the reference cases fails.
- English Apple dual embeddings use the preserved explicit-English probe, with installed
  assets only. Cache by exact text SHA-256, including revised versions. Missing or
  incompatible vectors are reported and do not authorize confident pair attachment.

## Retrieval and attachment

At a capture, retrieve only active, previously observed sources. The shared candidate
set is top five contextual similarities plus top five frozen TF–IDF similarities,
with reciprocal-rank fusion constant 60, one-based ranks and stable source-ID ties.
Zero lexical scores remain eligible for retrieval; unavailable contextual scores do not.
No vocabulary or corpus statistics are fitted on the current story or future captures.

Candidate threads contain at least one retrieved member. Rank their retrieved evidence
using the shared retrieval order, not neural scores. Strongest-member variants accept
a thread if any retrieved member meets that variant's unchanged threshold/eligibility.
Corroboration uses the top three retrieved members and requires:

- One-member thread: one supporting match, so new threads can grow.
- Two-member thread: both supporting matches.
- Three or more active members: two supporting matches among the top three retrieved.
  Insufficient retrieved evidence fails the quorum; it is not silently weakened.

Exactly one qualifying thread permits automatic attachment. Multiple qualifying threads
produce a proposal and leave the new capture in its own singleton; no qualifiers also
leave a singleton. None of these experimental policies automatically merges threads.
New singleton IDs are `t:<sourceID>`. Provisional singletons represent unassigned items;
they must not be mistaken for a semantically correct named project.

## Reference scope

The native Swift adapter uses the unmodified production ProjectEmbedding, ProjectMath
and ProjectTopicEvidence code. It mirrors new-capture placement's compatible vectors,
all-member support/coherence, centroid threshold, semantic check, lexical grounding and
clear-winner margin. It uses all active threads rather than the shared top-five retrieval.

This is not the entire ProjectGraphService: no local/cloud reasoner, periodic merge/split
maintenance, metadata generation or re-indexing after a revision. Both the placement
reference and controlled policies make automatic decisions only at capture; revisions
update text for future evidence while preserving existing assignments. Stable textual
thread IDs replace UUID tie ordering and member evidence is stably ordered. Disclose
these adaptations; do not describe this as a full production organization benchmark.

## Explicit corrections and information boundary

The C1 fixture compiler translates each scripted user project selection to a previously
observed, single-project anchor capture from that correction's dependency ancestry.
Choose the lexically first eligible capture ID, exclude the corrected target, and fail
if none exists. This is a **scripted user choice**, not model-discovered information:
the compiler may read annotated fixture membership solely to encode the explicit action.

The policy receives only `targetAnchors` and the action's source evidence, never initial
memberships, project definitions or expected state. It assigns the corrected source to
the union of those anchors' current runtime threads. A contaminated or fragmented
runtime destination is not magically repaired using semantic gold. Record the anchor
mapping separately for audit. Other captures are not regrouped by a correction.

Text revisions preserve membership; archive/restore preserve text, history and membership
while changing activity. The ledger must reject any unexpected NoteDocument text
normalization rather than silently changing hash expectations.

Offline content-addressed pair caches may cover all textual versions, but policy lookups
must be limited to currently observed versions. Freeze all predictions before loading
gold into the separate metric process. Reference case expected predictions are parity
checks only and must not become scorer features.

## Measurements and replay

Report per-prefix counts and denominators, per-story/order summaries, all seed variants,
and macro summaries. Include known-label pair precision/recall, wrong and missed
new-capture attachments, unknown-item joins, proposals, fragmentation and mixed threads.
A pair is semantically same only if its gold membership sets overlap; a bridge does not
make its two independent projects transitively identical. Unknown `[]` gold is excluded
from known-label precision/recall and reported separately. Archived sources are excluded
from active grouping metrics but retained for history checks.

A capture has a wrong attachment if it joins at least one known disjoint prior source;
it has a missed attachment if it fails to join at least one known same-project prior
source. Both may occur. Report the pair counts and eligible event denominators, not only
headline event rates. Compare before/after correction using the corrected prefix's truth,
so a change in annotation is not misreported as model recovery. Retrieval coverage is
reported separately and is undefined for the differently scoped native reference.

Replay policy commands through actual MemoryStore and ProvenanceSnapshot in a uniquely
named simulator-only harness/store. Check materialized state and history at every policy
prefix, persistence after reopening, and separate explicitly commanded merge/split/undo
invariants. This validates command execution, not semantic grouping quality. No fixture
may touch the installed personal Remember app or its database.

## Integrity, resources and pause

Bind C1 completion, source files, model/tokenizer/probe versions, policies, thresholds,
input projections and runtime configuration before benchmark scoring. A single inference
worker operates at a time. Save each embedding, inference batch and policy stream as an
immutable artifact; record completion last. Verify a stop/restart on a small reference
fixture before the full batch. Pauses wait for the current bounded batch, persist state,
stop worker/child probes and confirm before the user closes the laptop. A simulator batch
can stop after its current independent run; retain every completed receipt and database.

Keep total new diagnostic storage, generated projects/builds and temporary files within
4 GiB; preserve at least 10 GiB free. No automatic deletion of previous artifacts or
other tasks' output. Curate small summaries/manifests outside ignored runs. Stop after
this checkpoint with a diagnostic recommendation, not a production-qualified model.

The runner reserves 1 GiB of that cap for incremental simulator files outside the run
directory; the ledger coordinator separately measures that delta and stops if it exceeds
the reserve. Thus in-repository diagnostic writes cannot consume the full 4 GiB themselves.
For ledger transport only, source `c01` becomes `localc01` (including mutation targets and
expected-state keys), so it maps to the same UUID as singleton `t:c01`. This is an explicit
identifier adaptation, not a semantic change. Raw policy traces retain the C1 source IDs.
