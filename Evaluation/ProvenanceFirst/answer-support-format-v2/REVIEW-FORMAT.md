# Independent answer-form review

Read REVIEW.md, original answer-support/CONTRACT.md and SCORING.md in full. Review
the opposite split from the one you authored. No verifier/model outputs, new model
calls, gold edits, source edits, scoring edits, retrieval changes or prompt tuning.

Root prepares `proposals/{split}.json`, containing one entry per original supported
annotation. Each entry includes library, question, sourceId, revision, answerKey,
questionText, supportQuote, legacyAnswers and proposedAnswer (exactly supportQuote).
The proposals bind the original corpus and packet-label hashes. Inspect the full
eligible source context from original authored data, not just the nominated text.

Approve the passage as an answer only if it directly answers that precise question,
preserves entity/time/negation/units/uncertainty, is a single contiguous source
extract no longer than160characters, and contains no distracting additional claim
that makes it unsuitable as a focused answer. Existing evidence and answerKey must
stay unchanged. Reject only the extra passage form if unsuitable; keep old forms.
If any original factual/state label is actually wrong, record a blockingIssue and
stop; do not hide a label correction as a format decision. Do not invent variants.

Write only `reviews/{split}.json` using apply_patch:

```json
{
  "split": "development",
  "reviewer": "/root/independent_agent",
  "author": "/root/original_author",
  "inputSHA256": "proposal-file-sha256",
  "decisions": [
    {"id":"dev01:q1:s01:r1:0", "approve":true,
     "reason":"Brief contextual justification, with qualifiers checked."}
  ],
  "blockingIssues": [],
  "limitations": ["Agent review, not human ground truth."]
}
```

Use the actual entry IDs supplied by the proposal. Exactly one decision per entry,
including cases where the passage already equals an old answer. No output-informed
corrections. Save a partial report outside `reviews/` if pausing; never publish a
partial final review as complete. Stop when `pause.request.json` appears in this
folder; ask coordinator if context or original evidence is ambiguous.
