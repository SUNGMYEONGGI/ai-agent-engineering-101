import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// The link the kit prints: "[app] open https://<host>/?k=<access code>" (or http://127.0.0.1:8800/ locally).
public struct AppLink: Hashable, Sendable {
    public let base: URL
    public let accessCode: String?

    /// Accepts the bare link or the whole line the kit prints.
    public init?(_ text: String) {
        let text = text.replacingOccurrences(of: "\\", with: "")   // zsh pastes https://h/\?k\=code
        guard let r = text.range(of: #"https?://[^\s"'<>]+"#, options: .regularExpression),
              var comps = URLComponents(string: String(text[r])),
              let scheme = comps.scheme, ["http", "https"].contains(scheme), comps.host != nil else { return nil }
        accessCode = comps.queryItems?.first(where: { $0.name == "k" })?.value
        comps.query = nil
        comps.fragment = nil
        comps.path = ""
        guard let url = comps.url else { return nil }
        base = url
    }
}

public enum MiniAppError: Error, CustomStringConvertible {
    case http(Int, String)
    case noPageToken
    case badResponse

    public var description: String {
        switch self {
        case .http(401, _): return "접근 코드가 맞지 않습니다. kit이 출력한 [app] open 링크를 다시 붙여 넣어 주세요."
        case .http(let code, let body): return "서버 응답 \(code): \(body.prefix(120))"
        case .noPageToken: return "miniapp.js에서 page token을 찾지 못했습니다. kit 버전을 확인해 주세요."
        case .badResponse: return "알 수 없는 응답입니다."
        }
    }
}

/// HTTP client for the kit's mini app API (the same calls miniapp.js makes from the web page).
///
/// Access: the kit's gate accepts a cookie `miniapp_access=<access code>`, so every request carries it; no redirect
/// dance is needed. Page-only calls (offer tools, answer calls) also need the page token that the kit writes into
/// /miniapp.js, which only someone holding the access code can fetch.
public final class MiniAppClient: @unchecked Sendable {
    public let link: AppLink
    private let session: URLSession
    private var pageToken: String?

    public init(link: AppLink) {
        self.link = link
        let cfg = URLSessionConfiguration.ephemeral
        cfg.timeoutIntervalForRequest = 150          // /api/chat waits up to 120 s for the agent
        cfg.httpShouldSetCookies = false
        session = URLSession(configuration: cfg)
    }

    // MARK: API

    public func state() async throws -> MiniAppState {
        try JSONDecoder().decode(MiniAppState.self, from: try await send("GET", "/api/state"))
    }

    /// Sends the owner's message to the agent and waits for its answer (reply is nil when the agent was busy).
    public func chat(_ text: String, user: String) async throws -> ChatReply {
        let body = try JSONEncoder().encode(["text": text, "user": user])
        return try JSONDecoder().decode(ChatReply.self, from: try await send("POST", "/api/chat", body: body))
    }

    /// Gives the agent tools app_<name> that this app answers.
    @discardableResult
    public func offer(_ tools: [(name: String, description: String)]) async throws -> [String] {
        let body = try JSONEncoder().encode(["tools": tools.map { ["name": $0.name, "description": $0.description] }])
        let data = try await send("POST", "/api/offer", body: body, page: true)
        struct Out: Decodable { let offered: [String] }
        return try JSONDecoder().decode(Out.self, from: data).offered
    }

    /// Answers a pending call: a page tool's result, or a MeshKit consent ({"approved": true/false}).
    @discardableResult
    public func answer(_ id: String, result: JSONValue) async throws -> Bool {
        let body = try JSONEncoder().encode(["id": JSONValue.string(id), "result": result])
        let data = try await send("POST", "/api/answer", body: body, page: true)
        struct Out: Decodable { let ok: Bool }
        return try JSONDecoder().decode(Out.self, from: data).ok
    }

    public func consent(_ id: String, approved: Bool) async throws {
        try await answer(id, result: .object(["approved": .bool(approved)]))
    }

    // MARK: transport

    private func token() async throws -> String {
        if let t = pageToken { return t }
        let js = String(decoding: try await send("GET", "/miniapp.js"), as: UTF8.self)
        guard let r = js.range(of: #"'x-page-token':\s*'([^']+)'"#, options: .regularExpression) else {
            throw MiniAppError.noPageToken
        }
        let t = String(js[r]).components(separatedBy: "'").dropLast().last ?? ""
        guard !t.isEmpty else { throw MiniAppError.noPageToken }
        pageToken = t
        return t
    }

    /// The page token changes when the kit restarts; forget it so the next page call fetches the new one.
    public func resetPageToken() { pageToken = nil }

    private func send(_ method: String, _ path: String, body: Data? = nil, page: Bool = false) async throws -> Data {
        var req = URLRequest(url: link.base.appendingPathComponent(String(path.dropFirst())))
        req.httpMethod = method
        if let code = link.accessCode { req.setValue("miniapp_access=\(code)", forHTTPHeaderField: "Cookie") }
        if let body {
            req.httpBody = body
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        if page { req.setValue(try await token(), forHTTPHeaderField: "x-page-token") }
        let (data, resp) = try await data(for: req)
        guard let http = resp as? HTTPURLResponse else { throw MiniAppError.badResponse }
        if http.statusCode == 403 && page { pageToken = nil }
        guard (200..<300).contains(http.statusCode) else {
            throw MiniAppError.http(http.statusCode, String(decoding: data, as: UTF8.self))
        }
        return data
    }

    /// dataTask wrapped for async; works the same on iOS and on Linux (where the corelibs async API is uneven).
    private func data(for req: URLRequest) async throws -> (Data, URLResponse) {
        try await withCheckedThrowingContinuation { cont in
            session.dataTask(with: req) { data, resp, err in
                if let err { cont.resume(throwing: err) }
                else if let data, let resp { cont.resume(returning: (data, resp)) }
                else { cont.resume(throwing: MiniAppError.badResponse) }
            }.resume()
        }
    }
}
