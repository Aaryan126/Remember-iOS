import NaturalLanguage
import Testing
@testable import Remember

@MainActor struct SentenceModelRecoveryTests {
    @Test func successLoadsOnceAndReusesCacheWithoutWaiting() async throws {
        let cache = ProjectSentenceModelCache<Int>()
        var calls = 0, waits = 0
        let first = try await cache.model(for: .english, load: { _ in calls += 1; return 42 }, waitForReadiness: { waits += 1 })
        let second = try await cache.model(for: .english, load: { _ in calls += 1; return 99 }, waitForReadiness: { waits += 1 })
        #expect(first == 42 && second == 42)
        #expect(calls == 1 && waits == 0)
    }

    @Test func transientFailureWaitsThenRetriesOnceAndCachesSuccess() async throws {
        let cache = ProjectSentenceModelCache<Int>()
        var calls = 0, waits = 0
        let result = try await cache.model(for: .english, load: { language in
            #expect(language == .english)
            calls += 1
            return waits == 0 ? nil : 42
        }, waitForReadiness: { waits += 1 })
        #expect(result == 42 && calls == 2 && waits == 1)
        let cached = try await cache.model(for: .english, load: { _ in calls += 1; return nil }, waitForReadiness: { waits += 1 })
        #expect(cached == 42 && calls == 2 && waits == 1)
    }

    @Test func persistentFailureStopsAfterTwoCallsAndOneWait() async throws {
        let cache = ProjectSentenceModelCache<Int>()
        var calls = 0, waits = 0
        let result = try await cache.model(for: .english, load: { _ in calls += 1; return nil }, waitForReadiness: { waits += 1 })
        #expect(result == nil && calls == 2 && waits == 1)
    }

    @Test func failureDoesNotPoisonFutureAttempts() async throws {
        let cache = ProjectSentenceModelCache<Int>()
        let first = try await cache.model(for: .english, load: { _ in nil }, waitForReadiness: {})
        let later = try await cache.model(for: .english, load: { _ in 42 }, waitForReadiness: {})
        #expect(first == nil && later == 42)
    }

    @Test func languagesHaveSeparateCachesAndAreNotSubstituted() async throws {
        let cache = ProjectSentenceModelCache<Int>()
        let english = try await cache.model(for: .english, load: { _ in 42 }, waitForReadiness: {})
        var languages: [NLLanguage] = []
        let french = try await cache.model(for: .french, load: { languages.append($0); return nil }, waitForReadiness: {})
        #expect(english == 42 && french == nil && languages == [.french, .french])
    }

    @Test func cancellationDuringReadinessDoesNotRetry() async throws {
        let cache = ProjectSentenceModelCache<Int>()
        var calls = 0
        await #expect(throws: CancellationError.self) {
            try await cache.model(for: .english, load: { _ in calls += 1; return nil }, waitForReadiness: { throw CancellationError() })
        }
        #expect(calls == 1)
    }

    @Test func rechecksCacheAfterSuspension() async throws {
        let cache = ProjectSentenceModelCache<Int>()
        var outerCalls = 0
        let result = try await cache.model(for: .english, load: { _ in outerCalls += 1; return nil }, waitForReadiness: {
            _ = try await cache.model(for: .english, load: { _ in 42 }, waitForReadiness: {})
        })
        #expect(result == 42 && outerCalls == 1)
    }
}
