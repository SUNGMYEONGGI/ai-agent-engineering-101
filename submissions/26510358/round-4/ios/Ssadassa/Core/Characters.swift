import Foundation

/// The characters the app actually uses, one per job. The 12 designs live in asset/AI_Assistant_Character_Design_12.md
/// (images in asset/AI_Assistant_Character_Images_12/); a design joins this enum, and its image joins
/// Assets.xcassets/Characters/, only when an agent or screen starts to use it. Images are template images: black body,
/// transparent eyes, so they invert in dark mode.
public enum AgentCharacter: String, CaseIterable, Identifiable, Sendable {
    /// 호가: the agent itself (chat, cards, every market move).
    case hoga
    /// 엇갈림: a question the agent asks the owner (app_ask_owner).
    case eotgallim
    /// 받침: an outside app waiting for the owner's consent (MeshKit, app_ tools).
    case batchim

    public var id: String { rawValue }
    public var asset: String { "Characters/\(rawValue)" }

    public var name: String {
        switch self {
        case .hoga: return "호가"
        case .eotgallim: return "엇갈림"
        case .batchim: return "받침"
        }
    }

    public var role: String {
        switch self {
        case .hoga: return "가게 운영 에이전트"
        case .eotgallim: return "주인에게 묻기"
        case .batchim: return "확인 대기"
        }
    }

    /// The agents the owner can pick for the chat. One agent today; the next agent adds its character here.
    public static let agents: [AgentCharacter] = [.hoga]

    /// Which character stands for an agent move in the activity feed.
    public static func forMove(_ action: String) -> AgentCharacter {
        let a = action.lowercased()
        if a.hasPrefix("mesh_") || a.hasPrefix("app_") { return .batchim }
        return .hoga
    }
}

/// Sample state for the demo mode, so the design can be checked in the simulator without a running agent.
public enum DemoData {
    public static let owner = "owner-demo"

    public static func state(now: Double = Date().timeIntervalSince1970) -> MiniAppState {
        var s = MiniAppState(agent: "Hermes")
        s.chat = [
            ChatMessage(who: owner, text: "오늘 장사 어때?", ts: now - 900),
            ChatMessage(who: "agent", text: "오늘 장사를 카드로 정리했어요.", ts: now - 880),
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
                      "mesh_shop_catalog": "Hermes Shop 상품 목록", "mesh_grocery_purchase_essentials": "DailyMart 장보기"]
        return s
    }

    public static func consent(now: Double = Date().timeIntervalSince1970) -> PendingCall {
        PendingCall(id: "demo-consent", kind: "consent", name: "grocery.purchase_essentials",
                    args: .object(["items": .string("우유"), "budget_krw": .string("100")]), at: now)
    }

    public static let question = OwnerQuestion(id: "demo01", question: "소파 재고를 10개 더 살까요? 약 7M credits가 듭니다.",
                                               options: ["소파 10개 매입 승인", "5개까지만 매입", "이번 요청 거절"])

    public static let card = OwnerCard(title: "오늘 요약", body: "거래 23건 · 순이익 +412,300 credits\n가장 많이 팔린 것: 소파 A등급",
                                       ts: Date().timeIntervalSince1970 - 879)

    /// A desk as the agent would leave it: blocked at 문의 for 3 h, one open experiment, the winners table.
    public static func dash(now: Date = Date()) -> Dash {
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_US_POSIX"); f.timeZone = TimeZone(identifier: "Asia/Seoul")
        f.dateFormat = "yyyy-MM-dd HH:mm"
        let at = f.string(from: now.addingTimeInterval(-25 * 60)), day = String(at.prefix(10))
        f.dateFormat = "HH:mm"
        let judge = f.string(from: now.addingTimeInterval(35 * 60))
        let json = """
        {"funnel": {"at": "\(at)", "m": 81, "i": 0, "c": 0, "s": 0, "today": 2, "blocked": "i"},
         "stages": [["m", "시장 정산"], ["i", "문의"], ["c", "결제서"], ["s", "정산"]],
         "experiments": [
          {"at": "\(day) 12:10", "stage": "i", "diff": "카드가 긴 상품명으로 시작", "change": "짧은 명사 카드", "judge": "13:10", "result": "81/0/0/0 reverted", "state": "reverted"},
          {"at": "\(day) 13:15", "stage": "i", "diff": "재고 폭 13라인", "change": "25라인으로 확대", "judge": "14:15", "result": "90/2/1/1 kept", "state": "kept"},
          {"at": "\(at)", "stage": "i", "diff": "계란 가격 시장가 +14%", "change": "계란 B 중앙가로", "judge": "\(judge)", "result": "", "state": "open"}],
         "winners": [
          {"shop": "yms979", "card": "계란 20구 · 취나물 · 총각김치 2kg · 값은 정가보다 쌉니다", "units": "350", "lines": "30", "gap": "-5%"},
          {"shop": "dongne", "card": "둥굴레차 · 두부 · 쌀 2kg", "units": "210", "lines": "24", "gap": "-2%"},
          {"shop": "maeil", "card": "신선 계란, 김치", "units": "180", "lines": "19", "gap": "0%"},
          {"shop": "우리", "card": "계란 B 특란 20구 신선 무항생제 농장 직송", "units": "43", "lines": "13", "gap": "+14%"}],
         "tokens": {"today": 9485381, "cap": 15000000, "per_settle": 4742690, "settles_today": 2},
         "loss_today": 26000,
         "limits": {"max_loss_per_day": 30000, "max_pay_per_call": 20000, "max_pay_per_day": 200000, "daily_tokens": 15000000, "note": ""},
         "alerts": [{"kind": "stuck", "key": "demo-stuck", "text": "FUNNEL이 3시간째 '문의' 단계에서 멈춰 있습니다."},
                    {"kind": "loss", "key": "demo-loss", "text": "오늘 처분 손실 26,000 / 한도 30,000 credits (80% 이상)."}]}
        """
        return try! Dash.decode(Data(json.utf8))
    }

    public static let replies = [
        "확인했어요. 지금 시장 상황을 보고 바로 알려드릴게요.",
        "좋아요. 다음 공급 창에서 그렇게 할게요.",
        "지금 잔고는 2,184,000 credits, 학생 중 순위는 9위예요.",
    ]
}
