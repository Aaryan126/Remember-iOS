# Remember organization and provenance benchmark

This benchmark evaluates the production organization service separately from UI navigation and grounded-answer retrieval. Read [CONTRACT.md](CONTRACT.md) before authoring, reviewing, running, or interpreting results. It is agent-reviewed, not human-validated. No thresholds are tuned as part of the baseline.

See the [implementation and baseline report](../../docs/evaluations/2026-09-10-organization-benchmark.md) for executed checks, device coverage, results, and limitations.

The 10–11 September baseline has **144/144 core scenarios completed**, with [final raw results](results/core-complete-2026-09-11.json.gz) and [frozen-label scores](results/core-complete-score-2026-09-11.json). Neither mode meets the English-heldout semantic targets. The controlled-decision, embedding-only media, and public diagnostics also ran. Scale testing recorded one completion, one timeout, and one host-stopped incomplete workload; see the [incident record](scale/EXECUTION-2026-09-11.md). Extended local-metadata media repeats remain unexecuted. No device job is currently active, and no production grouping policy was tuned.

If the laptop or phone must be disconnected, use the [pause/resume instructions](RESUME.md). Completed scenarios do not need to be rerun.

## Suites

- `inputs-reviewed.json` and `labels.json`: 360 fictional memories, 12 independent libraries, 6 development/6 heldout. Labels stay on the host. `inputs.json` retains the initial draft; `amendments.json` records 24 pre-prediction sparse/long replacements following blind audit.
- `reviews/`: two blind source-based annotations, adjudication and adversarial audit. Original author labels are retained separately.
- `freeze.json`: hashes of inputs, labels, review artifacts, contract, and scorer, captured before predictions.
- `public/`: 200 BANKING77 test examples (20 intents × 10), independently sourced and separately scored. This is a subset diagnostic, not an official BANKING77/MTEB score or project-identity benchmark.
- `media/`: 36 generated files replacing three items in each source library, preserving 27 context items. Reference and extracted runs use the same families. Uncaptioned videos have an explicit unsupported-singleton expectation.
- `decisions/`: 12 controlled merge and 12 controlled split opportunities, derived from reviewed labels. See [DECISIONS.md](../../scripts/embedding-evaluation/DECISIONS.md) for the separate isolated runner and opportunity-based scoring.
- `scale/`: 100-, 500-, and 1,000-item synthetic workloads, using development content only. These measure runtime and resource use, not semantic generalization.
- `history-scenarios.json`: 24 integrity cases plus 100 seeded 50-command sequences. Fixture merge/split decisions test bookkeeping, not model semantic quality.
- The earlier 42-item evaluation remains unchanged under the original embedding probe and recorded-vector tests.

## Validate, review, freeze

```sh
python3 -m unittest discover -s scripts -p test_organization_eval.py -v
python3 scripts/organization_eval.py validate --inputs Evaluation/Organization/inputs-reviewed.json --labels Evaluation/Organization/labels.json
python3 scripts/organization_eval.py freeze --inputs Evaluation/Organization/inputs-reviewed.json --labels Evaluation/Organization/labels.json --reviews Evaluation/Organization/reviews/reviewer-a-final.json Evaluation/Organization/reviews/reviewer-b-final.json --evidence Evaluation/Organization/reviews/adjudication.json Evaluation/Organization/reviews/adversarial-audit.json Evaluation/Organization/amendments.json --output Evaluation/Organization/freeze.json
```

Artifacts refuse overwrites. Retain failed and successful releases; corrections require a new manifest. Existing frozen score baselines must never be silently regenerated after predictions are inspected.

The frozen decision contract's derivation example names the retained draft `inputs.json`. For this release, substitute **`inputs-reviewed.json`**; the tool correctly rejects the draft against the final freeze. The contract bytes are retained unchanged for reproducibility. The runnable derivation command is:

```sh
node scripts/embedding-evaluation/derive-decisions.mjs --inputs Evaluation/Organization/inputs-reviewed.json --labels Evaluation/Organization/labels.json --freeze Evaluation/Organization/freeze.json --output <new-decision-release-directory>
```

Public data preparation uses a pinned upstream revision and expected SHA256. Python certificate failures must be addressed with a trusted certificate installation or a normal TLS-verified download supplied through `--source`; never disable TLS verification.

```sh
python3 scripts/prepare_organization_public.py
python3 scripts/prepare_organization_media.py
```

