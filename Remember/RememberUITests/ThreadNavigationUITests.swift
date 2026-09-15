import XCTest

final class ThreadNavigationUITests: XCTestCase {
    override func setUpWithError() throws { continueAfterFailure = false }

    /// Reads an existing library without changing content, membership or settings.
    @MainActor func testExistingThreadsFinderAndHistoryReadOnly() throws {
        let app = XCUIApplication()
        app.launch()
        app.tabBars.buttons["Threads"].tap()
        XCTAssertFalse(app.segmentedControls["Project view"].exists)
        XCTAssertTrue(app.searchFields["Find a thread"].waitForExistence(timeout: 10))
        XCTAssertFalse(app.staticTexts["map-centered-title"].exists)
        capture("Threads map", app)
        let nodes = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "graph-node-"))
        XCTAssertTrue(nodes.firstMatch.waitForExistence(timeout: 10))
        let selectedTitle = nodes.firstMatch.label.replacingOccurrences(of: #", \d+ memor(?:y|ies)$"#, with: "", options: .regularExpression)
        app.searchFields["Find a thread"].tap()
        let rows = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "project-topic-"))
        XCTAssertFalse(rows.firstMatch.exists, "An empty search must keep the map visible.")
        XCTAssertTrue(app.descendants(matching: .any)["memory-map-canvas"].firstMatch.exists)
        XCTAssertFalse(app.navigationBars.buttons["BackButton"].exists, "Suggestions must appear on the Threads root.")
        capture("Empty thread search keeps map visible", app)
        let field = app.searchFields["Find a thread"]
        field.tap(); field.typeText("zz-no-matching-thread-902481")
        XCTAssertTrue(app.staticTexts["No matching threads"].waitForExistence(timeout: 5))
        field.typeText("\n")
        tapWhenUncovered(app.navigationBars.firstMatch.buttons["Close"])
        XCTAssertTrue(app.buttons["Recenter map"].waitForExistence(timeout: 5))
        field.tap()
        XCTAssertFalse(rows.firstMatch.exists)
        field.tap(); field.typeText("   ")
        XCTAssertFalse(rows.firstMatch.exists, "Whitespace is not a search.")
        field.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: 3))
        field.typeText(selectedTitle)
        XCTAssertTrue(app.staticTexts["Matching threads"].waitForExistence(timeout: 5))
        XCTAssertEqual(rows.firstMatch.label, selectedTitle)
        capture("Live thread matches", app)
        field.typeText("\n")
        rows.firstMatch.tap()
        XCTAssertTrue(app.descendants(matching: .any)["thread-history"].firstMatch.waitForExistence(timeout: 5))
        capture("Content first history", app)
        XCTAssertFalse(app.buttons["thread-activity-link"].exists, "Activity belongs in the menu, not a permanent card.")
        XCTAssertFalse(app.switches["View past state"].exists)
        XCTAssertFalse(app.sliders["History date"].exists)
        tapWhenUncovered(app.buttons["Thread options"])
        app.buttons["View past state"].tap()
        let historyDate = app.sliders["History date"]
        XCTAssertTrue(historyDate.waitForExistence(timeout: 5))
        historyDate.adjust(toNormalizedSliderPosition: 0)
        capture("Past state date controls", app)
        tapWhenUncovered(app.buttons["Thread options"])
        XCTAssertFalse(app.buttons["Rename thread"].exists)
        XCTAssertFalse(app.buttons["Archive thread…"].exists)
        app.buttons["Back to present"].tap()
        XCTAssertTrue(historyDate.waitForNonExistence(timeout: 5))
        tapWhenUncovered(app.buttons["Thread options"])
        app.buttons["thread-activity-link"].tap()
        XCTAssertTrue(app.navigationBars["Activity & decisions"].waitForExistence(timeout: 5))
        capture("Activity and decisions", app)
        tapWhenUncovered(app.navigationBars.firstMatch.buttons.element(boundBy: 0))
        tapWhenUncovered(app.navigationBars.firstMatch.buttons.element(boundBy: 0))
        if app.navigationBars.firstMatch.buttons["Close"].exists {
            tapWhenUncovered(app.navigationBars.firstMatch.buttons["Close"])
        }
        XCTAssertTrue(app.searchFields["Find a thread"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["Recenter map"].waitForExistence(timeout: 5))
        app.tabBars.buttons["Memories"].tap()
    }

    @MainActor func testSearchHistoryAndRenameUndo() throws {
        #if !targetEnvironment(simulator)
        throw XCTSkip("Creates a fictional note; simulator only")
        #else
        let app = XCUIApplication()
        app.launchArguments = ["-remember.project.cloudAssistance", "NO", "-remember.project.homeView", "Timeline"]
        app.launch()
        let title = "ZZZ Studio story \(UUID().uuidString.prefix(6))"
        app.buttons["Add a memory"].tap(); app.buttons["New Note"].tap()
        app.textFields["Title"].tap(); app.textFields["Title"].typeText(title)
        app.textViews.firstMatch.tap(); app.textViews.firstMatch.typeText("Keep the workbench beside the window.")
        app.buttons["Save"].tap()
        XCTAssertTrue(app.buttons["Add a memory"].waitForExistence(timeout: 10))
        app.tabBars.buttons["Threads"].tap()
        XCTAssertTrue(app.searchFields["Find a thread"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.segmentedControls["Project view"].exists)
        app.searchFields["Find a thread"].tap()
        let field = app.searchFields["Find a thread"]
        field.tap(); field.typeText(title + "\n")
        let row = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@ AND label == %@", "project-topic-", title)).firstMatch
        XCTAssertTrue(row.waitForExistence(timeout: 10)); row.tap()
        XCTAssertTrue(app.navigationBars[title].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["thread-review-suggestions"].exists, "A new standalone note has no suggestion to review.")
        let source = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "project-source-")).firstMatch
        XCTAssertTrue(source.waitForExistence(timeout: 5))
        XCTAssertEqual(app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "thread-event-")).count, 0)
        XCTAssertFalse(app.staticTexts["River"].exists)
        tapWhenUncovered(app.buttons["Thread options"]); app.buttons["Rename thread"].tap()
        let input = app.alerts.textFields["Thread name"]
        input.coordinate(withNormalizedOffset: CGVector(dx: 0.98, dy: 0.5)).tap()
        input.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: title.count))
        let renamed = "Renamed studio \(UUID().uuidString.prefix(6))"
        input.typeText(renamed); app.alerts.buttons["Save"].tap()
        XCTAssertTrue(app.navigationBars[renamed].waitForExistence(timeout: 5))
        tapWhenUncovered(app.buttons["Thread options"])
        app.buttons["thread-activity-link"].tap()
        let change = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@ AND label CONTAINS %@", "thread-event-", "Named")).firstMatch
        for _ in 0..<6 where !change.isHittable { app.swipeUp() }
        XCTAssertTrue(change.isHittable); change.tap()
        XCTAssertTrue(app.buttons["Undo this change"].waitForExistence(timeout: 5))
        app.buttons["Undo this change"].tap()
        tapWhenUncovered(app.navigationBars.firstMatch.buttons.element(boundBy: 0))
        tapWhenUncovered(app.navigationBars.firstMatch.buttons.element(boundBy: 0))
        XCTAssertTrue(app.navigationBars[title].waitForExistence(timeout: 5))
        capture("Story after reversible correction", app)
        #endif
    }

    @MainActor private func tapWhenUncovered(_ element: XCUIElement) {
        let banner = XCUIApplication(bundleIdentifier: "com.apple.springboard")
            .descendants(matching: .any)["NotificationShortLookView"].firstMatch
        if banner.exists {
            XCTAssertTrue(banner.waitForNonExistence(timeout: 20), "Wait for the notification to stop covering navigation.")
        }
        element.tap()
    }

    @MainActor private func capture(_ name: String, _ app: XCUIApplication) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name; attachment.lifetime = .keepAlways; add(attachment)
    }
}
