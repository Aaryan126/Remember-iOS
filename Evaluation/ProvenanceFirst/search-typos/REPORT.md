# Local typo tolerance — 24 September 2026

Status: **installed and verified on the iPhone** after the user's approval.
The source work and simulator/native checks did not access the personal library.
The subsequent authorized deployment took fresh verified local backups, installed
the reviewed signed build in place, and verified data preservation. No AI request,
dependency download, database migration or Git state change occurred.
See [deployment details and phone checks](DEPLOYMENT.md).

## Behavior

- Local Memories search and saved source/history passages share bounded
  Damerau–Levenshtein/optimal-string-alignment word matching.
- One edit for query words of 4–7 characters; two for 8–64 characters. Insertions,
  deletions, substitutions and adjacent swaps are supported. Case/accent folding
  and exact matching remain available. Fuzzy expansion stops above 16 distinct
  query words; words outside the fuzzy length range still match exactly.
- Exact/one-edit/two-edit token weights are 1/0.7/0.4. Existing exact phrase,
  title and tag boosts remain in ordinary card ranking. Comparable exact matches
  outrank variants, including when the approximate memory is newer.
- Numeric query terms and connected references containing digits require exact
  matches; shared components cannot substitute for a different full reference.
- Source-only and history boundaries remain intact. Quotes, revision IDs,
  pagination boundaries and originals are unchanged. Source passages never fall
  back to generated summaries or tags. Explicit AI/answer retrieval keeps its
  previous behavior; typo tolerance does not introduce automatic cloud calls.
- No new controls: typing and Return use the improved local search. The existing
  help alert explains spelling tolerance and exact numeric references.

## Verification

Commands use the existing resource guard, original accounting baseline, 32 GiB
cumulative ceiling and 10 GiB free-space reserve. The installed opening-fix
checkpoint's 141 bound files were preserved before edits; historical receipts
were not rewritten. Simulator data and native fixtures are fictional.

| Command | Result |
| --- | --- |
| `python3 -B scripts/provenance-first/search-typos/check.py unit` | Final source: 79 tests passed, no failures/skips or reported runtime warnings (87 executions including parameterized cases). Covers matcher, memory/source integration, browser, existing memory search, video and handoff suites. |
| `python3 -B scripts/provenance-first/search-typos/check.py native` | 52 source-projection regressions passed; compiled with complete concurrency checking and warnings as errors. Covers ledger validity, restoration, pagination, cancellation and safety limits. |
| `python3 -B scripts/provenance-first/search-typos/check.py ui` | 12 passed, zero failures/skips. Includes typo-to-card/source/history retrieval, original quote navigation and query retention; existing search motion, filters, light/dark header spacing and accessibility-sized text. |
| `python3 -B scripts/provenance-first/search-typos/check.py benchmark` | Optimized native matcher: 1,000 fictional documents, approximately 100 words each, five repetitions per query. Median 171 ms exact, 168 ms one-edit, 206 ms mixed one/two-edit query, 188 ms no-match. Expected 100/100/100/0 matching documents observed. |
| `python3 -B -m unittest discover -s scripts/organization-diagnostics/ledger -p 'test_prepare_project.py'` | 5 passed; the diagnostic source list includes the new matcher dependency. |
| `python3 -B scripts/provenance-first/search-typos/check.py prepare-device` | Normal app entrypoint and local GRDB dependency prepared, 111 source bindings. |
| `python3 -B scripts/provenance-first/search-typos/check.py build-device` | Passed: signed normal iPhone app and Share Extension. Source/product bindings and strict signatures verified. Initial attempt stopped before xcodebuild because the older shared device module cache was absent; the existing cold-build path and larger reservation resolved it with a separate cache. |
| `git diff --check` | Passed. Read-only Git inspection only. |

Final unit receipt: `../runs/search-typos/1790252252273195000.xcresult`.
UI receipt: `../runs/search-typos/1790252285484941000.xcresult`.
An earlier run passed 77 tests before the final punctuation guard and two extra
cache/cancellation tests; the 79-test run supersedes it. Native and benchmark
commands bind their compiled inputs in `source-regression.json` and
`benchmark.json` under the same ignored run directory.
Signed-build operation: `../runs/search-typos-device/operations/1790252337733736000.json`.
The app is at `../runs/search-typos-device/build/Build/Products/Debug-iphoneos/Remember.app`.
Xcode still emits existing deprecation/AppIntents diagnostics; these checks are
not a claim that the whole application builds without warnings.

## Limits and handoff

These timings measure only the matcher on the development Mac with a repeated
vocabulary, not full query/index/ledger/UI latency or iPhone performance. The
request-local comparison cache is capped at 8,192 entries; reaching that cap
does not discard candidates. Candidate lengths, edit bands and word/query limits
bound fuzzy work, with cancellation during comparisons. Very large or diverse
libraries still need device profiling before claiming a performance guarantee.

This handles word-level typos, not split/joined words, sound-alike names or
language-specific segmentation. Short-word exact matching intentionally avoids
broad false positives. Alphabetic codes cannot always be distinguished from
ordinary words; the strict reference rule applies to codes containing digits.

The authorized installation is complete. Phone smoke passed on the third attempt;
all 8 memory rows, 8 original files and 171 history events remain unchanged.
Remember is open for the user. No uninstall, data reset or restore occurred.
The original readiness report is preserved under the ignored device run directory
as `readiness-report.md`, matching the immutable `ready-to-install.json` receipt.

## Files changed

- `Remember/Remember/SearchTextMatcher.swift`: shared local matcher.
- `MemorySearch.swift`, `MemoryPipeline.swift`: opt ordinary Memories search into
  the matcher, including extracted-text chunks, preserving AI retrieval defaults.
- `SourceEvidenceSearch.swift`: use the same matcher on retained source passages.
- `UnifiedMemorySearchView.swift`: help text.
- `RememberTests/SearchTextMatcherTests.swift`, `UnifiedMemorySearchTests.swift`,
  `RememberUITests/UnifiedMemorySearchUITests.swift`: typo/ranking/scope/quote tests.
- `scripts/provenance-first/search-typos/`: bounded checks, native benchmark and
  deployment wrapper for the existing backup/signing/preservation safeguards.
- `scripts/organization-diagnostics/ledger/prepare_project.py`: source dependency.
- `readme.md`, `docs/unified-memory-search.md`, and this evaluation directory:
  behavior, validation, handoff and prior-checkpoint manifest.
