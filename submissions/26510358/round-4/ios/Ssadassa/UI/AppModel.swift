import SwiftUI
import UIKit

/// Everything the screens show, kept on the main actor. The work happens in Core (MiniAppSession).
@MainActor
final class AppModel: ObservableObject {
    enum Status { case live, busy, offline }

    @Published private(set) var state = MiniAppState()
    @Published private(set) var cards: [OwnerCard] = []
    @Published private(set) var questions: [OwnerQuestion] = []
    @Published private(set) var error: String?
    @Published private(set) var lastSeen: Date?
    @Published private(set) var sending: [String] = []
    @Published private(set) var limits: OwnerLimits
    @Published private(set) var now = Date()

    let link: AppLink
    let user: String
    private let session: MiniAppSession
    private let store = UserDefaultsLimits()
    private var handledConsents = Set<String>()
    private var clock: Timer?

    init(link: AppLink, user: String) {
        self.link = link
        self.user = user
        limits = store.load()
        let tools = OwnerTools(limitsStore: store)
        session = MiniAppSession(client: MiniAppClient(link: link), tools: tools)
        tools.onCard = { [weak self] card in Task { @MainActor in self?.cards.append(card) } }
        tools.onQuestion = { [weak self] q in
            Task { @MainActor in
                self?.questions.append(q)
                UINotificationFeedbackGenerator().notificationOccurred(.warning)
            }
        }
        session.onState = { [weak self] s in
            Task { @MainActor in
                guard let self else { return }
                let hadConsent = self.consent != nil
                self.state = s
                self.lastSeen = Date()
                if !hadConsent && self.consent != nil { UINotificationFeedbackGenerator().notificationOccurred(.warning) }
            }
        }
        session.onError = { [weak self] e in Task { @MainActor in self?.error = e } }
    }

    func start() {
        session.start()
        clock?.invalidate()
        clock = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.now = Date() }
        }
    }

    func stop() {
        session.stop()
        clock?.invalidate()
    }

    var status: Status {
        guard let seen = lastSeen, now.timeIntervalSince(seen) < 6 else { return .offline }
        return sending.isEmpty ? .live : .busy
    }

    var agentName: String { state.agent.isEmpty ? "agent" : state.agent }

    /// The first MeshKit call still waiting for the owner.
    var consent: PendingCall? { state.consents.first { !handledConsents.contains($0.id) } }

    var timeline: [TimelineItem] {
        var items = state.chat.map(TimelineItem.message) + cards.map(TimelineItem.card)
        items.sort { $0.ts < $1.ts }
        let mine = state.chat.filter { $0.who == user }.map(\.text)
        for text in sending where !mine.contains(text) { items.append(.sending(text)) }
        return items
    }

    func send(_ raw: String) {
        let text = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        sending.append(text)
        Task {
            do { _ = try await session.client.chat(text, user: user) } catch { self.error = String(describing: error) }
            if let i = sending.firstIndex(of: text) { sending.remove(at: i) }
        }
    }

    func answer(consent call: PendingCall, approved: Bool) {
        handledConsents.insert(call.id)
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        Task {
            do { try await session.consent(call, approved: approved) } catch { self.error = String(describing: error) }
        }
    }

    func answer(question q: OwnerQuestion, with text: String) {
        questions.removeAll { $0.id == q.id }
        let t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if !t.isEmpty { send(OwnerTools.answerMessage(q, t)) }
    }

    func save(limits new: OwnerLimits) {
        store.save(new)
        limits = store.load()
    }
}

enum TimelineItem: Identifiable {
    case message(ChatMessage)
    case card(OwnerCard)
    case sending(String)

    var id: String {
        switch self {
        case .message(let m): return "m" + m.id
        case .card(let c): return "c" + c.id.uuidString
        case .sending(let t): return "s" + t
        }
    }

    var ts: Double {
        switch self {
        case .message(let m): return m.ts
        case .card(let c): return c.ts
        case .sending: return .greatestFiniteMagnitude
        }
    }
}
