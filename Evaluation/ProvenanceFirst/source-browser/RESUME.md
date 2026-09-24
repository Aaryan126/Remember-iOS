# Resume source-first browsing

Completed checkpoint 1 is stopped. Closing the laptop loses no required work.
There are no model/API requests or long-running training processes to resume.

From the repository root, verify the saved boundary read-only:

```sh
python3 -B scripts/provenance-first/source-browser/check.py --unit verify
```

The verifier checks current source/artifact hashes, the preserved previous Stage B
checkpoint and unchanged resource policy. It does not rebuild, install, initialize
a model or read the personal vault. A changed binding requires investigation, not
rewriting a receipt to manufacture a match.

Before this checkpoint was sealed, its bounded units were `--unit build`, `--unit
test`, `--unit regression`, then `--unit seal`. After sealing, artifact-overwriting
commands intentionally refuse to run. A later approved checkpoint must use fresh
output paths and preserve this checkpoint's evidence; document source-version
changes explicitly if production files are subsequently edited.

Before sealing, `source-browser/PAUSE` stops dispatch at the next command boundary.
If pausing during an already-running compile/test, let that bounded local command
finish and save its receipt. Each command stops by itself; none schedules another
unit. Remove only this checkpoint's pause marker when explicitly resuming.

For approved checkpoint 2:

1. Read PLAN/REPORT and inspect current worktree without altering Git state.
2. Preserve prior frozen-input versions before changing previously bound source
   files. Do not alter old result ledgers, decisions or evaluation gates.
3. Implement explicit local source-search UI and exact-version navigation.
4. Test the real store/app integration, cancellation, scope and return navigation.
5. Check accessible light/dark UI and fictional-data device behavior. Stop/report
   before accessing a personal vault, changing retention or broadening model work.

Keep the original resource baseline, 21 GiB growth cap and 10 GiB free-space reserve.
Never use Git mutation commands in this repository.
