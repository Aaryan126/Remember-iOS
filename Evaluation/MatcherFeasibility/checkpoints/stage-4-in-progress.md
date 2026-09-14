# Stage 4 live checkpoint

**Historical note, superseded by [the completed Stage 4 checkpoint](stage-4.md).** No worker is now running. The text below records the earlier in-progress state.

Authorized scope: initial physical-iPhone feasibility only. Stage 5 is not authorized.

Initial phone discovery: wired iPhone 17 (iPhone18,3), iOS 26.6.1 build 23G83, developer mode enabled. Original Stage 1–3 hashes verified; isolated environment's 37 distributions and six original model assets verified. About 37 GiB free. Production Remember and its data are untouched.

## Preserved preflight attempt 01

`runs/stage-4-attempt-01` successfully built, signed, installed and completed one fresh-process phone launch. The first observed model+tokenizer preparation took 3.630714 seconds; first twenty-pass shortlist took 0.094456 seconds; sampled process footprint peaked at 163,251,072 bytes. This is one preliminary measurement, not a gate verdict.

Before the full sweep, report review found that UUID filename ordering was not chronological. Reporting now explicitly sorts by launch timestamps. The interruption exercise was expanded from 5 to 100 shortlists because this phone runs fast enough to finish five before the host could deliver a pause. This changes neither the latency test's 100 measurements per length nor the contract gates. Attempt 01 and its original source snapshots remain preserved. It is diagnostic evidence, not the final accepted run; use its snapshot to inspect its original implementation.

## Active attempt

`runs/stage-4-attempt-02` records the corrected reporting and longer interruption exercise. The Swift measurement app, tokenizer, runtime and model are unchanged. It will collect 10 process-cold launches, 100 warm shortlists at each of 256 and 512 tokens, 416 parity cases, and the separate interrupt/resume exercise. These are not reboot-cold launches; keep attempt 01's first observed preparation separate from cache-retaining restarts.

Pause command (wait for worker acknowledgement before disconnecting):

```sh
python3 scripts/matcher-feasibility/stage4.py pause --run Evaluation/MatcherFeasibility/runs/stage-4-attempt-02
```

Jobs are explicit and independently saved. Resume the same job configuration with `--resume`; completed job receipts cause a no-op. Source changes require a new attempt. Large build/model artifacts remain in the dedicated external workspace.
