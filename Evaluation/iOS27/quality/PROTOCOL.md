# Stage 2: bounded on-device grouping screen

Frozen before new phone inference. This is an exposed diagnostic, not a held-out
benchmark or production qualification. No production models, thresholds, personal
memories, paid APIs, PCC or Git state are changed.

## Question and controls

Can an iOS 27 local generative reviewer distinguish a continuing undertaking from
related-but-separate work, without breaking correct same-project decisions?

- Reuse the C5/C6 fictional release: 160 packets, 112 unique visible inputs,
  eight families. Score pair-only and context views separately. Gold labels were
  reviewed by agents, not independent humans. Report original and adjudicated gold.
- Compare the unchanged C7 prompt with ONE new boundary-focused prompt. Same
  structured schema, fresh session per request, greedy decoding, 600 output tokens,
  no prewarming, no truncation, no tools. Inputs contain only source IDs, source
  text and the queried pair: never gold, family, predictions or scores.
- Preserve historical simple-classifier and seed-29 pair controls. Additionally
  score all 56 distinct pairs on the phone with fresh Apple embeddings and both
  unchanged production FP16 and separately versioned FP32 evaluation exports.
- These are **pair acceptance controls**, not an end-to-end test of the D3
  retrieval/corroboration/online organizer. Pair models do not receive extra context.
- Report local-only, D3+veto, and D3+confirmation results. A veto uses an explicit
  separation result, otherwise keeps D3. Confirmation requires both to say same;
  explicit separation remains separation. Reviewer errors remain errors, never
  repaired or silently replaced with a baseline result.

## Fixed request budget and execution

Sort contexts by their existing visible-input SHA-256. Alternate reviewer order
per context. Run the first four contexts (eight scheduled calls) as an operational
pilot before the remainder; do not inspect gold-based quality to tune the prompt.
Run all 56 non-generative pair controls first. Repeat contexts at sorted indices
0, 28, 56 and 84 once per reviewer, after the main screen, for eight fixed repeats.

224 primary + 8 repeat generations = 232 scheduled calls. Including the two prior
Stage 1 generation attempts gives 234, below the approved total cap of 256. The
remaining 22 are unallocated, NOT permission to retry or search prompts. Every
launch is reserved before execution; an unresolved attempt prevents resending.
Count reservations conservatively even if the model was never reached.

Stop immediately on a failed control, a native model/runtime error, lost console,
or three consecutive invalid outputs. Otherwise collect invalid citations/schema
as errors. Pause between atomic units; each generation has a 60-second independent
app deadline, two-second cancellation grace, 120-second host console deadline.
Wait for foreground and protected data. Never count missing results as successful
abstentions. A partial screen cannot pass the gate. No automatic retry, repair,
prompt change, threshold tuning or sample replacement.

## Scoring and decision

Strictly validate schema and exact source quotations; decisive results must cite
both queried sources. Citation validity does not itself prove evidence supports
the verdict. Errors stay in recall/error denominators. Expand deduplicated requests
back to 160 packets per reviewer, but do not describe them as independent samples.
Report family-level and joint contrast checks, original/adjudicated sensitivity,
fixes and damages against fresh FP16 pair decisions, request latency and repeat
agreement. No inference of overall app accuracy from this challenge set.

All contextual-view conditions must pass for a candidate to justify a **fresh
validation proposal**, not deployment: same precision >=95%, same recall >=75%,
separation precision >=90%, separation recall >=80%, unsupported decisions on
uncertain cases <=10%, errors <=5%, and more fixed than damaged D3 decisions.
A fix means previously incorrect -> correct, not an error or merely less harmful
wrong answer. Report harmful same/separate changes separately.

## Checkpoints

Preparation saves data mappings, prompts, protocol, source/model/build hashes and
the deterministic schedule. Every phone unit saves raw output and its checksum.
`pause` stops at the next boundary; `status` must show `safeToClose: true` before
closing the laptop or disconnecting. `resume` skips completed units. If the console
is lost, use `collect` without inference; do not relaunch that unit.

Storage limits remain 8 GiB across `Evaluation/iOS27`, with 10 GiB free reserve.
Stop at the final report (or an operational blocker) for user review. No integration
or new model search is authorized by completion of this screen.
