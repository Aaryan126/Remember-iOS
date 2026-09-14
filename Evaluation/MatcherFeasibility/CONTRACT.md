# Matcher feasibility contract v1

Status: Stage 1 preparation. No model-quality result exists yet.

## Scope and checkpoints

Six stages: (1) prepare and freeze, (2) Mac baseline/reference outputs, (3) Core ML conversion, (4) initial phone measurements, (5) specialist training/evaluation, (6) trained phone verification. Stop after every stage and wait for the user's explicit continuation. Stage 1 does not run inference, training, conversion, or a phone app.

Use fictional English text only, local training, and an isolated phone probe. No personal vault, production app changes, paid compute, or Git-state changes. Large artifacts live outside the repository in the dedicated workspace recorded in the environment manifest. Do not delete unrelated files. Stop new heavyweight work below 10 GiB free.

## Dataset and labels

600 memories, 30 independent libraries, 20 memories each: mf01–mf18 training, mf19–mf24 development, mf25–mf30 test. Domains, continuing project identities, and named writing-template families are split-disjoint. This is agent-reviewed synthetic data, not human-validated or a deployment-representative sample. Distinct template names alone do not prove distinct language patterns; retain lexical overlap diagnostics and independent review limitations.

A context is a particular continuing project, event, or task, not a broad topic. Corrections and revisions within that context belong together. A source may belong to multiple contexts without merging them. Every supported context must have at least two single-context sources. Ambiguous sources have empty point memberships and an explicit reason; they remain in coverage reporting and separate abstention diagnostics.

Granularity follows the original Organization contract: budgets, designs, meetings, chapters, formats, and operational workstreams of one continuing project remain together. Distinct tasks qualify only when the sources support independently scoped undertakings, not merely separate departments or object names inside one project. Reviewers must not infer a fixed number of groups from the authored composition. Reviewed libraries may have fewer groups or no bridge/related examples individually; class and bridge coverage is required across the full corpus, not artificially forced into every library. Source amendments clarify genuinely missing scope; label revisions, rather than invented separation, resolve same-project workstreams.

For every unordered pair in a library:

1. If either item is ambiguous, label `uncertain` for diagnostics only.
2. If they share a context, label `same`.
3. Otherwise, if any of their contexts has an explicitly annotated relationship, label `related`.
4. Otherwise label `unrelated`.

Shared context takes precedence over related context. Relatedness is not transitively closed. A bridge between A and B does not imply all of A and B are one thread. This benchmark measures final-library pair relationships, not historical arrival-time truth or automatic merge safety.

Input files use an exact allowlist: schemaVersion; libraries containing id, split, items; items containing id and text only. Author labels, context definitions, rationales, tags, and reviewer decisions never enter model inputs or phone payloads. Model-facing code must read only input files; host evaluators explicitly load separate labels.

Train and development labels may be used for their declared purposes. Test labels are available only for Stage 1 annotation/integrity work, then remain sealed from model selection until Stage 5. Before opening test results, freeze selected weights and operating thresholds. Post-test tuning consumes that test release; a new independent test set is required for a new unbiased claim.

## Independent review

Two fresh-context reviewers read only this contract, repository safety rules, and the projected source inputs. They cannot read authoring files, candidate labels, each other's reviews, or predictions. They reconstruct source groups and explicitly supported related-group pairs; mark underdetermined sources ambiguous. Record short evidence summaries rather than hidden chain of thought. Model identity is `unknown` unless actually supplied.

Review JSON: schemaVersion, reviewer, model, blindToAuthorLabels=true, blindToPredictions=true, libraries. Each library contains id, groups [{id,members,evidence}], relatedGroupPairs [[id,id]], ambiguous [{id,reason}], issues [string]. Groups and ambiguity must cover each input exactly in the membership sense: nonambiguous items appear in one or more groups; ambiguous items appear in no groups. Every group has at least two single-group members.

Compare reviews by pair relationships, not arbitrary group names. A separate adjudication pass sees sources and both reviews, resolves all disagreements using source evidence, and preserves the original authoring/reviews. Final labels and adjudication are frozen before predictions. Reviewer consensus does not establish correctness; common-model errors and synthetic style cues remain risks.

## Frozen experiment defaults

Model: microsoft/MiniLM-L12-H384-uncased, pinned immutable revision and asset hashes. Add a three-class head in order [same, related, unrelated]. An initially seeded, untrained head is ONLY a conversion reference, never a semantic baseline. No remote model code execution. Prefer safetensors; if upstream supplies PyTorch weights, use a version with safe weights-only loading and verify the upstream content hash before loading in Stage 2.

Apple embeddings: preserve existing contextual/sentence extraction and normalization policy. Record language, dimension, revision, and model-space identifiers. Never combine vectors from incompatible Mac/phone model spaces.

