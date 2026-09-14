# Organization and provenance benchmark — 10–11 September 2026

## Status

The evaluation infrastructure, agent-reviewed corpus, controlled media fixtures, and history-integrity tests are implemented. **All 144 core scenarios completed on 11 September 2026 at 12:09 Singapore time**, and the full frozen-label score passed its input/label/scorer/contract integrity checks with no missing scenarios or libraries. **Neither mode meets the English-heldout semantic-quality targets.** Performance testing recorded one completed workload, one in-process timeout, and one host-stopped incomplete workload. The isolated app is stopped; extended local-metadata media repeats remain unexecuted. This is a completed core baseline and documented performance attempt, not a full performance pass or complete end-to-end media certification.

The final core phase resumed at 11:51 from 118 completed scenarios. All 118 records were verified exactly unchanged in the completed report. Recorded source hashes, device OS, and cached dependency revision matched before launch. Successful collection is not a claim of reliable semantic organization.

The 11 September phase resumed at 11:13 from 101 completed scenarios and completed 17 more before pausing. All 101 earlier completed records were verified exactly unchanged after resuming. Recorded source hashes, device OS (iOS 26.6.1), and the clean cached dependency revision matched before launch. The previously interrupted l09 scenario finished, and all 12 l09 scenarios recorded zero reasoning-call errors.

The run resumed at 20:45 following the earlier 19:59 pause. Source hashes, cached dependency revision, and device OS were verified unchanged. All 73 pre-pause completed records were structurally compared and remained exactly unchanged after resuming; 28 additional scenarios completed before the second pause. The 22 Python tests and 20 JavaScript tests were rerun successfully during this resumed phase.

No production grouping thresholds, prompts, source models, or application behavior were changed. The original 42-item embedding evaluation remains intact. No personal vault data was used, and hosted inference was disabled in the isolated benchmark apps.

## What was built

- A 360-memory fictional corpus in 12 separate libraries: six development and six heldout, including Spanish/English and French/English slices. A thread means a specific continuing context, not merely a shared topic. Multi-context sources may belong to multiple threads without merging those threads.
- Two independent, source-based agent reviews, followed by adjudication and a 72-item adversarial sample. An audit led to 24 pre-prediction amendments, introducing one sparse and one longer note per library. Original inputs and reviews are retained.
- Frozen hashes binding the final input, reviewed labels, reviews, adjudication, contract, and deterministic scorer before predictions. Labels never enter the phone app. Scoring rejects changed frozen labels, scorer bytes, or mismatched result manifests.
- Production-code device runners for five arrival orders and repeated local-reasoning runs, with actual embeddings, source/model manifests, membership snapshots, events, timing, availability, and resumable checkpoints.
- Twelve positive merge and twelve split-proposal opportunities seeded into controlled initial states. These measure actual batch behavior, separately from naturally evolved grouping.
- Thirty-six generated media files: twelve images, eight PDFs, eight audio clips, and eight videos, embedded in the original text-context libraries. Reference-text controls and actual extraction runs are scored separately.
- A pinned 200-example BANKING77 subset diagnostic and 100-, 500-, and 1,000-item development-content performance workloads.
- Twenty-four explicit history cases and 100 seeded, 50-command state-machine sequences with independent command-side expectations.

The [benchmark README](../../Evaluation/Organization/README.md) contains preparation and execution commands. The [contract](../../Evaluation/Organization/CONTRACT.md) defines metrics and preregistered targets.

## Completed validation

| Check | Observed result |
| --- | --- |
| Python scorer tests | 22 passed: 14 organization tests (including 100 seeded exact overlap-metric comparisons) and eight post-hoc audio diagnostic tests |
| JavaScript preparation, decision derivation, scoring, and active-checkpoint tests | 20 passed |
| Focused history benchmark | 24 explicit cases + 100 seeded sequences passed; 5,000 generated commands |
| Complete `RememberTests` simulator suite | 109 test functions in eight suites passed, including the two parameterized history functions |
| Signed organization and decision probe builds | Passed |
| Device smoke | Real embeddings available; isolated grouping and controlled split-proposal paths executed |
| Full core physical-device matrix | 144/144 completed; frozen-label scoring succeeded, but semantic targets failed |
| Frozen corpus and media asset audit | All checked hashes matched; both final reviews cover all 360 inputs |

