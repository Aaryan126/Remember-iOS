# Authoring format v1

Each split is a JSON object `{ "schemaVersion": 1, "split": "development" or
"evaluation", "libraries": [...] }`. Exactly twelve libraries per split.

Each library has `id` (`dev01`..`dev12` or `eval01`..`eval12`), `family` (unique
scenario-mechanism slug, not just a renamed domain), `description`, `projects`,
`events` (exactly 12), and `tasks` (exactly 4).

`projects` entries: `{ "id": "p1", "rootSourceId": "s01", "title": "..." }`.
Use two or three projects per library, each introduced by its own capture. Project
roots must exist before another source can be assigned to that project. This is
gold metadata, not an inference input. Project title must be justified by source.

Events have unique IDs `e01`..`e12`, `kind`, `sourceId` (`s01`, `s02`, ...),
`dependsOn` (earlier event IDs, listing all causal dependencies), and `gold`:
`{ "memberships": ["p1"], "disposition": "confirmed", "relatedProjects": [],
"rationale": "...", "evidence": [{"sourceId":"s01","revision":0,"quote":"exact text"}] }`.

- `capture`: adds a new source; fields `text`, `modality` (note/photo/voice/video/pdf/link),
  `locator` (human-readable fictional page/timestamp/text location). No assignments
  on capture: memberships belong only in gold. Root captures confirm their project.
- `revise`: known source; fields `text`, `locator`; increments revision from 0.
  It retains memberships, including any explicit correction. Only revise notes.
- `correct`: known source; fields `assignments` (project IDs, nonempty), `reason`
  (explicit fictional user instruction); gold matches that instruction. Corrections
  may resolve an ambiguous source or link it to both projects. Do not invent evidence
  in the source: `evidence` may be empty when `reason` is the explicit authority.
- `archive` / `restore`: known source; preserve revision and memberships; gold
  repeats its prior disposition and relationships.

`disposition`: confirmed (nonempty memberships), unresolved (empty), independent
(empty), related (empty memberships, nonempty relatedProjects). For confirmed,
relatedProjects must exclude its memberships. Unknown is not separate. Evidence
must refer only to exact text in a revision already observed at this event. Record
missing evidence honestly. Do not quote a later clarification at an earlier event.

Each task: `{ "id": "q1", "atEvent": "e06", "mode": "current" or "historical"
or "overlap" or "uncertain", "question": "natural user question", "answerable": true,
"expectedEvidence": [{"sourceId":"s01","revision":0,"quote":"..."}],
"rationale":"why these sources answer it" }`. Unanswerable tasks have empty
expectedEvidence. Current tasks must not require a superseded or archived source;
historical tasks may explicitly ask for old/archived evidence. Every quote must be
available at atEvent. Tasks evaluate evidence recovery, not answer generation.

`expectedEvidence` is the set of eligible relevant source/revision evidence, not
an arbitrary preferred citation. Include equally valid sources/revisions, or make
the question genuinely specific to the original document/version when that is the
user task. An explicitly false premise can support an answer of "no"; it must not
automatically be labeled unanswerable. Current/historical mode is evaluator metadata,
not a hidden fact a model must guess: the question must state the temporal intent.

Dependencies constrain a causal alternative schedule, not a late-arrival stress
test. Include explicitly derived decisions, revisions, and continuations whose
interpretation presupposes earlier events, including precursors named in rationale.
Unrelated captures need not be serialised merely to preserve their original order.

Cover overlap, continuity, related-but-distinct work, ambiguity and later correction,
genuine updates versus mere later mentions, archival, and noisy extraction across
the split. Each library needs at least one non-capture operation and multiple
source modalities; vary event schedules and task modes. At least four libraries
per split must exercise revisions, four archive/restore, four explicit corrections,
and four genuine multi-project source memberships. Include unanswered references.

No model predictions, automatic scores, real personal data, or AI-generated project
summaries as evidence. Text should be short but natural, typically 30–90 words per
capture, with meaningful distractors and evidence distributed across sources.
Avoid cloning the same event/story template with substituted nouns.

Authors save authored JSON using apply_patch. Reviewers save a separate JSON with
`reviewer`, `author`, `split`, `inputSHA256`, `libraries` entries `{id, verdict, issues}` and
`crossLibraryIssues`. An issue has `location`, `severity` (error/warning), `reason`,
and `suggestedFix`. Do not edit author files as a reviewer. Retain original reviews
and require re-review of any corrected substantive labels.
