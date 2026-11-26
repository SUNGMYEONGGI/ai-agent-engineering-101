import Foundation

/// The tools this app gives the agent (the same three as the web page in app/index.html).
/// The kit waits for each answer inside its polling loop, so every handler returns at once.
public final class OwnerTools: @unchecked Sendable {
    public static let offers: [(name: String, description: String)] = [
        ("show_card", "show the owner a card in the chat (a deal, a daily summary, a warning); args {title, body}. "
            + "Returns the card id. The owner may reply to a card: that chat message starts with "
            + "\"[스레드 답장 · 카드 <id>: ...]\"."),
        ("owner_limits", "the owner's current limits: {max_loss_per_day, max_pay_per_call, max_pay_per_day (credits), "
            + "daily_tokens, note, set_at}. Read before paying or cutting a loss; stay inside them. The same values are "
            + "in owner_limits.json. No args."),
        ("ask_owner", "ask the owner a question when a decision is risky or unclear (a large payment, a new strategy). "
            + "args {question, options (optional list of short answers; write each as the action it allows, with the "
            + "item and the amount, e.g. \"소파 5개까지 매입 승인\", \"이번 요청 거절\")}. Returns at once; the answer arrives later as a "
            + "chat message from the owner starting with \"[주인 답변]\". Do not wait for it: keep to the safe choice "
            + "until it comes."),
    ]

    private let limitsStore: LimitsStore
    public var onCard: (OwnerCard) -> Void = { _ in }
    public var onQuestion: (OwnerQuestion) -> Void = { _ in }

    public init(limitsStore: LimitsStore = UserDefaultsLimits()) {
        self.limitsStore = limitsStore
    }

    /// Runs one page tool call. Unknown tools answer with an error string, like the web SDK does.
    public func handle(_ call: PendingCall) -> JSONValue {
        switch call.name {
        case "app_show_card":
            let card = OwnerCard(title: call.args["title"]?.display ?? "", body: call.args["body"]?.display ?? "",
                                 ts: Date().timeIntervalSince1970)
            onCard(card)
            return .object(["shown": .string(card.tag),
                            "note": .string("a reply to this card starts with [스레드 답장 · 카드 \(card.tag): ...]")])
        case "app_owner_limits":
            return limitsStore.load().asJSON
        case "app_ask_owner":
            let q = call.args["question"]?.display.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            guard !q.isEmpty else { return .string("error: question is required") }
            let options = (call.args["options"]?.array ?? []).prefix(6).map(\.display)
            let question = OwnerQuestion(id: String(UUID().uuidString.prefix(6)).lowercased(), question: q,
                                         options: Array(options))
            onQuestion(question)
            return .object(["asked": .string(question.id),
                            "note": .string("the owner sees it now; the answer comes as a chat message starting with [주인 답변]")])
        default:
            return .string("error: this app has no tool \(call.name)")
        }
    }

    /// The chat message that carries the owner's answer back to the agent.
    public static func answerMessage(_ q: OwnerQuestion, _ answer: String) -> String {
        "[주인 답변] (질문 \(q.id): \(q.question)) \(answer)"
    }

    /// A thread reply to a card (from OCTO CREW's transcript.ts): the first line names the card, so the agent knows
    /// which deal or warning the owner means. Same format as the web page.
    public static func threadReply(_ c: OwnerCard, _ text: String) -> String {
        let flat = { (s: String) in s.split(whereSeparator: \.isWhitespace).joined(separator: " ") }
        return "[스레드 답장 · 카드 \(c.tag): \(flat(c.title)) — \(String(flat(c.body).prefix(120)))]\n\(text)"
    }

    /// Splits a sent message into the quoted card line (nil when it is not a thread reply) and the owner's words.
    public static func splitThread(_ text: String) -> (quote: String?, body: String) {
        let head = "[스레드 답장 · 카드 "
        guard text.hasPrefix(head), let nl = text.firstIndex(of: "\n"), text[text.index(before: nl)] == "]",
              let colon = text[..<nl].range(of: ": ") else { return (nil, text) }
        return (String(text[colon.upperBound..<text.index(before: nl)]), String(text[text.index(after: nl)...]))
    }
}

public protocol LimitsStore: Sendable {
    func load() -> OwnerLimits
    func save(_ limits: OwnerLimits)
}

public struct UserDefaultsLimits: LimitsStore {
    private let key = "ssadassa.limits"
    public init() {}

    public func load() -> OwnerLimits {
        guard let data = UserDefaults.standard.data(forKey: key),
              let v = try? JSONDecoder().decode(OwnerLimits.self, from: data) else { return OwnerLimits() }
        return v
    }

    public func save(_ limits: OwnerLimits) {
        var v = limits
        if v.setAt.isEmpty { v.setAt = ISO8601DateFormatter().string(from: Date()) }   // the server's copy keeps its own
        UserDefaults.standard.set(try? JSONEncoder().encode(v), forKey: key)
    }
}
