import Foundation

/// The 12 assistant characters (asset/AI_Assistant_Character_Design_12.md). Images live in
/// Assets.xcassets/Characters/<rawValue> as template images: black body, transparent eyes, so they invert in dark mode.
public enum AgentCharacter: String, CaseIterable, Identifiable, Sendable {
    case teum, kkwemi, cheungcheung, ppichim, galqui, doegam, batchim, eotgallim, hoga, deulchang, matpyo, gyeonbon

    public var id: String { rawValue }
    public var asset: String { "Characters/\(rawValue)" }

    public var name: String {
        switch self {
        case .teum: return "틈"
        case .kkwemi: return "꿰미"
        case .cheungcheung: return "층층"
        case .ppichim: return "삐침"
        case .galqui: return "갈퀴"
        case .doegam: return "되감"
        case .batchim: return "받침"
        case .eotgallim: return "엇갈림"
        case .hoga: return "호가"
        case .deulchang: return "들창"
        case .matpyo: return "맞표"
        case .gyeonbon: return "견본"
        }
    }

    public var role: String {
        switch self {
        case .teum: return "빈 시간 찾기"
        case .kkwemi: return "자료 연결"
        case .cheungcheung: return "우선순위 정리"
        case .ppichim: return "알림"
        case .galqui: return "자료 분류"
        case .doegam: return "이전 작업 이어가기"
        case .batchim: return "확인 대기"
        case .eotgallim: return "두 선택지 비교"
        case .hoga: return "가격 협상"
        case .deulchang: return "재고와 매입 창"
        case .matpyo: return "정산 확인"
        case .gyeonbon: return "구매 후보 비교"
        }
    }

    /// The four made for the OuroLabs Market app come first in the picker.
    public static let marketFirst: [AgentCharacter] =
        [.hoga, .deulchang, .matpyo, .gyeonbon, .teum, .kkwemi, .cheungcheung, .ppichim, .galqui, .doegam, .batchim, .eotgallim]

    /// Which character stands for an agent move in the activity feed (the spec's role of each character).
    public static func forMove(_ action: String) -> AgentCharacter {
        let a = action.lowercased()
        if a.hasPrefix("mesh_") || a.hasPrefix("app_") { return .batchim }
        if a == "reply" || a.contains("a2a") || a.contains("haggle") || a.contains("quote") { return .hoga }
        if a == "forge_tool" { return .cheungcheung }
        if a == "read_tool" { return .kkwemi }
        if a == "write_note" || a.contains("memory") || a.contains("recall") { return .doegam }
        if a == "sleep" { return .teum }
        if a.contains("pay") || a.contains("settle") || a.contains("ledger") { return .matpyo }
        if a.contains("stock") || a.contains("restock") || a.contains("wholesale") || a.contains("price") { return .deulchang }
        if a.contains("catalog") || a.contains("compare") || a.contains("market") || a.contains("board") { return .gyeonbon }
        if a.contains("card") { return .galqui }
        return .ppichim
    }
}

/// Sample state for the demo mode, so the design can be checked in the simulator without a running agent.
public enum DemoData {
    public static let owner = "owner-demo"

    public static func state(now: Double = Date().timeIntervalSince1970) -> MiniAppState {
        var s = MiniAppState(agent: "싸다싸")
        s.chat = [
            ChatMessage(who: owner, text: "오늘 장사 어때?", ts: now - 900),
            ChatMessage(who: "agent", text: "오늘 23건 팔았어요. 순이익은 +412,300 credits이고, 소파가 제일 잘 나가요.", ts: now - 880),
            ChatMessage(who: owner, text: "수수료 계산은 맞게 하고 있지?", ts: now - 600),
            ChatMessage(who: "agent", text: "네. /api/chain에서 읽은 대로 1% + 210으로 계산해요. 첫 정산이 통과해서 pay_limit도 올렸어요.", ts: now - 585),
        ]
        s.moves = [
            Move(action: "reply", thought: "손님 김○○님이 의자 가격을 물어 와서 같은 등급 시장가에 맞춰 답함"),
            Move(action: "pay_guard", thought: "도매 매입 48,000 credits: 1회 한도 안, 하루 누적 312,000"),
            Move(action: "restock", thought: "지난 24시간 판매 기준으로 소파 3개, 우유 10개 매입"),
            Move(action: "forge_tool", thought: "stock_and_price v3: C등급 파손률을 가격에 반영"),
            Move(action: "write_note", thought: "RULES에 수수료 공식 확정, FAILED에 503 재시도 기록"),
            Move(action: "sleep", thought: "새 공급 창까지 6분, 메시지가 오면 깨어남"),
        ]
        s.forged = ["a2a_handler": "손님과 에이전트 메시지에 코드로 바로 답함", "market_call": "entity card의 http로 시장 호출",
                    "pay_guard": "모든 송금의 관문: 한도와 수수료 확인", "stock_and_price": "판매 기록으로 매입·가격 결정",
                    "memory": "notes.md를 RULES/NOW/FAILED로 정리"]
        s.appTools = ["app_show_card": "카드 보여주기", "app_owner_limits": "주인 한도", "app_ask_owner": "주인에게 묻기",
                      "mesh_shop_catalog": "싸다싸 가게 상품 목록", "mesh_grocery_purchase_essentials": "DailyMart 장보기"]
        return s
    }

    public static func consent(now: Double = Date().timeIntervalSince1970) -> PendingCall {
        PendingCall(id: "demo-consent", kind: "consent", name: "grocery.purchase_essentials",
                    args: .object(["items": .string("우유"), "budget_krw": .string("100")]), at: now)
    }

    public static let question = OwnerQuestion(id: "demo01", question: "소파 재고를 10개 더 살까요? 약 7M credits가 듭니다.",
                                               options: ["사도 돼", "5개만", "하지 마"])

    public static let card = OwnerCard(title: "오늘 요약", body: "거래 23건 · 순이익 +412,300 credits\n가장 많이 팔린 것: 소파 A등급",
                                       ts: Date().timeIntervalSince1970 - 300)

    public static let replies = [
        "확인했어요. 지금 시장 상황을 보고 바로 알려드릴게요.",
        "좋아요. 다음 공급 창에서 그렇게 할게요.",
        "지금 잔고는 2,184,000 credits, 학생 중 순위는 9위예요.",
    ]
}
