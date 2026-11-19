import Foundation

/// What `GET /api/state` of the kit's mini app returns (scripts/round4/miniapp.py, `get_state`).
public struct MiniAppState: Decodable, Sendable {
    public var agent: String
    public var chat: [ChatMessage]
    public var calls: [PendingCall]
    public var moves: [Move]
    public var appTools: [String: String]
    public var forged: [String: String]

    enum CodingKeys: String, CodingKey {
        case agent, chat, calls, moves, forged
        case appTools = "app_tools"
    }

    public init(from d: Decoder) throws {
        let c = try d.container(keyedBy: CodingKeys.self)
        agent = (try? c.decode(String.self, forKey: .agent)) ?? "agent"
        chat = (try? c.decode([ChatMessage].self, forKey: .chat)) ?? []
        calls = (try? c.decode([PendingCall].self, forKey: .calls)) ?? []
        moves = (try? c.decode([Move].self, forKey: .moves)) ?? []
        appTools = (try? c.decode([String: String].self, forKey: .appTools)) ?? [:]
        forged = (try? c.decode([String: String].self, forKey: .forged)) ?? [:]
    }

    public init(agent: String = "agent") {
        self.agent = agent; chat = []; calls = []; moves = []; appTools = [:]; forged = [:]
    }

    /// MeshKit calls waiting for a person to allow or refuse them.
    public var consents: [PendingCall] { calls.filter { $0.kind == "consent" } }
}

public struct ChatMessage: Decodable, Hashable, Identifiable, Sendable {
    public let who: String
    public let text: String
    public let ts: Double
    public var id: String { "\(ts)|\(who)|\(text.count)|\(text.prefix(24))" }
}

/// A call from the agent that the page (here: this app) must answer: a page tool, or a MeshKit consent.
public struct PendingCall: Decodable, Hashable, Identifiable, Sendable {
    public let id: String
    public let kind: String          // "tool" or "consent"
    public let name: String
    public let args: JSONValue
    public let at: Double

    public var argPairs: [(String, String)] {
        if case .object(let o) = args { return o.keys.sorted().map { ($0, o[$0]!.display) } }
        return []
    }
}

public struct Move: Decodable, Hashable, Sendable {
    public let action: String
    public let thought: String
}

public struct ChatReply: Decodable, Sendable {
    public let reply: String?
    public let state: String?
}

/// A card the agent asked to show (app_show_card).
public struct OwnerCard: Hashable, Identifiable, Sendable {
    public let id = UUID()
    public let title: String
    public let body: String
    public let ts: Double
    /// The short id the agent gets back from app_show_card and sees in thread replies.
    public var tag: String { String(id.uuidString.prefix(6)).lowercased() }
}

/// A question the agent asked the owner (app_ask_owner). The answer goes back as a chat message.
public struct OwnerQuestion: Hashable, Identifiable, Sendable {
    public let id: String
    public let question: String
    public let options: [String]
}

/// The owner's limits the agent reads with app_owner_limits.
public struct OwnerLimits: Codable, Hashable, Sendable {
    public var maxPayPerCall: Int = 20_000
    public var maxPayPerDay: Int = 200_000
    public var buyerAllowed: Bool = true
    public var note: String = ""
    public var setAt: String = ""

    public init() {}

    public var asJSON: JSONValue {
        .object(["max_pay_per_call": .number(Double(maxPayPerCall)), "max_pay_per_day": .number(Double(maxPayPerDay)),
                 "buyer_allowed": .bool(buyerAllowed), "note": .string(note), "set_at": .string(setAt),
                 "source": .string("owner, in the iOS app")])
    }
}
