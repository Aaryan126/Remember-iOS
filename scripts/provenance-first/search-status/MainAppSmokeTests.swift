import XCTest

/// Normal-app navigation only: no personal sources opened or changed, no AI calls.
final class MainAppSmokeTests: XCTestCase {
    @MainActor func testNativeSearchDismissalAndCompactMenuInNormalApp() throws {
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
        for (query, dismissKeyboard, clearBeforeClose) in [("", false, false), ("f", false, false),
                                         ("transitionnomatch92851", false, false),
                                         ("f", true, false), ("f", false, true), ("", false, false)] {
            XCTAssertTrue(search.waitForExistence(timeout: 15))
            search.tap()
            XCTAssertTrue(app.navigationBars.buttons["Close"].waitForExistence(timeout: 10))
            XCTAssertFalse(app.buttons["search-options-menu"].exists)
            XCTAssertTrue(app.scrollViews["memory-library-scroll"].isHittable)
            XCTAssertFalse(add.exists)
            if !query.isEmpty {
                search.typeText(query + (dismissKeyboard ? "\n" : ""))
                XCTAssertTrue(app.buttons["search-options-menu"].waitForExistence(timeout: 10))
            }
            if clearBeforeClose {
                search.buttons["Clear text"].tap()
                XCTAssertFalse(app.buttons["search-options-menu"].exists)
            }
            app.navigationBars.buttons["Close"].tap()
            XCTAssertTrue(add.waitForExistence(timeout: 10))
            XCTAssertTrue(search.waitForExistence(timeout: 10))
            // A native empty field can expose nil, an empty string, or its
            // placeholder. Require the field to exist after dismissal first;
            // a retained query must fail regardless of that representation.
            let value = search.value
            XCTAssertTrue(value == nil || (value as? String) == ""
                          || (value as? String) == "Search your memories",
                          "Closing search must clear the query")
            XCTAssertEqual(add.frame.minY, originalY, accuracy: 2)
            XCTAssertFalse(app.buttons["search-options-menu"].exists)
        }
        search.tap()
        search.typeText("transitionnomatch92851\n")
        let empty = app.staticTexts["search-no-memories"]
        XCTAssertTrue(empty.waitForExistence(timeout: 15))
        XCTAssertEqual(empty.label, "No matching current memories")
        XCTAssertEqual(empty.frame.midX, app.frame.midX, accuracy: 2)
        XCTAssertFalse(app.activityIndicators["search-status-loading"].exists)
        let menu = app.buttons["search-options-menu"]
        XCTAssertTrue(menu.waitForExistence(timeout: 15))
        XCTAssertGreaterThan(empty.frame.midY - menu.frame.maxY, 90)
        XCTAssertFalse(app.staticTexts["search-active-filters"].exists)
        let title = app.staticTexts["search-results-title"]
        let count = app.staticTexts["search-results-count"]
        XCTAssertTrue(title.exists)
        XCTAssertTrue(count.exists)
        XCTAssertEqual(title.frame.midY, count.frame.midY, accuracy: 1)
        XCTAssertEqual(title.frame.midY, menu.frame.midY, accuracy: 1)
        XCTAssertGreaterThanOrEqual(menu.frame.height, 44)
        XCTAssertEqual(title.frame.midY - search.frame.maxY, 32, accuracy: 2)
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
