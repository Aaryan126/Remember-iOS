# Checkpointed matcher feasibility plan

This is an experiment, not integration into Remember. Keep the existing embeddings; test whether a compact English pair matcher adds enough reliable judgment to justify integration. The untrained MiniLM classification head is only a numerical conversion reference, not a useful matcher.

## Execution and stop points

| Stage | Work and saved evidence | Hardware | Initial estimate | Exit decision |
| --- | --- | --- | --- | --- |
| 1. Prepare | 600 fictional sources; separate train/development/test libraries; two independent agent reviews and adjudication; historical baseline snapshot; model/environment versions; hashes and resume notes | Mac | 3–5 h | Freeze only after complete coverage, resolved labels and integrity checks. Stop. |
| 2. Baseline/reference | Extract existing Apple embedding features; build the small logistic classifier; evaluate candidate retrieval; save original MiniLM reference outputs, tokenizer settings and seed | Mac | 2–4 h | Check features and baseline coverage. No test-label-based selection. Stop. |
| 3. Convert | Convert the reference candidate to Core ML; compare tokenizer/numerical outputs; build an isolated probe with fictional inputs | Mac | 3–6 h | Require conversion parity; otherwise recommend a correction before device work. Stop. |
| 4. Initial phone feasibility | Measure storage, process-cold startup, warm shortlist latency, peak process memory, interruptions and thermal conditions; save raw logs/configuration | Mac + connected, unlocked iPhone | 1–3 h | Decide whether this architecture is practical enough to train. Stop. |
| 5. Specialist experiment | Train locally with resumable checkpoints; choose weights/thresholds using development only; freeze the choice; evaluate untouched test labels once; compare with the frozen simple baseline | Mac | 6–12 h | Continue only if the quality signal merits a device candidate. Otherwise recommend no-go or a separately scoped correction. Stop. |
| 6. Trained phone verification | Convert the selected trained candidate; repeat parity and device tests, including threshold-decision consistency; save candidate and final recommendation | Mac + connected, unlocked iPhone | 2–4 h | Go/no-go for a subsequent integration proposal, not automatic integration. Stop. |

Original total: **17–34 active hours**, excluding approval pauses and corrective work. After Stage 1: **14–29 active hours** remain. Progress can be faster or slower; update estimates from measured work rather than treating these as a deadline. A stage can finish earlier than its initial allowance.

## Before and after each stage

1. Read the latest checkpoint and verify frozen hashes, package versions, model bytes and disk space. Stop new heavyweight work below 10 GiB free. Ask before any cleanup; do not delete unrelated files.
2. Use a new immutable attempt directory, with run settings and explicit stage authorization. Never overwrite prior successes or failures. Do not change Git state or the production app.
3. Send progress and revised remaining-time estimates during work. Save resumable training state every 50 optimizer steps and each epoch. Interrupted timing batches restart as distinct attempts, not invented partial timings.
4. At the checkpoint, report what succeeded, what the evidence means, what remains uncertain, whether correction is needed, the next action/hardware/time, and total remaining work.
5. **Stop and wait for the user to continue.** No background training or device collection should keep running across a deliberate checkpoint pause. It is safe to close the laptop at the stopped checkpoint; the phone can be disconnected.

## If a stage disappoints

- **Bad labels, feature gaps or suspiciously easy baseline:** inspect the cause before training. Allow roughly 1–3 hours for initial diagnosis; expanding/re-authoring data requires a new estimate and review. Do not tune against heldout test labels.
- **Conversion fails parity:** try a supported export/operator path or precision choice in a separately recorded attempt. Initial investigation may take 2–6 hours; success is not guaranteed.
- **Phone budget fails:** identify token-length, compute-unit, memory or model-size causes. Report the trade-off before a smaller/quantized candidate; any new candidate repeats parity and quality checks. Initial investigation may take 2–6 hours.
- **Trained matcher does not beat the simple classifier:** report no demonstrated benefit. Keep the simpler option as the reference; do not bundle the neural model merely because it trained. Larger data/model experiments need a new scope and budget.
- **Test-driven changes become necessary:** that test set is consumed. Freeze a new independently reviewed test release before making a fresh unbiased quality claim.

Detailed definitions, selection rules and numerical gates are in [CONTRACT.md](CONTRACT.md). The current stage and safe continuation instructions are in [RESUME.md](RESUME.md). Agent-reviewed synthetic data supports a feasibility decision, not a claim of production reliability or human-validated correctness.
