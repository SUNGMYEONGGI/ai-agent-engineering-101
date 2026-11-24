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
    /// The card the owner is replying to in a thread, if any.
    @Published var replyTo: OwnerCard?
    @Published private(set) var limits: OwnerLimits
    @Published private(set) var now = Date()
    /// Bumped on each real state change the characters react to (new reply, card, question, consent).
    @Published private(set) var beat = 0
    /// The open tab (0 대화, 1 활동, 2 나) and the request card the chat should scroll to: 확인 rows jump here.
    @Published var tab = UserDefaults.standard.integer(forKey: "tab")   // `-tab N` lands in UserDefaults
    @Published var focus: String?
    /// What the owner decided or changed in this session, with the outcome the agent reported afterwards.
    @Published private(set) var log: [Decision] = []
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
        if s.chat.filter({ $0.who == "agent" }).count != agentLines { beat += 1; settle() }
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
        #if DEBUG
        // `-demo-flow`: plays 확인 → card → 허용 → 활동 by itself, so `xcrun simctl io screenshot` can check it
        // without taps (Xcode 27's DeviceHub opens no window to click). Demo data only; never in a release build.
        if ProcessInfo.processInfo.arguments.contains("-demo-flow") {
            DispatchQueue.main.asyncAfter(deadline: .now() + 5) { [weak self] in self?.show(self?.firstPendingID) }
            DispatchQueue.main.asyncAfter(deadline: .now() + 8) { [weak self] in
                guard let self, let c = self.consent else { return }
                self.answer(consent: c, approved: true)
                self.tab = 1
            }
        }
        #endif
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
                settle()
            }
            if let i = sending.firstIndex(of: text) { sending.remove(at: i) }
        }
    }

    /// Sends what the owner typed, as a thread reply when a card is selected.
    func sendDraft(_ raw: String) {
        let text = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        send(replyTo.map { OwnerTools.threadReply($0, text) } ?? text)
        replyTo = nil
    }

    /// Requests waiting for the owner: the MeshKit consent first (the agent is blocked on it), then questions.
    var pendingCount: Int { questions.count + (consent == nil ? 0 : 1) }
    var firstPendingID: String? { consent.map { "consent-\($0.id)" } ?? questions.first.map { "q-\($0.id)" } }

    /// Opens the chat on a request card (the 확인 button and the 확인 필요 rows).
    func show(_ id: String?) {
        withAnimation(.easeOut(duration: 0.2)) { tab = 0 }
        focus = id
    }

    func answer(consent call: PendingCall, approved: Bool) {
        handledConsents.insert(call.id)
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        let scope = call.argPairs.map { "\($0.0): \($0.1)" }.joined(separator: ", ")
        log.insert(Decision(kind: .consent, title: call.name, choice: approved ? "이번 1회 허용" : "이번 요청 거절",
                            details: [("실행할 작업", call.name), ("적용 범위", "이번 1회" + (scope.isEmpty ? "" : " · " + scope))],
                            status: approved ? .running : .declined, after: lastAgentTS), at: 0)
        if isDemo {
            guard approved else { return }
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { [weak self] in
                guard let self else { return }
                self.state.chat.append(ChatMessage(who: "agent", text: "DailyMart에 우유를 주문했어요. 영수증 rcpt-demo01을 확인했습니다.",
                                                   ts: Date().timeIntervalSince1970))
                self.beat += 1
                self.settle()
            }
            return
        }
        Task {
            do { try await session?.consent(call, approved: approved) } catch { self.error = String(describing: error) }
        }
    }

    func answer(question q: OwnerQuestion, with text: String) {
        let t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !t.isEmpty else { return }
        questions.removeAll { $0.id == q.id }
        log.insert(Decision(kind: .question, title: q.question, choice: t, details: [("질문", q.question), ("내 답", t)],
                            status: .running, after: lastAgentTS), at: 0)
        send(OwnerTools.answerMessage(q, t))
    }

    func save(limits new: OwnerLimits) {
        let old = limits
        store.save(new)
        limits = store.load()
        let changes: [(String, String, String)] = [
            ("한 번 최대 송금", old.maxPayPerCall.formatted(), new.maxPayPerCall.formatted()),
            ("하루 최대 송금", old.maxPayPerDay.formatted(), new.maxPayPerDay.formatted()),
            ("남길 말", old.note.isEmpty ? "없음" : old.note, new.note.isEmpty ? "없음" : new.note),
        ]
        let rows = changes.filter { $0.1 != $0.2 }.map { ($0.0, "\($0.1) → \($0.2)") }
        guard !rows.isEmpty else { return }
        log.insert(Decision(kind: .limits, title: "한도 변경", choice: "\(rows.count)개 항목",
                            details: rows + [("변경한 사람", "주인 · 이 iOS 앱")], status: .done, after: 0), at: 0)
    }

    private var lastAgentTS: Double { state.chat.last { $0.who == "agent" }?.ts ?? 0 }

    /// A running decision is settled by the agent's next chat line: the kit hands the MeshKit receipt (or the
    /// owner's answer) to the agent only, so that line is the first place the app can see the outcome.
    // ponytail: words in the reply decide 완료/실패; if the kit ever exposes per-call results in /api/state, read those instead.
    private func settle() {
        for i in log.indices where log[i].status == .running {
            guard let reply = state.chat.first(where: { $0.who == "agent" && $0.ts > log[i].after }) else { continue }
            let failed = ["실패", "오류", "못 했", "못했", "error", "denied", "거절됐"].contains { reply.text.lowercased().contains($0) }
            log[i].status = failed ? .failed : .done
            log[i].result = reply.text
        }
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

/// One thing the owner decided (a consent, an answer) or changed (limits), shown in 활동.
struct Decision: Identifiable {
    enum Kind { case consent, question, limits }
    enum Status { case running, done, failed, declined }

    let id = UUID()
    let kind: Kind
    let title: String
    let choice: String
    let details: [(String, String)]
    var status: Status
    /// The agent chat line that settles it must come after this time.
    let after: Double
    var result: String?
    let at = Date()
}
