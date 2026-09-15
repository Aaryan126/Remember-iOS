# Remember Pro cloud organization: measured pilot, not enabled

Updated 15 September 2026. Product direction: richer, explicitly opted-in cloud
thread review is intended for **Remember Pro / paying users**. This is Remember's
own product tier, not an OpenAI subscription or a model named GPT-5.4 Pro. The pilot
used ordinary GPT-5.4. No paid-user organization experience is enabled yet.

Recommendation: keep local D3 as the offline default and evaluate
an opt-in cloud **project-context reviewer**, initially in suggestion-only mode.
Do not replace embeddings with an LLM or assume a larger model solves grouping.

## Completed Pro feasibility test — 14 September 2026

The [GPT-5.4 pilot report](../Evaluation/CloudMatcher/pilot-01/REPORT.md) records
112 actual API requests using `gpt-5.4-2026-03-05`, low reasoning effort, structured
decisions and validated source quotations. The eight agent-reviewed fictional
families yield 160 diagnostic packets: 80 pair-only and 80 with context. Identical
visible inputs were deduplicated. No personal memories were sent.

Primary context-view results (32 same, 32 separate, 16 insufficient-evidence cases):

| Measurement | Simple baseline | Current D3 pair scorer | GPT-5.4 context reviewer |
|---|---:|---:|---:|
| Same-project precision | 47.1% | 48.1% | **93.5%** |
| Same-project recall | 75.0% | 78.1% | **90.6%** |
| Wrong connections on 32 separate-project cases | 22 | 22 | **2** |
| Unsupported decisions on 16 uncertain cases | 5 | 5 | **0** |
| Invalid outputs / 80 packets | 0 | 0 | 1 |

GPT corrected 40 D3 decisions but damaged three correct decisions. It still made
shared-source/identifier-collision mistakes. Requiring D3 and GPT to agree raised
precision to 95.7%, but reduced recall to 68.8%; independent context review is the
more promising balanced candidate, with local retrieval retained.

Measured token-derived cost was **US$0.4842725 before tax**, below the approved $5
cap; median request latency was **2.49 s**, p95 **4.37 s**. These tiny requests do
not establish production per-user costs, capacity or response-time guarantees.
The runner passed 14 safety tests and 193 existing diagnostic tests; completed
replay made no further API calls. All five frozen exploration checks passed.

**This is not a 93.5% accuracy promise for Pro users.** It is an exposed synthetic
pair/context diagnostic, not fresh validation of retrieval, full River grouping,
real media or user preferences. The app's corroboration policy was not executed
in that comparison. The historical P2 qualification remains unchanged. See the
[frozen protocol](../Evaluation/CloudMatcher/pilot-01/PROTOCOL.md) and
[verification receipt](../Evaluation/CloudMatcher/pilot-01/verification.json).

Before launch: test fresh families and chronological grouping; implement consent,
authenticated subscription enforcement, quotas and suggestion acceptance. Intended
Pro UX is a reviewable explanation grounded in relevant captures, with local
organization working offline and no silent merging or history rewriting.

## What already exists

The repository already contains an OpenAI Responses/Embeddings client and a development
proxy. Ask, AI search and optional capture enrichment can use them; their existence
does not establish whether a particular phone has a configured, working connection.
The new D3 organizer never calls the old local/cloud project reasoner.

The proxy currently requests `gpt-5.5` through `OPENAI_MODEL`; it is not a production
subscription backend. No StoreKit entitlement enforcement or authenticated paid-user
organization route was found in the inspected app/server code. Premium access needs
those controls before launch, even if the product already has a paid-tier design.

## Where cloud reasoning might help

Our observed problem is often **project identity**, not vocabulary similarity: two
memories can discuss the same subject but belong to different clients, assignments
or events. D3 scores text pairs; a cloud reviewer could inspect the incoming capture,
several sources from each candidate thread, explicit identifiers, revisions and user
corrections together. The pilot supports its ability to distinguish “same continuing
project”, “related but separate” and “insufficient evidence” on the diagnostic.
Whether that becomes a reliable end-to-end product improvement remains unmeasured.

