import XCTest
final class FeedbackDemoUITests: XCTestCase {
    override func setUpWithError() throws { continueAfterFailure = false }
    @MainActor func testFeedbackScreenTour() throws {
        #if !targetEnvironment(simulator)
        throw XCTSkip("Fictional feedback fixture is simulator-only")
        #else
        let app = XCUIApplication()
        app.launchArguments = ["-remember.appearance", "light", "-remember.project.cloudAssistance", "NO"]
        app.launch()
        XCTAssertTrue(app.buttons["Add a memory"].waitForExistence(timeout: 20))
        snap("memories", app)
        app.buttons["Add a memory"].tap()
        snap("capture-dial", app)
        app.buttons["Close add menu"].tap()
        app.tabBars.buttons["Project"].tap()
        let picker = app.segmentedControls["Project view"]
        XCTAssertTrue(picker.waitForExistence(timeout: 10))
        picker.buttons["Timeline"].tap()
        snap("project-timeline", app)
        picker.buttons["Graph"].tap()
        let nodes = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "graph-node-"))
        XCTAssertTrue(nodes.firstMatch.waitForExistence(timeout: 15))
        snap("bubbles", app)
        let canvas = app.descendants(matching: .any)["memory-map-canvas"].firstMatch
        let candidate = try XCTUnwrap(nodes.allElementsBoundByIndex.filter { $0.isHittable && canvas.frame.insetBy(dx: 1, dy: 1).contains($0.frame) }.max { $0.frame.width < $1.frame.width })
        candidate.press(forDuration: 0.7)
        XCTAssertTrue(app.buttons["map-focus-preview"].waitForExistence(timeout: 5))
        snap("bubble-preview", app)
        app.buttons["map-focus-preview"].tap()
        XCTAssertTrue(app.navigationBars["Thread history"].waitForExistence(timeout: 5))
        snap("river", app)
        app.swipeUp()
        snap("river-history", app)
        app.navigationBars.firstMatch.buttons.element(boundBy: 0).tap()
        app.tabBars.buttons["Settings"].tap()
        XCTAssertTrue(app.staticTexts["Appearance"].waitForExistence(timeout: 5))
        snap("settings", app)
        app.staticTexts["Privacy & AI"].tap()
        XCTAssertTrue(app.navigationBars["Privacy & AI"].waitForExistence(timeout: 5))
        snap("privacy", app)
        app.navigationBars.firstMatch.buttons.element(boundBy: 0).tap()
        app.buttons["AI Help"].tap()
        XCTAssertTrue(app.staticTexts["Ask your memories"].waitForExistence(timeout: 5))
        snap("ask", app)
        app.buttons["Close"].tap()
        app.terminate()
        app.launchArguments = ["-remember.appearance", "dark", "-remember.project.cloudAssistance", "NO"]
        app.launch()
        XCTAssertTrue(app.buttons["Add a memory"].waitForExistence(timeout: 15))
        snap("memories-dark", app)
        app.tabBars.buttons["Project"].tap()
        XCTAssertTrue(picker.waitForExistence(timeout: 5))
        picker.buttons["Graph"].tap()
        XCTAssertTrue(nodes.firstMatch.waitForExistence(timeout: 10))
        snap("bubbles-dark", app)
        app.terminate()
        #endif
    }
    @MainActor private func snap(_ name: String, _ app: XCUIApplication) {
        let a = XCTAttachment(screenshot: app.screenshot()); a.name = name; a.lifetime = .keepAlways; add(a)
    }
}
