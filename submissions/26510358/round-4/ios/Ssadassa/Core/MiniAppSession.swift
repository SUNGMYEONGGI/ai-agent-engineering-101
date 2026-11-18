import Foundation

/// The app's link to its agent while it is open: offers the owner tools, polls the state every 1.5 s (as
/// miniapp.js does), answers page-tool calls at once, and hands everything else to the UI.
public final class MiniAppSession: @unchecked Sendable {
    public let client: MiniAppClient
    public let tools: OwnerTools
    public var onState: (MiniAppState) -> Void = { _ in }
    public var onError: (String?) -> Void = { _ in }

    private var task: Task<Void, Never>?
    private var answered = Set<String>()
    private var offered = false
    private let interval: UInt64

    public init(client: MiniAppClient, tools: OwnerTools, interval: Double = 1.5) {
        self.client = client
        self.tools = tools
        self.interval = UInt64(interval * 1_000_000_000)
    }

    public func start() {
        guard task == nil else { return }
        task = Task { [weak self] in
            while !Task.isCancelled {
                await self?.tick()
                try? await Task.sleep(nanoseconds: self?.interval ?? 1_500_000_000)
            }
        }
    }

    public func stop() {
        task?.cancel()
        task = nil
    }

    /// One poll. Public so a test can drive it step by step.
    public func tick() async {
        do {
            if !offered {
                try await client.offer(OwnerTools.offers)
                offered = true
            }
            let s = try await client.state()
            // The kit forgets our tools when it restarts; offer them again if the agent lost them.
            if !OwnerTools.offers.allSatisfy({ s.appTools["app_" + $0.name] != nil }) {
                client.resetPageToken()
                offered = false
            }
            for call in s.calls where call.kind == "tool" && !answered.contains(call.id) {
                answered.insert(call.id)
                try await client.answer(call.id, result: tools.handle(call))
            }
            onState(s)
            onError(nil)
        } catch {
            offered = false
            onError(String(describing: error))
        }
    }

    /// Allow or refuse a MeshKit call.
    public func consent(_ call: PendingCall, approved: Bool) async throws {
        answered.insert(call.id)
        try await client.consent(call.id, approved: approved)
    }
}
