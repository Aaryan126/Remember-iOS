import XCTest

final class MemoryThreadNavigationUITests: XCTestCase {
    @MainActor private func launch(_ arguments: [String] = []) throws -> XCUIApplication {
        guard Bundle(for: Self.self).bundleIdentifier?.contains("SourceBrowserUI") == true else {
            throw XCTSkip("Fictional isolated simulator checks only")
        }
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchArguments = ["--memory-return"] + arguments
        app.launch()
        XCTAssertTrue(app.searchFields["Search your memories"].waitForExistence(timeout: 15))
        return app
    }

    @MainActor private func search(_ text: String, in app: XCUIApplication) {
        let field = app.searchFields["Search your memories"]
        field.tap()
        field.typeText(text + "\n")
        XCTAssertTrue(app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "library-memory-")).firstMatch.waitForExistence(timeout: 10))
    }

    @MainActor private func back(_ app: XCUIApplication) {
        app.navigationBars.buttons["BackButton"].tap()
    }

    @MainActor func testSearchThreadBackAndInteractiveCancellationPreserveResults() throws {
        let app = try launch()
        search("NOVA", in: app)
        let link = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "search-thread-")).firstMatch
        XCTAssertTrue(link.waitForExistence(timeout: 10))
        let initialY = link.frame.minY
        link.tap()
        XCTAssertTrue(app.buttons["thread-target-entry"].waitForExistence(timeout: 10))
        let edge = app.coordinate(withNormalizedOffset: CGVector(dx: 0.005, dy: 0.5))
        edge.press(forDuration: 0.05, thenDragTo: app.coordinate(withNormalizedOffset: CGVector(dx: 0.2, dy: 0.5)),
                   withVelocity: .slow, thenHoldForDuration: 0.5)
        XCTAssertTrue(app.buttons["thread-target-entry"].exists)
        edge.press(forDuration: 0.05, thenDragTo: app.coordinate(withNormalizedOffset: CGVector(dx: 0.9, dy: 0.5)))
        XCTAssertTrue(link.waitForExistence(timeout: 10))
        XCTAssertEqual(app.searchFields["Search your memories"].value as? String, "NOVA")
        XCTAssertEqual(link.frame.minY, initialY, accuracy: 3)
        link.tap()
        XCTAssertTrue(app.buttons["thread-target-entry"].waitForExistence(timeout: 10))
        back(app)
        XCTAssertTrue(link.waitForExistence(timeout: 10))
    }

    @MainActor func testPhotoBottomRightLinkAndExtractedText() throws {
        let app = try launch(["--unified-dark"])
        app.buttons["library-memory-11111111-1111-1111-1111-111111111111"].tap()
        let link = app.buttons["memory-thread-link"]
        XCTAssertTrue(link.waitForExistence(timeout: 10))
        XCTAssertGreaterThan(link.frame.midX, app.frame.midX)
        XCTAssertGreaterThan(link.frame.midY, app.frame.height * 0.7)
        XCTAssertLessThan(link.frame.maxY, app.frame.maxY)
        let screenshot = XCTAttachment(screenshot: app.screenshot())
        screenshot.name = "Photo with bottom-right thread shortcut"
        screenshot.lifetime = .keepAlways
        add(screenshot)
        let title = app.staticTexts["Return transition photo"]
        XCTAssertLessThan(title.frame.maxY, link.frame.maxY)
        app.buttons["Memory details"].tap()
        let disclosure = app.buttons["memory-extracted-text-disclosure"]
        XCTAssertTrue(disclosure.waitForExistence(timeout: 5))
        disclosure.tap()
        XCTAssertTrue(app.staticTexts["A fictional teal photo"].waitForExistence(timeout: 5))
        app.buttons["Done"].tap()
        link.tap()
        XCTAssertTrue(app.buttons["thread-target-entry"].waitForExistence(timeout: 10))
        back(app)
        XCTAssertTrue(link.waitForExistence(timeout: 10))
    }

    @MainActor func testNoteLinkRemainsVisibleAndHidesDuringEditing() throws {
        let app = try launch(["-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityXXXL"])
        search("NOVA", in: app)
        app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "library-memory-")).firstMatch.tap()
        let link = app.buttons["memory-thread-link"]
        XCTAssertTrue(link.waitForExistence(timeout: 10))
        XCTAssertTrue(link.isHittable)
        app.buttons["Edit"].tap()
        XCTAssertFalse(link.exists)
        app.buttons["Cancel"].tap()
        XCTAssertTrue(link.waitForExistence(timeout: 5))
        link.tap()
        XCTAssertTrue(app.buttons["thread-target-entry"].waitForExistence(timeout: 10))
        back(app)
        XCTAssertTrue(link.waitForExistence(timeout: 5))
    }

    @MainActor func testHistoricalSearchTargetsExactRevisionAndReturnsToFilters() throws {
        let app = try launch()
        search("Parcel", in: app)
        app.buttons["search-options-menu"].tap()
        app.buttons["Include history"].tap()
        let old = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@ AND label CONTAINS %@", "search-passage-", "ORBIT-27")).firstMatch
        XCTAssertTrue(old.waitForExistence(timeout: 10))
        for _ in 0..<5 where !old.isHittable { app.swipeUp() }
        old.tap()
        XCTAssertTrue(app.staticTexts["evidence-exact-quote"].waitForExistence(timeout: 10))
        let link = app.buttons["evidence-thread-link"]
        for _ in 0..<6 where !link.isHittable { app.swipeUp() }
        XCTAssertTrue(link.isHittable)
        link.tap()
        let selected = app.buttons["thread-target-entry"]
        XCTAssertTrue(selected.waitForExistence(timeout: 10))
        XCTAssertFalse(app.staticTexts["Selected revision"].exists)
        selected.tap()
        XCTAssertTrue(app.navigationBars["Saved revision"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format: "label CONTAINS %@", "ORBIT-27")).firstMatch.exists)
        back(app)
        XCTAssertTrue(selected.waitForExistence(timeout: 5))
        back(app)
        XCTAssertTrue(app.staticTexts["evidence-exact-quote"].waitForExistence(timeout: 5))
        back(app)
        XCTAssertEqual(app.searchFields["Search your memories"].value as? String, "Parcel")
        XCTAssertEqual(app.staticTexts["search-active-filters"].label, "Including history")
    }
    @MainActor func testMultipleThreadsOfferNamedChoicesFromSearchAndMemory() throws {
        let app = try launch(["--thread-multiple"])
        search("NOVA", in: app)
        // Other retained fixtures also match NOVA. Select the shared memory,
        // rather than relying on the order of search results.
        let link = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@ AND value == %@",
                                                    "search-thread-", "2 threads")).firstMatch
        XCTAssertTrue(link.waitForExistence(timeout: 10))
        let memoryCardID = link.identifier.replacingOccurrences(of: "search-thread-", with: "library-memory-")
        link.tap()
        app.buttons["Additional context"].tap()
        XCTAssertTrue(app.navigationBars["Additional context"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.buttons["thread-target-entry"].exists)
        back(app)
        app.buttons[memoryCardID].tap()
        app.buttons["memory-thread-link"].tap()
        app.buttons["Additional context"].tap()
        XCTAssertTrue(app.navigationBars["Additional context"].waitForExistence(timeout: 10))
        back(app)
        XCTAssertTrue(app.buttons["memory-thread-link"].waitForExistence(timeout: 5))
    }

    @MainActor func testThreadShortcutLoadsTargetBeforeInitialHistoryWindow() throws {
        let app = try launch(["--thread-long-history"])
        search("Parcel NOVA", in: app)
        app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "search-thread-")).firstMatch.tap()
        let selected = app.buttons["thread-target-entry"]
        XCTAssertTrue(selected.waitForExistence(timeout: 10))
        let scrolledToTarget = XCTNSPredicateExpectation(
            predicate: NSPredicate(format: "hittable == true"), object: selected)
        XCTAssertEqual(XCTWaiter.wait(for: [scrolledToTarget], timeout: 5), .completed)
        let screenshot = XCTAttachment(screenshot: app.screenshot())
        screenshot.name = "River focused on older target"
        screenshot.lifetime = .keepAlways
        add(screenshot)
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format: "label CONTAINS %@", "NOVA-42")).firstMatch.isHittable)
        app.swipeUp()
        let context = app.staticTexts.matching(NSPredicate(format: "label CONTAINS %@", "Surrounding context")).firstMatch
        XCTAssertTrue(context.waitForExistence(timeout: 5))
        back(app)
        XCTAssertEqual(app.searchFields["Search your memories"].value as? String, "Parcel NOVA")
    }

    @MainActor func testPDFTextAndMediaControlsRemainAccessibleAboveThreadLink() throws {
        for (kind, suffix) in [("pdf", "301"), ("audio", "302"), ("video", "303")] {
            let app = try launch(["--thread-media"])
            search("ThreadMedia " + kind, in: app)
            app.buttons["library-memory-33333333-3333-3333-3333-333333333" + suffix].tap()
            let link = app.buttons["memory-thread-link"]
            XCTAssertTrue(link.waitForExistence(timeout: 10))
            let initialY = link.frame.minY
            if kind == "pdf" {
                app.buttons["Memory details"].tap()
                let disclosure = app.buttons["memory-extracted-text-disclosure"]
                XCTAssertTrue(disclosure.waitForExistence(timeout: 5))
                disclosure.tap()
                XCTAssertTrue(app.staticTexts["Fictional PDF source text"].waitForExistence(timeout: 5))
                app.buttons["Done"].tap()
            } else {
                let play = app.buttons[kind == "audio" ? "Play voice memory" : "Play video"]
                XCTAssertTrue(play.waitForExistence(timeout: 10))
                XCTAssertLessThan(play.frame.maxY, link.frame.minY)
                play.tap()
                if kind == "audio" {
                    XCTAssertTrue(app.buttons["Stop voice memory"].waitForExistence(timeout: 10))
                    app.buttons["Stop voice memory"].tap()
                } else {
                    XCTAssertTrue(app.descendants(matching: .any)["Saved video player"].firstMatch.waitForExistence(timeout: 10))
                }
            }
            app.swipeUp()
            XCTAssertTrue(link.isHittable)
            XCTAssertEqual(link.frame.minY, initialY, accuracy: 3)
            link.tap()
            XCTAssertTrue(app.buttons["thread-target-entry"].waitForExistence(timeout: 10))
            back(app)
            XCTAssertTrue(link.waitForExistence(timeout: 5))
            app.terminate()
        }
    }

}
