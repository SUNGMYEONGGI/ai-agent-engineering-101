import SwiftUI
import UIKit

/// Everything the screens show, kept on the main actor. The work happens in Core (MiniAppSession).
/// In demo mode nothing is polled: the screens run on DemoData so the design can be checked without an agent.
@MainActor
final class AppModel: ObservableObject {
    enum Status { case live, busy, offline, demo }

    @Published private(set) var state = MiniAppState()
    @Published private(set) var cards: [OwnerCard] = []
    @Published private(set) var questions: [OwnerQuestion] = []
    @Published private(set) var error: String?
    @Published private(set) var lastSeen: Date?
    @Published private(set) var sending: [String] = []
    @Published private(set) var limits: OwnerLimits
    @Published private(set) var now = Date()
    /// Bumped on each real state change the characters react to (new reply, card, question, consent).
    @Published private(set) var beat = 0
    @Published var character: AgentCharacter {
        didSet { UserDefaults.standard.set(character.rawValue, forKey: "ssadassa.character"); beat += 1 }
    }

    let link: AppLink?
    let user: String
    var isDemo: Bool { link == nil }
    private let session: MiniAppSession?
    private let store = UserDefaultsLimits()
    private var handledConsents = Set<String>()
    private var demoConsent: PendingCall?
    private var clock: Timer?

    /// link == nil: demo mode.
    init(link: AppLink?, user: String) {
        self.link = link
        self.user = link == nil ? DemoData.owner : user
        limits = store.load()
        character = AgentCharacter(rawValue: UserDefaults.standard.string(forKey: "ssadassa.character") ?? "") ?? .hoga
        guard let link else {
            session = nil
            state = DemoData.state()
            cards = [DemoData.card]
            questions = [DemoData.question]
            return
        }
        let tools = OwnerTools(limitsStore: store)
        session = MiniAppSession(client: MiniAppClient(link: link), tools: tools)
        tools.onCard = { [weak self] card in Task { @MainActor in self?.cards.append(card); self?.beat += 1 } }
        tools.onQuestion = { [weak self] q in
            Task { @MainActor in
                self?.questions.append(q)
                self?.beat += 1
                UINotificationFeedbackGenerator().notificationOccurred(.warning)
            }
        }
        session?.onState = { [weak self] s in Task { @MainActor in self?.apply(s) } }
        session?.onError = { [weak self] e in Task { @MainActor in self?.error = e } }
    }

    private func apply(_ s: MiniAppState) {
        let hadConsent = consent != nil
        let agentLines = state.chat.filter { $0.who == "agent" }.count
        state = s
        lastSeen = Date()
        if s.chat.filter({ $0.who == "agent" }).count != agentLines { beat += 1 }
        if !hadConsent && consent != nil {
            beat += 1
            UINotificationFeedbackGenerator().notificationOccurred(.warning)
        }
    }

    func start() {
        clock?.invalidate()
        clock = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.now = Date() }
        }
        if let session { session.start(); return }
        // Demo: a MeshKit consent arrives a few seconds in, the way a real one would.
        DispatchQueue.main.asyncAfter(deadline: .now() + 4) { [weak self] in
            guard let self, self.demoConsent == nil, !self.handledConsents.contains("demo-consent") else { return }
            self.demoConsent = DemoData.consent()
            self.beat += 1
            UINotificationFeedbackGenerator().notificationOccurred(.warning)
        }
    }

    func stop() {
        session?.stop()
        clock?.invalidate()
    }

    var status: Status {
        if isDemo { return sending.isEmpty ? .demo : .busy }
        guard let seen = lastSeen, now.timeIntervalSince(seen) < 6 else { return .offline }
        return sending.isEmpty ? .live : .busy
    }

    var agentName: String { state.agent.isEmpty ? "agent" : state.agent }

    /// The first MeshKit call still waiting for the owner.
    var consent: PendingCall? {
        if isDemo { return demoConsent.flatMap { handledConsents.contains($0.id) ? nil : $0 } }
        return state.consents.first { !handledConsents.contains($0.id) }
    }

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
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
        Task {
            if let session {
                do { _ = try await session.client.chat(text, user: user) } catch { self.error = String(describing: error) }
            } else {
                try? await Task.sleep(nanoseconds: 1_200_000_000)
                let t = Date().timeIntervalSince1970
                state.chat.append(ChatMessage(who: user, text: text, ts: t))
                state.chat.append(ChatMessage(who: "agent", text: DemoData.replies[state.chat.count % DemoData.replies.count], ts: t + 0.1))
                beat += 1
            }
            if let i = sending.firstIndex(of: text) { sending.remove(at: i) }
        }
    }

    func answer(consent call: PendingCall, approved: Bool) {
        handledConsents.insert(call.id)
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        if isDemo {
            let t = Date().timeIntervalSince1970
            state.chat.append(ChatMessage(who: "agent", text: approved
                ? "DailyMart에 우유를 주문했어요. 영수증 rcpt-demo01을 확인했습니다."
                : "알겠어요. DailyMart 주문은 하지 않았어요.", ts: t))
            beat += 1
            return
        }
        Task {
            do { try await session?.consent(call, approved: approved) } catch { self.error = String(describing: error) }
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
