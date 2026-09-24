# Approved resource-only amendment: 21 GiB

19 September 2026. After the saved 19 GiB resource hold, the user approved using
2 GiB more and continuing: “there is space in disk, so u can just use moer 2gb,
no issie , carry on”. The resulting conservative growth allowance is **21 GiB**.
The original accounting baseline and **10 GiB free-space reserve** are unchanged.

This changes only the resource policy for the already approved Stage A. It does
not authorize Stage B, additional generation requests, tuning, downloads, cleanup,
phone use, production changes, or Git mutations. Stop for review after Stage A.

The original controller, build bindings, approval, failed attempts and stopped
checkpoint remain byte-identical. A separate `as_approved.py` entry point verifies
those records and supplies the amended resource guard for that process only.
Direct invocation of the original runner still uses the original 19 GiB guard.
No recompilation or replacement of the already verified native build is needed.
