# Resuming the physical-device baseline

The core matrix can be paused. Completed terminal scenarios are retained; an interrupted running scenario restarts from a clean disposable database. Do not mark partial coverage as a completed benchmark.

## Current state — core complete, device stopped

The **core matrix finished all 144/144 scenarios at 12:09 Singapore time on 11 September 2026**. The [final archive](results/core-complete-2026-09-11.json.gz) and [frozen-label score](results/core-complete-score-2026-09-11.json) have no missing scenarios/libraries. All 118 previously completed records remain exactly unchanged. Do not rerun the core baseline. Both modes fail the semantic-quality targets; completion is not a quality pass.

Device work stopped on **11 September 2026 at 12:32:38 Singapore time**. The 100-item scale workload completed; the 500-item workload timed out at 372/500; the 1,000-item workload was host-stopped after progress ceased and remains incomplete. Its last console progress is 238/1,000, but its last durable checkpoint contains 200 inputs. Only the isolated app was stopped, and its process was verified absent. See the [final scale collection](results/scale-terminal-2026-09-11.json.gz) and [incident record](scale/EXECUTION-2026-09-11.md). The raw `running` status was preserved, not changed to a pass or in-process timeout.

Scale configuration identity: `404d9cd587c7ac3470fa703caf850aaed693442b3092001eb978607a79cc7771`. Configuration: `/var/folders/kq/24ntx4h97hlc01sy6x4t1t_r0000gn/T/RememberOrganizationProbe-1gfymR/configuration.json`. Collected host output: `/tmp/organization-scale-20260911.json`; log: `/tmp/organization-scale-20260911.log`. The configured host timeout was 2,100 seconds and each workload had a 600-second cooperative bound. The earlier host stop is explicitly documented as post-hoc, not the configured overall timeout.

No process or test batch remains active. Further work is diagnosis of the incomplete 1,000-item workload and, if requested, the unexecuted extended local-metadata media suite. A retry must preserve all current evidence and use fresh output/log filenames. Reusing the scale configuration skips the completed 100-item and terminal 500-item timeout, but restarts the incomplete 1,000-item scenario from zero; it does not resume at capture 200. Verify foreground/lifecycle behavior and deadline handling before assuming the prior stall is a production algorithm defect. Do not rerun the completed core baseline or silently replace failures.

An earlier [scale checkpoint collected at 12:21](results/scale-checkpoint-02-2026-09-11.json.gz) preserves the completed 100-item run (46.97 seconds), the **500-item timeout at 372/500 items after 600.07 seconds**, and the then-active 1,000-item workload. It is historical evidence, not the latest state. All core scenarios remain complete.

## Execution history — resumed at 11:51

Resumed at the user's request on **11 September 2026 at 11:51 Singapore time**, from **118/144 completed scenarios**. Pre-resume collection and structural comparison verified that every completed record is unchanged. Recorded source hashes, device OS (iOS 26.6.1), and the clean cached GRDB revision matched. The interrupted scenario restarts cleanly.

Active output: `/tmp/organization-core-resumed-20260911-02.json`; log: `/tmp/organization-core-resumed-20260911-02.log`. Twenty-six core scenarios remained at launch, followed by all three scale workloads and final full-matrix scoring. Preserve all earlier artifacts and use fresh filenames for collections. The pause below is historical, not the current execution state.

At 11:55 Singapore time, a live [English-complete checkpoint](results/core-english-complete-2026-09-11.json.gz) saved **122 completed scenarios**, including all 120 English scenarios and two multilingual scenarios. The [partial full-matrix score](results/core-english-score-2026-09-11.json) preserves missing multilingual coverage. English-heldout results fail the preregistered quality targets; details are in the baseline report. Multilingual execution remains active and scale workloads remain pending.

## Latest durable paused checkpoint — 11 September

Paused at the user's request on **11 September 2026 at 11:33 Singapore time**. Only the isolated benchmark process was terminated, and it was verified absent from the device process list. Final collection exited with expected incomplete-coverage status 2.

