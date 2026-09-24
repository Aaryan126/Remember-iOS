import Testing
import UIKit
@testable import Remember

@MainActor
struct SearchResultsHandoffTests {
    @MainActor private final class Harness {
        let window = UIWindow(frame: CGRect(x: 0, y: 0, width: 402, height: 874))
        let surface = SearchHandoffSurface(frame: CGRect(x: 0, y: 116, width: 402, height: 420))
        var captured: [CGRect] = []
        var durations: [TimeInterval] = []
        var changes: [() -> Void] = []
        var completions: [(Bool) -> Void] = []
        var snapshotSucceeds = true
        lazy var handoff = SearchResultsHandoff(snapshot: { [unowned self] _, rect in
            captured.append(rect)
            return snapshotSucceeds ? UIView() : nil
        }, animate: { [unowned self] duration, change, completion in
            durations.append(duration)
            changes.append(change)
            completions.append(completion)
        })

        init() {
            window.addSubview(surface)
            handoff.attach(surface)
        }
    }

    @Test func retainsOutgoingPixelsUntilFadeCompletes() throws {
        let h = Harness()
        h.handoff.begin(reduceMotion: false)
        let frozen = try #require(h.surface.frozen)
        #expect(h.captured == [CGRect(x: 0, y: 116, width: 402, height: 420)])
        #expect(frozen.alpha == 1)
        #expect(!frozen.isUserInteractionEnabled && frozen.accessibilityElementsHidden)
        #expect(h.durations == [0.28])
        h.changes[0]()
        #expect(frozen.alpha == 0)
        #expect(h.surface.frozen === frozen)
        h.completions[0](true)
        #expect(h.surface.frozen == nil && frozen.superview == nil)
    }

    @Test func nativeLayoutDoesNotMoveTheFrozenContent() throws {
        let h = Harness()
        h.handoff.begin(reduceMotion: false)
        let frozen = try #require(h.surface.frozen)
        let before = frozen.convert(frozen.bounds, to: h.window)
        h.surface.frame.origin.y += 54
        h.surface.layoutSubviews()
        #expect(frozen.convert(frozen.bounds, to: h.window) == before)
    }

    @Test func reopeningCancelsAndOldCompletionCannotRemoveNewSnapshot() throws {
        let h = Harness()
        h.handoff.begin(reduceMotion: false)
        let old = try #require(h.surface.frozen)
        h.handoff.cancel()
        #expect(old.superview == nil)
        h.handoff.begin(reduceMotion: false)
        let new = try #require(h.surface.frozen)
        h.completions[0](false)
        #expect(h.surface.frozen === new)
        h.completions[1](true)
        #expect(h.surface.frozen == nil)
    }

    @Test func reducedMotionUsesShortOpacityOnlyHandoff() throws {
        let h = Harness()
        h.handoff.begin(reduceMotion: true)
        let frozen = try #require(h.surface.frozen)
        let frame = frozen.frame
        h.changes[0]()
        #expect(h.durations == [0.12])
        #expect(frozen.frame == frame && frozen.transform == .identity)
    }

    @Test func failedSnapshotAndDetachedSurfaceDoNotLeaveOverlays() {
        let h = Harness()
        h.snapshotSucceeds = false
        h.handoff.begin(reduceMotion: false)
        #expect(h.surface.frozen == nil && h.changes.isEmpty)
        h.snapshotSucceeds = true
        h.surface.removeFromSuperview()
        h.handoff.begin(reduceMotion: false)
        #expect(h.surface.frozen == nil && h.changes.isEmpty)
    }

    @Test func leavingWindowReleasesSnapshot() throws {
        let h = Harness()
        h.handoff.begin(reduceMotion: false)
        let frozen = try #require(h.surface.frozen)
        h.surface.removeFromSuperview()
        #expect(h.surface.frozen == nil && frozen.superview == nil)
    }
}
