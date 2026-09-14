# P2 attempt 02: English coverage restored

The authorized language amendment is implemented in a separate adapter; no frozen attempt-01 source or evidence was overwritten. This is an intermediate P2 checkpoint, not a model-quality result or a stage-completion stop.

| Check | Result |
| --- | --- |
| Training source embeddings | 480/480 available |
| Previously available training embeddings | 478/478 exactly unchanged |
| Previously unavailable training embeddings | 2/2 restored, valid 512-dimensional unit vectors |
| Calibration source embeddings | 240/240 available |
| Training pair features | 4,560/4,560 complete |
| Calibration pair features | 2,280/2,280 complete |
| Validation tests | 88 passed |
| Legacy feasibility tests | 183 passed |
| Organization tests | 22 passed |
| P1 and original P2 verification | Passed |
| Separate-process MPS fixture pause/resume | Passed |

The same explicit-English provider serves both baseline and hybrid. No source filtering, imputation, new model asset download, app change, label change, split change or gate change. Evaluation remains closed until model/threshold selection is frozen. This does not establish multilingual or automatic-language reliability.

Manifest SHA-256: `0ca79ad477e4a3dae1e114a969f6fb5ad86aa326292139c59c6955a82fba75a6`.

Coverage receipt SHA-256: `7fde8084b1d593d01e84ddd3e05f07e92adea67d6b370b32fcf8c4dd2e0bbe87`.

Commands run successfully: unittest discovery in `scripts/matcher-validation`, `scripts/matcher-feasibility`, and `scripts` (pattern `test_organization*.py`); `p1_release.py verify`; `p2.py verify`; `p2_english.py prepare`; `p2_english.py exercise --pause-after-steps 2`; `p2_english.py exercise --resume`.

`p2_english.py run --pause-after-steps 2` subsequently paused successfully on the real `seed-17-0` MiniLM fit, at step 2 / offset 32. The complete recovery file is 267,638,258 bytes, SHA-256 `74c87c3c261e8ed020ad06e84f67f100b8fcf3349f0bc87d65603b5b6667c588`. `p2_english.py verify` passed after exit. The active runner was then restarted with `run --resume`; do not treat this historical pause as a current safe-to-close confirmation.

The baseline calibration selection accepted 167 known pairs: 159 true positives and 8 related-but-separate false positives (95.21% precision, 42.09% macro recall). It accepted 9 additional uncertain-label pairs, reported separately. This is calibration, not held-out evaluation or neural quality evidence.

The real-model resumption receipt `runs/validation-02/resumptions/1789273063811803000.json` confirms full state restored from step 2. The worker subsequently passed step 125, saving verified states at steps 50 and 100. Early compute was approximately 0.20 seconds per effective batch; checkpoint serialization/reload adds substantial overhead. Remaining P2 was revised to roughly 3–4 active hours at this point, subject to sustained throughput and prediction/reporting time.

See [RESUME](../RESUME.md) and live receipts for the latest worker state. Next are the twelve fixed fits, calibration and one held-out evaluation. Stop after P2 for review, without launching P3.
