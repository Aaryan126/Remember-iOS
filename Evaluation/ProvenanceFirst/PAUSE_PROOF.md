# Observed pause/resume proof — checkpoint 1

Both checks used the frozen benchmark, not just mocked tests.

## Compiler

`checkpoint.py run --max-libraries 1` stopped after dev01. An explicit pause request
was saved; `resume` verified identity, preserved the request under a resumed name,
and compiled the remaining 23 libraries.

The original `units/dev01/receipt.json` was unchanged before/after resume:

- SHA256: `c5238aeb7f72a4de216ffb3c83354cfa52edcd14d0d96aee513effd5ba8bd3d7`
- mtime nanoseconds: `1789623802725219780`

## Native production-ledger replay

`native_probe.py --max-runs 1 --invariants` passed the invariant suite, completed
dev01-chronological, closed its database and exited with native status `paused`.
The coordinator then saved a pause request, acknowledged resume after verification,
and launched `native_probe.py` without the run limit. It finished the other 23 runs.

The first native receipt was unchanged before/after resume:

- Receipt basename: `c24061e387e75955e1040f21550156ae45562ddf4374d00ef2549ce81ef84765.receipt.json`
- SHA256: `5da10b007e2c459c3f47c30fe040af79d4e823b120efb12196989c5d7d2a124f`
- mtime nanoseconds: `1789623832936349282`

The final verifier checked all 24 native receipts and their ledger hashes, the
current code/dependency bindings, input identity, and the invariant execution binding.
No completed first unit was recomputed. This demonstrates cooperative bounded-unit
pause/resume; it does not promise recovery of an unacknowledged pause or an arbitrary
power failure at every instruction.

After completion, root confirmed author/reviewer work was stopped, no scoped probe
or build process remained, and shut down the simulator booted for this experiment.
The physical phone was not used. It is safe to close the laptop for this checkpoint.
