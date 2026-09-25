import XCTest

final class SourceEvidenceMediaUITests: XCTestCase {
    override func setUpWithError() throws { continueAfterFailure = false }

    @MainActor private func launch(_ args: [String] = []) throws -> XCUIApplication {
        guard Bundle.main.bundleIdentifier?.contains("SourceBrowserUI") == true else {
            throw XCTSkip("Fictional isolated app only")
        }
        let app = XCUIApplication()
        app.launchArguments = args
        app.launch()
        XCTAssertTrue(app.searchFields["Search saved text"].waitForExistence(timeout: 15))
        return app
    }

    @MainActor private func open(_ word: String, in app: XCUIApplication) {
        let field = app.searchFields["Search saved text"]
        field.tap(); field.typeText(word + "\n")
        let result = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@ AND label CONTAINS %@",
            "evidence-result-", word)).firstMatch
        XCTAssertTrue(result.waitForExistence(timeout: 10)); result.tap()
        XCTAssertTrue(app.staticTexts["evidence-exact-quote"].waitForExistence(timeout: 5))
    }

    @MainActor private func reach(_ element: XCUIElement, in app: XCUIApplication) {
        for _ in 0..<8 where !element.isHittable { app.swipeUp() }
        XCTAssertTrue(element.isHittable)
    }

    @MainActor private func capture(_ name: String, _ app: XCUIApplication) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name; attachment.lifetime = .keepAlways; add(attachment)
    }

    @MainActor private func dismissPreview(_ name: String, in app: XCUIApplication, image: Bool = false) {
        let preview = app.otherElements["QLPreviewControllerView"]
        XCTAssertTrue(preview.waitForExistence(timeout: 10))
        if image {
            // The presentation shell appears before the remote image canvas. A
            // tap during that handover can land on the image and hide its chrome.
            XCTAssertTrue(app.otherElements["Image canvas"].waitForExistence(timeout: 15), app.debugDescription)
        }
        // iOS 27 exposes the native close action, not the older “Done” label.
        // Image previews may hide their controls until the content is tapped.
        let close = app.buttons["QLOverlayDoneButtonAccessibilityIdentifier"]
        if !close.waitForExistence(timeout: 3) { preview.tap() }
        XCTAssertTrue(close.waitForExistence(timeout: 10), app.debugDescription)
        capture(name, app)
        close.tap()
        // Some simulator runtimes retain Quick Look's outgoing accessibility view.
        // Require its controls to disappear and the real source's Back control to
        // become usable; the caller then exercises navigation and query retention.
        let closed = XCTNSPredicateExpectation(predicate: NSPredicate(format: "exists == false"), object: close)
        let returned = XCTNSPredicateExpectation(predicate: NSPredicate(format: "isHittable == true"),
            object: app.navigationBars["Saved source"].buttons["BackButton"])
        let result = XCTWaiter.wait(for: [closed, returned], timeout: 5)
        capture(name + " after close", app)
        XCTAssertEqual(result, .completed, app.debugDescription)
    }

    @MainActor func testImageOriginalAndQuickLookReturn() throws {
        let app = try launch()
        open("photo", in: app)
        let original = app.buttons["evidence-open-original"]
        reach(original, in: app)
        capture("Inline fictional image", app)
        original.tap()
        dismissPreview("Image Quick Look", in: app, image: true)
        XCTAssertTrue(app.navigationBars["Saved source"].waitForExistence(timeout: 5))
        app.navigationBars.buttons["BackButton"].tap()
        XCTAssertEqual(app.searchFields["Search saved text"].value as? String, "photo")
    }

    @MainActor func testTextOriginalAndCurrentRiverRoundTrip() throws {
        let app = try launch()
        open("document", in: app)
        let original = app.buttons["evidence-open-original"]
        reach(original, in: app); original.tap()
        dismissPreview("Text Quick Look", in: app)
        let thread = app.buttons["evidence-thread-link"]
        reach(thread, in: app); capture("Explicit current River context", app); thread.tap()
        XCTAssertTrue(app.buttons["Thread options"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["thread-target-entry"].exists)
        capture("Current River from saved evidence", app)
        app.navigationBars.buttons["BackButton"].tap()
        XCTAssertTrue(app.navigationBars["Saved source"].waitForExistence(timeout: 5))
        app.navigationBars.buttons["BackButton"].tap()
        XCTAssertEqual(app.searchFields["Search saved text"].value as? String, "document")
        XCTAssertFalse(app.navigationBars["Imported history"].exists)
    }

    @MainActor func testInlineAudioDoesNotOpenQuickLookAndStopsOnBackground() throws {
        let app = try launch()
        open("audio", in: app)
        let play = app.buttons["Play voice memory"]
        reach(play, in: app); play.tap()
        XCTAssertTrue(app.buttons["Stop voice memory"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Playing locally"].exists)
        XCTAssertFalse(app.otherElements["QLPreviewControllerView"].exists)
        capture("Inline silent audio playback", app)
        XCUIDevice.shared.press(.home); app.activate()
        XCTAssertTrue(play.waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["Stop voice memory"].exists)
        play.tap()
        XCTAssertTrue(app.buttons["Stop voice memory"].waitForExistence(timeout: 5))
        app.navigationBars.buttons["BackButton"].tap()
        XCTAssertEqual(app.searchFields["Search saved text"].value as? String, "audio")
    }

    @MainActor func testInlineVideoAndLeavingDetail() throws {
        let app = try launch()
        open("moving", in: app)
        let play = app.buttons["Play video"]
        reach(play, in: app); play.tap()
        let player = app.descendants(matching: .any)["Saved video player"].firstMatch
        XCTAssertTrue(player.waitForExistence(timeout: 10))
        XCTAssertFalse(app.otherElements["QLPreviewControllerView"].exists)
        capture("Inline silent video player", app)
        app.navigationBars.buttons["BackButton"].tap()
        XCTAssertEqual(app.searchFields["Search saved text"].value as? String, "moving")
    }

    @MainActor func testBriefVoicePlaybackFinishesAndCanReplay() throws {
        let app = try launch()
        open("brief", in: app)
        let play = app.buttons["Play voice memory"]
        reach(play, in: app); play.tap()
        XCTAssertTrue(app.staticTexts["Finished"].waitForExistence(timeout: 10))
        XCTAssertTrue(play.exists)
        XCTAssertFalse(app.buttons["Stop voice memory"].exists)
        capture("Completed brief voice recording", app)
        play.tap()
        XCTAssertTrue(app.staticTexts["Finished"].waitForExistence(timeout: 10))
        XCTAssertFalse(app.otherElements["QLPreviewControllerView"].exists)
        app.navigationBars.buttons["BackButton"].tap()
        XCTAssertEqual(app.searchFields["Search saved text"].value as? String, "brief")
    }

    @MainActor func testCorruptVideoRetainsEvidenceAndOffersRetry() throws {
        let app = try launch()
        open("corrupt", in: app)
        let play = app.buttons["Play video"]
        reach(play, in: app); play.tap()
        XCTAssertTrue(app.buttons["Retry video"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.staticTexts["Video unavailable. Try again or open the saved original in details."].exists)
        XCTAssertTrue(app.staticTexts["evidence-exact-quote"].label.contains("retained evidence"))
        capture("Corrupt video honest failure", app)
    }

    @MainActor func testAccessibleScopeAndExpandableLimitations() throws {
        let app = try launch(["--evidence-dark", "-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityXXXL"])
        let field = app.searchFields["Search saved text"]
        field.tap(); field.typeText("unicorn\n")
        let scope = app.buttons.matching(NSPredicate(format: "identifier == %@", "evidence-scope")).firstMatch
        XCTAssertTrue(scope.waitForExistence(timeout: 5)); scope.tap()
        app.buttons["Include history"].tap()
        capture("Large text scope selection", app)
        let limitations = app.buttons["Search limitations"]
        reach(limitations, in: app); limitations.tap()
        capture("Large text expanded limitations", app)
        limitations.tap()
        let empty = app.staticTexts["No matching saved text"]
        reach(empty, in: app); app.swipeUp()
        capture("Large text compact empty state", app)
        XCTAssertTrue(empty.exists)
    }
}
