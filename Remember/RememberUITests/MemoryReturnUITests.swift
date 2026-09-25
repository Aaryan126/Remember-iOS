import XCTest

final class MemoryReturnUITests: XCTestCase {
    @MainActor private func launch(_ arguments: [String] = []) throws -> XCUIApplication {
        guard Bundle(for: Self.self).bundleIdentifier?.contains("SourceBrowserUI") == true else {
            throw XCTSkip("Fictional simulator library only")
        }
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchArguments = ["--memory-return"] + arguments
        if !arguments.contains("--memory-return-light") { app.launchArguments.append("--unified-dark") }
        app.launch()
        XCTAssertTrue(app.buttons["capture-menu-toggle"].waitForExistence(timeout: 15))
        return app
    }

    @MainActor func testPhotoBackAndInteractiveCancellationRestoreLibraryControls() throws {
        let app = try launch()
        let photo = app.buttons["library-memory-11111111-1111-1111-1111-111111111111"]
        let add = app.buttons["capture-menu-toggle"]
        let initial = add.frame
        for swipeBack in [false, true] {
            XCTAssertTrue(photo.waitForExistence(timeout: 10))
            photo.tap()
            XCTAssertTrue(app.buttons["Memory details"].waitForExistence(timeout: 10))
            XCTAssertFalse(add.isHittable)
            XCTAssertFalse(app.tabBars.buttons["Memories"].isHittable)
            if swipeBack {
                let edge = app.coordinate(withNormalizedOffset: CGVector(dx: 0.005, dy: 0.5))
                let short = app.coordinate(withNormalizedOffset: CGVector(dx: 0.20, dy: 0.5))
                edge.press(forDuration: 0.05, thenDragTo: short, withVelocity: .slow, thenHoldForDuration: 0.5)
                XCTAssertTrue(app.buttons["Memory details"].exists, "Short swipe should cancel")
                XCTAssertFalse(add.isHittable)
                XCTAssertFalse(app.tabBars.buttons["Memories"].isHittable)
                edge.press(forDuration: 0.05, thenDragTo: app.coordinate(withNormalizedOffset: CGVector(dx: 0.9, dy: 0.5)))
            } else {
                app.navigationBars.buttons.firstMatch.tap()
            }
            assertLibrary(app, expectedAddFrame: initial)
        }
        add.tap()
        XCTAssertTrue(app.buttons["Close add menu"].waitForExistence(timeout: 5))
        app.buttons["Close add menu"].tap()
    }

    @MainActor func testReturnInLightMode() throws {
        let app = try launch(["--memory-return-light"])
        let initial = app.buttons["capture-menu-toggle"].frame
        app.buttons["library-memory-11111111-1111-1111-1111-111111111111"].tap()
        XCTAssertTrue(app.buttons["Memory details"].waitForExistence(timeout: 10))
        XCTAssertFalse(app.tabBars.buttons["Memories"].isHittable)
        app.navigationBars.buttons.firstMatch.tap()
        assertLibrary(app, expectedAddFrame: initial)
    }

    @MainActor func testReturnPreservesScrolledLibraryPosition() throws {
        let app = try launch(["--transition-long-library"])
        let scroll = app.scrollViews["memory-library-scroll"]
        scroll.swipeUp()
        scroll.swipeUp()
        let cards = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "library-memory-"))
        let card = try XCTUnwrap(cards.allElementsBoundByIndex.first { $0.isHittable && $0.frame.minY > 220 })
        let originalY = card.frame.minY
        card.tap()
        XCTAssertTrue(app.buttons["Memory details"].waitForExistence(timeout: 10))
        app.navigationBars.buttons.firstMatch.tap()
        XCTAssertTrue(app.buttons["capture-menu-toggle"].waitForExistence(timeout: 10))
        XCTAssertEqual(card.frame.minY, originalY, accuracy: 2)
        XCTAssertTrue(app.tabBars.buttons["Memories"].isSelected)
    }

    @MainActor func testMemoryBesideAddControlRemainsTappable() throws {
        let app = try launch(["--transition-long-library"])
        let add = app.buttons["capture-menu-toggle"]
        let cards = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "library-memory-"))
        let card = try XCTUnwrap(cards.allElementsBoundByIndex.first {
            $0.isHittable && $0.frame.midX > app.frame.midX
                && $0.frame.midY > add.frame.minY - 150
                && $0.frame.maxY < add.frame.minY
        })
        card.tap()
        XCTAssertTrue(app.buttons["Memory details"].waitForExistence(timeout: 10))
        app.navigationBars.buttons.firstMatch.tap()
        XCTAssertTrue(add.waitForExistence(timeout: 10))
    }

    @MainActor func testSearchResultBackPreservesQueryAndControls() throws {
        let app = try launch()
        let search = app.searchFields["Search your memories"]
        search.tap()
        search.typeText("Unicorn\n")
        let card = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "library-memory-")).firstMatch
        XCTAssertTrue(card.waitForExistence(timeout: 10))
        card.tap()
        XCTAssertTrue(app.buttons["Memory details"].waitForExistence(timeout: 10))
        XCTAssertFalse(app.tabBars.buttons["Memories"].isHittable)
        app.navigationBars.buttons.firstMatch.tap()
        XCTAssertTrue(search.waitForExistence(timeout: 10))
        XCTAssertEqual(search.value as? String, "Unicorn")
        XCTAssertTrue(app.buttons["search-options-menu"].exists)
        XCTAssertFalse(app.buttons["capture-menu-toggle"].isHittable)
        app.navigationBars.buttons["Close"].tap()
        XCTAssertTrue(app.buttons["capture-menu-toggle"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.tabBars.buttons["Memories"].isSelected)
    }

    @MainActor private func assertLibrary(_ app: XCUIApplication, expectedAddFrame: CGRect) {
        let add = app.buttons["capture-menu-toggle"]
        XCTAssertTrue(add.waitForExistence(timeout: 10))
        XCTAssertTrue(add.isHittable)
        XCTAssertTrue(app.searchFields["Search your memories"].isHittable)
        XCTAssertTrue(app.buttons["AI Help"].isHittable)
        XCTAssertTrue(app.tabBars.buttons["Memories"].isSelected)
        XCTAssertEqual(add.frame.minY, expectedAddFrame.minY, accuracy: 2)
    }
}
