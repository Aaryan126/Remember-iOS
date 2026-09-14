# Controlled merge / split opportunities

This supplementary diagnostic measures actual production batch decisions on controlled initial states. It does **not** represent naturally evolved capture histories, and its success rate must not be combined with natural clustering scores.

The host derives 24 cases from the frozen reviewed Remember corpus: one merge and one split opportunity per library. It selects only unambiguous single-membership sources, deterministically by source timestamp and opaque ID, never by model results.

- Merge: four sources from the same reviewed context, seeded into two separate unpinned two-member threads.
- Split: two sources from each of two distinct reviewed contexts, seeded into one unpinned four-member thread.

The device receives only source excerpts, generic initial memberships, source IDs, and split/library metadata. Expected partitions, opportunity types, acceptable complementary split subsets, and source gold context names remain host-side. Derived input and label files are independently hashed before execution.

## Derive and prepare

```sh
node scripts/embedding-evaluation/derive-decisions.mjs \
  --inputs Evaluation/Organization/inputs.json \
  --labels Evaluation/Organization/labels.json \
  --freeze Evaluation/Organization/freeze.json \
  --output Evaluation/Organization/decisions

node scripts/embedding-evaluation/prepare-decisions.mjs \
  --inputs Evaluation/Organization/decisions/inputs.json \
  --freeze Evaluation/Organization/decisions/freeze.json \
  --grdb /tmp/RememberProvenance/SourcePackages/checkouts/GRDB.swift \
  --mode both --split all --derived-data /tmp/RememberDecisionProbeBuild
```

`derive` refuses to overwrite an existing directory or accept mismatched core frozen inputs/labels. The derived freeze also binds this contract, the scorer, and the probe source. Preparation verifies these hashes and only projects permitted fields into a temporary standalone project. Scoring requires the same freeze hash recorded by the device plus unchanged inputs, labels, scorer, contract, and probe. The old probe and main organization probe are not modified.

## Execute and collect

Use the paths printed by preparation. The app has its own identifier and no App Group entitlement. Never uninstall or reset Remember.

```sh
xcodebuild -project <generated-project> -scheme OrganizationDecisionProbe \
  -destination 'platform=iOS,id=<paired-device-UDID>' \
  -derivedDataPath /tmp/RememberDecisionProbeBuild \
  -disableAutomaticPackageResolution -allowProvisioningUpdates build
xcrun devicectl device install app --device <device-ID> <generated-app>
xcrun devicectl device process launch --device <device-ID> \
  --console --timeout 1800 SimpleStudio.Remember.OrganizationDecisionProbe
xcrun devicectl device copy from --device <device-ID> \
  --source <printed-Documents-result-path> --destination /tmp/organization-decisions-results.json \
  --domain-type appDataContainer --domain-identifier SimpleStudio.Remember.OrganizationDecisionProbe
```

Each scenario inserts original source/enrichment events, obtains actual Apple vectors, and seeds four current-policy placement events with valid source revisions and non-user origin. These are explicitly marked initial-state events, not scored predictions. There are no pins or altered policy thresholds. Four placements trigger the normal early-library batch rule. Repeated production synchronization settles merge/proposal/checkpoint events, bounded to 16 passes and a cooperative ten-minute limit. The host timeout is needed for non-cooperative OS calls.

The service's current cached-placement path normally bypasses the reasoner. Local batch merges and split proposals are heuristic decisions, so embedding/local modes may yield the same results; do not imply independent Foundation Models evaluation when recorded reasoning calls are zero. Missing embedding IDs remain in the opportunity denominator and are separately reported. No cloud reasoning is allowed.

The app atomically saves each completed/error/timeout scenario, closes its database before removing the unique temporary directory, and resumes terminal scenarios on relaunch. A `running` case restarts cleanly after interruption. Results include initial/final memberships, only **post-seeding** events, citations, vectors, model availability, and timing. A process exit of zero means collection finished, not that decisions were correct.

## Score

```sh
node scripts/embedding-evaluation/score-decisions.mjs \
  --inputs Evaluation/Organization/decisions/inputs.json \
  --labels Evaluation/Organization/decisions/labels.json \
  --freeze Evaluation/Organization/decisions/freeze.json \
  --results /tmp/organization-decisions-results.json
node --test scripts/embedding-evaluation/score-decisions.test.mjs
```

Report merge and split opportunity recall separately, with exactly 12 opportunities per mode when all libraries were selected. Missing, errored, timed-out, or unavailable cases are not silently dropped. Event precision is undefined (`null`) when no corresponding events were observed. A merge succeeds only when a real merge event yields the required final partition. A split succeeds only when an acceptable complementary subset is proposed **without automatically changing memberships**. Incorrect proposals and unexpected membership rewrites are explicit failures. The scorer also verifies that observed seeded partitions match the frozen initial state.

These cases are constructed from the main reviewed labels and are not a new independent held-out set. Their purpose is to distinguish lack of opportunity from failure to act, alongside the independent capture-order benchmark and deterministic provenance-integrity tests.
