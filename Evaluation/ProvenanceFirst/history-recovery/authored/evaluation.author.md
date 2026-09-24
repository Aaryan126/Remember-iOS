# Evaluation author record

Author: history_author_eval. Authored 19 September 2026 for checkpoint 1.

`evaluation.json` contains twelve fresh fictional libraries, 144 events and 48
evidence-recovery questions. Each library has one current, historical, overlap and
unanswerable uncertain question. Scope is explicit: historical questions use
`includeHistory`; the other questions use `current`.

The six historical questions in eval01–06 require archived, unrevised documents
at their query prefixes. The six in eval07–12 require superseded revisions of
notes that remain active. Questions seeking original versions identify the
original document explicitly; later quotations and retrospective mentions do not
silently become equally eligible original-document evidence.

Coverage: eight libraries contain revisions, nine explicit corrections, ten
archive and restore operations, and all twelve contain genuinely shared sources.
Lifecycle order varies: temporary reopening followed by rearchive; correction
before revision of a shared note; repeated amendments; restored background;
archived originals; and later explicitly stale mentions. The source narratives
cover only the twelve evaluation domains assigned by the coordinator.

Only AGENTS.md, FORMAT.md, CONTRACT.md, history-recovery/PLAN.md and the existing
fixture validator were read for authoring. No older benchmark fixture, development
fixture, model output, inferred label, ranking result or performance stratum was
used. Source text was handled as untrusted fictional data. No Git state, production
file, dependency, model, or external account was changed.

Validation actually run:

- `PYTHONDONTWRITEBYTECODE=1 python3 -c 'import sys; from pathlib import Path; sys.path.insert(0, "scripts/provenance-first"); from fixtures import load, validate_split; validate_split(load(Path("Evaluation/ProvenanceFirst/history-recovery/authored/evaluation.json")))'` — PASS.
- A read-only Python assertion check using `validate_library` snapshots verified
  exact task-mode coverage, explicit scopes, empty uncertain-task evidence, the
  archived/current-revision condition for eval01–06, and the active/superseded
  condition for eval07–12 — PASS.

Validated JSON SHA256 after review corrections:
`c586e946b72bac762fdda3c25690f53411d3f8bf66cd5ef26eb82bc1aae484fb`.

The original authored SHA256 was
`e581d28380ef3ca9773782e70da09f618bcd635df2df95f0453ac53d61fabf66`.
The independent initial review is retained at
`../reviews/evaluation.initial.json`. Subsequent corrections are documented in
`evaluation.changes.md` and await independent re-review. Original authoring was
blind to development. The later assigned cross-split review and coordinator
adjudication informed eval12's mechanism redesign, without model predictions or
performance information.

Limitations: these are author-labelled fictional expectations awaiting independent
agent review, not human ground truth. Media are extracted text plus invented
locators; no OCR, speech recognition, frame understanding or actual media recovery
was tested. Exact quotation validation checks existence, not semantic relevance
or completeness. The author's temporal assertions do not prove search ranking,
abstention, production integration or real-user utility. Cross-split originality
requires independent review because the evaluation author did not inspect the
development split. Missing pre-import revisions, unavailable originals and lost
media locators cannot be recovered from these authored traces and were not
invented as retained evidence.

The explicitly incomplete nine-library checkpoint at
`../drafts/evaluation.partial.json` is a pause/resume authoring receipt only; use
`evaluation.json` for review and compilation. No model evaluation was run.
