# Stage 1 complete — prepared, not evaluated

Saved 11 September 2026. **Stopped here; Stage 2 has not started.** No inference, training, Core ML conversion or phone installation was performed. No production behavior or Git state changed.

## What is ready

- [Six-stage plan](../PLAN.md), [experimental contract](../CONTRACT.md), frozen settings and [resume instructions](../RESUME.md).
- 600 fictional English memories in 30 libraries, with input-only files separated from host-only labels. Train: 360 memories/18 libraries; development: 120/6; test: 120/6. Domains and named author-template families are split-disjoint.
- Two independent, author-label-blind reviews; separate source-grounded adjudication; preserved original reviews and six source amendments. Latest source revisions are bound to their reviews before release.
- 114 final contexts, with 2–5 contexts per library. Fifty memories have overlapping memberships; 57 are explicitly ambiguous. Source lengths are 8–172 words.
- A historical baseline snapshot and hashes for six prior evidence files and 51 production Swift files. These all remained unchanged. Historical scores are not comparisons on this new dataset.
- Pinned MiniLM revision, verified original assets, isolated Python environment and exact package lock. Apple Silicon MPS is available. No model weights have been loaded for inference.

## Dataset audit, not model results

Every library contributes 190 unordered pairs, totaling 5,700. Ambiguous-source pairs remain visible but are excluded from supervised class loss.

| Split | Same project | Related projects | Unrelated | Uncertain | Total pairs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Training | 903 | 212 | 1,712 | 593 | 3,420 |
| Development | 245 | 232 | 441 | 222 | 1,140 |
| Test | 312 | 127 | 464 | 237 | 1,140 |
| Total | 1,460 | 571 | 2,617 | 1,052 | 5,700 |

The two latest independent reviews differed on **162 pairs across 19 libraries**. Adjudication resolved those decisions and independently checked areas of agreement. Compared with provisional author labels, final labels changed **553 pairs across 13 libraries**. Neither number is a model accuracy score.

Important correction: a game's mechanics and expansion, a booklet's chapters and cover, or an exhibit's fabrication and audio work can belong to one continuing project. Different workstreams are not automatically different threads. Conversely, borrowing a template does not always mean a memory belongs to the donor project. Shared procurement, physical transfers and explicit joint work can justify overlapping memberships. Where ownership remains unclear, the source stays ambiguous rather than acquiring invented certainty.

Six notes had genuine missing-scope clarification. Their original text hashes and reasons are preserved, and both reviewers reviewed the revised test input batch. No notes were rewritten simply to restore the author's preferred number of groups. Per-library requirements for bridges/class diversity were removed before freeze because they would force incorrect labels; full-corpus class and bridge coverage remains required. No model predictions informed these changes.

No normalized exact source duplicates were found, no exact matches to the historical benchmark were found, and the cross-split five-word-shingle Jaccard screen produced no flags at its 0.20 threshold. This **does not prove** semantic independence or eliminate repeated synthetic writing patterns.

## Mac resources and setup correction

The isolated workspace is `~/Library/Application Support/RememberMatcherFeasibility/v1`; it uses approximately **1 GiB**. Latest free-space check: **38,450,987,008 bytes**, about **35.8 GiB**. The repository experiment evidence is only a few megabytes.

The six original model/tokenizer/card assets total **133,717,050 bytes (133.7 MB)**. These are original desktop assets, not the eventual Core ML phone package or an app-size measurement. The earlier 70–130 MB phone planning estimate remains unverified.

Selected environment: Python 3.11.15, PyTorch 2.7.0, Transformers 4.53.3, Core ML Tools 9.0, scikit-learn 1.5.1 and NumPy 1.26.4. All 37 installed distributions match the resolved lock. Initial scikit-learn 1.7.1 produced an optional Core ML converter compatibility warning; it was replaced with 1.5.1 in the isolated environment and verification passed. Initial records remain under `setup-attempts/initial/`. Import success is not proof of conversion feasibility.

## Validation actually run

```sh
python3 -m unittest discover -s scripts/matcher-feasibility -p test_experiment.py -q
python3 -m unittest discover -s scripts -p 'test_organization*.py' -q
python3 scripts/matcher-feasibility/experiment.py verify --freeze Evaluation/MatcherFeasibility/freeze.json
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/environment.py --workspace "$MATCHER_WORKSPACE" --output Evaluation/MatcherFeasibility --verify-only
```

Results: **36 preparation tests passed; 22 existing organization/audio tests passed; all 57 frozen files verified; six model assets and 37 package versions verified; `pip check` passed.** The full corpus projection, review aggregation, adjudication finalization and 5,700-pair audit also passed. A separate SHA-256 comparison confirmed all six historical artifacts and 51 snapshotted production files unchanged. No Swift build or iPhone tests were needed or run for this Mac-only stage.

Freeze SHA-256: `b5291755a161344e83cc9f85f91307d50214aad4da05b558650c2dc3bdd71641`.

## Verdict and next checkpoint

**Ready for Stage 2, subject to your continuation. No additional corrective step is currently required.** This is a preparation verdict, not evidence that MiniLM improves grouping.

Stage 1 finished substantially faster than its initial 3–5-hour allowance: approximately 20–25 minutes of execution, helped by parallel author/review work and a straightforward environment setup. Do not extrapolate that speed to training or device conversion.

Next: implement and run the simple classifier/reference-output experiment on the **Mac only**, initially **2–4 hours**. No phone connection is needed. Compare baseline coverage and development performance before proceeding. Stages 2–6 remain approximately **14–29 active hours**, excluding approval pauses and unexpected corrections. Stop again after Stage 2.

Limitations: this is English synthetic, agent-reviewed data, not human validation or real-user robustness evidence. Agent reviewers can share mistakes. Thirty small libraries and final-library pair labels do not validate long-term arrival-order behavior, safe automatic merges, extraction from media, or multilingual performance. Development/test class proportions differ and should be reported, not silently balanced away. Separate chronological/production-level evaluation remains necessary after feasibility succeeds.

All completed work is saved. No experiment jobs remain running; you may close the laptop or disconnect the phone. To continue later, ask to resume Stage 2 and use the preflight in [RESUME.md](../RESUME.md).

Files added for this task are confined to `Evaluation/MatcherFeasibility/` and `scripts/matcher-feasibility/`. Large downloaded assets and the isolated environment are outside the repository in the dedicated workspace. Nothing was staged, committed or published.
