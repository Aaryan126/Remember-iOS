# GPT-5.4 screening pilot — frozen before paid inference

Approved by user 14 September 2026: fictional text only, Mac-only, maximum US$5
pre-tax API usage. No app changes, new training, personal vault access or Git changes.

## Question and comparison

Can a hosted context reviewer distinguish shared continuing projects from related but
separate undertakings better than the existing D3 **pair scorer**? This is not yet
an evaluation of candidate retrieval, C3 corroboration, full River grouping or user UX.

Reuse all 160 C6 adjudicated packets from eight agent-reviewed fictional families;
identical visible inputs deduplicate to 112 calls (56 pair-only, 56 contextual inputs).
Only `pair` and visible `sources` enter the API request. No labels, reviewer rationales,
domain/family metadata, expected outputs, model scores or previous packets are sent.
Earlier C7 prompt is reused unchanged; no prompt tuning after results are visible.
These cases are exposed diagnostics, not a fresh holdout or independent user sample.

Controls: cached simple baseline and seed-29 D3 at their existing frozen thresholds.
The D3 control is the same trained scorer/threshold as the app, before Core ML rounding
and without app-level corroboration. Do not describe its packet errors as live app errors.
New conditions: GPT alone, D3 with conflict veto, and D3 with confirmation. Veto retains
D3 unless GPT explicitly finds separation; confirmation requires both to assert same.
Both propagate GPT errors rather than hiding them as correct abstentions. This measures
the proposed reviewer itself, not the separately recommended production local fallback.

## API and budget

- Direct Responses API; exact snapshot `gpt-5.4-2026-03-05`, low reasoning effort,
  strict JSON schema, exact evidence quotes, short rationale, no tools, no conversation,
  `store: false`, standard service tier. Do not change the app proxy's model setting.
- 2,000 maximum output tokens including reasoning; conservative bound of 4,000 input
  tokens (serialized request UTF-8 bytes plus 512 framing allowance must fit). Oversized
  inputs stop; evidence is never truncated. Validate actual usage against these bounds.
- Standard pricing verified in official OpenAI documentation: $2.50/M input, $0.25/M
  cached input, $15/M output. Reserve $0.04 durably before each call. At most 120 calls
  including any setup/retries means at most $4.80 under these request bounds. Budget
  code separately enforces $5. No blind retries or unbounded SDK retry behavior.
- Unknown-billing/in-flight interrupted requests retain the full reservation and are
  not resent. They become explicit errors. Invalid outputs are retained, not regenerated
  until a favorable answer appears. Stop on three consecutive errors or auth/rate errors.
- Check model access with a non-inference GET. First run two benchmark requests to check
  schema/transport/usage only, save a pause checkpoint, then resume the remaining inputs.
  Those two original responses remain in the scored results; no semantic tuning.

`store: false` does not imply zero provider retention; normal API monitoring policies
still apply. Credentials come from the existing environment or ignored local `.env` and
are never printed or saved to artifacts. No key is placed in an app or prompt.

## Reporting and decision

Freeze inputs, prompt, runner, validators, metric helpers and controls by SHA-256.
Save every raw successful API envelope, parsed outcome, timing and usage before moving
on. Save only HTTP status for provider errors to avoid echoed credential/request details.
Use separate immutable reservation and response files, single-worker locking, checksummed
units and a pause marker. Replaying/resuming completed work must make no further paid calls.

Report counts and rates separately for pair and context views and per family: same-project
precision/recall, separation precision/recall, unsupported assertions on ambiguous inputs,
errors, scope/bridge/clarification contrast checks, and D3 decisions fixed versus damaged.
Errors stay in recall/accuracy denominators. Repeated packets are correlated; 160 packets
are not 160 independent trials. Report family-level variation instead of a misleading
independent-packet significance claim.

Use C7's pre-existing exploratory checks for the standalone context reviewer: separation
precision ≥90%, separation recall ≥80%, same-project recall ≥75%, unsupported assertions
on uncertain cases ≤10%, errors ≤5%. Passing only justifies fresh validation; it is not
permission to enable cloud organization or proof of production quality. The primary
interpretation must weigh fewer false attachments against lost true connections and
damaged correct local decisions, not choose a policy solely by its headline precision.

Estimate $1.50–$3 and 1–2 hours including harness/tests/report. Report actual token-derived
USD separately from reserved unknown charges and taxes. Phone not needed.

Sources:
- https://developers.openai.com/api/docs/models/gpt-5.4
- https://developers.openai.com/api/docs/pricing
- https://developers.openai.com/api/docs/guides/structured-outputs
- https://developers.openai.com/api/docs/guides/reasoning
