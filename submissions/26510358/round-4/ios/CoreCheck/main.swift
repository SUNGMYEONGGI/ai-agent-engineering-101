import Foundation
import SsadassaCore

// Drives the app's Core against a running mini app (ops/preview_app.py, or the kit with --app), the way the iOS app
// does: offer the owner tools, poll, answer page-tool calls, allow a MeshKit consent. Each agent-side call is made
// as a "/tool ..." chat message, which the preview's stub agent turns into the same tool call the real agent makes.
//   swift run CoreCheck "http://127.0.0.1:18800/?k=<code>"

var fails: [String] = []
func check(_ name: String, _ ok: Bool, _ detail: String = "") {
    print("\(ok ? "PASS" : "FAIL")  \(name)  \(detail.prefix(160))")
    if !ok { fails.append(name) }
}

guard CommandLine.arguments.count > 1, let link = AppLink(CommandLine.arguments[1]) else {
    print("usage: CoreCheck \"<[app] open link>\""); exit(2)
}
check("AppLink parses the kit's line", AppLink("[app] open https://a-b.trycloudflare.com/?k=XYZ")?.accessCode == "XYZ"
      && AppLink("[app] open https://a-b.trycloudflare.com/?k=XYZ")?.base.absoluteString == "https://a-b.trycloudflare.com")

final class Box: @unchecked Sendable { var questions: [OwnerQuestion] = []; var cards: [OwnerCard] = []; var state: MiniAppState?; var error: String? }
let box = Box()
let client = MiniAppClient(link: link)
let tools = OwnerTools()
tools.onQuestion = { box.questions.append($0) }
tools.onCard = { box.cards.append($0) }
let session = MiniAppSession(client: client, tools: tools, interval: 0.5)
session.onState = { box.state = $0 }
session.onError = { box.error = $0 }

let bad = MiniAppClient(link: AppLink(link.base.absoluteString + "/?k=wrong")!)
do { _ = try await bad.state(); check("wrong access code is refused", link.accessCode == nil) }
catch { check("wrong access code is refused", "\(error)".contains("접근 코드")) }

session.start()
try await Task.sleep(nanoseconds: 2_000_000_000)
check("poll works", box.state != nil, box.error ?? "")
let toolNames = Set(box.state?.appTools.keys.map { $0 } ?? [])
check("owner tools offered", ["app_show_card", "app_owner_limits", "app_ask_owner"].allSatisfy(toolNames.contains),
      toolNames.sorted().joined(separator: ","))

let r1 = try await client.chat("/tool app_owner_limits {}", user: "corecheck")
check("agent reads owner_limits", r1.reply?.contains("max_pay_per_call") == true, r1.reply ?? "nil")

let r2 = try await client.chat(#"/tool app_show_card {"title":"요약","body":"거래 3건"}"#, user: "corecheck")
check("agent shows a card", r2.reply == "shown" && box.cards.last?.title == "요약", r2.reply ?? "nil")

let r3 = try await client.chat(#"/tool app_ask_owner {"question":"소파 더 살까요?","options":["사도 돼","하지 마"]}"#, user: "corecheck")
check("agent asks the owner", r3.reply?.contains("asked") == true && box.questions.last?.options == ["사도 돼", "하지 마"],
      r3.reply ?? "nil")
if let q = box.questions.last {
    let msg = OwnerTools.answerMessage(q, "하지 마")
    _ = try await client.chat(msg, user: "owner")
    let s = try await client.state()
    check("owner answer reaches the agent's chat", s.chat.contains { $0.text == msg })
}

if box.state?.appTools["mesh_shop_catalog"] != nil {
    async let reply = client.chat(#"/tool mesh_shop_catalog {"query":"의자"}"#, user: "corecheck")
    var consented = false
    for _ in 0..<40 {
        try await Task.sleep(nanoseconds: 500_000_000)
        if let c = box.state?.consents.first {
            check("consent sheet data", c.name == "shop.catalog" && c.argPairs.first?.0 == "query", "\(c.argPairs)")
            try await session.consent(c, approved: true); consented = true; break
        }
    }
    let r4 = try await reply
    check("MeshKit allow returns a verified receipt", consented && r4.reply?.contains("\"receipt\"") == true, r4.reply ?? "nil")
} else {
    print("SKIP  MeshKit consent (no mesh_shop_catalog tool on this app)")
}
session.stop()
print(fails.isEmpty ? "\nALL PASS" : "\nFAILED: \(fails.joined(separator: ", "))")
exit(fails.isEmpty ? 0 : 1)
