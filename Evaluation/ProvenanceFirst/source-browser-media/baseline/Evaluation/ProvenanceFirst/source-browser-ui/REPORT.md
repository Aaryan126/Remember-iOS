# Source browser UI integration

## What changed

Threads now has a **Search saved evidence** overflow action, separate from the
existing thread finder. It searches retained source text locally, not generated
summaries or cloud answers. Current is the default; Include history explicitly
includes older revisions and archived sources.

Opening a result shows the matched saved revision, not a substitute from the
latest memory. Revision, archive, extraction and imported-history limitations are
visible. Back restores the query, scope and results. Missing originals leave
retained text readable. Unsafe paths and filenames reused across revisions do not
receive a misleading original-file action. Optional River context is explicitly
current context, not a reconstruction of the historical River.

The new repository adapter and cancellation-aware screen model keep store access
out of the view. Search is debounced and paginated against a pinned ledger boundary;
stale responses cannot replace a newer query's results.

## Verified results

All run IDs below refer to `../runs/source-browser-ui/`.

| Check | Result | Run |
| --- | --- | --- |
| Real-store/state and existing presentation/appearance tests | 21 passed, zero skipped | `1789830128775924000` |
| Simulator UI flows | 3 passed, zero skipped | `1789830006882766000` |
| Full production-entrypoint source build, isolated bundle, not launched | Passed | `1789830202078159000` |
| Signed physical-phone fixture build | Passed | `1789830227986712000` |
| First physical-phone UI attempt | Runner initialization timeout; no test case executed | `1789830284119486000` |
| Physical iPhone 17 / iOS 27.0 UI retry | 3 passed, zero failures/skips | `1789830517891741000` |
| Resource guard unit tests | 3 passed | `test_check.py` |
| Historical input verification | Passed, including 17 frozen foundation files | `check.py verify` |

The three UI flows cover current/history separation, exact older-revision text,
direct Back, archived text with unavailable original, dark accessibility XXXL,
honest empty results, and the real Threads menu entry/return. All seven final
simulator captures were inspected; see [visual review](VISUAL-QA.md).

The phone retry passed without source changes. Its seven screenshots were also
opened and inspected. The initial failure was runner setup, not an app assertion;
its exact cause is not established. The separately bundled fictional app and runner
were installed; no production Remember install or personal-vault inspection was
performed. Device OS build: 24A437. Screenshot review does not replace a full
accessibility audit; extreme text size still requires substantial scrolling.

## Interpretation and limits

This is source-browsing functionality and engineering verification, **not a new
retrieval-quality win**. The earlier foundation's 52 native and 25 regression passes
are preserved historical results, not tests rerun here. D3 organization, model
weights, prior failed ranking/verifier results and cloud experiments are unchanged.

Fixtures are deliberately small and fictional: a receipt changed from ORBIT-27 to
NOVA-42, an archived ARCHIVE-8 receipt whose original is absent, and a generated
summary containing “unicorn” that must not become source evidence.

Not covered by these UI tests: photo/audio/video original playback, tapping the
text-original Quick Look action, the current-River context destination, VoiceOver,
all accessibility settings, large real libraries, or user relevance judgments.
The diagnostic does not initialize the organizer. It cannot establish production
vault performance or full-app runtime compatibility merely from its source build.

## Scope and reproducibility

- Diagnostic bundle: `SimpleStudio.Remember.SourceBrowserUI`, labelled Evidence
  Check. Separate container, verified signed products, no shared app-group access.
- Fixture launcher exists only in copied diagnostic inputs. Production launcher
  remains unchanged. Dependencies are copied locally; no remote package resolution.
- Original accounting baseline is unchanged. Approved checkpoint ceiling is
  26 GiB with a 10 GiB free-space reserve; old 21/24 GiB approvals remain archived.
- Earlier failed/interrupted runs remain preserved and are not counted as passes.
  Test-selector, search-close and fixture-appearance corrections did not change
  production navigation to accommodate tests.
- No model/API requests, Git mutations, unrelated cleanup or private-vault reads.

Commands used: `check.py verify`, `prepare`, `build`, `prepare-fixture`, `test-unit`,
`test-ui`, `build-phone`, `test-phone`, and Python unittest discovery for
`scripts/provenance-first/source-browser-ui/test_check.py`. Exact xcodebuild commands,
source bindings, exit codes and resource measurements are saved in run receipts.

Verification is complete; `checkpoint-stop.json` is the final saved gate once the
completion command succeeds. Stop for user review. Broader multimedia/usability checks or production deployment
need their own bounded follow-up, not an automatic new model experiment.
