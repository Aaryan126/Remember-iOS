# Unified search installed in main Remember — 23 September 2026

## Outcome

Installed in place as `SimpleStudio.Remember` on the connected physical iPhone 17,
iOS 27.0 (24A437). The existing signing team, share extension and app-group identity
were verified, and the D3 matcher remains bundled. No uninstall, restore, forced
regrouping, model/threshold change, paid AI request or Git state change.

The app now has unified Memories search with Include history, Source text only and
exact saved-passage links. The duplicate Threads menu entry is gone. Keyboard
submission is local; Ask AI remains independent. Try the new controls by tapping
Search your memories in Memories.

## Verification

| Check | Result |
|---|---|
| Signed normal-entrypoint app + extension build | Passed |
| App/team/app-group signatures; bundled local model | Passed |
| Pre-install backup | 182 files verified; SQLite healthy; 11 migrations match |
| Startup safety | 8 indexed memories; no pending captures/shared inbox/video requeue; cloud assistance off |
| Physical-phone navigation smoke | 1/1 passed, 0 failures/skips/reported runtime warnings |
| Memory records | All 8 rows unchanged |
| Provenance history | All 171 events unchanged |
| Original media | All 8 files byte-identical |
| Post-install backup | 183 files verified; SQLite healthy |
| Deployment guard regression tests | 3 existing inventory tests + 4 resource/pause tests passed |
| Whitespace check | `git diff --check` passed |

The phone smoke uses a fictional unlikely-match query, toggles both search options,
checks empty results, verifies the duplicate Threads action is absent, and returns
to Memories. It does not open personal search results, capture/edit/archive content,
invoke AI or export personal screenshots. This is a bounded engineering smoke, not
a new search-quality benchmark, full device regression, or answer-support test.
Existing compiler/deprecation/AppIntents warnings remain in build logs; zero runtime
warnings refers specifically to the test-result summary, not every tool message.

## Reproducible actions and receipts

Commands were run in order using `python3 -B scripts/provenance-first/unified-search/deploy.py`:
`resources`, `prepare`, `build`, `backup`, `inspect-backup`, `install`, `smoke`,
`post-backup`, `compare`, `launch`, then `finish` after documentation was saved.
Guard tests used `python3 -B -m unittest discover` with `-s scripts/provenance-first/main-app-deployment`
and `-s scripts/provenance-first/unified-search`, both with `-p 'test_*.py'`.

Private ignored run root: `Evaluation/ProvenanceFirst/runs/unified-search-deployment/`.

- Signed build: operation `1790164816667712000`.
- Pre-update backup: `backup-1790164868387628000`.
- In-place install: operation `1790164936489249000`.
- Phone smoke: operation `1790164960303221000`, result
  `smoke-1790164958462639000.xcresult` (test duration 29.736 seconds).
- Post-update snapshot: `post-install-1790165013892788000`.
- Aggregate preservation proof: `preservation.json`.

Copies are private and owner-readable, with file inventories and SHA-256 checks.
Backup database checks inspect copies only, not the live phone database. Raw memory
text, originals, credentials and personal screenshots are not included in this report.

## Storage and stop boundary

The user approved proceeding after the earlier hold. The additional cumulative
allowance was bounded to 1 GiB (32 GiB total), with the original accounting baseline
and 10 GiB free reserve unchanged. Prior SDK module caches were reused; new products
and receipts were kept separate, preserving older signed artifacts. No caches/files
were deleted. The final resource snapshot is bound in checkpoint-stop.json.

The outstanding normal-entrypoint compile check is resolved by the signed physical
device build, not an additional simulator build. Earlier implementation testing
(17 native, 6 simulator UI cases) remains documented in docs/unified-memory-search.md.

Stop for user review after reopening the app. Further deployments need a fresh
backup and preservation checks. Recovery is not automatic: retain both snapshots
and request explicit direction before any restore or downgrade.
