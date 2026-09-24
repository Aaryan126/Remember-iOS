# Stage A stopped for review — extraction-format qualification failed

Preparation, independent packet review, native replay and final audit are complete.
The first neutral control returned a correct cited sentence but not the frozen
minimal answer span. The stop rule was followed: no retries, prompt changes,
remaining controls or benchmark verifier requests.

- 16 libraries, 128 questions, 138 event prefixes and 16 reopen checks verified.
- Retrieval support: development 30/32; evaluation 31/32 answerable questions.
- Each split retains all eight missing-fact and eight conflict packets.
- 276 regression tests passed; 384 returned citations passed integrity audit.
- One model request: runtime, schema and citation passed; exact answer granularity
  failed (`Receipt code: ORBIT-27.` versus `ORBIT-27`).
- Seven controls intentionally not run. Reproducibility and four-state capability
  remain unqualified; this is not a factual-reasoning benchmark result.
- 21 GiB approved resource allowance; original baseline and 10 GiB reserve intact.
- Production app, phone, paid APIs, Git state and previous experiments unchanged.

All workers/probes stopped; simulator shut down. Safe to close the laptop.
Stage B remains unapproved and must not run under this failed qualification.
See [report](REPORT.md), [decision instructions](RESUME.md), and `stage-a-stop.json`.

## Historical progress notes — superseded by the stop above

The user approved an additional 2 GiB. The new scoped allowance is 21 GiB,
with the same original baseline and 10 GiB reserve. The old 19 GiB hold and
all immutable artifacts remain preserved. Use `as_approved.py runner ...` for
this continuation; see RESOURCE-AMENDMENT-21.md and RESOURCE-RESUME-NOTE.md.

All 16 libraries now have verified native replay: 138 event prefixes, 128
query scopes and 16 database reopen checks. Fixed retrieval is running.
No verifier generations have run; Stage B remains unapproved.

## Previous stopped checkpoint (preserved context)

User approved Stage A, independent author/reviewer agents, and the scoped 19 GiB
growth allowance. See APPROVAL.md and approval.json; the original baseline and
10 GiB reserve remain unchanged. Old frozen files/results are preserved.

Fresh metadata-only Mac readiness now reports the local model available with an
8,192-token context. This does not qualify generation or semantic quality. No
benchmark verifier requests have run; Stage B remains unapproved.

Both 8-library / 64-question splits have passed independent cross-review and are
frozen. Pre-freeze changes improved affirmative/negative balance and reduced
explicit conflict clues; no retrieval or model outputs guided these changes.
Preparation and pause/resume hash-and-mtime preservation checks passed. The first
67 isolated unit tests passed (not yet the final regression receipt).

Native replay initially encountered a harness compatibility issue before processing data:
the old launcher permits input under Documents/HistoryRecovery and output only
inside its original experiment workspace. The rejected attempt and confirmed
simulator shutdown are preserved. A separate launcher with the same frozen index
implementation now builds successfully; no old output folder was changed.

The 19 GiB conservative growth guard stopped replay. Three of sixteen libraries
have verified native receipts: 25 event prefixes and 24 query scopes, with reopen
checks. One completed native receipt was revalidated and its missing host record
saved after the guard fired; it was not rerun. All workers are stopped and the
owned simulator is confirmed shut down. Safe to close the laptop.

The stopped checkpoint measured 19.42 GiB conservative growth and 22.46 GiB free.
Whole-Mac free-space decline controls this measurement; do not attribute all of it
to this experiment. No cleanup, baseline reset or cap increase was performed.
The new build and dependency copy are about 266 MiB.

74 new harness tests passed. Independent scoring audit corrected equivalent
multi-citation scoring and documented conservative shorter-quote treatment in
SCORING.md. Previous ranking/history suites also passed (31 and 22 tests).
No benchmark retrieval or verifier generations have run. Remaining replay,
retrieval, packet review, control compilation, technical controls and final
regression/freeze/audit are pending. Stage A is not complete; Stage B is unapproved.

See [saved checkpoint and continuation instructions](RESUME.md).

Pause request:

```sh
python3 -B scripts/provenance-first/answer-support/as_runner.py pause
```

Wait for coordinator confirmation that workers/agents and any owned native process
have stopped before closing the laptop. Status alone does not establish agent
shutdown. The coordinator will stop for review at the end of Stage A.