Function counts and parameterized-case counts above are different measures, not additive test totals. Passing integrity tests establishes the tested invariants; it does not establish semantic grouping quality.

The Python and JavaScript suites were rerun successfully on 11 September after core collection. Relative links in the report, benchmark README, and execution/resume notes were checked and all resolved locally. The full Swift simulator results above are the earlier 10 September run; no production Swift code changed during the subsequent device resumes.

## Public subset result

The embedding-only chronological BANKING77 diagnostic processed 200/200 items with no unavailable embeddings, producing 125 clusters in 113.37 seconds. Pairwise precision was **64.52%** and recall **11.11%** (100 true-positive, 55 false-positive, and 800 false-negative pairs). Eight of twelve observed merges were consistent with the intent labels; four were not.

This is evidence of substantial fragmentation and some over-grouping **on this intent-label diagnostic**. BANKING77 intent identity differs from Remember's specific-project identity, so this result must not be substituted for the Remember heldout score or advertised as a standard BANKING77 benchmark score. Original text/labels, source revision, selection rule, and attribution are retained in [public provenance](../../Evaluation/Organization/public/provenance.json). Dataset source: [PolyAI BANKING77](https://huggingface.co/datasets/PolyAI/banking77).

The [verified public score](../../Evaluation/Organization/public/score-verified-2026-09-10.json) checks the input/label/result freeze binding. Its earlier public freeze does not bind scorer/contract bytes, unlike the main benchmark. Its runner also predates final telemetry and cooperative-deadline hardening; the production grouping code was unchanged. The earlier score is retained rather than silently overwritten.

## Device matrix

The prepared core matrix contains 144 scenarios: 12 libraries × (five embedding-only orders + five local orders + two additional chronological local repeats). The first media comparison uses embedding-only reference and extracted modes (12 libraries each), isolating extraction from local generated metadata. Extended media configurations also support local metadata/reasoning and chronological repeats; those are reported separately if executed. The controlled-decision matrix contains 48 scenarios (24 cases × two modes); the scale matrix contains three embedding-only workloads.

The core matrix completed **144/144 scenarios**, with zero scenario-level blocked/error/timeout outcomes. It recorded 1,813 reasoning calls, one reasoning-call error, and 420 unavailable-embedding observations across repeated multilingual scenarios. These capability/error facts remain visible despite scenario completion. Missing, blocked, errored, or timed-out scenarios are not passes. A command's successful exit only establishes execution completion, not that quality targets were met.

The final [core archive](../../Evaluation/Organization/results/core-complete-2026-09-11.json.gz) and [core score](../../Evaluation/Organization/results/core-complete-score-2026-09-11.json) contain all 144 scenarios. Archive SHA-256: `29a946ab22e9ccb1c7fe23080ec9e1bd3ad9cd937cac1f5919bf076b77c95327`. Earlier paused/live checkpoints and interrupted attempts remain separate historical artifacts, not silently overwritten. The controlled-decision, embedding-only media comparison, and public diagnostic suites are complete. Scale collection is stopped with unsuccessful larger workloads documented below. See [execution/resume notes](../../Evaluation/Organization/RESUME.md).

The completed l08 runs include one reasoning-call error; successful scenario completion is not an error-free-model claim. Its local runs took approximately 78–136 seconds, versus 54–69 seconds for l07. Before the second user-requested pause, l09's first local run had shown no new capture progress for roughly a minute; the device was connected/unlocked and the probe process remained present. The cause was not established. This interrupted attempt is retained as running/incomplete, not relabeled as a timeout or a pass. Timing variation and interruptions prevent precise remaining-time guarantees.

### Completed English core results

All 120 English core scenarios completed: ten libraries, five embedding-only orders and seven local-reasoning runs per library. The earlier [English-complete checkpoint](../../Evaluation/Organization/results/core-english-complete-2026-09-11.json.gz) and [partial score](../../Evaluation/Organization/results/core-english-score-2026-09-11.json) remain historical evidence. The final core score above includes the subsequent multilingual coverage; the completed English results are unchanged.

On the five **heldout English libraries**, neither mode met the preregistered 99% precision / 85% recall targets:

