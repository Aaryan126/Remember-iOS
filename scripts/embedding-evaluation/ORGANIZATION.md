# Isolated organization benchmark runner

This is separate from the original 42-item `EmbeddingProbe.swift`, which remains unchanged. The new app identifier is `SimpleStudio.Remember.OrganizationProbe`; it has no app-group entitlement and never opens Remember's personal store. Every scenario uses its own temporary database. Cloud assistance is forcibly disabled in this app's defaults before any service starts.

## Prepare, build, and run

```sh
node scripts/embedding-evaluation/prepare-organization.mjs \
  --inputs Evaluation/Organization/inputs-reviewed.json \
  --grdb /tmp/RememberProvenance/SourcePackages/checkouts/GRDB.swift \
  --split development --mode embedding
```

Preparation prints a temporary project and `configuration.json` path. It only reuses an existing GRDB checkout. It invokes no Git commands or package downloads. Only explicitly allowlisted inputs are embedded; labels and reviewer notes do not travel to the device. Source files, inputs, and media assets are hashed. Held-out/public execution additionally requires `--freeze` with an exact `inputsSHA256` match. Media hashes are required in the frozen inputs themselves.

```sh
node scripts/embedding-evaluation/run-organization.mjs \
  --config <generated-configuration.json> --device <paired-iPhone-UDID> \
  --action all --output /tmp/organization-development-results.json \
  --host-timeout 3600
```

`--action build`, `run`, and `collect` can be used independently. Builds disable automatic package resolution; only standard signing provisioning is allowed. Collection refuses to overwrite existing reports or raw sidecars. The host verifies source hashes before build/execution, so re-prepare if source changes; collection alone can retrieve an older configuration and verifies its recorded configuration hash instead. A successful command is not evidence of organization quality: score the results separately.

Preparation options:

- `--split development|heldout|public|all`, default development.
- `--mode embedding|local|both`, default both. Local mode is explicitly blocked when Foundation Models is unavailable.
- `--orders chronological,reverse,interleaved,seed17,seed29`; optional comma-separated subset.
- `--libraries` comma-separated IDs and `--max-runs` limit completed attempts per app launch; zero means unlimited.
- `--timeout` per-scenario cooperative limit, default/max 600 seconds. OS calls may not promptly honor cancellation; the host timeout bounds collection waits. Interrupted scenarios are `running`, not passed.
- `--media extracted|reference`, default extracted, for controlled media/reference comparisons.
- `--derived-data` optional reusable build-cache path to avoid recompiling dependencies between configurations; run builds serially when sharing this path.

The two seeded orders use a fixed 64-bit linear congruential generator and Fisher–Yates shuffle. Interleaving uses six consecutive chronological chunks read round-robin unless an explicit input-only arrival permutation was frozen. It never reads gold thread labels. Local chronological order runs three times; all other mode/order combinations run once. Stable input UUIDs avoid randomizing input tie-breaks, but production merge UUIDs and local generation remain real sources of run variation.

## Output and resuming

Atomic `Documents/organization-<configurationSHA256>.json` writes occur at scenario start and termination. During a scenario, only its current-run payload is checkpointed in `organization-<configurationSHA256>-active.json`; finished runs and their vectors are not repeatedly serialized at each capture. The primary report contains expected run IDs, source/model/OS manifests, final memberships, post-capture snapshots, first-synchronize and settled memberships, safe ledger facts, observed vectors, graph edges, availability and timings. Repeated synchronization follows the production observation/merge cycle until event count is stable, bounded by `2 * inputCount + 4` passes. No thresholds or guard rules are bypassed.

Collection saves the raw primary as `<output>.primary.json`. When it contains a running scenario, collection optionally retrieves `<output>.active.json` and merges that checkpoint into a **new** output artifact only if configuration, run ID, current attempt, input order, metadata, and progress match. Terminal runs are never replaced. Stale, missing, malformed, or mismatched active checkpoints leave the primary unchanged. Use `--active-checkpoint no` to disable this optional merge. A restarted scenario gets a new attempt ID, so an earlier interrupted attempt cannot overwrite the new attempt. Original sidecars and archives are never overwritten.

Relaunching the same configuration skips completed/blocked/error/timeout scenarios. An interrupted `running` scenario restarts from a fresh database; previously completed scenarios are preserved. To retry a blocked scenario after model availability changes, prepare a separately identified configuration (for example, an order/library subset), preserving the old report. Reports are not silently overwritten to conceal failures.

`peakSampledResidentBytes` samples the app's whole-process resident size at capture boundaries. It is not an exact per-stage allocation peak or a battery measurement. `synchronizeMilliseconds` includes insertion, enrichment, and synchronization; embedding/reasoning timings are also separated. Device metadata model strings come from the provider spaces and current Foundation Models availability, not an invented weight version.

## Controlled media

Media inputs have `kind`, a relative `assetPath`, `assetSHA256`, `referenceText`, optional `caption`, and the usual ID/timestamp. Asset paths must resolve within the inputs directory. Preparation copies assets into the separate app under hash-based filenames.

Extracted mode uses production Vision/PDF extraction and installed-model `OnDeviceSpeechTranscriber`. It never substitutes the reference transcript for failed speech. Video reads the user caption only; uncaptioned videos provide empty text and unsupported evidence, not inferred audiovisual understanding. Extraction output and failures are retained in the report. Reference mode supplies the reference text as extracted content; it is an oracle-text diagnostic, not a claim that the app extracted it.

Libraries with `slice: media` run `LocalCaptureAnalyzer` on all contextual and media inputs. Embedding mode uses its native deterministic/entity fallback; local mode enables Foundation Models enrichment. Core text libraries intentionally keep source-derived titles and empty tags to isolate organization from metadata generation. Their relationship results therefore cannot certify tag-derived edges. Graph edges are the actual `ProjectGraphMap` first-40-node view; total and visible cluster counts are reported to make clipping explicit.

Scale inputs can use `slice: scale` and ordinary text items; use chronological order, an explicit run limit, and the 600-second bound. Scale snapshots/checkpoint writes are sampled at approximately 20 evenly spaced checkpoints plus the final state, avoiding quadratic diagnostic history overwhelming the test. Core and media snapshots remain per-capture. Reporting overhead is timed separately. The runner does not duplicate or reduce a timed-out library to obtain a pass.

## Harness checks

```sh
node --test scripts/embedding-evaluation/prepare-organization.test.mjs
node --test scripts/embedding-evaluation/merge-organization-checkpoint.test.mjs
node --check scripts/embedding-evaluation/prepare-organization.mjs
node --check scripts/embedding-evaluation/run-organization.mjs
```

Preparation tests cover label exclusion, expected coverage, frozen held-out/public hashes, duplicate IDs, invalid permutations/options, media hashes and asset path restrictions. Physical-device smoke results and full benchmark quality belong in the evaluation report, not in this runner's success exit code.
