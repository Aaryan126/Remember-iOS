import XCTest

/// Fictional no-match query only; never open, edit or delete personal sources.
final class MainAppSmokeTests: XCTestCase {
    @MainActor func testCompactSearchMenuInNormalApp() throws {
        continueAfterFailure = false
        XCTAssertEqual(Bundle(for: Self.self).bundleIdentifier, "SimpleStudio.RememberUITests")
        let app = XCUIApplication()
        app.launch()
        XCTAssertTrue(app.tabBars.buttons["Memories"].waitForExistence(timeout: 30))
        app.tabBars.buttons["Memories"].tap()
        let search = app.searchFields["Search your memories"]
        XCTAssertTrue(search.waitForExistence(timeout: 15))
        search.tap()
        search.typeText("compactsearchnomatch92851\n")
        let menu = app.buttons["search-options-menu"]
        XCTAssertTrue(menu.waitForExistence(timeout: 15))
        XCTAssertFalse(app.switches["search-include-history"].exists)
        XCTAssertFalse(app.staticTexts["search-active-filters"].exists)
        menu.tap()
        app.buttons["Source text only"].tap()
        XCTAssertTrue(app.staticTexts["search-no-passages"].waitForExistence(timeout: 15))
        menu.tap()
        app.buttons["Include history"].tap()
        XCTAssertTrue(app.staticTexts["search-active-filters"].label.contains("Including history"))
        XCTAssertTrue(app.staticTexts["search-no-passages"].waitForExistence(timeout: 15))
        app.buttons["search-reset-filters"].tap()
        XCTAssertFalse(app.staticTexts["search-active-filters"].exists)
        let close = app.navigationBars.buttons["Close"]
        XCTAssertTrue(close.waitForExistence(timeout: 5))
        close.tap()
        XCTAssertTrue(app.tabBars.buttons["Memories"].isSelected)
    }
}
