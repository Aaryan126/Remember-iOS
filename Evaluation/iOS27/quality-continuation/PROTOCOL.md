# Approved Stage 2 continuation after transport interruption

The user's “Carry on” approves the recovery described in `quality/REPORT.md`.
Freeze this record and the continuation runner before any new generation.

The original app binary, prompts, schema, 112-input/160-packet corpus, 56 pair
controls, schedule, 600-token greedy decoding, metrics and gates are unchanged.
Do not edit the original runner, manifest, checkpoint, pause marker or evidence.
The original directory is read-only except its shared worker-lock file, which
prevents concurrent original/continuation workers. No production/cloud/Git changes.

Exactly one historical exception is authorized: `c7-004` has a reserved launch,
CoreDevice EOF, no recovered output/trace and verified process closure. Retain it
as a **host transport error with unknown model execution**, not a fabricated native
response, abstention, successful answer or dropped sample. Count its reservation
against the 256-attempt limit and expand its error to every corresponding scored
packet. Never retry it. This is an explicit deviation from the original execution
protocol, not a change to the quality criteria.

Read-only device recovery checks verify the isolated app, process absence and
lock state. Start with the next scheduled request, `boundary-004`, as the connection
check. It is an existing scheduled request, not an extra smoke input. There are
223 unattempted generations (215 primary, eight repeats). Preserve the original
order and all previously completed outputs. Total scheduled attempts including
two previous Stage 1 attempts remain 234, counting the unknown launch conservatively.

Retain the original immediate stop on any NEW native/runtime/transport failure or
three consecutive invalid model outputs. The historical transport disposition is
not itself a model output; it breaks the consecutive-output streak. No automatic
retry or further exception is allowed. Preflight failure before launch consumes no
model attempt. Every new launch is reserved first; unresolved reservations prevent
relaunch. Host deadline 120 seconds; frozen app watchdog 60 seconds plus two-second
grace. Pause between atomic units and recover saved device files without inference.

New evidence belongs only in this directory. Final analysis combines the original
64 units, the explicit transport disposition, and new units, preserving origin and
checksums. Include the error in all full-denominator metrics; an incomplete screen
cannot pass. Report original and adjudicated gold, both pair/context views, family
and contrast checks, fixes/damages, repeats and latency. Historical controls and
fresh FP16/FP32 pair proxies are not full-organizer or real-world app accuracy.

Stop for review after the report or a new blocker. No prompt tuning, sample
replacement, training, integration or gate relaxation. The 8 GiB experiment cap
and 10 GiB free-space reserve remain in force. Pause/resume commands now use
`scripts/ios27-quality-continuation/run.py`; do not resume the original runner.
