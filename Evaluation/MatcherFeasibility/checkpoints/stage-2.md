# Stage 2 complete — baseline and original reference saved

11 September 2026. **Stopped at this checkpoint. Stage 3 has not started.** No production integration, task-specific neural training, Core ML conversion or phone testing occurred.

## Outcome

The lightweight baseline meets the pilot's development operating-point requirement, but only by accepting a small fraction of possible matches. This is a useful comparison target, not a production-ready grouping system. No obligatory corrective rerun is currently needed before conversion feasibility work.

| Development result | Value | Meaning |
| --- | ---: | --- |
| Same-project precision | 96.05% | 73 correct and 3 incorrect accepted known pairs |
| Same-project recall, pooled | 29.80% | 73 of 245 true same-project pairs accepted; 172 missed |
| Mean recall across six libraries | 29.94% | The contract's selection objective |
| Accepted pairs / all 1,140 pairs | 6.67% | 76 accepted; includes ambiguous pairs in the opportunity denominator |
| Ambiguous-pair acceptance | 0 / 222 | The cautious operating point accepted none of these uncertain pairs |
| Retrieval: at least one correct neighbor | 108 / 108 eligible memories | Meets the development retrieval diagnostic, in libraries of only 20 items |
| Retrieval: all relevant neighbors recovered | 369 / 490 = 75.31% | Retrieval is not perfect; the shortlist still misses relevant neighbors |

These are **development results used for model/threshold selection**, not heldout test performance. The earlier app benchmark used different data and metrics; its percentages are not directly comparable. The untouched test evaluation is still reserved for Stage 5.

Without the cautious threshold, simply accepting the highest-scoring `same` class gives **37.13% precision and 91.84% pooled recall**, with 381 incorrect accepted known pairs and 134 accepted ambiguous pairs. Do not deploy that behavior. The baseline's scores are not calibrated probabilities of correctness: even scores above 0.99 can be wrong.

Descriptive 95% library-bootstrap intervals after development selection: precision **93.69–100%**; pooled recall **18.70–44.86%**; macro recall **18.70–45.10%**. Six synthetic libraries are insufficient for a production guarantee, and these intervals do not undo selection bias.

## What ran

1. Reverified the Stage 1 freeze, package lock and original model hashes.
2. Built an isolated macOS Swift probe using a verbatim extraction of the production `AppleProjectEmbedding` provider and normalization function. It preserves language detection, sentence chunking, contextual token averaging and separate vector spaces. No production source was changed.
3. Extracted **480/480 embeddings successfully**: 360 training memories and 120 development memories. All were recognized as English in one recorded model space, with 512-dimensional contextual and sentence vectors. Actual extraction summed to approximately **61.6 seconds** on this Mac.
4. Fitted word unigram/bigram TF-IDF on training text only. Built six symmetric pair features: contextual cosine, sentence cosine, word TF-IDF cosine, character-trigram overlap, numeric-token overlap and text-length ratio.
5. Fitted StandardScaler and three balanced logistic-regression candidates (`C = 0.1, 1, 10`) on **2,827 unambiguous training pairs**. Produced complete outputs for all 3,420 training and 1,140 development pairs, including ambiguity diagnostics; no missing predictions.
6. Selected on development only, following the frozen precision/recall/tie-break rules. All three C values accept the same 76 known pairs at their respective qualifying thresholds. The stipulated higher-threshold tie-break selects **C = 10**, threshold **0.994161103056994**. This is not evidence that its tiny score difference is meaningful.
7. Loaded the pinned MiniLM backbone with safe weights-only loading, offline/local files and remote code disabled. Only the expected classification weight and bias were newly initialized, with seed 17. No neural optimizer or fine-tuning ran.
8. Saved safe reference weights, config, tokenizer, exact input IDs/masks/segment IDs, logits and probabilities for **104 fixture pairs × two directions × two lengths = 416 cases**. Lengths are 256/512; fixtures include empty text, Unicode, numbers/punctuation, exact length boundaries and overflow. Six cases intentionally truncate. Reloading the saved safe weights reproduced the checked logits exactly (maximum absolute difference **0.0**).

The reference head is **untrained**. Its outputs are numerical targets for Stage 3 conversion parity, not predictions whose semantic quality should be compared with the baseline.

## What the errors show

All three cautious false positives are `related` projects mistaken for `same`:

- `mf22-i02` / `mf22-i04`: adult and youth performances share the venue and title, but differ in participants, times and staging. Score: 0.99916.
- `mf24-i04` / `mf24-i05`: main-house and detached-studio solar work share an address, but have different roof/inverter plans. Score: 0.99971.
- `mf24-i05` / `mf24-i18`: studio planning versus an update to the main-house cable-route quote. Score: 0.99682.

