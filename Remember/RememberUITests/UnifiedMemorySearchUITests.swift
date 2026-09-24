import XCTest

final class UnifiedMemorySearchUITests: XCTestCase {
    @MainActor private func launch(_ arguments: [String] = []) throws -> XCUIApplication {
        guard Bundle(for: Self.self).bundleIdentifier?.contains("SourceBrowserUI") == true else {
            throw XCTSkip("Fictional isolated simulator checks only")
        }
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchArguments = arguments
        app.launch()
        return app
    }

    @MainActor private func search(_ text: String, in app: XCUIApplication) {
        let field = app.searchFields["Search your memories"]
        XCTAssertTrue(field.waitForExistence(timeout: 10))
        field.tap()
        field.typeText(text + "\n")
        XCTAssertTrue(app.buttons["search-options-menu"].waitForExistence(timeout: 10))
    }

    @MainActor private func toggle(_ label: String, in app: XCUIApplication) {
        let menu = app.buttons["search-options-menu"]
        for _ in 0..<5 where !menu.isHittable { app.swipeDown() }
        menu.tap()
        let option = app.buttons[label]
        XCTAssertTrue(option.waitForExistence(timeout: 5))
        option.tap()
    }

    @MainActor func testSearchHeaderAlignmentAndBalancedSpacing() throws {
        for arguments in [[], ["--unified-dark"]] {
            let app = try launch(arguments)
            let field = app.searchFields["Search your memories"]
            XCTAssertTrue(field.waitForExistence(timeout: 10))
            field.tap()
            field.typeText("Unicorn")
            assertBalancedSearchHeader(in: app)
            capture("Balanced search header, keyboard open \(arguments)", in: app)
            field.typeText("\n")
            assertBalancedSearchHeader(in: app)
            capture("Balanced search header, keyboard closed \(arguments)", in: app)
            app.terminate()
        }
    }