| Mode | Completed heldout runs | Pair precision | Pair recall | Overlap-aware B-cubed precision / recall |
| --- | --- | --- | --- | --- |
| Embedding only | 25 | 77.12% | 31.65% | 88.61% / 51.92% |
| Local reasoning | 35 | 18.01% | 59.50% | 30.55% / 71.06% |

These are macro library averages, averaging runs within each library. The local mode includes three chronological repeats, so chronological order has greater weight than each other order in that mode's aggregate. The artifact retains individual orders/repeats. Descriptive library-bootstrap 95% intervals are 73.28–81.70% / 24.35–38.94% for embedding precision/recall, and 16.97–19.01% / 55.17–65.38% for local precision/recall. Five synthetic libraries do not establish deployment confidence.

Embedding-only runs recorded **19 retrospectively prohibited merges out of 55 observed merges** on heldout English; none were unscored. Local runs recorded no literal merge events, but their very low pair precision exposes incorrect placement joins. Zero merge events therefore does not establish safe grouping. Grouped-item fractions were 76.53% and 94.57%, respectively; more automation was not higher accuracy. No embeddings were unavailable in these English runs. One reasoning-call error occurred across the 35 heldout local runs and remains recorded despite successful scenario completion.

Development English results showed the same broad pattern: embedding precision/recall 77.65% / 27.50%, local 19.16% / 58.55%. The conclusion is a **failed semantic-quality baseline**, not merely an extraction or missing-model issue. Model-versus-integration causes still require isolated development experiments; no production policy was changed during collection.

### Multilingual and relationship diagnostics

Each multilingual slice has only one 30-source library, not enough to estimate language-wide performance. All twelve scenarios per library completed, but embeddings were unavailable for the same **19/30 Spanish/English sources** and **16/30 French/English sources** in every run. This accounts for all 420 unavailable observations across the core matrix; no English-core embeddings were unavailable. Missing embeddings were not dropped or replaced with reference vectors.

| Slice | Embedding pair precision / recall | Local pair precision / recall |
| --- | --- | --- |
| Spanish/English development | 65.71% / 7.35% | 25.37% / 7.77% |
| French/English heldout | 72.42% / 10.88% | 15.57% / 13.03% |

Local mode made 45 and 76 reasoning calls, respectively, with no recorded reasoning-call errors in these slices. Availability gaps and poor recall both matter; successful calls do not establish useful organization. One-library bootstrap intervals collapse to the observed value and must not be presented as statistical certainty. These are separate diagnostics, not substitutes for the English acceptance score.

On the frozen shared-source relationship labels for heldout English, actual displayed graph edges yielded **0 true positives, 0 false positives, and 75 false negatives** in embedding mode; local mode yielded **12 true positives, 36 false positives, and 93 false negatives**. Counts pool dependent repeated runs and the local mode has more repeats. This evaluates the actual first-40-node display and the scorer's greatest-overlap mapping, not unrestricted semantic relatedness. It does not validate reliable graph connections; broad tag-derived connections remain outside the core's deterministic, empty-tag metadata setup.

### Controlled decision results

All 48 controlled scenarios completed. In **each** mode, the service performed the expected merge in **2/12 opportunities (16.7%)** and produced **0/12 expected split proposals**. Both observed merge events were correct, but a two-event, positive-opportunity sample does not establish general merge safety. Split memberships stayed unchanged, and no citation-integrity failures were observed.

Ten of twelve cases per opportunity type had all required embeddings available; the two multilingual cases had availability gaps. Missing capability remains in the opportunity denominator. Both modes recorded zero reasoning calls because this seeded cached-placement path exercises the current batch heuristics, not the local language model. The two modes therefore do not demonstrate separate model performance here.

See the frozen [decision score](../../Evaluation/Organization/decisions/score-2026-09-10.json) and [raw archive](../../Evaluation/Organization/results/decisions-2026-09-10.json.gz). The successful smoke split and poor reviewed-case split recall are both retained: a smoke success was not substituted for benchmark quality.

### Media results

All 24 embedding-only scenarios completed: twelve reference-text controls and twelve actual-extraction runs. Actual extraction returned nonempty evidence for all twelve images, eight PDFs (including scanned PDFs), eight audio clips, and four captioned videos. The four captionless videos correctly recorded `no_source_evidence`. No extraction call threw an error.

