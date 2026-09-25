import XCTest

/// Read-only normal-app navigation: no editing, captures or AI requests.
final class MainAppSmokeTests: XCTestCase {
    @MainActor func testMemoryReturnRestoresLibraryControls() throws {
        continueAfterFailure = false
        XCTAssertEqual(Bundle(for: Self.self).bundleIdentifier, "SimpleStudio.RememberUITests")
        let app = XCUIApplication()
        app.launch()
        let memories = app.tabBars.buttons["Memories"]
        XCTAssertTrue(memories.waitForExistence(timeout: 30))
        memories.tap()
        let add = app.buttons["capture-menu-toggle"]
        XCTAssertTrue(add.waitForExistence(timeout: 10))
        let originalY = add.frame.minY
        let cards = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "library-memory-"))
        XCTAssertTrue(cards.firstMatch.waitForExistence(timeout: 15))
        for swipeBack in [false, true] {
            let card = try XCTUnwrap(cards.allElementsBoundByIndex.first { $0.isHittable })
            card.tap()
            XCTAssertTrue(app.buttons["Memory details"].waitForExistence(timeout: 10))
            XCTAssertFalse(add.isHittable)
            XCTAssertFalse(memories.isHittable)
            if swipeBack {
                app.coordinate(withNormalizedOffset: CGVector(dx: 0.01, dy: 0.5))
                    .press(forDuration: 0.1,
                           thenDragTo: app.coordinate(withNormalizedOffset: CGVector(dx: 0.9, dy: 0.5)),
                           withVelocity: .slow, thenHoldForDuration: 0.2)
                XCTAssertTrue(app.buttons["Memory details"].waitForNonExistence(timeout: 10),
                              "The edge gesture must actually leave the detail screen")
            } else {
                app.navigationBars.buttons.firstMatch.tap()
            }
            XCTAssertTrue(add.waitForExistence(timeout: 10))
            XCTAssertTrue(add.isHittable)
            XCTAssertTrue(memories.isSelected)
            XCTAssertTrue(app.searchFields["Search your memories"].isHittable)
            XCTAssertTrue(app.buttons["AI Help"].isHittable)
            XCTAssertEqual(add.frame.minY, originalY, accuracy: 2)
        }
    }
}
