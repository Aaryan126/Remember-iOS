# Organization benchmark contract v1

## Product truth, not implementation imitation

A thread is one specific continuing context (a project, assignment, trip, event, or distinct task). A broad discipline is not sufficient. Different budgets, designs and meetings for the same project belong together when the supplied evidence supports that identity. Two assignments in one class or two trips to the same city remain separate. Mere shared vocabulary, format, or style is not identity.

A source explicitly about two contexts may belong to both; it must not cause the contexts themselves to merge. Revisions, changed dates and contradictory statements about one context remain together, with historical order preserved. A singleton is correct when no other supplied source supports a shared context. Never invent missing context. Mark genuine ambiguity rather than forcing a grouping. Relationship links and membership are separate labels; related contexts need not merge.

## Blind agent review

Authors write inputs and candidate labels. Two fresh-context reviewers independently receive ONLY this contract and inputs.json, not author-labels.json, the application code, thresholds, old fixtures, predictions, or each other's decisions. They may read AGENTS.md. They inspect every item in each assigned library. Library context is allowed, future evidence is not allowed when reviewing temporal checkpoints.

Each reviewer writes a review JSON with schemaVersion=1, reviewer ID, role, actual model identity if known (otherwise unknown), blindToPredictions=true, and libraries. Every library contains id, memberships (item ID to nonempty list of reviewer-defined thread IDs), ambiguous (item IDs), rationale (item ID to brief source-grounded justification), and issues. Labels are compared by member relationships, never by matching arbitrary thread names. Reviews record judgments, not hidden chain of thought. Do not simply copy the author's intended narrative.

An adjudicator sees both reviews and the sources after independent review. Resolve disagreements through source evidence; allow ambiguity or permitted alternatives. Preserve all original reviews. An adversarial audit repeats a deterministic 20% item sample in shuffled order, checking evidence, superficial keywords and label leakage. Consensus is not proof of correctness; identical model families can share errors. This dataset is agent-reviewed, not human-validated.

## Files and isolation

inputs.json contains {schemaVersion:1,libraries:[{id,split,slice,items:[{id,text,kind,timestamp}]}]}. No gold IDs in input metadata. Natural project identifiers in actual source content are valid evidence. Author labels and reviewed labels contain {schemaVersion:1,libraries:[{id,memberships,relationships,ambiguous,rationale}]}. Relationship entries use first, second (gold thread IDs), related (boolean), evidence (item IDs).

Six libraries are development and six heldout. l01–l05 are development English; l06–l10 heldout English; l11 development multilingual; l12 heldout multilingual. Each has 30 items. Keep source/paraphrase/revision/media families within a split. Public data is separately labeled public and separately scored. No private vault data.

The phone receives allowlisted inputs and run configuration only, NEVER any labels or reviewer artifacts. The runner calls production code in an isolated app/container, with hosted inference disabled. No policy tuning in this milestone. Freeze dataset/review/scoring hashes before any predictions. Heldout results consume that benchmark version for later tuning purposes.

## Preregistered metrics and targets

Core: pair precision >=0.99 and recall >=0.85 on unambiguous heldout English cases, with zero explicitly prohibited automatic merges. Report counts, macro library averages, fragmentation and automation/abstention; no merging means undefined precision, not 100%. Agent disagreement/ambiguous coverage must be reported. These targets are diagnostics, not statistical certification.

Pairwise truth means two items share at least one valid thread; pairwise prediction means they share at least one observed thread. Also calculate overlap-aware B-cubed using multiplicity: for each item, average min(number of shared predicted clusters, number of shared gold clusters)/number of shared predicted clusters over predicted neighbors; recall swaps the denominator and neighbors to gold. Include self. This reduces to ordinary B-cubed for partitions. Report macro per-item then per-library values. Reference: Amigó et al., https://doi.org/10.1007/s10791-008-9066-8.

Primary scores exclude explicitly ambiguous items and report them separately; never silently exclude missing predictions. Results with missing/unrecognized/duplicate inputs are invalid. Membership arrays must be nonempty with unique cluster IDs. Run failures are not semantic successes. Related edge scoring maps predicted groups to the greatest Jaccard-overlap gold group, deterministic lexical tie break, and separately counts ambiguous mappings.

30-item libraries are independent scoring units; arrival orders/repeats are not additional independent samples. Bootstrap library averages with 2,000 resamples and seed 1729; small-library intervals are descriptive, not a generalization guarantee. Scorer computes deterministic metrics; agents do not grade app outputs for the headline score. Reasons may be examined afterward for failure analysis.

Provenance integrity must show zero observed invariant violations. Scripted/injected merge decisions test bookkeeping only, not semantic merge correctness. Missing models, extraction failures, unavailable assets, timeouts, and unexecuted modes stay visible. Video analysis currently covers captions only. Scope does not include new video understanding, hierarchy, threshold changes, or hosted inference.
