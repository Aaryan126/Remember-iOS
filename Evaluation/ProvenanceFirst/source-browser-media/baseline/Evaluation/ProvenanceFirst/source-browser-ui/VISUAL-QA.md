# Source browser visual review

## Simulator — reviewed, 19 September 2026

Result: `runs/source-browser-ui/1789830006882766000.xcresult` (all three UI cases passed).
All seven PNG attachments in `runs/source-browser-ui/ui-review-1789830006882766000/`
were opened and inspected, not inferred from text assertions.

- Light current results: readable passage, Current scope, revision/date and explicit
  source-only disclaimer; no generated summary presented as evidence.
- Earlier revision: ORBIT-27 remains visible with “Earlier revision—not the current
  version”; saved-original action and extraction caveats are distinct from the quote.
- Archived source: ARCHIVE-8 remains readable with archive context and an explicit
  unavailable-original message. No misleading file-open action is offered.
- Dark accessibility XXXL: actual black/dark surfaces, scaled text, readable wrapped
  scope explanation and reachable no-match title after scrolling. The native search
  field shows only part of its query at this extreme size; it scrolls horizontally.
  Long explanatory text requires vertical scrolling. This is not a claim that every
  accessibility size, VoiceOver flow, device or contrast setting was audited.
- Native overflow menu: saved-evidence action appears alongside Activity & decisions
  and Archive. The fixture deliberately does not initialize the organizer, so the
  underlying Threads loading state is expected, not a test of map rendering.
- Entry from Threads: the same current-source results appear. XCTest separately
  confirms closing active search, then using Back returns to the thread finder.

Earlier dark-labelled captures used a launch-default override that did not actually
enable dark appearance. They are retained but are **not** evidence of dark-mode QA.
The diagnostic launcher now uses an explicit fixture-only preferred color scheme.
Earlier failed/interrupted result bundles are not counted as full UI-suite passes.

## Physical phone — reviewed, 19 September 2026

Physical iPhone 17, iOS 27.0 build 24A437. Run
`runs/source-browser-ui/1789830517891741000.xcresult`: all three UI cases passed,
zero failures/skips. All seven PNGs in
`runs/source-browser-ui/phone-review-1789830517891741000/` were opened and inspected.
The exported manifest maps each image to its test and physical device.

- Current light results show NOVA-42, revision 2, Current selected, and the explicit
  source-only caveat. The same result is visible after entering from Threads.
- Saved earlier revision shows ORBIT-27, revision 1, and the earlier-version warning;
  original-file action and recognition/page/timestamp caveats are separate.
- Archived missing-original detail keeps ARCHIVE-8 readable, states the memory is
  archived and the file unavailable, and does not offer a broken open action.
- Dark accessibility XXXL is actually dark, with wrapped scope text and a visible
  no-match title after scrolling. The system search chrome is very large and its
  query is only partially visible. Long explanations span multiple screenfuls.
  This is functional coverage, not an accessibility-polish sign-off. A future
  usability pass should assess the extreme-size layout and VoiceOver.
- The native Threads overflow contains Search saved evidence, Activity & decisions
  and Archive. Its deliberately unobserved fixture model still shows a loading
  background; this test does not validate map rendering or real-vault loading.

The original-action button and current-River context destination were not opened by
these tests. Photo, audio and video playback remain outside this checkpoint's UI
coverage. The first phone attempt timed out in automation initialization, then the
unchanged retry passed; the failed attempt is preserved, not silently discarded.
