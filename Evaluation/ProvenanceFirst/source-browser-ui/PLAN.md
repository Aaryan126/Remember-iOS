# Source browser checkpoint 2 — approved integration

The user approved the next recommended checkpoint after the 52-test foundation.
Estimated active work: 4–8 hours, with review stop after verification. Mac first;
connected/unlocked phone only for a separately bundled fictional-data diagnostic.

## Bounded work

1. Verify checkpoint 1 and preserve any baseline input before editing it. Keep
   previous model results, evaluation labels and receipts unchanged. Use new run
   paths, no Git writes, no dependency fetches, and no model/API requests.
2. Add a local “Search saved evidence” entry in Threads. Preserve existing thread
   search and D3. Default to Current; Include history explicitly adds archived and
   superseded sources. Related results are not verified answers.
3. Add cancellation-aware screen state, bounded pagination and exact-version
   resolution. Changing query/scope cancels and invalidates old requests. Returning
   from a detail preserves search scope, query and results.
4. Show a read-only saved-source detail, matched passage and retained field context,
   revision/archive/partial/imported-gap information. Never substitute current text.
   Open originals only after local path/existence/version checks. Same-filename reuse
   is not proof of original-version identity. Missing media does not hide retained text.
   Optionally open explicitly labelled current River context, preserving normal Back.
5. Add deterministic real-store and screen-state tests; build the full app sources
   using a locally copied dependency, with remote resolution disabled. Test navigation,
   light/dark, large text and unavailable-original states using fictional fixtures.
6. Use a separate diagnostic bundle/container for any device check: never install over
   Remember or read the user's vault. Record actual checks and any blocked steps.

## Boundaries

- No training, cloud verifier, new auto-assignment policy, retention migration or
  personal-vault inspection. Historical quality scores are not new UI quality scores.
- Original cap was 21 GiB, later 24 GiB. After the next hold the user authorized
  continuation using the proposed 26 GiB ceiling (`resource-amendment-26.json`),
  retaining the baseline and 10 GiB free-space reserve. Earlier approvals are preserved.
  Record build estimates and inspect accounting between bounded units; stop if the
  guard cannot accommodate a build rather than silently increasing the allowance.
- Snapshot only affected historical inputs into this checkpoint if needed. Do not
  modify the old checkpoint's hashes to pretend edited sources are unchanged.
- No automatic next experiment. Save progress and stop after this checkpoint.