**Nonempty output is not necessarily accurate output.** The Spanish and French audio clips produced visibly garbled transcripts while still reporting completed extraction. The current transcriber chooses the device locale, not a detected per-file language. A separately labeled post-hoc audio diagnostic examines transcript accuracy; successful API completion is not used as an accuracy score.

The [audio diagnostic](../../Evaluation/Organization/media/AUDIO-DIAGNOSTIC.md) found 66 word edits over 265 reference words (**24.91% normalized WER**) across all eight clips. The six English clips pooled to 6.22%; the single Spanish and French clips scored 88.89% and 61.11%. The diagnostic preserves accents and numeric forms, does not clip WER, and counts missing/failed transcripts as deletions rather than dropping them. Its code, normalization, and exact archived input/result bindings were separately frozen before computation, but the metric was added after observing the extraction issue and is explicitly **post-hoc**, not preregistered. These synthetic, partly code-switched clips do not establish language-wide speech accuracy or isolate the cause of errors.

Across the six heldout media libraries, including the French/English library, macro pair precision/recall were **74.82% / 27.40%** with reference text and **72.96% / 26.88%** with actual extraction. These are not the English-only core acceptance scores. Each condition has only one arrival-order run, and production merge-ID variation remains possible, so the small difference is not a precise causal estimate. More importantly, the low reference-text recall shows that extraction failures alone cannot explain the grouping weakness.

The reference and extracted runs recorded 39 and 40 unavailable embedding observations respectively, including the four intentionally unsupported captionless videos. Availability is retained alongside scores rather than filtered out. On the narrow shared-source relationship labels, actual extraction yielded three correct displayed links, two incorrect links, and 33 missing expected links across the twelve libraries; this does not certify broad semantic relatedness.

See the [reference score](../../Evaluation/Organization/media/score-reference-2026-09-10.json), [extracted score](../../Evaluation/Organization/media/score-extracted-2026-09-10.json), and corresponding raw archives in [results](../../Evaluation/Organization/results). Extended local-metadata media repeats have not yet been executed; the main core suite separately exercises the local reasoning path.

### Instrumented performance workloads

| Workload | Outcome | Completed inputs | Elapsed scenario time | Peak sampled app memory |
| --- | --- | --- | --- | --- |
| 100 | Completed | 100/100 | 46.97 seconds | 95.23 MiB |
| 500 | In-process timeout | 372/500 | 600.07 seconds | 130.61 MiB |
| 1,000 | Host-stopped, incomplete | 238 logged; 200 durably checkpointed | Unavailable | Unavailable |

The 500-item workload recorded `CancellationError()`. The 1,000-item workload stopped reporting capture progress at 12:24:54 and did not produce an in-process terminal result. Only the verified isolated app process was terminated at 12:32:38 Singapore time, after the nominal scenario deadline and a grace period. This was a **post-hoc host stop before the configured overall 2,100-second host timeout**, not a normal completed scenario or an in-process timeout. Connection/process checks did not establish foreground lifecycle state or isolate the cause. The raw status remains `running`; the scenario is incomplete and is not scored as successful.

The [final scale collection](../../Evaluation/Organization/results/scale-terminal-2026-09-11.json.gz), [console log](../../Evaluation/Organization/results/scale-console-2026-09-11.log), and [incident record](../../Evaluation/Organization/scale/EXECUTION-2026-09-11.md) preserve these distinctions. The last durable 1,000-item checkpoint contains 200 captures because it saves every 50 inputs; the last console line reports 238. No terminal timing or memory value is invented for that workload. Earlier checkpoints remain historical evidence. Neither larger workload completed, and no failure was retried away.

These workloads repeat development-source content and have no semantic gold labels. They include Debug-build, full-process, event-replay, graph-map, and diagnostic work; the measurements are not an isolated production-service profile or release-app capacity guarantee. Memory is sampled at capture boundaries and excludes separate OS/model services. Reporting serialization took 0.21 seconds for the 100-item workload and 0.24 seconds for the partial 500-item workload, but those values do not capture all diagnostic work. Partial-run availability records may include an interrupted in-flight input; they must not be read as a language/model capability test. No configured timeout value, workload size, or production behavior was changed after observing performance; the separate post-hoc stop is explicitly recorded above.