The latest durable [paused archive](results/core-paused-2026-09-11.json.gz) and [partial score](results/core-paused-score-2026-09-11.json) preserve **118/144 completed scenarios**, plus interrupted `l10-local-seed17-0` at **23/30 inputs**. **26 scenarios remain**, including the interrupted scenario, which restarts cleanly. Seventeen scenarios completed during this resumed phase; all earlier completed results remain retained. One reasoning-call error is recorded among completed runs. No scale workload has run, and the English core slice is not yet complete.

The collected host output `/tmp/organization-core-resumed-20260911.json` must not be overwritten. Resume with the unchanged configuration and fresh output/log filenames. Earlier live and paused checkpoints below are historical backups, not the latest state.

## Execution history — resumed 11 September

Resumed at the user's request on **11 September 2026 at 11:13 Singapore time**. The connected phone remained on iOS 26.6.1, all recorded source hashes matched, and the cached GRDB checkout remained clean at the recorded revision. Pre-resume collection confirmed that all **101 completed scenario records are exactly unchanged** from the latest paused archive. The interrupted scenario restarts from a fresh disposable database.

This phase used host output `/tmp/organization-core-resumed-20260911.json`, with log `/tmp/organization-core-resumed-20260911.log`. Its final partial collection/scoring is retained above. Full-matrix collection/scoring and all three scale workloads remain pending. Use new filenames for future collections; do not overwrite earlier evidence. The 10 September pause details below remain historical evidence.

A live [11 September checkpoint](results/core-checkpoint-01-2026-09-11.json.gz), collected at 11:23 Singapore time, preserves **109 completed scenarios**. All 101 previously completed records were compared structurally and remain unchanged. All 12 l09 scenarios completed with zero recorded reasoning-call errors; the resumed local runs took approximately 50–67 seconds. The interrupted scenario passed its prior stopping point and finished. The benchmark is still running; this is not a pause or final coverage claim.

## Earlier paused checkpoint — 10 September

Paused at the user's request on 10 September 2026 at **21:13 Singapore time**. The isolated probe was terminated and verified absent from the device process list. The host collected its final checkpoint and exited with expected incomplete-coverage status 2.

The latest durable [paused archive](results/core-paused-02-2026-09-10.json.gz) and [partial score](results/core-paused-02-score-2026-09-10.json) preserve **101/144 completed scenarios**, plus interrupted `l09-local-chronological-0` at **5/30 inputs**. **43 scenarios remain**, including that interrupted scenario, which restarts cleanly. It had stopped showing new capture progress for roughly a minute before the user requested this pause; the phone was still unlocked/connected and the probe process was present. The cause was not established, and this user interruption is not labeled a model timeout or successful scenario. One reasoning-call error is recorded among the completed scenarios (in l08); no completed scenario is marked failed.

No scale workload has run. Resume using the unchanged configuration below, but choose new host output/log filenames: `/tmp/organization-core-resumed-20260910.json` now contains this completed collection and must not be overwritten. Earlier checkpoints below are historical backups, not the latest state.

## Configuration and execution history

The core configuration identity is:

```text
f87a50dccce766d928730f0806d59136cbf3f3f900daf8fb8064da52c9abefa0
```

It uses `inputs-reviewed.json`, the original `freeze.json`, all 12 libraries, both modes, all five orders, the standard local chronological repeats, and a 600-second scenario timeout.

Paused at the user's request on 10 September 2026 at 19:59 Singapore time. The isolated probe was terminated and verified no longer running; the host wrapper collected its final checkpoint and exited with the expected incomplete-coverage status 2. The latest durable backup is [core-paused-2026-09-10.json.gz](results/core-paused-2026-09-10.json.gz), with [partial score](results/core-paused-score-2026-09-10.json). It contains **73/144 completed scenarios**, plus interrupted `l07-embedding-reverse-0` at 29/30 inputs. There are **71 scenarios remaining**, including that interrupted scenario, which must restart from a clean disposable database. Archive SHA-256: `7022b7ddab557572d2e3c146b657d1c76866092c5ffc2dbd2b6766c7cf6dfd13`.

The earlier [departure checkpoint](results/core-departure-checkpoint-2026-09-10.json.gz) contains 35 completed scenarios and a partial 36th and remains historical evidence. Never restore an older backup over newer device progress. No scale workload was started during this pause.

