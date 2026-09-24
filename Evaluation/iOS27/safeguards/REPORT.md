# Current-organizer safeguards on the physical iPhone

16 September 2026. **23 tests passed; zero failed or skipped**, on iPhone 17 with
iOS 27.0 (24A437). Xcode's result bundle and portable `test-summary.json` /
`test-tests.json` record the actual executed cases, not just a successful build.

The isolated app uses copies of the current production sources, including the real
`D3ProjectOrganizer`, `MemoryStore`, GRDB/SQLite and `ProvenanceSnapshot`. It has a
different bundle ID (`SimpleStudio.Remember.Stage1Safety`), no app-group entitlement
and an inert entry point. Each store test creates its own fictional temporary
database. The personal Remember app was not reinstalled or launched, and its store
was not accessed. No model/threshold or production source changes were made here.

## Coverage

- **13 existing D3 tests:** corroboration and invalid-score rejection; ambiguous
  matches stay separate; deterministic bounded retrieval; ordered batch attachment
  without automatic merge/split or repeated placement; legacy assignments and user
  renames preserved; archived threads excluded; unavailable matching and explicit
  retry; explicit assignments preserved; cancellation cannot append placement;
  existing bundled FP16 model loads and scores symmetrically; revised placed items
  are not reassigned; unsupported text stays separate; concurrent edits invalidate
  stale placement.
- **7 existing readiness-cache tests:** success caching, wait-and-retry, bounded
  persistent failure, recovery after a prior failure, separate language caches,
  cancellation during readiness, and rechecking the cache after suspension.
- **3 additional tests:** actual SQLite triggers reject ledger UPDATE/DELETE and
  duplicate capture is idempotent; threshold equality is inclusive but the adjacent
  lower floating-point score is rejected; a fourth retrieved match cannot bypass
  the first-three corroboration rule.

The organizer/store tests use injected embeddings/matcher responses to force safety
branches deterministically. The bundled-model test uses the real FP16 matcher. The
separate boundary experiment tests real FP16/FP32 inference and Apple embeddings.
Do not describe the store cases as end-to-end quality testing of FP32 or the local
language model. These 23 selected tests are not the full application/UI test suite,
long-duration reliability testing or exhaustive coverage of every ledger operation.

## Isolated dependency and build recovery

The old local GRDB cache was absent. The existing `Package.resolved` pins version
7.11.1 / revision `b83108d10f42680d78f23fe4d4d80fc88dab3212`. Its source archive was
restored into this ignored build workspace, with archive and file hashes recorded.
No Git action or dependency upgrade occurred. The pinned package has no normal
remote dependency requirements; its documentation-only environment switch was
rejected by the preparation script. See the [pinned GRDB package manifest](https://github.com/groue/GRDB.swift/blob/b83108d10f42680d78f23fe4d4d80fc88dab3212/Package.swift).

Python's HTTPS attempt failed certificate verification before downloading. The
system `curl` trust store succeeded with TLS verification intact. No certificate
checks were disabled. Archive paths and symlinks were validated before extraction.

The first build failed because the generated test target lacked a signing team.
That failed receipt remains preserved. A separate signing-retry project applies
the existing app team to the isolated test target; production signing is unchanged.
The retry returned success and produced the signed test bundle. Its compiler log
also contains Xcode diagnostics saying some commands "failed with exit code 0",
plus Sendable/deprecation warnings; these were retained, not hidden. Actual device
execution subsequently passed all 23 tests, with no reported runtime warnings.

## Reproducibility / saved checkpoint

`manifest.json` binds original sources, generated copies and all dependency files.
`signing-retry.json` records the isolated configuration change. `test-inputs.json`
binds the signed app/test binary. Original build failure, successful retry and test
execution receipts remain separate. The `.xcresult` bundle stays local/ignored;
portable test reports omit device name and identifier.

```sh
python3 -B scripts/ios27-safeguards/run.py verify
python3 -B scripts/ios27-safeguards/run.py status
```

The saved test batch is not automatically rerun. `run` preserves the existing result;
an unresolved test reservation requires inspecting the result bundle before any
new attempt. The pause boundary is between test batches; the completed batch took
about six seconds. Do not run preparation again over the saved source tree.