Baseline: StandardScaler plus multinomial logistic regression, C in [0.1,1,10], class_weight=balanced, max_iter=2000, random_state=17. Features: contextual cosine, sentence cosine, word TF-IDF cosine, character-trigram Jaccard, number-token Jaccard, and smaller/larger text-length ratio. Fit vocabulary, IDF, scaler, and weights on training libraries only. Lowercase word unigrams/bigrams; Jaccard of two empty sets is zero; zero/absent vector is missing evidence, not a fabricated match. Report availability and retain missing cases in coverage.

Candidate retrieval: for each source, exclude itself; union the top five contextual-embedding matches and top five word-TF-IDF matches within its library. Resolve score ties by source ID, deduplicate, never consult gold. Maximum ten candidates, possibly fewer. All-pair classification and candidate-conditioned classification are separate reports. Candidate recall@10 is the fraction of eligible sources with at least one other same-context source retrieved. Also report fraction of all relevant candidates retrieved. This measures candidate retrieval, not chronological production grouping.

Training: local PyTorch/MPS, seeds [17,29,41], at most 3 epochs each, AdamW learning_rate=2e-5, weight_decay=0.01, effective batch 16, microbatch initially 8 with gradient accumulation. Reduce microbatch on memory pressure while retaining effective batch and recording the change. Use inverse-frequency weighted cross-entropy from training labels. Include both pair orientations only inside the same split, assigning half weight to each. All pairs containing ambiguous sources are excluded from supervised loss, not silently treated as negative. Maximum total pair length 512; longest-first truncation, record affected examples. Save optimizer/random/data-position state every 50 optimizer steps and each epoch; MPS exact bitwise reproducibility is not promised.

Development selection: use the maximum of class probabilities as class prediction; same-context acceptance additionally requires same to be the winning class and P(same)>=threshold. Search thresholds at observed development P(same) values. Maximize macro-library same-context recall subject to pooled precision>=0.95 and >=30 accepted unordered pairs. Break ties by higher precision, then higher threshold; select simpler/earlier candidate for remaining ties. For pair direction, average probability vectors over both orientations. These are empirical operating points, not guaranteed calibrated correctness. If no candidate qualifies, report no qualifying model. No test-set selection.

Quality gate: on untouched test libraries, pooled same-context precision>=0.95 and >=30 accepted unordered pairs; macro-library recall improves >=0.05 over the frozen simple baseline; pooled precision drops <=0.01 relative to that baseline; candidate recall@10>=0.90. Baseline with undefined precision does not qualify for a clean comparative pass. Report all-pair and candidate-conditioned metrics separately; apply matcher gates to all unambiguous unordered pairs and retrieval gate separately. These pilot gates do not replace production 0.99 precision / 0.85 recall targets.

Report TP/FP/FN, per-library and pooled precision/recall, macro recall, automation fraction, confusion matrix, ambiguity coverage and accepted-ambiguity fraction. Undefined precision stays null, never 1.0. Describe uncertainty with 2,000 library bootstrap resamples, seed1729; dependent pairs/repeats are not independent samples. Every declared item needs an output/status; missing data cannot turn into a pass.

## Conversion and device gates

FP16 first, batch1, supported pair lengths256 and512. Verify exact token IDs, masks, segment IDs, padding, truncation, and label order on >=100 non-test pairs including empty input, Unicode, punctuation, numbers, and length boundaries. Require finite outputs, max absolute probability difference<=0.01, and >=99% class agreement. At Stage6 report threshold-decision disagreement separately and require device-quality gates to hold too. Compression must repeat these checks, never substitute a storage result for quality.

Probe bundle: SimpleStudio.Remember.MatcherProbe, no production App Group, labels or private data. Ten process-cold loads and >=100 warm measurements, cold preparation reported separately. Warm ten-pair shortlist p95<=1second at length256; peak sampled probe process RAM<=500MB; no crash/lost completed records. Report512-token measurements, cold startup, system-memory visibility limits, thermal state and sampling frequency separately. Stage4 measures both pair directions when assessing the ten-pair decision path, consistent with the probability averaging policy. Package sizes and runtime caches are separate; 70–130MB is a planning estimate, not a guaranteed pass criterion.

## Persistence and release integrity

Write immutable run artifacts and atomic completion markers; retain failed runs. Freeze source inputs, final labels, both independent reviews, adjudication, authoring/split metadata, contract, configuration, validation code/tests, environment lock, and model manifest. Verify hashes before each subsequent stage. Do not rewrite frozen files to pass a check. Amendments require a new version and an explicit report.

At each checkpoint report completion/verdict, artifact locations, unresolved risks, correction estimate if needed, next action and hardware, remaining stage time and remaining overall work. Stop at the checkpoint. An unexpected interruption can rerun only the unfinished measurement batch; training resumes from its last valid checkpoint. Before launching future jobs, recheck disk and preserve the old evidence.
