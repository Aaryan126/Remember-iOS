# P2 final result — English-only attempt 02

All twelve fits completed: three out-of-fold fits and one final fit for each of seeds 17, 29 and 41. **The hybrid failed the prospective all-seeds gate and is not qualified for production.** Do not select the one passing seed after seeing evaluation results.

| Candidate | Precision | Macro recall | Correct / incorrect accepted known pairs | Per-seed gate |
|---|---:|---:|---:|---|
| Refitted simple baseline | 95.94% | 43.84% | 189 / 8 | Control |
| D3 hybrid, seed 17 | 94.59% | 65.15% | 280 / 16 | Fail: precision |
| D3 hybrid, seed 29 | 95.79% | 58.39% | 250 / 11 | Pass |
| D3 hybrid, seed 41 | 94.62% | 61.64% | 264 / 15 | Fail: precision |

Precision is the fraction of accepted known-label pairs that really belong together. Macro recall averages recovery of same-thread pairs across libraries. Accepted uncertain pairs are excluded from those precision counts: baseline 7; hybrids 6, 5 and 4 respectively. The required precision was 95%; all seeds cleared the recall-gain check, but two failed precision.

The simple baseline is a fitted feature classifier, not raw embedding similarity. D3 combines the existing features with a trained MiniLM pair score; it is not the app's Foundation Models local reasoner.

The benchmark has 960 fictional, agent-reviewed text sources in 48 libraries and 9,120 within-library pairs. Family-separated splits contain 24 training, 12 calibration and 12 evaluation libraries. Evaluation used 240 sources and 2,280 pairs, including 1,875 known-label pairs and 442 same-thread pairs. Thresholds were selected using calibration, not evaluation. The older final test was not opened. This does not establish full-media or production grouping quality, and production ledger replay was not run.

English was explicitly selected for this English benchmark after automatic language detection made two training sources unavailable. This was an isolated experimental amendment, not a production language-routing fix. The old attempt and all labels remain unchanged.

## Interpretation and next step

The hybrid finds substantially more matches, but related-yet-separate material is still a major source of false attachments. More training is not automatically the answer. First clarify the intended continuing-project River boundary and diagnose decisions in chronological context. New diagnostic labels must not rewrite this failed qualification result.

The [portable checkpoint snapshot](../CheckpointSnapshot/2026-09-13.json) records exact counts and source hashes. Original detailed uncertainty, thresholds and slice results remain in local `runs/validation-02/report.json`; completion receipt SHA-256:

`1fc484bd5f2c6f787713ffa010a874aecf9eec1bed4640cae3951119edf2b830`

See [restore requirements](../CheckpointSnapshot/README.md) and [the separately gated plan](../CheckpointSnapshot/NEXT_PLAN.md).
