import XCTest

/// Navigation-only main-app check. No seeding, personal-result opening or editing.
final class MainAppSmokeTests: XCTestCase {
    @MainActor func testUnifiedSearchInNormalApp() throws {
        continueAfterFailure = false
        XCTAssertEqual(Bundle(for: Self.self).bundleIdentifier, "SimpleStudio.RememberUITests")
        let app = XCUIApplication()
        app.launch()
        XCTAssertTrue(app.tabBars.buttons["Memories"].waitForExistence(timeout: 30))
        app.tabBars.buttons["Memories"].tap()
        let search = app.searchFields["Search your memories"]
        XCTAssertTrue(search.waitForExistence(timeout: 15))
        search.tap()
        search.typeText("unifieddeploymentnomatch83917\n")
        let history = app.switches["search-include-history"]
        let sourceOnly = app.switches["search-source-only"]
        XCTAssertTrue(history.waitForExistence(timeout: 15))
        XCTAssertTrue(sourceOnly.exists)
        sourceOnly.tap()
        XCTAssertTrue(app.staticTexts["search-no-passages"].waitForExistence(timeout: 15))
        history.tap()
        XCTAssertTrue(app.staticTexts["search-no-passages"].waitForExistence(timeout: 15))
        XCTAssertFalse(app.buttons["Try AI search"].exists)
        let close = app.navigationBars.buttons["Close"]
        XCTAssertTrue(close.waitForExistence(timeout: 5))
        close.tap()
        let threads = app.tabBars.buttons["Threads"]
        XCTAssertTrue(threads.waitForExistence(timeout: 5))
        threads.tap()
        XCTAssertTrue(app.searchFields["Find a thread"].waitForExistence(timeout: 15))
        let more = app.navigationBars.buttons.matching(NSPredicate(format: "label CONTAINS[c] %@", "More")).firstMatch
        XCTAssertTrue(more.waitForExistence(timeout: 5))
        more.tap()
        XCTAssertTrue(app.buttons["Activity & decisions"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["Search saved evidence"].exists)
        // Dismiss the menu without choosing a data-affecting action.
        app.tapCoordinateOutsideMenu()
        app.tabBars.buttons["Memories"].tap()
        XCTAssertTrue(app.tabBars.buttons["Memories"].isSelected)
    }
}

private extension XCUIApplication {
    @MainActor func tapCoordinateOutsideMenu() {
        coordinate(withNormalizedOffset: CGVector(dx: 0.08, dy: 0.55)).tap()
    }
}
