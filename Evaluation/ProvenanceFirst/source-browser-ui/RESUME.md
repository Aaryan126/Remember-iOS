# Checkpoint 2 — stop for user review

Implementation and required verification are complete. Read REPORT.md, STATUS.md
and VISUAL-QA.md. `checkpoint-stop.json` is the authoritative saved completion
record; do not overwrite it or silently modify its bound inputs.

## Verified runs

Under `Evaluation/ProvenanceFirst/runs/source-browser-ui/`:

- Native 21/21: `1789830128775924000`.
- Simulator UI 3/3: `1789830006882766000`.
- Full production-entrypoint source build (build only): `1789830202078159000`.
- Signed fictional phone build: `1789830227986712000`.
- Phone UI 3/3: `1789830517891741000` (iPhone 17, iOS 27.0 build 24A437).
- Initial phone automation-setup failure: `1789830284119486000`, preserved.

All fourteen final simulator/phone PNGs were inspected. Three resource-guard unit
tests, historical binding verification and `git diff --check` also passed.

Finalizer (already executed if the completion record exists; never overwrite it):

```sh
python3 -B scripts/provenance-first/source-browser-ui/check.py checkpoint \
  --unit-run 1789830128775924000 --ui-run 1789830006882766000 \
  --phone-run 1789830517891741000 --build-run 1789830202078159000
```

## On a future approved continuation

1. Inspect the saved checkpoint and local changes before editing. Preserve all old
   receipts, including failed/interrupted attempts. Start a new bounded follow-up
   record rather than redefining this checkpoint's evidence.
2. Read-only checks remain available:
   `python3 -B scripts/provenance-first/source-browser-ui/check.py verify` and
   `python3 -B scripts/provenance-first/source-browser-ui/check.py resources`.
3. The approved ceiling is 26 GiB (`resource-amendment-26.json`), original baseline
   unchanged, with a 10 GiB free reserve. No unrelated cache deletion or baseline
   reset. A new build must fit its reservation before dispatch.
4. Current copied inputs are the fictional launcher. Do not accidentally install
   production Remember. Phone tests require the separately signed diagnostic and
   unchanged signed-product/preparation bindings. Rebuild if those inputs change.
5. Recommended next scope is a focused multimedia, current-River and accessibility
   usability pass, then an explicitly scoped production deployment decision. It is
   not another model-training or answer-verifier experiment.

Diagnostic bundle `SimpleStudio.Remember.SourceBrowserUI` is labelled Evidence Check
and remains on the phone with fictional fixtures. Production Remember, its vault,
the organizer and model policies are unchanged. No Git state was changed.

The checkpoint is stopped. No owned build/test process needs to keep running; it is
safe to disconnect the phone or close the laptop. During future active units a
`PAUSE` file in this directory prevents dispatch and stops the owned process group
at the monitored boundary. No next unit follows automatically.
