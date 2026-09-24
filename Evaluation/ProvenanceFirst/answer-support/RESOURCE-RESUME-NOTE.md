# Mutable progress status: explicit lifecycle handling

The first 21 GiB adapter verified every hold-time file hash, including the native
launcher's live `status.json`. Independent audit identified that replay legitimately
updates that counter, so exact-byte checking it would block the next command.

Its exact hold-time bytes and the original adapter source were archived and hash
checked before correction. The first amendment receipt is preserved unchanged.
The v2 receipt binds the corrected adapter and archive. No native source, build,
scoring rule, corpus, prior result or resource allowance was changed.

Only `runs/answer-support/native-output/status.json` is treated as mutable status.
The old checkpoint verifies its archived bytes instead of demanding that the live
counter remain at three completed libraries. Every other checkpoint artifact still
requires an exact hash. Actual completion is established from native ledger,
projection, source/version/scope and reopen receipts, never from that status file.
