# History-aware recovery — approved implementation boundary

Checkpoint 1 only: audit retained evidence; implement an isolated, rebuildable
version-aware index; author and independently agent-review 24 fresh libraries
(12 development, 12 evaluation; 12 events and four questions each); prove coverage,
version/citation integrity and durable pause/resume. Stop for user review.

Default search scope is `current`; `includeHistory` is an explicit user choice.
Do not infer scope from labels. No app integration, personal-vault access, production
migration, model inference/training, paid API, download or Git mutation is authorized.
Checkpoint 2 (ranking/abstention comparison) and checkpoint 3 (conditional device/UI
integration) require separate approval. This checkpoint makes no ranking claim.

Fresh fixtures extend the existing FORMAT.md/CONTRACT.md: every task adds `scope`
(`current` or `includeHistory`); each library has one current, historical, overlap
and uncertain question. Historical questions: dev01–06/eval01–06 require archived
sources, dev07–12/eval07–12 require superseded revisions. Both splits must have
distinct scenario families, not noun-substituted templates. Earlier fixtures are
regression evidence only. Author and reviewer must differ; review is prediction-blind.

Save checkpoint artifacts after each bounded unit. Pause finishes/cancels that unit,
stops workers and verifies receipts before declaring safe to close. Resume checks
hashes and skips completed work. Missing pre-import history, missing originals and
lost historical media locators are limitations, never invented evidence.

Estimate: checkpoint 1 6–10 active hours; checkpoint 2 8–14 hours if approved;
conditional integration 6–12 hours. Report revised estimates at review stops.