### Checkpoint-overhead correction

The initial core run was deliberately stopped during its 22nd scenario, before heldout predictions, after discovering that per-capture checkpointing rewrote the growing archive of all preceding scenarios. At scenario eight that archive was already about 5.2 MB, and reporting time was increasing with every scenario. The benchmark runner was changed to keep per-capture active-run checkpoints separate from the completed-results archive. This changes measurement/storage overhead, not production grouping, data, labels, or scoring.

The pre-correction [raw archive](../../Evaluation/Organization/results/core-precheckpoint-fix-2026-09-10.json.gz) and [score](../../Evaluation/Organization/results/core-precheckpoint-fix-score-2026-09-10.json) are retained, including their missing/incomplete coverage. They are diagnostics, not silently discarded model failures or a completed core baseline. Original probe source is retained alongside the archive. Final execution uses a fresh configuration manifest; variation between reruns must not be attributed to a grouping-policy improvement.

## Interpretation limits

- **Agent-reviewed, not human-validated.** Agreement is not proof of truth; reviewers can share correlated errors. The final reviews agreed after source amendments. One ambiguous original Spanish source was clarified before predictions, so zero final ambiguity does not validate ambiguous-input handling.
- **Narrow synthetic diversity.** The libraries repeat a similar context/bridge/singleton template. Of 360 inputs, 336 remain short notes of roughly 27–37 words; the longest amended note has 215 words. This is not a long-document benchmark. Libraries are the resampling units, but their shared template limits statistical independence and generalization claims.
- **Audit scope.** The 72-item audit sampled the original corpus; all 24 amendments were subsequently reviewed, with overlap. It was not a fresh, independently blinded 20% sample of the entire final corpus.
- **Decision scope.** Controlled merge cases are positive opportunities. Their event precision is not a general false-positive/safety estimate. Unexpected merges in split cases can fail the split outcome but are not included in the decision scorer's merge precision. Natural-capture merge diagnostics remain separate.
- **Model use is observed, not assumed.** Foundation Models availability is not proof of use. Core local runs record actual reasoner calls; controlled cached-placement batch cases can use heuristics and make zero reasoner calls in either mode.
- **Media scope.** Assets inherit reviewed text labels; they have no independent asset-level semantic review. Audio uses local synthetic voices, videos use test patterns, and video support is caption-only. Four captionless videos have explicit unsupported-singleton expectations. Media relationship labels cover shared-source links, not unrestricted semantic relatedness.
- **History scope.** The tests check replay, memberships, revisions, pins, archives, corrections, immutable history, and backward references. They do not exercise actual media-byte restoration, live recap generation, wall-clock backoff, daily scheduling, or randomized merge/split operations. Explicit cases cover merge/split bookkeeping.
- **Runtime scope.** Timings come from signed Debug probes with diagnostic instrumentation and retained result data, not an optimized release build. Sampled resident memory covers the benchmark process, not every separate OS/model service; it is not an exact allocation peak or battery test. Device/model caches can be warm and thermal conditions are not controlled, so these are not cold-start or release-performance certifications. Scenario cancellation is cooperative; host timeouts are still necessary for OS calls that do not promptly cancel.
- **No tuning on this baseline.** Once heldout predictions are inspected, this release is historical evidence. Future fixes should use development failures; independent improvement claims require a fresh heldout release.

## Development failure analysis

An independent read-only analysis of the first completed `l01` development scenarios found both fragmentation and unsafe joins. In embedding-only chronological order, pair precision/recall were 71.4% / 22.1%, with 16 predicted threads versus nine reviewed contexts. Juniper sources `l01-i15` and `l01-i26` grouped together while `l01-i11` and `l01-i17` remained singleton. Lamp-checklist `l01-i13` merged with the unrelated trust metaphor `l01-i20`; an Orchard observation later joined that cluster. All source embeddings were available.

The first two local chronological repeats had precision of 18.7% and 17.2%, with 187 and 197 false-positive pairs. Each recorded 21 accepted reasoning decisions and no reasoner errors. In the second repeat, `l01-i05` was assigned to a candidate its rationale described as unrelated; `l01-i20` similarly received a candidate assignment while its explanation described a distinct subject.

