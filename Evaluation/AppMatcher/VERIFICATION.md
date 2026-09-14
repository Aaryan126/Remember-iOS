# D3 app integration verification

14 September 2026. **Implemented and installed on the connected iPhone 17.**
This is an engineering integration of frozen P2 seed 29 plus C3 corroboration,
explicitly requested by the user, not a new production qualification result.
No training, threshold fitting, cloud organization requests or personal-vault
benchmarking were performed. Historical evaluation reports are unchanged.

## Results

| Check | Result |
|---|---|
| Original PyTorch → Core ML, 16 pairs / 32 directions | Passed; 16/16 final decisions agree; maximum neural-probability delta 0.00126332 |
| Native Swift tokenizer/features/scorer, same 16 pairs | Passed; exact tokens and decisions; maximum feature delta 2.034e-9; score delta 5.337e-10 |
| New D3 integration tests | 13 passed in final suite |
| Full final unit suite, established iOS 26.5 simulator | **128 passed, 0 failed, 0 skipped**; 250 runs including parameterized cases |
| Signed iPhone build | Passed |
| In-place installation, `SimpleStudio.Remember`, iPhone 17 | Succeeded; no uninstall or data reset |
| Exported asset hashes / frozen input hashes | 6 / 3 verified unchanged |
| Exporter syntax / whitespace diff check | Passed |

The 13 new tests cover corroboration, ambiguous matches, deterministic retrieval,
batch ordering, existing placements/renames, archived threads, unavailable matching
and retry, manual assignment, cancellation, actual bundled model execution, revised
source preservation, unsupported text and concurrent-edit rejection.

The first full run on the new isolated simulator had 123 passes and two failing
legacy tests: `ProjectClusteringTests.groundedTermsRejectSharedStyleAndUnrelatedHandsOnTasks`
and `RecordedProjectEmbeddingTests.realDeviceVectorsStayTopicPureAcrossArrivalOrders`.
This reproduces the language-asset-dependent issue already documented in
`docs/threads-interface.md`. Both passed on the established simulator; neither the
old policy nor its assertions were changed. Initial result:
`/tmp/RememberD3Integration/Logs/Test/Test-Remember-2026.09.14_18-35-42-+0800.xcresult`.

Final-source result:
`/tmp/RememberD3Integration/Logs/Test/Test-Remember-2026.09.14_18-40-21-+0800.xcresult`.
These local Xcode artifacts are not necessary app resources and are not published.

## Commands actually run

Export used the existing matcher-feasibility virtual environment's Python:

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" \
  scripts/app-matcher/export_d3.py

swiftc -parse-as-library Remember/Remember/D3Tokenizer.swift \
  Remember/Remember/D3Features.swift Remember/Remember/D3PairMatcher.swift \
  Remember/Remember/D3OrganizationPolicy.swift scripts/app-matcher/D3ParityProbe.swift \
  -o /tmp/RememberD3ParityProbe
/tmp/RememberD3ParityProbe Remember/Remember/MatcherAssets Evaluation/AppMatcher/parity-inputs.json

DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild \
  -project Remember/Remember.xcodeproj -scheme Remember -configuration Debug \
  -destination 'platform=iOS Simulator,id=5741ED23-9F8F-4FB6-84E9-FE1E83225998' \
  -derivedDataPath /tmp/RememberD3Integration \
  -clonedSourcePackagesDirPath /tmp/RememberOpenAIReset/SourcePackages \
  -disableAutomaticPackageResolution CODE_SIGNING_ALLOWED=NO \
  -parallel-testing-enabled NO -only-testing:RememberTests test -quiet

git --no-optional-locks diff --check
```

The signed build used the same project/scheme, `Debug`, the connected physical iOS
destination, `/tmp/RememberD3Phone` derived data, the same package cache,
`-disableAutomaticPackageResolution -skipPackageUpdates build -quiet`.
Installation used `xcrun devicectl device install app` with that device and
`/tmp/RememberD3Phone/Build/Products/Debug-iphoneos/Remember.app`.

## Storage and remaining checks

The exported model package is 66,878,102 bytes. `du -sk` measured the signed debug
app bundle at 92,872 KiB (~90.7 MiB), including a 65,336 KiB compiled model. This is
Mac-side allocated bundle storage, **not** App Store download size, the iPhone's
total Documents & Data, or peak inference memory. Approximately 14 GiB remained
free on the Mac at final verification; no caches or user files were deleted.

Actual model execution was verified on Mac and simulator. Installation is not an
end-to-end performance test: phone cold/warm grouping latency, large-library behavior,
thermal load and peak memory for this integrated build remain open. The user's
existing phone captures were not used as evaluation examples or uploaded. A small
fictional-library phone performance check is the recommended next validation step.

## Source identity

Core integration SHA-256 values at final build:

| File under `Remember/` | SHA-256 |
|---|---|
| `Remember/D3Features.swift` | `c8411b142c75114c7f3ac9a1304fd6f5a3da996f1810fe48afcff3a791044a36` |
| `Remember/D3OrganizationPolicy.swift` | `906170c3d6a2f00d4821a7f7e474111f402153f68814406bb9825a08fe334608` |
| `Remember/D3PairMatcher.swift` | `f081f369f021d3e2ead38191a5e4b2612d75fd482715bb9531efa346f0b1af57` |
| `Remember/D3ProjectOrganizer.swift` | `1b2e85c815399b1cd04cbfbd5e8adaf1a25da9aed064388f5613c96e99369985` |
| `Remember/D3Tokenizer.swift` | `f0fb9064f307b580804076e42feaf48a95f8a23e90b7d7fdf7457048a1c6999f` |
| `Remember/ProjectViewModel.swift` | `ff7b6d3d22d81c35d6248ef17e943e31d34ccf5e644ee8aa9079fb0ffd1854e5` |
| `RememberTests/D3OrganizationTests.swift` | `12a67629e53192d3f2e044a6d9974309d0e3e1a80cef228705162033321db00c` |

`conversion.json` binds the bundled model, vocabulary and feature parameters;
`inputs.json` binds the frozen source artifacts. Existing unrelated UI/documentation
work was preserved. No staging, commit, branch change or other Git mutation was performed.
