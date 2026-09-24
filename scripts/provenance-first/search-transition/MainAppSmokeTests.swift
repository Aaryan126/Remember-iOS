import XCTest

/// Normal-app navigation only: no personal sources opened or changed, no AI calls.
final class MainAppSmokeTests: XCTestCase {
    @MainActor func testSearchTransitionAndCompactMenuInNormalApp() throws {
        continueAfterFailure = false
        XCTAssertEqual(Bundle(for: Self.self).bundleIdentifier, "SimpleStudio.RememberUITests")
        let app = XCUIApplication()
        app.launch()
        XCTAssertTrue(app.tabBars.buttons["Memories"].waitForExistence(timeout: 30))
        app.tabBars.buttons["Memories"].tap()
        let search = app.searchFields["Search your memories"]
        let add = app.buttons["capture-menu-toggle"]
        XCTAssertTrue(add.waitForExistence(timeout: 10))
        let originalY = add.frame.minY
        for query in ["", "transitionnomatch92851", ""] {
            XCTAssertTrue(search.waitForExistence(timeout: 15))
            search.tap()
            XCTAssertTrue(app.buttons["search-options-menu"].waitForExistence(timeout: 10))
            XCTAssertFalse(add.exists)
            if !query.isEmpty { search.typeText(query + "\n") }
            app.navigationBars.buttons["Close"].tap()
            XCTAssertTrue(add.waitForExistence(timeout: 10))
            XCTAssertEqual(add.frame.minY, originalY, accuracy: 2)
            XCTAssertFalse(app.buttons["search-options-menu"].exists)
        }
        search.tap()
        search.typeText("transitionnomatch92851\n")
        let menu = app.buttons["search-options-menu"]
        XCTAssertTrue(menu.waitForExistence(timeout: 15))
        XCTAssertFalse(app.staticTexts["search-active-filters"].exists)
        menu.tap()
        app.buttons["Source text only"].tap()
        XCTAssertTrue(app.staticTexts["search-no-passages"].waitForExistence(timeout: 15))
        menu.tap()
        app.buttons["Include history"].tap()
        XCTAssertTrue(app.staticTexts["search-active-filters"].label.contains("Including history"))
        app.buttons["search-reset-filters"].tap()
        XCTAssertFalse(app.staticTexts["search-active-filters"].exists)
        app.navigationBars.buttons["Close"].tap()
        XCTAssertTrue(app.tabBars.buttons["Memories"].isSelected)
    }
}