These local repeats had **zero literal merge events**: the false joins occurred through placement events. Therefore zero prohibited merge events is not a sufficient safety criterion; pairwise grouping precision remains essential.

Code inspection identifies plausible contributors, not isolated causal proof: the reasoner fallback can receive the top two similarity candidates without requiring the lexical-grounding filter; a valid candidate ID plus nonempty rationale can pass acceptance; candidate descriptions expose only three members. The existing prompt already prohibits broad-topic grouping. Follow-up work should isolate these mechanisms using development data and explicit negative placement tests before any policy change. No threshold or prompt was tuned during this evaluation.

## Recommended development follow-up — not implemented in this baseline

1. **Prioritize incorrect joins before increasing automation.** Reproduce the source-grounded development failures and isolate candidate generation, candidate evidence, and structured decision acceptance. Test negative placements and valid-looking candidate IDs paired with contradictory rationales. Do not substitute a rationale-word regex for semantic validation or tune against the inspected heldout cases.
2. **Then address fragmentation and multi-context evidence.** Add development checks for paraphrases, revisions, and sources belonging to two contexts without fusing those contexts. Measure placement accuracy and distinct-context preservation separately from literal merge events.
3. **Improve batch opportunities independently.** The controlled suite exposes low merge recall and missing split proposals. Inspect candidate eligibility and the unsupported local split path with dedicated development cases; do not infer success from final cluster counts or a smoke split.
4. **Make capability gaps explicit.** Investigate multilingual embedding availability and speech locale behavior. Keep unavailable/unsupported inputs visible in the product and evaluation; no claims of broad-language or video-understanding support follow from these fixtures.
5. **Validate improvements on new evidence.** The current heldout release has now been inspected. Keep it as a historical regression baseline, and create a fresh, more diverse heldout release before claiming independent quality gains. Agent consensus remains useful review evidence, not human validation.

These priorities follow from the completed diagnostics and earlier development-code inspection. They are proposed follow-up work, not production changes or experimentally established root causes. Runtime findings must be interpreted separately from semantic quality.

## Commands and evidence

Host checks:

```sh
python3 -m unittest discover -s scripts -p 'test_organization*.py' -v
node --test scripts/embedding-evaluation/prepare-organization.test.mjs scripts/embedding-evaluation/derive-decisions.test.mjs scripts/embedding-evaluation/score-decisions.test.mjs scripts/embedding-evaluation/merge-organization-checkpoint.test.mjs
git --no-optional-locks diff --check
```

Full simulator suite:

```sh
xcodebuild -project Remember/Remember.xcodeproj -scheme Remember \
  -destination 'platform=iOS Simulator,id=5741ED23-9F8F-4FB6-84E9-FE1E83225998' \
  -configuration Debug -derivedDataPath /tmp/RememberOrganizationHistory \
  -clonedSourcePackagesDirPath /tmp/RememberProvenance/SourcePackages \
  -disableAutomaticPackageResolution CODE_SIGNING_ALLOWED=NO \
  -parallel-testing-enabled NO -only-testing:RememberTests test
```

The simulator run log is `/tmp/remember-organization-all-unit.log`. Focused history evidence is `/tmp/remember-organization-history-verified.log` and the corresponding `.xcresult`. Physical runs use the connected iPhone 17 on iOS 26.6.1 and separate `SimpleStudio.Remember.OrganizationProbe` / `SimpleStudio.Remember.OrganizationDecisionProbe` containers, never the personal Remember app.

Host toolchain: Xcode 26.5 (17F42), Python 3.13.12, Node.js 22.23.1. The existing clean local GRDB 7.11.1 checkout at revision `b83108d10f42680d78f23fe4d4d80fc88dab3212` was reused without package resolution updates; its revision matches the project's `Package.resolved`. This was checked with read-only Git commands with optional locks disabled. Run manifests bind `Package.swift`, not every dependency file, so the recorded clean revision is an additional reproducibility requirement.

Python's initial upstream download failed local CA verification. The pinned public CSV was instead downloaded using normal TLS-verified `curl`, then validated offline against its expected SHA256. TLS verification was not disabled. No Git state was changed.
