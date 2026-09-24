# Phone generation readiness — failed smoke check, safely stopped

16 September 2026. **Model availability passed; generation smoke did not complete.**
No grouping-quality evaluation or paid API call occurred.

The physical iPhone 17 / iOS 27.0 (24A437) reported Foundation Models `available`
with a 4,096-token context. Contextual embedding assets retained the expected
identifier, revision and dimension. A direct sentence-model lookup returned nil in
this fresh environment process; this is distinct from the production retry provider,
which successfully supplied embeddings in all 24 fresh boundary pairs.

The existing frozen Stage 1 smoke prompt asks for the explicit code `ORBIT-27` from
one fictional receipt. It uses a fresh `LanguageModelSession`, a one-field generated
type, greedy sampling and a maximum response budget of 100 tokens. Only **one**
generation attempt was dispatched. No answer/result marker was received before
`devicectl`'s 120-second command deadline; it exited with code 2. Attempting to collect
the atomic device result file also found no checkpoint. Raw logs and the attempt
reservation were preserved. No retry was made.

Availability metadata alone therefore does not establish usable generation. This
does **not** show poor reasoning quality, prove the underlying model's exact stall
point, or establish a cause such as downloading, prompt failure or OS regression.
The current probe emits its result only at the end, so finer-grained instrumentation
is needed to distinguish session construction from response execution. A later
device check reported `passcodeRequired: false` and `unlockedSinceBoot: true`;
that snapshot is not proof of screen/foreground state throughout the request.

## Safe closure

After the host deadline, the isolated process was still present. Its executable path
was matched against the saved installation and independently verified bundle ID
`SimpleStudio.Remember.Stage1Readiness`. Only that process was terminated, then the
device process list confirmed it absent. See `closure-reserved.json`,
`termination.json` and `closure.json`. No main-app or Apple system process was killed.

**It is safe to disconnect/close after this checkpoint.** The original generic
runner conservatively reports `safeToClose: false` for a missing native unit even
after a separately documented host termination; `closure.json` and the parent
checkpoint record the verified closure. No fake native result was inserted to change
that status. The unresolved reservation deliberately prevents automatic re-execution.

## Next bounded diagnostic

Before Stage 2, use a separately versioned probe with timestamps around model check,
session initialization, prewarm if supported, and response/stream progress; include
an explicit app-side deadline/cancellation and saved terminal outcome. First run
the same tiny prompt once, with the phone foregrounded and unlocked. If it again
stalls, stop and inspect device/runtime evidence before any larger prompt sweep.
Keep the old timeout receipt unchanged. Do not count this failure as a bad grouping
decision or keep repeatedly spending the screen's inference budget on smoke retries.

This diagnostic needs the connected phone. Estimate 1–2 hours for instrumentation
and a bounded check, excluding any OS/model readiness wait. It may identify a
platform blocker rather than something that can be repaired in Remember.
