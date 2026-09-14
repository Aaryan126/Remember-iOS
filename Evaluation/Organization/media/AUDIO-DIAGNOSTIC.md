# Post-hoc audio transcript diagnostic — 2026-09-10

All eight audio extractions returned completed, nonempty text. That completion status does not establish transcript accuracy. The separate [diagnostic artifact](audio-diagnostic-2026-09-10.json) records 66 word edits across 265 reference words: **24.91% corpus word error rate (WER)** and **23.47% mean item WER**.

| Audio item | Reference words | Word edits | WER |
| --- | ---: | ---: | ---: |
| l01-i15 | 31 | 4 | 12.90% |
| l02-i15 | 33 | 3 | 9.09% |
| l03-i15 | 29 | 1 | 3.45% |
| l04-i15 | 31 | 2 | 6.45% |
| l09-i08 | 34 | 2 | 5.88% |
| l10-i08 | 35 | 0 | 0.00% |
| l11-i08 | 36 | 32 | 88.89% |
| l12-i08 | 36 | 22 | 61.11% |

This analysis is **post-hoc, not preregistered**: it was added after poor Spanish/French transcripts were noticed. Its scorer and normalization semantics were frozen in [a separate manifest](audio-diagnostic-freeze-2026-09-10.json) before computing these numbers. This does not retroactively make the diagnostic preregistered, modify the organization benchmark, or establish a quality threshold.

Normalization casefolds text and extracts Unicode alphanumeric word runs (`[^\W_]+`). Punctuation, apostrophes, hyphens, and underscores separate tokens. Accents and numeric forms are retained; there is no stemming, number expansion, or language-specific substitution. Standard unit-cost Levenshtein distance counts word substitutions, deletions, and insertions. WER is edits divided by reference words and may exceed 100%. Consequently, equivalent number spellings can count as errors. Corpus WER pools edits and reference words; mean item WER weights each audio item equally.

Every frozen audio item remains in coverage. A missing or failed run/extraction contributes an empty hypothesis and one deletion per reference word. Completed empty transcripts are likewise scored. Reference text is used only as the comparison script, never as fallback extraction. Images, PDFs, and videos are outside this diagnostic.

The actual production transcriber chooses `Locale.current`, not each file's language (`Remember/Remember/OnDeviceSpeechTranscriber.swift`). The large l11/l12 error rates are consistent with a language mismatch, but this run does not isolate causality or establish multilingual speech accuracy. Synthetic voices, short scripts, eight examples, and this normalization limit generalization. WER also does not measure semantic adequacy or organization quality.

The diagnostic binds the exact bytes of the portable [extracted-result archive](../results/media-extracted-2026-09-10.json.gz), the media input file and corpus freeze, and the diagnostic scorer. To reproduce into a new output path:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts -p test_organization_audio_diagnostic.py -v
python3 scripts/organization_audio_diagnostic.py score \
  --inputs Evaluation/Organization/media/inputs.json \
  --corpus-freeze Evaluation/Organization/media/freeze.json \
  --results Evaluation/Organization/results/media-extracted-2026-09-10.json.gz \
  --diagnostic-freeze Evaluation/Organization/media/audio-diagnostic-freeze-2026-09-10.json \
  --output /tmp/new-audio-diagnostic.json
```

Outputs refuse overwrites. A new diagnostic version requires a separate `freeze` invocation and new artifact paths; preserve this release.
