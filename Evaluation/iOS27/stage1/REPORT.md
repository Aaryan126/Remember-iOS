# Stage 1 checkpoint — stopped on compatibility, not completed

15 September 2026. Stage 2 has **not** started. All work is saved and the runner is
paused; it is safe to close the laptop. No app installation, personal-memory access,
paid API call or generative-model request occurred.

## Implemented and checked

- Isolated native compatibility probe and host runner, using copied production D3
  sources and the verbatim production Apple embedding provider declarations.
- Separate Mac command and signed iPhone app build. The bundle identifier is
  `SimpleStudio.Remember.IOS27Compatibility`, not the personal app.
- Frozen input/source/binary hashes, immutable unit results, source-only fixtures,
  per-unit attempt reservations, bounded processes and disk checks.
- `pause`, `resume`, `status`, `evaluate`, `verify`, and device checkpoint collection.
  Unknown attempts are retained, never blindly rerun. Failed saved checks stop resume.
- Twelve runner tests passed. A real Mac stop/pause/resume preserved the first unit's
  SHA-256 and modification time, then saved the next unit before stopping on its failure.

## Observed environment

macOS 27.0 (26A428), Xcode 27.0 (27A266a). Approximately 59.1 GiB free at checkpoint;
experiment files/cache use approximately 300 MiB, below the 8 GiB cap. The 10 GiB
free-space reserve remains intact.

The Mac reports:

- Apple contextual embedding assets available, identifier
  `5C45D94E-BAB4-4927-94B6-8B5745C46289`, revision 1, dimension 512.
- Sentence embedding revision 1, dimension 512. These match the expected metadata;
  **numeric embedding compatibility has not yet been tested**.
- Foundation Models unavailable with `modelNotReady`; reported context size is zero.
  This means unavailable at the time of the check, not a usable zero-token model.
  Model readiness after the OS upgrade must be verified before generation.

The iPhone remains paired but live discovery reports disconnected. Device detail
retrieval could not establish a connection. Cached iOS 27 information is not a new
device-runtime measurement. The signed probe was built but **not installed or run**.

## First parity result

Fixture `hv19a-i01--hv19a-i02`, using frozen vectors and the CPU-only Core ML path:

| Check | Result |
|---|---:|
| Tokenizer | Exact match |
| Maximum feature difference | 9.024e-10; passes existing 1e-8 tolerance |
| Saved Core ML combined score | 0.04326161838920552 |
| New Mac combined score | 0.043268823303469435 |
| Absolute score difference | **7.204914263918283e-6** |
| Existing score tolerance | **1e-7** |
| Final decision | Unchanged: both below threshold 0.9804276486193665 |
| Overall parity | **Failed numeric tolerance** |

Model loading took 0.1295 s; first and second directional inferences took 0.0292 s
and 0.0175 s. These are one Mac fixture, not latency percentiles, a controlled cold/warm
benchmark, iPhone timings or complete River organization measurements. Process resident
memory was sampled before/after the unit (9,797,632 / 30,130,176 bytes), not at its peak.

The difference is small and did not change this decision. It does **not** demonstrate
quality regression. However, it exceeds the frozen numerical compatibility criterion,
so the runner stopped without relaxing it. Compiler/runtime changes are a hypothesis,
not an established cause. We have not examined all 16 pairs or threshold-near behavior.

## Pending work and next decision

Stage 1 remains incomplete: remaining parity cases, actual embedding-vector comparisons,
phone model availability/execution, generation smoke check and isolated organizer-store
safeguard tests are pending. The current probe implements native compatibility checks;
the separate ledger test integration has not yet been implemented. It must use the
current D3 organizer and an isolated store, not the old graph-policy harness.

Before Stage 2, recommend a separately recorded **compatibility investigation**, preserving
this failed attempt. Collect all 16 numeric comparisons in diagnostic-only mode, compare
neural versus combined-score drift, and determine whether any final decisions change.
Do not relabel these failed checks as passes or adjust thresholds/weights. A revised
cross-runtime tolerance, if warranted, needs an explicit documented decision.

Also reconnect/unlock the phone and verify Apple Intelligence readiness on the device.
The Mac is not a substitute for the phone's model. No settings, assets or entitlements
were changed to force availability.

Estimated next work: 1–2 hours for the bounded parity investigation; after connectivity
and model readiness, approximately 2–4 hours for the remaining Stage 1 work. Stage 2
remains approximately 4–8 hours if compatibility is resolved. These estimates exclude
model download/waiting time and any larger repair discovered by the investigation.

## Reproduction and evidence

Commands actually run from the repository root:

```sh
python3 -B -m unittest discover -s scripts/ios27-evaluation -p 'test_*.py'
python3 -B scripts/ios27-evaluation/run.py prepare
python3 -B scripts/ios27-evaluation/run.py build --platform mac
python3 -B scripts/ios27-evaluation/run.py build --platform phone
python3 -B scripts/ios27-evaluation/run.py run --platform mac --max-units 1
python3 -B scripts/ios27-evaluation/run.py pause
python3 -B scripts/ios27-evaluation/run.py run --platform mac
python3 -B scripts/ios27-evaluation/run.py resume --platform mac --max-units 1
python3 -B scripts/ios27-evaluation/run.py evaluate
python3 -B scripts/ios27-evaluation/run.py verify
python3 -B scripts/ios27-evaluation/run.py pause
python3 -B scripts/ios27-evaluation/run.py status
git --no-optional-locks diff --check
```

The paused run returned the expected exit 75. The resumed parity run returned exit 1
after saving its numeric failure. `verify` and whitespace checks passed. The first Mac
build needed an `await` for model compilation; this probe-only fix was made before
freezing or inference, with the failed build log retained. Final builds passed.

See [checkpoint](checkpoint.json), [manifest](manifest.json),
[resume proof](resume-proof.json), `units/`, `attempts/`, and `build-attempts/`.
Build products are ignored caches, not app resources to publish. No Git state changed.