This suggests that coarse similarity features do not reliably distinguish shared subject matter from project identity. It motivates testing a text-aware specialist, but **does not establish that MiniLM will solve it**. Labels, thresholds and experiment settings were not revised in response to these errors.

## Pause/resume was tested, not just documented

The live run paused after **114 completed embeddings**, saved a boundary record, closed its child process and exited. Resume verified the same code/data/model inputs and skipped those records. The final audit confirmed all 114 retained their original pre-pause timestamps, with no completed record lost or rewritten.

You can say **“pause now”**, wait for the saved-boundary confirmation, close the laptop, then say **“resume”** later. A sudden closure may require repeating an unfinished item/batch; the agent cannot save new progress while the laptop is asleep. Build/model-load work may delay reaching a cooperative pause boundary. Future stages will retain equivalent checkpoint behavior; neural optimizer checkpointing is implemented with Stage 5, not claimed complete now.

## Validation and reproducibility

Actually run:

```sh
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" -m unittest discover -s scripts/matcher-feasibility -p 'test_*.py' -q
python3 -m unittest discover -s scripts -p 'test_organization*.py' -q
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage2.py verify --run Evaluation/MatcherFeasibility/runs/stage-2-attempt-01
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/audit_stage2.py --run Evaluation/MatcherFeasibility/runs/stage-2-attempt-01 --output Evaluation/MatcherFeasibility/checkpoints/stage-2-audit.json
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/environment.py --workspace "$MATCHER_WORKSPACE" --output Evaluation/MatcherFeasibility --verify-only
```

Results: **56 feasibility tests passed** (36 Stage 1 + 20 Stage 2), and **22 existing organization/audio tests passed**. Swift probe compilation passed. The independent artifact audit reproduced training-only vocabulary/IDF, pair-label joins, exported classifier probabilities (maximum difference **0.0**) and threshold selection using a separate brute-force calculation. Candidate lists contain no self/cross-library entries or duplicates. A completed `run --resume` verified the checkpoint without restarting inference.

All **908 run JSON files and five external artifacts** verified, alongside all 57 Stage 1 frozen files. Six original model assets and 37 package versions verified; `pip check` passed. Six historical artifacts and 51 snapshotted production Swift files remain unchanged. No test-label interpretation or heldout test scoring occurred; integrity checks only hash those frozen files.

Completion marker SHA-256: `b8cd3fee4bfd87e5befb54d7fe81b7749fb1de28eace90f5de76cfa8ff44e888`.

## Saved files and resources

- Run: `Evaluation/MatcherFeasibility/runs/stage-2-attempt-01/` (approximately **26 MiB**).
- Portable selected baseline: `baseline-selected.json` (**422,593 bytes**), including TF-IDF state. This excludes Apple embedding assets and is not an app-size estimate.
- Main evidence: `embedding-summary.json`, `baseline-summary.json`, candidate predictions under `baseline/`, and reference fixtures/cases plus `reference-summary.json`.
- External reference: `~/Library/Application Support/RememberMatcherFeasibility/v1/stage2/stage-2-attempt-01/reference/`. Safe FP32 model weights: **133,467,884 bytes**. These are not the eventual Core ML package size.
- Independent audit: [stage-2-audit.json](stage-2-audit.json).
- Implementation: `stage2.py`, `stage2_metrics.py`, `stage2_reference.py`, `Stage2EmbeddingProbe.swift`, `test_stage2.py`, `audit_stage2.py` under `scripts/matcher-feasibility/`.

The complete isolated external workspace is about **1.1 GiB**. Latest disk check: **36,851,470,336 bytes free**, approximately **34.3 GiB**, comfortably above the 10 GiB stop threshold. Global Python packages, production app files and Git state were not changed.

## Next step and time estimate

**Ready to proceed to Stage 3 when you authorize it.** No additional correction is required now. Keep the cautious baseline frozen; its low recall is the performance gap the specialist must improve, not a reason to quietly loosen acceptance.

Stage 3: convert the saved reference candidate to Core ML, verify token/output parity and build the isolated probe app. **Mac only; initially 3–6 active hours**, updated after the first conversion. Phone testing is Stage 4, not Stage 3. Stages 3–6 remain approximately **12–25 active hours**, excluding pauses and unexpected corrections.

This stage ran far faster than its original 2–4-hour allowance: the actual collection run spanned **126.6 seconds**, including its deliberate pause/resume, plus implementation and final audit time. That is not a forecast for conversion or specialist training. Everything is saved and no experiment process remains running.

Implementation references: the selected package versions follow [scikit-learn's logistic-regression API](https://scikit-learn.org/1.5/modules/generated/sklearn.linear_model.LogisticRegression.html) and [Transformers' local model-loading API](https://huggingface.co/docs/transformers/v4.53.0/en/main_classes/model). All result claims above come from this local run, not those documentation sources.
