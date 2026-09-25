import SwiftUI
import UIKit

/// Join UIKit's navigation animation, including its interactive progress and
/// cancellation. A path/onAppear animation starts too late during swipe-back.
struct LibraryControlsTransition<Content: View>: UIViewControllerRepresentable {
    let reduceMotion: Bool
    @ViewBuilder var content: () -> Content

    func makeUIViewController(context: Context) -> LibraryControlsController<Content> {
        let controller = LibraryControlsController(rootView: content())
        controller.reduceMotion = reduceMotion
        controller.view.backgroundColor = .clear
        controller.safeAreaRegions = []
        return controller
    }

    func updateUIViewController(_ controller: LibraryControlsController<Content>, context: Context) {
        controller.rootView = content()
        controller.reduceMotion = reduceMotion
    }

    func sizeThatFits(_ proposal: ProposedViewSize, uiViewController: LibraryControlsController<Content>, context: Context) -> CGSize? {
        uiViewController.sizeThatFits(in: proposal.replacingUnspecifiedDimensions())
    }
}

final class LibraryControlsController<Content: View>: UIHostingController<Content> {
    var reduceMotion = false
    private var searchSnapshot: UIView?
    private var snapshotTraits: UITraitCollection?
    private var snapshotWindowSize = CGSize.zero
    private var snapshotFrame = CGRect.zero

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        view.alpha = 1
        navigationController?.viewControllers.first?.navigationItem.searchController?.searchBar.searchTextField.alpha = 1
        guard !reduceMotion,
              let library = navigationController?.viewControllers.first,
              let search = library.navigationItem.searchController,
              !search.isActive,
              let window = search.searchBar.window else { return }
        // Cache only the inactive field, after UIKit has restored its glass.
        // During navigation UIKit temporarily removes that background.
        let field = search.searchBar.searchTextField
        let rect = field.convert(field.bounds, to: window)
        guard rect.width > 0, rect.height > 0 else { return }
        var rendered = false
        let image = UIGraphicsImageRenderer(size: rect.size).image { context in
            context.cgContext.translateBy(x: -rect.minX, y: -rect.minY)
            rendered = window.drawHierarchy(in: window.bounds, afterScreenUpdates: true)
        }
        guard rendered else { searchSnapshot = nil; return }
        snapshotTraits = traitCollection
        snapshotWindowSize = window.bounds.size
        snapshotFrame = field.convert(field.bounds, to: library.view)
        searchSnapshot = UIImageView(image: image)
        searchSnapshot?.layer.cornerRadius = rect.height / 2
        searchSnapshot?.clipsToBounds = true
        searchSnapshot?.isUserInteractionEnabled = false
        searchSnapshot?.accessibilityElementsHidden = true
    }

    override func viewDidDisappear(_ animated: Bool) {
        super.viewDidDisappear(animated)
        // Prepare before UIKit snapshots the returning page on the next pop.
        view.alpha = 0
        navigationController?.viewControllers.first?.navigationItem.searchController?.searchBar.searchTextField.alpha = 0
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        guard animated, !reduceMotion,
              let navigation = navigationController,
              let library = navigation.viewControllers.first,
              let transition = transitionCoordinator,
              transition.viewController(forKey: .to) === library,
              let departing = transition.viewController(forKey: .from),
              departing !== library else {
            view.alpha = 1
            navigationController?.viewControllers.first?.navigationItem.searchController?.searchBar.searchTextField.alpha = 1
            return
        }

        // Use the public search controller; leave its field, focus, query and
        // native navigation placement under SwiftUI's control.
        let searchBar = library.navigationItem.searchController?.searchBar
        let inactiveSearch = library.navigationItem.searchController?.isActive == false
            && searchBar?.text?.isEmpty != false
        let matchingAppearance = !traitCollection.hasDifferentColorAppearance(comparedTo: snapshotTraits)
            && traitCollection.preferredContentSizeCategory == snapshotTraits?.preferredContentSizeCategory
            && navigation.view.window?.bounds.size == snapshotWindowSize
        let snapshot = inactiveSearch && matchingAppearance ? searchSnapshot : nil
        // The live field is detached during navigation. Its frozen appearance
        // travels with the library, keeping the native placeholder aligned.
        if let snapshot {
            snapshot.frame = snapshotFrame
            library.view.addSubview(snapshot)
            snapshot.alpha = 0
        }
        view.alpha = 0
        view.transform = CGAffineTransform(translationX: 0, y: 12)
        searchBar?.searchTextField.alpha = 0
        let accepted = transition.animate(alongsideTransition: { [weak self, weak searchBar, weak snapshot] _ in
            self?.view.alpha = 1
            self?.view.transform = .identity
            if snapshot?.superview != nil {
                snapshot?.alpha = 1
            } else {
                searchBar?.searchTextField.alpha = 1
            }
        }, completion: { [weak self, weak searchBar, weak snapshot] context in
            // Also restore on cancellation, so the next return starts cleanly.
            self?.view.alpha = context.isCancelled ? 0 : 1
            self?.view.transform = .identity
            searchBar?.searchTextField.alpha = context.isCancelled ? 0 : 1
            snapshot?.removeFromSuperview()
        })
        if !accepted {
            view.alpha = 1
            view.transform = .identity
            searchBar?.searchTextField.alpha = 1
            snapshot?.removeFromSuperview()
            searchSnapshot = nil
        }
    }
}