Embeddings should still retrieve a small candidate set locally. Initially ask for
review only when the user requests it or the local result is ambiguous. Record the
local result alongside the suggestion so we can measure overrides that help **and**
overrides that harm. Sampling confident local decisions during evaluation is important:
reviewing only uncertain cases cannot detect confident false attachments.

## Proposed flow

1. Capture and local organization continue immediately, even without connectivity.
2. With explicit opt-in and a verified paid entitlement, send bounded source excerpts
   and candidate IDs to an authenticated backend. Do not upload the entire vault.
3. The backend calls a pinned model with untrusted-content boundaries and a strict
   output schema: decision, allowed thread ID or null, supporting source IDs,
   contradictory source IDs, and a short explanation. No autonomous tools or writes.
4. Validate IDs, evidence references, response completeness and current source revision
   on the server and app. A source ID citation alone is not proof the conclusion is true.
5. Present a reviewable suggestion. Timeout, refusal, invalid output, revoked consent,
   stale state or lost connectivity leaves the local result intact.
6. On user acceptance, append a normal provenance event with the policy/model version
   and expected sequence. Never silently merge existing threads or rewrite history.

Structured Outputs reduces malformed responses, but does not guarantee correct
decisions; OpenAI explicitly documents remaining semantic mistakes.
[Official structured-output guidance](https://developers.openai.com/api/docs/guides/structured-outputs).

## Evaluate before building a paid dependency

Use existing exposed C6/C7 cases for prompt debugging, then freeze the prompt, candidate
retrieval, decision policy and model configuration before evaluating a new held-out
set. Compare: simple classifier, shipped D3, and D3 plus cloud review using identical
candidate context. Add a small oracle-retrieval diagnostic to distinguish missed
candidates from reasoning errors. Do not tune on the held-out results.

Measure false attachments, final thread purity and recall, missed reconnections,
uncertainty/abstention, overrides that damage a correct local result, chronological
replay across arrival orders, and preservation of corrections. Include explicit
separations, same-name projects, topic changes, missing evidence and prompt injection.
Report uncertainty by library, not just a single pooled percentage.

Also measure p50/p95 latency, timeout/failure rate, tokens and **cost per capture**.
Approve a fixed test-call/token budget first. Start with one capable reference model
and one lower-cost candidate supported by the account, rather than an open-ended model
sweep. Snapshot/version availability and prices must be checked when that test starts.
Per-user cost depends on reviewed captures × tokens per review × current token prices,
plus retries and backend operation. A paid subscription is not an unlimited API budget.

## Privacy and production requirements

- Keep API keys on the backend, never in the iPhone app. Add authenticated client
  access, server-verified entitlements, quotas, rate limits, request-size/output caps,
  idempotency, abuse handling and minimal content-free operational logs. The current
  development proxy is insufficient for a public paid service.
  [Official API authentication guidance](https://developers.openai.com/api/reference/overview).
- Use explicit cloud-organization consent, separate from the existing enrichment
  toggle; explain exactly which excerpts leave the device. Preserve offline use and
  cancellation. Provider processing does not become on-device because the app uses a proxy.
- API data is not used for training by default unless opted in, but that is not zero
  retention. Default abuse-monitoring logs can retain content for up to 30 days, with
  exceptions. `store: false` does not by itself eliminate monitoring or model-specific
  prompt-cache retention. Recheck the chosen model and account's retention eligibility
  before offering privacy promises.
  [Official data controls](https://developers.openai.com/api/docs/guides/your-data).

The app integration added no cloud organization route or billing code. A separate,
approved fictional-data API pilot subsequently ran as documented above. No personal
memories were transmitted, and no additional API calls were made for this doc update.

## iOS 27: keep provider cost separate from product tier

Apple now documents conditional no-API-cost access to Private Cloud Compute for
eligible Small Business Program developers with the managed entitlement and download
limits. It is still cloud processing with daily user quotas, not the offline free
tier. Our account eligibility and entitlement have not been verified. This may be
worth a separate comparison before fixing Pro provider economics; it does not imply
quality parity with GPT or change the current tier implementation.
[Apple eligibility](https://developer.apple.com/private-cloud-compute/).

See the [iOS 27 free-tier assessment](ios27-free-tier-assessment.md) for the strictly
on-device opportunities and the toolchain prerequisites.
