import XCTest

final class SourceEvidenceUITests: XCTestCase {
    override func setUpWithError() throws { continueAfterFailure = false }

    @MainActor private func app(_ arguments: [String] = []) throws -> XCUIApplication {
        guard Bundle.main.bundleIdentifier?.contains("SourceBrowserUI") == true else {
            throw XCTSkip("Only run against the separately bundled fictional source-browser diagnostic")
        }
        let app = XCUIApplication()
        app.launchArguments = arguments
        app.launch()
        return app
    }

    @MainActor private func search(_ text: String, in app: XCUIApplication) {
        let field = app.searchFields["Search saved text"]
        XCTAssertTrue(field.waitForExistence(timeout: 10))
        field.tap(); field.typeText(text + "\n")
    }

    @MainActor private func result(_ phrase: String, in app: XCUIApplication) -> XCUIElement {
        app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@ AND label CONTAINS %@", "evidence-result-", phrase)).firstMatch
    }

    @MainActor private func capture(_ name: String, _ app: XCUIApplication) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name; attachment.lifetime = .keepAlways; add(attachment)
    }

    @MainActor func testCurrentHistoryExactVersionAndDirectBack() throws {
        let app = try app()
        search("receipt", in: app)
        XCTAssertTrue(result("NOVA-42", in: app).waitForExistence(timeout: 10))
        XCTAssertFalse(result("ORBIT-27", in: app).exists)
        capture("Current sources light", app)
        app.segmentedControls["evidence-scope"].buttons["Include history"].tap()
        let old = result("ORBIT-27", in: app)
        XCTAssertTrue(old.waitForExistence(timeout: 10))
        old.tap()
        let quote = app.staticTexts["evidence-exact-quote"]
        XCTAssertTrue(quote.waitForExistence(timeout: 10))
        XCTAssertTrue(quote.label.contains("ORBIT-27"))
        XCTAssertFalse(quote.label.contains("NOVA-42"))
        XCTAssertTrue(app.staticTexts["evidence-version-status"].label.contains("Earlier revision"))
        capture("Exact older revision", app)
        app.navigationBars.buttons["BackButton"].tap()
        XCTAssertTrue(app.searchFields["Search saved text"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.searchFields["Search saved text"].value as? String, "receipt")
        XCTAssertTrue(app.segmentedControls["evidence-scope"].buttons["Include history"].isSelected)
        XCTAssertTrue(result("ORBIT-27", in: app).waitForExistence(timeout: 5))
        XCTAssertFalse(app.navigationBars["Imported history"].exists)
        let archived = result("ARCHIVE-8", in: app)
        for _ in 0..<4 where !archived.isHittable { app.swipeUp() }
        XCTAssertTrue(archived.isHittable); archived.tap()
        XCTAssertTrue(quote.waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["evidence-version-status"].label.contains("archived"))
        let unavailable = app.staticTexts.containing(NSPredicate(format: "label CONTAINS %@", "original file is unavailable")).firstMatch
        for _ in 0..<4 where !unavailable.isHittable { app.swipeUp() }
        XCTAssertTrue(unavailable.exists)
        XCTAssertFalse(app.buttons["evidence-open-original"].exists)
        capture("Archived source without original", app)
    }

    @MainActor func testDarkLargeTextAndHonestEmptyState() throws {
        let app = try app(["--evidence-dark", "-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityXXXL"])
        search("unicorn", in: app)
        let empty = app.staticTexts["No matching saved text"]
        XCTAssertTrue(empty.waitForExistence(timeout: 10))
        capture("Dark large-text scope", app)
        // ContentUnavailableView's accessibility frame includes its icon, so
        // isHittable alone can be true before the title is actually onscreen.
        app.swipeUp()
        for _ in 0..<5 where !empty.isHittable { app.swipeUp() }
        XCTAssertTrue(empty.isHittable)
        capture("Dark large-text no match", app)
    }

    @MainActor func testThreadsPreservesFinderWithoutDuplicateEvidenceSearch() throws {
        let app = try app(["--evidence-entry"])
        XCTAssertTrue(app.searchFields["Find a thread"].waitForExistence(timeout: 10))
        let more = app.navigationBars.buttons.matching(NSPredicate(format: "label CONTAINS[c] %@", "More")).firstMatch
        XCTAssertTrue(more.waitForExistence(timeout: 5)); more.tap()
        capture("Threads overflow menu", app)
        XCTAssertFalse(app.buttons["Search saved evidence"].exists)
        XCTAssertTrue(app.buttons["Activity & decisions"].exists)
        XCTAssertTrue(app.buttons["Archive"].exists)
    }
}
