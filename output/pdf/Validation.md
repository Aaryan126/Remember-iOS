# Remember product review: validation and provenance

Prepared 14 September 2026. The final deliverable is `Remember_Product_Review.pdf` (16 A4 pages). Supporting files are `screenshots/`, `source/`, `verification_summary.txt`, and `quality-check.json`.

## Results

- Simulator app build/test: passed.
- Existing unit suite: 109 Swift Testing test functions in 8 suites passed.
- Existing light and dark appearance tours: 2 passed, zero failures.
- Disposable demo-library seed: 1 passed, zero failures.
- Dedicated demo UI tour: 1 passed, zero failures; 12 screenshots captured.
- Python development proxy syntax: passed.
- PDF: all 16 pages rendered and visually reviewed. Required screen/content checks, page-count check, nonempty-page check and generation-time text bounds passed. No pending-result placeholders remain.
- Read-only `git --no-optional-locks diff --check`: passed. No tracked app source changes remain. Existing untracked diagnostic work was preserved.

No live OpenAI response, physical-device test, model-training experiment or new semantic-quality benchmark was run for this review. Historical evaluation results in the PDF retain their original dates and limitations.

## App checks actually run

From the repository root:

```sh
xcodebuild -project Remember/Remember.xcodeproj -scheme Remember \
  -destination 'platform=iOS Simulator,id=5741ED23-9F8F-4FB6-84E9-FE1E83225998' \
  -configuration Debug -derivedDataPath /tmp/RememberFeedbackReview \
  -clonedSourcePackagesDirPath /tmp/RememberProvenance/SourcePackages \
  -disableAutomaticPackageResolution -skipPackageUpdates CODE_SIGNING_ALLOWED=NO \
  -parallel-testing-enabled NO -only-testing:RememberTests \
  -only-testing:RememberUITests/AppearanceReviewUITests/testLightSurfaces \
  -only-testing:RememberUITests/AppearanceReviewUITests/testDarkSurfaces \
  -resultBundlePath /tmp/remember-feedback-review.xcresult test

python3 -m py_compile server/openai_proxy.py

git --no-optional-locks diff --check
```

The screen fixture files retained in `source/` were temporarily placed in the respective test targets, then removed after successful capture. They are not production app features. The seed only accepts an empty simulator library and refuses physical devices. It inserts nine fictional notes through the app's persistence APIs and arranges seven threads through user-correction APIs. This is a UI demonstration, not evidence of automatic organization quality.

```sh
xcodebuild -project Remember/Remember.xcodeproj -scheme Remember \
  -destination 'platform=iOS Simulator,id=DE1153D8-7109-4821-9C9C-475AAAE5AA42' \
  -configuration Debug -derivedDataPath /tmp/RememberFeedbackReview \
  -clonedSourcePackagesDirPath /tmp/RememberProvenance/SourcePackages \
  -disableAutomaticPackageResolution -skipPackageUpdates CODE_SIGNING_ALLOWED=NO \
  -parallel-testing-enabled NO -only-testing:RememberTests/FeedbackDemoSeedTests \
  -resultBundlePath /tmp/remember-feedback-seed.xcresult test

xcodebuild -project Remember/Remember.xcodeproj -scheme Remember \
  -destination 'platform=iOS Simulator,id=DE1153D8-7109-4821-9C9C-475AAAE5AA42' \
  -configuration Debug -derivedDataPath /tmp/RememberFeedbackReview \
  -clonedSourcePackagesDirPath /tmp/RememberProvenance/SourcePackages \
  -disableAutomaticPackageResolution -skipPackageUpdates CODE_SIGNING_ALLOWED=NO \
  -parallel-testing-enabled NO \
  -only-testing:RememberUITests/FeedbackDemoUITests/testFeedbackScreenTour \
  -resultBundlePath /tmp/remember-feedback-tour.xcresult test-without-building

xcrun xcresulttool export attachments \
  --path /tmp/remember-feedback-tour.xcresult \
  --output-path /tmp/remember-feedback-demo-images
```

The dedicated simulator is named `Remember Feedback Demo`, an iPhone 17 on iOS 26.5. Screenshots are unretouched; PDF placement adds a rounded frame. The simulated status bar was set to 9:41. No personal phone content was copied. Screenshot timestamps and provenance are in `screenshots/manifest.json`.

## PDF generation and QA

The ReportLab source is retained in `source/build_feedback_pdf.py`. It uses the screenshots and verification summary in this folder. The exact generation entrypoint at creation time was `python3 tmp/pdfs/build_feedback_pdf.py`; the retained equivalent is:

```sh
python3 output/pdf/source/build_feedback_pdf.py
pdftoppm -r 110 -png output/pdf/Remember_Product_Review.pdf tmp/pdfs/final
pdfinfo output/pdf/Remember_Product_Review.pdf
```

A Python `pdfplumber` extraction check could not start because that optional package was not installed (`ModuleNotFoundError`). The installed Poppler `pdftotext -bbox output/pdf/Remember_Product_Review.pdf tmp/pdfs/final-text.html` then aborted with exit 134 and a C++ `std::out_of_range: basic_string` error; the cause was not isolated. Rendering with `pdftoppm` and metadata inspection with `pdfinfo` both succeeded. A separate temporary Python environment with `pypdf` successfully extracted all pages and verified required content, page count and absence of pending placeholders. Visual review and the generator's text bounds checks verified layout. These tooling fallbacks did not change the PDF content.

No user action is required to open or share the PDF. Production readiness gaps and proposed product priorities are described in the document, not treated as completed work.
