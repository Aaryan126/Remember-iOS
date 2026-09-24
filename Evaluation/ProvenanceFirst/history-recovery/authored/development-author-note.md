# Development author note

Author: history_author_dev. Scope: the twelve allocated development scenarios only.
Authored input: `development.json`, SHA-256
`a74baacf34b6cbe489a9720f1ad955449093f99c82b418ee4222ed5f253215ee`.

This fresh fictional split contains 12 libraries, 144 events, and 48 tasks. Every
library has one current, historical, overlap, and unanswerable uncertain task.
Task scope is explicit: historical tasks use `includeHistory`; the other tasks
use `current`. Each historical task in dev01–06 targets an archived, unrevised
artifact at its query prefix. Each historical task in dev07–12 targets a
superseded revision of a note that remains active at its query prefix.

The allocated domains are graft trials, costume restoration, ferry signage,
kiln maintenance, fictional school meal labels, acoustic lining tests, glacier
equipment packing, a neighborhood tool library, print edition numbering,
insect specimen loans, community radio scheduling, and roof runoff collection.
Questions distinguish original documents from later mentions when both could
otherwise supply a fact. Corrections may resolve project ownership while leaving
missing words, identifiers, or measurements unknown. Shared sources connect
distinct continuing undertakings without merging them.

Validation run with `PYTHONDONTWRITEBYTECODE=1 python3` using the existing
`scripts/provenance-first/fixtures.py`: `load`, `validate_split`, and
`validate_library` all passed. Additional assertions passed for the exact task
mode set, explicit scopes, unanswerable uncertain tasks, and the required archived
versus superseded state at every historical query prefix. The existing
`alternate_events` produced a complete twelve-event causal schedule for every
library. These are structural and citation/state checks, not independent semantic
review or any ranking test. Independent review and correction status appears below.

An incomplete dev01–09 draft was saved at
`../drafts/development-partial-09.json` for pause/resume before the final authoring
unit. It is retained as an authoring checkpoint and is not a complete split.

Limitations: all people, projects, services, observations, and records are
fictional; these expectations are agent-authored and are not human ground truth.
Media are extracted text and fictional locators only. No OCR, ASR, image analysis,
playback, missing-original recovery, model inference, or ranking was performed.
Source text is untrusted data. During initial authoring this author did not read
the evaluation split, older benchmark fixtures, model outputs, or scores. After
authoring, this agent independently reviewed evaluation and recorded findings in
`../reviews/evaluation.initial.json`; no model outputs or scores were involved.
Cross-split freshness and semantic review remain agent judgments. No production files,
Git state, dependencies, or downloads were changed.

## Independent-review corrections

Initial authored SHA-256:
`4137507aad02204aebbe2a71328a02d67568fba07b490f9bc1be2322b27168f6`.
The independent development review by `/root/history_author_eval` found five
missing dependencies: dev01/e10 now depends on e03, dev01/e11 on e04,
dev07/e05 on e03, dev08/e09 on e06, and dev10/e11 on e04. These edges preserve
the antecedents explicitly referred to by the later sources in alternate causal
schedules. The dev12/q4 rationale now explains document-specific selection rather
than claiming that no other source repeats the support face. Source text,
memberships, questions, and expected evidence were not changed by this correction.

The existing validator, all scope/history assertions, and explicit checks that
each of the five antecedents precedes its continuation in `alternate_events`
passed on the corrected input. A separate change log retains the old hash and
exact affected fields. Independent re-review of the corrected hash is pending.
The root adjudicator is addressing the dev11/eval12 mechanism-overlap warning
through changes to evaluation; this author did not edit that split.
