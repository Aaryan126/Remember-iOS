# Checkpoint 2 — verification passed; stop for review

## Current continuation

The user authorized continuation using the proposed 26 GiB ceiling. Original
baseline and 10 GiB reserve retained; `resource-amendment-26.json` records this.
No files were deleted. Historical checks and three Python guard tests pass.

- Final native run `1789830128775924000`: **21/21 passed**.
- Final simulator UI run `1789830006882766000`: **3/3 passed**.
- All seven final simulator captures were inspected; see `VISUAL-QA.md`.
- Full production-entrypoint source build `1789830202078159000`: passed. Build only,
  isolated bundle; production Remember was not launched or installed.
- Signed fictional phone build `1789830227986712000`: passed.
- Physical iPhone 17 / iOS 27.0 (24A437), run `1789830517891741000`:
  **3/3 UI cases passed**, zero failures/skips; seven phone screenshots inspected.
- First phone attempt `1789830284119486000` failed while enabling automation,
  before any app test executed. A fresh bounded retry passed without source changes;
  the exact cause of that initial setup timeout is not established.
- Diagnostic Evidence Check was installed separately. Production Remember and its
  personal vault were not accessed or replaced. No model/API calls or Git mutations.

See [report](REPORT.md) for checks and limitations. The completion command validates
the four final run receipts and writes `checkpoint-stop.json`; that receipt is the
authoritative completion record. Stop here for user review, not a new experiment.
No further disk cleanup is needed: after the successful phone run approximately
19.05 GiB was free and conservative growth was 22.82 GiB, within the 26 GiB ceiling.

Two additional harness issues were corrected: native active search has a Close
button before navigation Back, and the old appearance launch-default override
did not actually make the window dark. The test now closes search, then explicitly
uses Back; the fixture launcher forces requested appearance without changing the
production app. The final dark large-text capture also scrolls to the empty state.

## Historical 24 GiB hold (superseded)

Everything below records earlier states, not the current test/device/budget status.

### Saved state at that hold

The user approved 24 GiB (+3 GiB) for this checkpoint only. The original baseline,
historical budget policies, and 10 GiB reserve were preserved. The new guard has
three passing Python tests. Historical input verification passes (17 foundation
files plus the prior gates, with the explicitly archived original ProjectView).

- `1789824505866552000`: **21/21 native tests passed**, zero skipped/failed: 11
  real-store/state checks, 6 thread-presentation checks, 4 appearance checks. The
  corrected database cleanup ran without the earlier vnode/unlink warnings.
- The Threads menu issue was a **test selector error**. A valid failure capture
  (`1789824396179982000`) shows a native button labelled “Search saved evidence”
  without the custom SwiftUI identifier. The test now uses the visible label and
  requires the overflow button to exist. No production navigation workaround added.
- `1789824573952471000`: current/history/exact-version/direct-Back/archive case
  passed; dark large-text empty state passed. The corrected menu entry opened Saved
  evidence successfully, but the guard interrupted typing before the rest of that
  case completed. Exit -15; **this is not a passing UI suite**. Final screenshot
  review and complete UI rerun remain pending.
- `1789824035287035000`: selector failure, then prolonged verbose diagnostic
  collection; explicitly stopped and preserved. Subsequent runs skip verbose
  system diagnostics, not assertions, test logs, or screenshot attachments.
- Menu screenshot/accessibility hierarchy from the valid failure bundle were
  inspected. This does not substitute for light/dark/detail visual QA.
- Isolated phone build/test commands and signed-bundle/app-group checks are added,
  but **phone build, installation and tests have not run**. The phone is detected.
- Final production-entrypoint build rerun and completion receipt remain pending.

At the latest read-only measurement: free **19,155,873,792 bytes (17.84 GiB)**;
conservative growth **25,807,093,760 bytes (24.035 GiB)**, slightly above the 24 GiB
cap. Scoped study/code was 2,136,526,848 bytes and registered simulator growth
3,528,982,528 bytes; the larger whole-Mac decline controls the gate. This checkpoint's
run directory was about 922 MiB. These figures do not attribute all disk decline to
this work. The 10 GiB reserve itself is intact. No automatic cleanup or cap increase.