    @MainActor private func assertBalancedSearchHeader(in app: XCUIApplication) {
        let field = app.searchFields["Search your memories"]
        let title = app.staticTexts["search-results-title"]
        let count = app.staticTexts["search-results-count"]
        let menu = app.buttons["search-options-menu"]
        let card = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "library-memory-")).firstMatch
        XCTAssertTrue(card.waitForExistence(timeout: 10))
        XCTAssertTrue(title.exists)
        XCTAssertTrue(count.exists)
        XCTAssertTrue(menu.exists)
        XCTAssertEqual(title.frame.midY, count.frame.midY, accuracy: 1)
        XCTAssertEqual(title.frame.midY, menu.frame.midY, accuracy: 1)
        XCTAssertGreaterThanOrEqual(menu.frame.height, 44)
        let above = title.frame.midY - field.frame.maxY
        let below = card.frame.minY - title.frame.midY
        XCTAssertEqual(above, below, accuracy: 2,
                       "The header center should sit halfway between the search bar and grid")
        XCTAssertEqual(above - menu.frame.height / 2, 10, accuracy: 2,
                       "Space above the header touch target should be halved from 20pt to 10pt")
        XCTAssertEqual(below - menu.frame.height / 2, 10, accuracy: 2,
                       "Space below the header touch target should also be 10pt")
    }

    @MainActor func testFiltersAreHiddenByDefaultAndResetRestoresPlainSearch() throws {
        let app = try launch()
        search("ORBIT", in: app)
        XCTAssertFalse(app.switches["search-include-history"].exists)
        XCTAssertFalse(app.switches["search-source-only"].exists)
        XCTAssertFalse(app.staticTexts["search-active-filters"].exists)
        XCTAssertFalse(app.buttons["Try AI search"].exists)
        toggle("Include history", in: app)
        XCTAssertTrue(app.staticTexts["search-active-filters"].waitForExistence(timeout: 5))
        XCTAssertTrue(passage("ORBIT-27", in: app).waitForExistence(timeout: 10))
        app.buttons["search-reset-filters"].tap()
        XCTAssertFalse(app.staticTexts["search-active-filters"].exists)
        XCTAssertFalse(passage("ORBIT-27", in: app).exists)
        app.buttons["search-options-menu"].tap()
        app.buttons["How search works"].tap()
        XCTAssertTrue(app.alerts["How search works"].waitForExistence(timeout: 5))
        app.alerts.buttons["OK"].tap()
    }

    @MainActor func testTyposFindCardsAndOriginalPassagesAcrossFilters() throws {
        let app = try launch()
        search("parcle", in: app)
        let card = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "library-memory-")).firstMatch
        XCTAssertTrue(card.waitForExistence(timeout: 10))
        toggle("Source text only", in: app)
        XCTAssertTrue(passage("NOVA-42", in: app).waitForExistence(timeout: 10))
        XCTAssertFalse(card.exists)
        toggle("Include history", in: app)
        let old = passage("ORBIT-27", in: app)
        XCTAssertTrue(old.waitForExistence(timeout: 10))
        for _ in 0..<4 where !old.isHittable { app.swipeUp() }
        old.tap()
        let quote = app.staticTexts["evidence-exact-quote"]
        XCTAssertTrue(quote.waitForExistence(timeout: 10))
        XCTAssertTrue(quote.label.contains("Parcel ORBIT-27"))
        XCTAssertFalse(quote.label.contains("parcle"))
        app.navigationBars.buttons["BackButton"].tap()
        XCTAssertTrue(passage("ORBIT-27", in: app).waitForExistence(timeout: 10))
        XCTAssertEqual(app.searchFields["Search your memories"].value as? String, "parcle")
    }

    @MainActor func testClosingSearchPreservesScrolledLibraryAcrossRepeatedSessions() throws {
        try verifyRepeatedSearchDismissal(scrolled: true)
    }

    @MainActor func testClosingSearchPreservesTopOfLibraryAcrossRepeatedSessions() throws {
        try verifyRepeatedSearchDismissal(scrolled: false)
    }

    @MainActor private func verifyRepeatedSearchDismissal(scrolled: Bool) throws {
        let app = try launch(["--transition-long-library"] + (scrolled ? [] : ["--unified-dark"]))
        let library = app.scrollViews["memory-library-scroll"]
        XCTAssertTrue(library.waitForExistence(timeout: 10))
        if scrolled { library.swipeUp() }
        let cards = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "library-memory-"))
        let anchor = try XCTUnwrap(cards.allElementsBoundByIndex.first { $0.isHittable })
        let identifier = anchor.identifier
        let initialFrame = anchor.frame
        for (query, dismissKeyboard, clearBeforeClose) in [
            ("", false, false), ("Unicorn", false, false),
            ("transition-no-match-92851", false, false),
            ("Unicorn", true, false), ("Unicorn", false, true),
            ("", false, false)
        ] {
            let field = app.searchFields["Search your memories"]
            field.tap()
            XCTAssertTrue(app.navigationBars.buttons["Close"].waitForExistence(timeout: 5))
            XCTAssertTrue(library.isHittable, "Empty focus must keep the browsing grid visible")
            XCTAssertFalse(app.buttons["search-options-menu"].exists,
                           "Empty focus must not insert a second results layout")
            XCTAssertFalse(app.buttons["capture-menu-toggle"].exists)
            if !query.isEmpty {
                field.typeText(query + (dismissKeyboard ? "\n" : ""))
                XCTAssertTrue(app.buttons["search-options-menu"].waitForExistence(timeout: 5))
                XCTAssertFalse(library.isHittable, "Populated search must own interaction")
            }
            if clearBeforeClose {
                // Control: manually clear before closing, as compared with native
                // Cancel clearing the query. Both must restore the same library.
                field.buttons["Clear text"].tap()
                XCTAssertTrue(library.isHittable)
                XCTAssertFalse(app.buttons["search-options-menu"].exists)
            }
            app.navigationBars.buttons["Close"].tap()
            XCTAssertTrue(library.waitForExistence(timeout: 5))
            let restored = app.buttons[identifier]
            XCTAssertTrue(restored.isHittable)
            XCTAssertEqual(restored.frame.minY, initialFrame.minY, accuracy: 2,
                           "Closing search must preserve the browsing offset")
            XCTAssertFalse(app.buttons["search-options-menu"].exists)
            XCTAssertEqual(field.value as? String, "Search your memories",
                           "Native cancellation must clear the populated query")
        }
        capture("Library after repeated search dismissal", in: app)
    }

    @MainActor func testClearingQueryPreservesFiltersUntilCancel() throws {
        let app = try launch()
        search("ORBIT", in: app)
        toggle("Include history", in: app)
        let field = app.searchFields["Search your memories"]
        field.tap()
        field.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: 5))
        XCTAssertFalse(app.buttons["search-options-menu"].exists)
        XCTAssertTrue(app.scrollViews["memory-library-scroll"].isHittable)
        field.typeText("ORBIT\n")
        XCTAssertEqual(app.staticTexts["search-active-filters"].label, "Including history")
        XCTAssertTrue(passage("ORBIT-27", in: app).waitForExistence(timeout: 10))
        app.navigationBars.buttons["Close"].tap()
        search("ORBIT", in: app)
        XCTAssertFalse(app.staticTexts["search-active-filters"].exists)
    }

    @MainActor private func passage(_ phrase: String, in app: XCUIApplication) -> XCUIElement {
        app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@ AND label CONTAINS %@", "search-passage-", phrase)).firstMatch
    }

    @MainActor private func capture(_ name: String, in app: XCUIApplication) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    @MainActor func testCurrentPassageAndKeyboardSubmissionStayLocal() throws {
        let app = try launch()
        search("NOVA", in: app)
        let snippet = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "search-snippet-")).firstMatch
        XCTAssertTrue(snippet.waitForExistence(timeout: 10))
        for _ in 0..<4 where !snippet.isHittable { app.swipeUp() }
        capture("Current memory with saved passage", in: app)
        XCTAssertFalse(app.staticTexts["AI-assisted memory matches"].exists)
        snippet.tap()
        XCTAssertTrue(app.staticTexts["evidence-exact-quote"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.staticTexts["evidence-exact-quote"].label.contains("NOVA-42"))
        app.navigationBars.buttons["BackButton"].tap()
        XCTAssertEqual(app.searchFields["Search your memories"].value as? String, "NOVA")
    }

    @MainActor func testEmptyLibraryStillAllowsHistorySearch() throws {
        let app = try launch(["--unified-empty-library"])
        XCTAssertTrue(app.staticTexts["Save your first memory"].waitForExistence(timeout: 10))
        search("ARCHIVE", in: app)
        toggle("Include history", in: app)
        XCTAssertTrue(passage("ARCHIVE-8", in: app).waitForExistence(timeout: 10))
    }

    @MainActor func testThreadsMenuHasNoDuplicateSearch() throws {
        let app = try launch(["--unified-threads"])
        XCTAssertTrue(app.searchFields["Find a thread"].waitForExistence(timeout: 10))
        let more = app.navigationBars.buttons.matching(NSPredicate(format: "label CONTAINS[c] %@", "More")).firstMatch
        XCTAssertTrue(more.waitForExistence(timeout: 5))
        more.tap()
        XCTAssertTrue(app.buttons["Activity & decisions"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["Search saved evidence"].exists)
    }

    @MainActor func testHistoryOpensExactRevisionAndBackPreservesSearch() throws {
        let app = try launch()
        search("ORBIT", in: app)
        XCTAssertFalse(passage("ORBIT-27", in: app).exists)
        toggle("Include history", in: app)
        let old = passage("ORBIT-27", in: app)
        XCTAssertTrue(old.waitForExistence(timeout: 10))
        for _ in 0..<4 where !old.isHittable { app.swipeUp() }
        old.tap()
        let quote = app.staticTexts["evidence-exact-quote"]
        XCTAssertTrue(quote.waitForExistence(timeout: 10))
        XCTAssertTrue(quote.label.contains("ORBIT-27"))
        XCTAssertFalse(quote.label.contains("NOVA-42"))
        app.navigationBars.buttons["BackButton"].tap()
        XCTAssertEqual(app.searchFields["Search your memories"].value as? String, "ORBIT")
        XCTAssertEqual(app.staticTexts["search-active-filters"].label, "Including history")
        XCTAssertFalse(app.navigationBars["Imported history"].exists)
    }

    @MainActor func testSourceOnlyExcludesGeneratedSummary() throws {
        let app = try launch()
        search("Unicorn", in: app)
        let card = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "library-memory-")).firstMatch
        XCTAssertTrue(card.waitForExistence(timeout: 10))
        toggle("Source text only", in: app)
        XCTAssertTrue(app.staticTexts["search-no-passages"].waitForExistence(timeout: 10))
        XCTAssertFalse(card.exists)
        XCTAssertFalse(app.buttons["Try AI search"].exists)
    }

    @MainActor func testDarkLargeTextSourceSearch() throws {
        let app = try launch(["--unified-dark", "-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityXXXL"])
        search("ARCHIVE", in: app)
        toggle("Source text only", in: app)
        toggle("Include history", in: app)
        let archived = passage("ARCHIVE-8", in: app)
        for _ in 0..<5 where !archived.isHittable { app.swipeUp() }
        XCTAssertTrue(archived.waitForExistence(timeout: 10))
        XCTAssertTrue(archived.label.contains("Archived"))
        capture("Unified search dark large text", in: app)
    }
}
