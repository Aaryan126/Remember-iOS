import XCTest

/// Navigation-only check on the normal app. Never seed, edit or delete captures.
final class MainAppSmokeTests: XCTestCase {
    @MainActor func testSavedEvidenceEntryAndReturnInNormalApp() throws {
        continueAfterFailure = false
        XCTAssertEqual(Bundle(for: MainAppSmokeTests.self).bundleIdentifier, "SimpleStudio.RememberUITests")
        let app = XCUIApplication()
        app.launch()
        XCTAssertTrue(app.tabBars.buttons["Memories"].waitForExistence(timeout: 30))
        let threads = app.tabBars.buttons["Threads"]
        XCTAssertTrue(threads.exists)
        threads.tap()
        XCTAssertTrue(app.searchFields["Find a thread"].waitForExistence(timeout: 20))
        let more = app.navigationBars.buttons.matching(NSPredicate(format: "label CONTAINS[c] %@", "More")).firstMatch
        XCTAssertTrue(more.waitForExistence(timeout: 5))
        more.tap()
        let entry = app.buttons["Search saved evidence"]
        XCTAssertTrue(entry.waitForExistence(timeout: 5))
        entry.tap()
        let search = app.searchFields["Search saved text"]
        XCTAssertTrue(search.waitForExistence(timeout: 10))
        search.tap()
        search.typeText("sourcebrowserdeploymentnomatch2147\n")
        XCTAssertTrue(app.staticTexts["No matching saved text"].waitForExistence(timeout: 20))
        let segmented = app.segmentedControls["evidence-scope"]
        if segmented.exists {
            segmented.buttons["Include history"].tap()
        } else {
            app.buttons["evidence-scope"].tap()
            app.buttons["Include history"].tap()
        }
        XCTAssertTrue(app.staticTexts["No matching saved text"].waitForExistence(timeout: 20))
        XCTAssertFalse(app.otherElements["evidence-error"].exists)
        let close = app.navigationBars.buttons["Close"]
        if close.exists { close.tap() }
        let back = app.navigationBars.buttons["BackButton"]
        XCTAssertTrue(back.waitForExistence(timeout: 5))
        back.tap()
        XCTAssertTrue(app.searchFields["Find a thread"].waitForExistence(timeout: 10))
        app.tabBars.buttons["Memories"].tap()
        XCTAssertTrue(app.tabBars.buttons["Memories"].isSelected)
    }
}
