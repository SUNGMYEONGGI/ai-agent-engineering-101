import Foundation

/// What `GET /owner/dash` returns (ops/owner_desk.py, served next to the kit on the same host and access cookie):
/// the FUNNEL, EXP, WIN and LOSS lines the agent writes in notes.md, the shim's token use, the owner's limits and the
/// three alerts (funnel stuck 2 h, loss at 80%, token cap).
public struct Dash: Decodable, Sendable {
    public struct Funnel: Decodable, Sendable {
        public let at: String
        public let m, i, c, s: Int
        public let today: Int?
        /// The first stage that is 0 while the one before it is not ("i", "c" or "s").
        public let blocked: String?

        public func value(_ key: String) -> Int {
            switch key { case "m": return m; case "i": return i; case "c": return c; default: return s }
        }
    }

    public struct Experiment: Decodable, Hashable, Identifiable, Sendable {
        public let at: String
        public let stage, diff, change, judge, result: String?
        public let state: String                  // open, kept, reverted
        public let veto: String?                  // stop, revert: the owner's veto
        public var id: String { at }
        public var isOpen: Bool { state == "open" && veto == nil }
    }

    public struct Winner: Decodable, Hashable, Sendable {
        public let shop, card, units, lines, gap: String
        public var isUs: Bool { shop == "우리" }
    }

    public struct Tokens: Decodable, Sendable {
        public let today: Int
        public let cap: Int
        public let perSettle: Int?
        public let settlesToday: Int?
    }

    public struct Alert: Decodable, Hashable, Identifiable, Sendable {
        public let kind, key, text: String
        public var id: String { key }
    }

    public let funnel: Funnel?
    public let stages: [[String]]
    public let experiments: [Experiment]
    public let winners: [Winner]
    public let tokens: Tokens
    public let lossToday: Int
    public let limits: OwnerLimits
    public let alerts: [Alert]

    public static func decode(_ data: Data) throws -> Dash {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return try d.decode(Dash.self, from: data)
    }

    /// "판정까지 23분" from an experiment's start (KST, as the agent writes it) and its judge time HH:MM.
    public static func judgeLeft(_ e: Experiment, now: Date = Date()) -> String {
        guard let judge = e.judge, judge.count >= 5 else { return "" }
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_US_POSIX")
        f.timeZone = TimeZone(identifier: "Asia/Seoul")
        f.dateFormat = "yyyy-MM-dd HH:mm"
        guard let start = f.date(from: e.at), var end = f.date(from: String(e.at.prefix(10)) + " " + judge.prefix(5)) else { return "" }
        if end < start { end += 86_400 }
        let min = Int((end.timeIntervalSince(now) / 60).rounded())
        return min > 0 ? "판정까지 \(min)분" : "판정 시각 \(judge.prefix(5)) 지남"
    }
}