Resumed on the same phone on 10 September 2026 at 20:45 Singapore time. Pre-resume collection confirmed 73 completed scenarios and the matching interrupted checkpoint. All recorded production/probe source hashes matched, the cached GRDB revision remained clean and unchanged, and the device remained on iOS 26.6.1. The interrupted scenario restarted with fresh progress. Current host output is `/tmp/organization-core-resumed-20260910.json`, with log `/tmp/organization-core-resumed-20260910.log`; the durable paused archive above remains untouched. Collection and full-matrix scoring are pending while the run is active.

A live [resumed checkpoint](results/core-resumed-checkpoint-01-2026-09-10.json.gz), collected at 20:56 Singapore time, contains 89 completed scenarios and one running scenario. Its SHA-256 is `c4e1c09a5293ae4283d2dbd9fa99085cdc3ab4a1ba8d14ae0066d3881a365339`. All 73 pre-pause completed records were compared structurally and remain exactly unchanged after resumed execution. This is a backup, not a pause; device progress may be newer.

The subsequent [checkpoint 02](results/core-resumed-checkpoint-02-2026-09-10.json.gz), collected at 21:10 Singapore time, contains 98 completed scenarios and one running scenario. Libraries l07 and l08 each have all 12 scenarios complete; l08 records one reasoning-call error despite scenario completion. No embedding was unavailable in either library. The run remains active.

## Pause

Collect a checkpoint with the existing configuration and a new output filename. To stop battery-intensive work, terminate **only** the process whose executable is `OrganizationProbe.app/OrganizationProbe`. Do not terminate, reset, or uninstall the personal `SimpleStudio.Remember` application. Collect again after stopping and retain the newest partial report as a separate archive.

Unexpected disconnection does not erase saved scenarios. The app may continue using battery while foregrounded, or become suspended/terminated when locked or backgrounded. Do not assume it keeps running while the laptop is asleep or the phone is locked; explicitly pause before leaving when possible.

## Resume

Reconnect and unlock the same paired phone. Confirm that the production/probe sources and device OS have not changed; the recorded run used iOS 26.6.1. If the environment changed, preserve the old baseline and explicitly record a new execution phase instead of silently mixing environments.

Reuse the clean GRDB 7.11.1 source checkout at revision `b83108d10f42680d78f23fe4d4d80fc88dab3212`, matching the project's `Package.resolved`. Do not fetch, pull, switch, or change Git state to obtain it. If the cached checkout is no longer available, resolve that prerequisite before resuming.

The temporary project can be reused while it exists. If it was cleared, prepare it again using the unchanged inputs and flags:

```sh
node scripts/embedding-evaluation/prepare-organization.mjs \
  --inputs Evaluation/Organization/inputs-reviewed.json \
  --freeze Evaluation/Organization/freeze.json \
  --grdb <existing-GRDB-checkout> \
  --split all --mode both \
  --derived-data /tmp/RememberOrganizationCoreBuild
```

Check that the printed configuration hash equals the identity above. If it differs, investigate the source/configuration difference; do not pretend the new configuration is a resume. Use the newly printed `configuration.json` path in the following commands and choose fresh output filenames:

```sh
node scripts/embedding-evaluation/run-organization.mjs \
  --config <configuration.json> --device <paired-device-ID> \
  --action collect --output <new-pre-resume-checkpoint.json>

node scripts/embedding-evaluation/run-organization.mjs \
  --config <configuration.json> --device <paired-device-ID> \
  --action all --output <new-resumed-result.json> --host-timeout 7200
```

Collection exits with status 2 while scenarios remain pending/running; this is expected, not a failed checkpoint copy. Inspect the collection summary. The `all` action rebuilds if needed, installs the isolated probe, and resumes terminal scenario coverage. It does not clear the benchmark container or personal vault. If a ready signed build still exists, `--action run` avoids rebuilding.

When the core matrix finishes, score against the same frozen labels and archive the result under new filenames. Then run the three scale workloads. The controlled-decision suite and embedding-only media reference/extraction comparison are already complete; they do not need to be repeated. Extended local-metadata media repeats remain unexecuted and must stay labeled as such.