Media generation requires the existing macOS Swift/CoreGraphics toolchain, local Samantha (English), Mónica (Spanish), and Thomas (French) speech voices, and ffmpeg. It never records the microphone or reads Photos. Generated PDF/image documents are deliberately plain diagnostic fixtures; noisy/scanned variants exercise extraction. Video files contain a synthetic test pattern, not a depicted event. Four videos have captions and four have no text evidence. TTS audio does not establish robustness to real accents or conversational speech.

The [separate post-hoc audio diagnostic](media/AUDIO-DIAGNOSTIC.md) measures normalized transcript word error without changing the frozen organization scorer. Nonempty extraction output is not treated as proof of transcription accuracy.

## Isolated device execution

Use an unlocked, paired iPhone with Developer Mode. Reuse the cached GRDB checkout; no Git commands or dependency resolution updates are needed. The helper compiles the current production source in a separate `SimpleStudio.Remember.OrganizationProbe` app without the personal app's App Group. It sets cloud assistance off in its own defaults and never opens the real vault.

```sh
node scripts/embedding-evaluation/prepare-organization.mjs --inputs Evaluation/Organization/inputs-reviewed.json --freeze Evaluation/Organization/freeze.json --grdb /tmp/RememberProvenance/SourcePackages/checkouts/GRDB.swift --split all --mode both
```

The command returns a temporary `configuration.json`. Use its exact path:

```sh
node scripts/embedding-evaluation/run-organization.mjs --config <configuration.json> --device <paired-device-id> --action all --output <new-result.json> --host-timeout 7200
python3 scripts/organization_eval.py score --inputs Evaluation/Organization/inputs-reviewed.json --labels Evaluation/Organization/labels.json --freeze Evaluation/Organization/freeze.json --results <new-result.json> --output <new-score.json>
```

Preparation options include `--libraries`, `--orders`, `--mode embedding|local|both`, `--split development|heldout|all`, `--max-runs`, and `--timeout` (scenario seconds, maximum 600). Production source hashes are checked before build/run. Collection validates the original configuration identity and can retrieve historical results after local code changes. Do not modify production or probe sources during an active baseline.

Five input-only orders are chronological, reverse, interleaved, seed17, and seed29. Interleaved means round-robin traversal of six chronological chunks; it does not consult gold threads. Local chronological scenarios repeat three times. Raw source text receives deterministic metadata in the core suite to isolate organization; media runs use the local capture analyzer and its native extraction path. Local Foundation Models being available is not itself proof that any reasoning call occurred: inspect recorded call counts.

For public data use its own inputs/freeze, `--split all --mode embedding --orders chronological`. For media use its own inputs/freeze and `--orders chronological --media reference` or `--media extracted`. Reference text is a diagnostic control, never a fallback after failed actual extraction.

Scenarios checkpoint atomically. Reusing a configuration resumes after terminal scenarios; an interrupted running scenario restarts from an empty disposable database. Choose a new output filename for each collection. Missing runs, blocked models, extraction failures and timeouts are reported, not silently treated as passing or excluded. The host exit code checks run completion; semantic scores remain a separate result.

## Interpretation

Report pairwise precision/recall, overlap-aware B-cubed, fragmentation and grouped-item fraction, per library/mode/order. Bootstrap intervals resample libraries, not dependent pairs or repetitions. The small number of libraries makes these descriptive intervals, not deployment guarantees. All-singleton precision is undefined. Ambiguous items are enumerated and excluded from primary point-label scores.

Immediate/settled membership snapshots provide retrospective final-label diagnostics only. They are not temporal action ground truth. Event-level checks separately report whether an observed merge is consistent with final context labels. Merge recall and autonomous split-proposal quality are not inferred from final groups; the separate controlled-decision suite supplies those opportunities. Graph edge scoring is distinct from membership and only sees the first 40 display nodes.

Initial English-heldout targets are 99% pairwise precision, 85% pairwise recall, and no prohibited automatic merges. Missing capability/coverage and undefined metrics prevent a blanket pass claim. A poor semantic result is a valid completed baseline, not permission to tune labels or thresholds. Provenance-invariant failures are critical findings.

After opening heldout results, that release is a historical baseline. Future fixes use development evidence; genuinely independent improvement claims require fresh heldout data. No cloud evaluation, real-user validation, broad-language certification, battery certification, hierarchy, or video understanding is implied.

## References

- [B-cubed and overlapping clustering evaluation](https://doi.org/10.1007/s10791-008-9066-8)
- [Correlated Errors in Large Language Models](https://proceedings.mlr.press/v267/kim25e.html)
- [BANKING77 source and license](https://huggingface.co/datasets/PolyAI/banking77)
- [Stateful testing and independent state models](https://hypothesis.readthedocs.io/en/latest/stateful.html)
