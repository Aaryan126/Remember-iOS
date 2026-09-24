# Answer-support authoring format

Read PLAN.md and CONTRACT.md completely. This format replaces only the old fixture
shape for this new experiment. Write fictional source text, never model predictions.

Each split file: `{"schemaVersion":1,"split":"development"|"evaluation",
"author":"/root/<agent>","libraries":[...]}`. Exactly eight libraries, IDs dev01–08
or eval01–08. Each library has id, family (distinct mechanism, not a noun-substituted
template), description, events, tasks. No project-membership labels needed.

Events: sequential e01..eNN, at most 16; source IDs s01..s08 (at most eight sources).
Each has id, kind, sourceId. capture additionally has text, modality
(note/photo/voice/video/pdf/link), locator. revise has text, locator; only active
notes may be revised. archive/restore only change visibility. Revisions start at
0 and increment. Text is trimmed, nonempty, at most 800 characters, naturally
written extracted evidence. At least two modalities, one archived source and one
superseded note per library. Vary event chronology and query boundaries; use a
later event as a real update, not a reason to silently overwrite unrelated facts.

Exactly eight tasks per library with id q1..q8 in any category order. Fields:
id, category, atEvent, scope, question, gold. Each required category occurs once:
current_a, current_b, archived, superseded, explicit_missing, topical_only,
conflict, wrong_scope. archived/superseded scope is includeHistory; others current.
First four categories have corpus verdict supported, the remaining four have
explicit_missing, not_established, conflicting, not_established respectively.
Two current supported questions may include a negative answer or paraphrase.

gold has exactly verdict, answers, missingEvidence, rationale.
answers is a list of {sourceId, revision, quote, answerSpans, answerKey}.
quote is a short verbatim support passage; answerSpans is a nonempty list of
acceptable minimal verbatim answer variants contained in that quote (max160 chars
each); answerKey groups semantically equivalent answers, e.g. "blue". If multiple
sources genuinely answer, include ALL, sharing the same answerKey. Each supported
task has one distinct answerKey; each conflict has at least two incompatible keys.
For conflict, annotate both competing answer passages/values. All answer spans
must preserve necessary entity, unit, negation and time qualifiers.
missingEvidence is a list of {sourceId, revision, quote}; nonempty only for
explicit_missing. Its quote must explicitly state the requested detail was not
recorded/identified/measured, not mere lack of an answer in a passage. For
not_established, both lists are empty. rationale explains why the full eligible
corpus yields that verdict; ambiguity is not evidence of falsehood.

Gold refers only to sources/revisions already captured at atEvent and eligible
under explicit scope. archived supported task targets an archived latest revision;
superseded task targets an older revision of an active note. Current answers cannot
use an archived or superseded source. Missing facts and disagreement must be about
the exact requested fact/entity/time. A yes/no question can legitimately be answered
by a negative statement. Do not mark every negative passage unanswerable.

Historical tasks require at least one target of their specified historical kind,
not that every legitimate alternative citation is historical. If a current amendment
explicitly repeats the old value, include that support too; never remove correct
gold solely to force a history-only result. Report how often current evidence alone
also suffices, and do not describe those questions as requiring inaccessible history.

Each library: four supported, four non-answering; at least one query before final
event. Across the split include meaningful question polarity contrasts, multiple
valid citations, noisy fictional extraction, unrelated date/value distractors,
paraphrases, and hostile quoted instructions (source data, never actual commands).
Do not reuse the old history-recovery scenarios or copy them with renamed nouns.
Do not optimize wording to the lexical scorer, model outputs or expected thresholds.

Independent corpus review is prediction-blind. Review every eligible passage for
alternative correct answers and state contradictions, not just nominated evidence.
Review file: {reviewer,author,split,inputSHA256,libraries:[{id,verdict,issues}],
crossLibraryIssues}. issues: {location,severity:error|warning,reason,suggestedFix}.
Reviewers do not edit author files. Preserve initial reviews and re-review any
substantive corrections before freezing. Later packet review checks labels after
fixed retrieval, still without verifier/model outputs. Agent review is not human
ground truth; document limitations. Save through apply_patch, no Git actions.