All owned build/test processes have exited and the simulator is shut down. `PAUSE`
prevents dispatch. Safe to close the laptop/disconnect the phone. Resume needs
restored headroom (preferably 2–3 GiB) or explicit further resource direction; the
phone build preflight reserves 1 GiB. No Git changes or personal-vault access.

## Earlier saved work

Implemented local entry point, Current/Include history search, retained-version
detail, original-file safeguards, cancellation/pagination state and tests.

Changed files: `ProjectView.swift`; new `SourceEvidenceSearchView.swift`,
`SourceEvidenceBrowserModel.swift`, `SourceEvidenceBrowserRepository.swift`,
`SourceEvidenceBrowserTests.swift`, `SourceEvidenceUITests.swift`; isolated tooling
in `scripts/provenance-first/source-browser-ui/`; this checkpoint's documents and
`docs/provenance-first.md`. Prior unrelated worktree changes were preserved.

- First full app-source simulator build: passed (isolated bundle/local dependency).
- Real-store/state tests: 11 passed in the first run. Temporary-database cleanup
  was subsequently corrected to close connections before removing fixture files;
  the corrected tests compile, but their execution rerun remains pending.
- UI log: exact current/history navigation and direct Back passed; dark large-text
  empty state passed. Threads menu-entry test failed to locate the new entry and
  needs diagnosis (real navigation issue versus test selector is not yet established).
- Resource guard exceeded 21 GiB during UI result collection and stopped the owned
  process group. The UI xcresult is incomplete (missing Info.plist), so screenshots
  have not been visually inspected. Preserve the readable test log; do not report
  the UI suite or checkpoint as passed.
- Physical-phone build/install/tests: not started.
- Production Remember has not been installed or launched by this checkpoint.

The only edited pre-existing app source is `ProjectView.swift` (new menu entry).
Its exact frozen original was recovered read-only from HEAD and checked against
the old history approval SHA-256, then saved in `baseline/ProjectView.swift`.
The original verifier now correctly rejects the edited live screen. The new
integration verifier explicitly resolves just that input to the matching archived
version and runs the prior gates unchanged. Old results/hashes are not rewritten.

Resume/inspect:

```sh
python3 -B scripts/provenance-first/source-browser-ui/check.py verify
```

Builds/tests use `Evaluation/ProvenanceFirst/runs/source-browser-ui/`; each bounded
command has its own timestamped log/receipt. Before running another unit, inspect
active processes and receipts; do not blindly repeat a device operation. A `PAUSE`
file in this checkpoint stops dispatch and terminates an owned build/test process
group at the next monitored boundary. No new unit follows automatically.

The approved checkpoint-specific 24 GiB growth cap and 10 GiB reserve are in force.
See `resource-amendment-24.json`; the original baseline and old policies are unchanged. Stop and request
direction if a later device build cannot fit; do not reset accounting or remove
unrelated caches. No Git mutations, model calls, paid calls or personal-vault access.

At the hold, whole-Mac free-space decline was approximately 21.93 GiB from the
unchanged baseline, with 19.95 GiB free. This checkpoint's run directory occupied
about 724 MiB; whole-Mac decline is not all attributed to this work. Requested next
decision: allow a scoped increase to 24 GiB (+3 GiB), retaining the 10 GiB reserve.
The user subsequently approved that increase with “Yes”. The owned simulator was shut down successfully;
the diagnostic app had already exited and no owned build/test worker remains.

Saved receipts/logs:

- `runs/source-browser-ui/1789818255051219000.*`: successful initial full app-source build.
- `runs/source-browser-ui/1789818307869591000.*`: 11 passing real-store/state tests.
- `runs/source-browser-ui/1789818419334524000.*`: two passing UI cases, one failure,
  interrupted result collection; exit -15. Do not retry without inspecting this hold.
