# Unified search — implemented and subsequently deployed

23 September 2026. No worker remains running. Safe to close the laptop.

The initial build hold below is resolved by the separately approved signed
main-app build and physical-phone update. See
[deployment results](../unified-search-deployment/REPORT.md): normal-app smoke 1/1
passed; 8 memories, 171 events and 8 originals unchanged. The new UI is installed.

Plan, behavior, exact commands and caveats: [unified search](../../../docs/unified-memory-search.md).

## Completed

- Preserved 139 bindings from the previous main-app deployment in baseline.json
  and baseline/, without rewriting that deployment's receipts.
- Unified Memories search, explicit history/source-only options, passage snippets,
  exact-version detail/back navigation; removed duplicate Threads menu entry.
- Keyboard Return is local search; Ask AI is unchanged, AI search remains explicit.
- Ignore rules cover additional model formats and private run/archive artifacts.
- Native test receipt 1790164003570083000: 17 passed, zero failures/skips.
- Final simulator UI receipt 1790164261477119000: 6 passed, zero failures/skips.
- Light/current and dark/large-text captures inspected. One heading-only correction
  followed the UI test run; see the documentation's exact validation scope.

## Initial hold / historical resume instructions

The isolated normal-entrypoint project is prepared under runs/unified-search/project.
`check.py build` stopped at the resource guard before launching xcodebuild: its
768 MiB reservation would exceed the approved 31 GiB cumulative growth ceiling.
The 10 GiB free reserve and original accounting baseline remain unchanged.

After freeing around 1 GiB or separately approving a resource amendment:

```sh
python3 -B scripts/provenance-first/unified-search/check.py resources
python3 -B scripts/provenance-first/unified-search/check.py prepare
python3 -B scripts/provenance-first/unified-search/check.py build
```

Do not clean caches or change old receipts/budgets automatically. Current source is
not installed on the personal iPhone. A later deployment needs its own controlled
backup/data-preservation checks. No new model/AI-answer integration is enabled.
