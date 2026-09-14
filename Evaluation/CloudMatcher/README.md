# Cloud matcher screening

**Completed:** [pilot-01 final report](pilot-01/REPORT.md). All 112 requests are saved;
token-derived cost was **US$0.4843 before tax**. GPT-5.4 passed the frozen exploratory
checks, but is **not production-qualified**. The experiment is stopped for review;
no additional paid run or cloud integration has started. See
[verification](pilot-01/verification.json) for replay and test evidence.

User-approved GPT-5.4 pilot, 14 September 2026. See
[the frozen protocol](pilot-01/PROTOCOL.md). No production integration is authorized
by this experiment. C1–C7 and the current app remain unchanged.

The pilot uses 112 unique fictional inputs, expanded back to the original 160 packets
for comparison with cached controls. Maximum 120 inference calls, maximum US$5 pre-tax.
The runner enforces a $0.04 pre-call reservation under bounded input/output sizes,
records unknown-billing calls conservatively, and never blindly retries them.

## Commands

Use the existing feasibility environment; no new package installation is needed:

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" \
  scripts/cloud-matcher/pilot.py status
```

Replace `status` with:

- `pause`: request a stop after the current response is saved. Wait for the worker to
  report `safeToClose: true` before closing the laptop.
- `predict --resume`: resume only missing inputs without reissuing saved/unknown calls.
- `evaluate`: reconstruct all predictions and metrics from saved outputs; no API calls.
- `proof`: save/check the initial two completed inputs' hashes and modification times.

`freeze` binds the experiment before inference. `preflight` makes a non-inference model
access check; it never substitutes another model. Do not rerun setup in a new directory
to bypass the shared budget. A future experiment requires separate explicit approval.

Credentials are read from `OPENAI_API_KEY` or the repository's existing ignored `.env`.
They are never printed, copied into artifacts or sent to a third-party proxy. The app's
development proxy and model configuration are not modified.

## Evidence layout

- `pilot-01/manifest.json`: frozen source hashes, model, settings and prices.
- `pilot-01/attempts/`: durable pre-call reservations and checksummed raw results.
- `pilot-01/units/`: immutable interpreted outcomes keyed by visible-input hash.
- `pilot-01/resume-before.json`, `resume-after.json`: pause/resume evidence.
- `pilot-01/summary.json`, `predictions/`: generated comparison after completion.
- `pilot-01/REPORT.md`: interpretation and limitations after completion.

Test runner safety without network activity:

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" \
  -m unittest discover -s scripts/cloud-matcher -p 'test_*.py'
```

This pilot tests pair/context judgments, not the app's retrieval, corroboration,
whole-library organization, media extraction or paid subscription backend. Reused,
agent-reviewed synthetic cases can reveal promise but cannot establish real-world
accuracy. `store: false` does not mean zero provider retention.
