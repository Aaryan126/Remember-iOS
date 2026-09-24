import SwiftUI
import UIKit

/// Keep rendered results stable while Cancel clears the live query. Fading the
/// live ScrollView instead would let its content/insets change during dismissal.
/// Snapshots never leave memory and never contain the keyboard or search chrome.
@MainActor
final class SearchResultsHandoff {
    typealias Snapshot = @MainActor (UIWindow, CGRect) -> UIView?
    typealias Animate = @MainActor (TimeInterval, @escaping () -> Void, @escaping (Bool) -> Void) -> Void

    private weak var surface: SearchHandoffSurface?
    private let snapshot: Snapshot
    private let animate: Animate

    init(snapshot: @escaping Snapshot = { window, rect in
        window.resizableSnapshotView(from: rect, afterScreenUpdates: false, withCapInsets: .zero)
    }, animate: @escaping Animate = { duration, changes, completion in
        UIView.animate(withDuration: duration, delay: 0,
                       options: [.curveEaseOut, .allowUserInteraction, .beginFromCurrentState],
                       animations: changes, completion: completion)
    }) {
        self.snapshot = snapshot
        self.animate = animate
    }

    func attach(_ surface: SearchHandoffSurface) {
        if self.surface !== surface { cancel() }
        self.surface = surface
    }

    func cancel() { surface?.clear() }

    /// Called synchronously BEFORE the search binding empties, not on a timer
    /// after SwiftUI has already replaced results with the browsing grid.
    func begin(reduceMotion: Bool) {
        cancel()
        guard let surface, let window = surface.window else { return }
        let visibleBounds = surface.bounds.inset(by: surface.safeAreaInsets)
        let rect = surface.convert(visibleBounds, to: window).intersection(window.bounds)
        guard !rect.isNull, rect.width > 0, rect.height > 0,
              let frozen = snapshot(window, rect) else { return }
        frozen.isUserInteractionEnabled = false
        frozen.accessibilityElementsHidden = true
        frozen.accessibilityIdentifier = "search-dismissal-snapshot"
        surface.show(frozen, in: rect)
        // Only opacity changes, including with Reduce Motion. The shorter fade
        // avoids a hard content flash without adding spatial motion.
        animate(reduceMotion ? 0.12 : 0.28, { frozen.alpha = 0 }) { [weak surface, weak frozen] _ in
            guard let frozen, surface?.frozen === frozen else { return }
            surface?.clear()
        }
    }
}

@MainActor
final class SearchHandoffSurface: UIView {
    private(set) var frozen: UIView?
    private var windowRect = CGRect.zero

    func show(_ frozen: UIView, in rect: CGRect) {
        clear()
        self.frozen = frozen
        windowRect = rect
        addSubview(frozen)
        setNeedsLayout()
        layoutIfNeeded()
    }

    func clear() {
        frozen?.layer.removeAllAnimations()
        frozen?.removeFromSuperview()
        frozen = nil
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        guard let frozen, let window else { return }
        // Native search/keyboard layout can move this host. Keep the outgoing
        // pixels at their original screen position rather than moving them twice.
        frozen.frame = convert(windowRect, from: window)
    }

    override func didMoveToWindow() {
        super.didMoveToWindow()
        if window == nil { clear() }
    }
}

struct SearchResultsHandoffOverlay: UIViewRepresentable {
    let handoff: SearchResultsHandoff

    func makeUIView(context: Context) -> SearchHandoffSurface {
        let view = SearchHandoffSurface()
        view.isUserInteractionEnabled = false
        view.accessibilityElementsHidden = true
        // The native content host changes its safe-area frame before its visible
        // chrome finishes moving. Don't crop the fixed snapshot to those new
        // bounds; navigation chrome still draws above this content overlay.
        view.clipsToBounds = false
        handoff.attach(view)
        return view
    }

    func updateUIView(_ view: SearchHandoffSurface, context: Context) {
        handoff.attach(view)
    }

    static func dismantleUIView(_ view: SearchHandoffSurface, coordinator: ()) {
        view.clear()
    }
}
