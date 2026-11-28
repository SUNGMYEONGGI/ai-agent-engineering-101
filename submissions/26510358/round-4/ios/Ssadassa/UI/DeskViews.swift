import SwiftUI

/// The first thing on the chat screen: the desk's alerts, the FUNNEL in one line with the blocked stage in red, and
/// today's model tokens. Tapping it opens the desk sheet.
struct DeskStrip: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        if let d = model.dash {
            Button { model.showDesk = true } label: {
                VStack(alignment: .leading, spacing: 8) {
                    if d.limits.isStopped { AlertRow(text: "매입 정지 중: 에이전트는 송금하지 않아요. 나 탭에서 다시 시작할 수 있어요.") }
                    ForEach(d.alerts) { a in AlertRow(text: a.text) }
                    if let f = d.funnel { FunnelLine(funnel: f, stages: d.stages) }
                    else { Text("FUNNEL 줄이 아직 없어요. 에이전트의 다음 실행 뒤에 보여요.").font(Theme.rounded(.caption)).foregroundStyle(Theme.mute) }
                    TokenMeter(tokens: d.tokens)
                    RankLine(market: d.market, until: d.limits.untilEnd(now: model.now))
                }
                .padding(.horizontal, 18).padding(.vertical, 10)
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .buttonStyle(.plain)
            .accessibilityHint("가게 현황 열기")
            .overlay(alignment: .bottom) { Divider() }
        } else if let e = model.deskError {
            Text("현황 서버에 닿지 못했어요. \(e)").font(Theme.rounded(.caption)).foregroundStyle(Theme.mute).lineLimit(2)
                .padding(.horizontal, 18).padding(.vertical, 8)
        }
    }
}

private struct AlertRow: View {
    let text: String
    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: "exclamationmark.circle.fill").foregroundStyle(Theme.fail)
            Text(text).font(Theme.rounded(.footnote, .medium)).foregroundStyle(Theme.ink).multilineTextAlignment(.leading)
            Spacer(minLength: 0)
        }
        .padding(10)
        .background(Theme.fail.opacity(0.12), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

struct FunnelLine: View {
    let funnel: Dash.Funnel
    let stages: [[String]]

    var body: some View {
        HStack(spacing: 4) {
            ForEach(Array(stages.enumerated()), id: \.offset) { i, st in
                if i > 0 { Image(systemName: "arrow.right").font(.system(size: 9, weight: .bold)).foregroundStyle(Theme.mute) }
                let bad = funnel.blocked == st[0]
                HStack(alignment: .firstTextBaseline, spacing: 3) {
                    Text(st.count > 1 ? st[1] : st[0]).font(Theme.rounded(.caption2, bad ? .bold : .regular))
                    Text(funnel.value(st[0]).formatted()).font(Theme.rounded(.subheadline, .bold)).monospacedDigit()
                }
                .foregroundStyle(bad ? Theme.fail : Theme.ink)
                .padding(.horizontal, 7).padding(.vertical, 4)
                .background(bad ? Theme.fail.opacity(0.14) : Theme.soft, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
                .lineLimit(1).minimumScaleFactor(0.8)
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("최근 60분 FUNNEL" + (funnel.blocked.map { ", 막힌 단계 \($0)" } ?? ""))
    }
}

/// 순위 18 / 44, and the time left in the round on the right.
struct RankLine: View {
    let market: Dash.Market?
    let until: String
    var body: some View {
        if market?.rank != nil || !until.isEmpty {
            HStack {
                if let r = market?.rank { Text("순위 **\(r)** / \(market?.of ?? 0)") }
                Spacer()
                if !until.isEmpty { Text(until) }
            }
            .font(Theme.rounded(.caption)).foregroundStyle(Theme.mute).monospacedDigit()
        }
    }
}

struct TokenMeter: View {
    let tokens: Dash.Tokens
    var body: some View {
        let ratio = tokens.cap > 0 ? min(1, Double(tokens.today) / Double(tokens.cap)) : 0
        HStack(spacing: 8) {
            Text(String(format: "토큰 %.1fM / %.1fM", Double(tokens.today) / 1e6, Double(tokens.cap) / 1e6))
            ProgressView(value: ratio).tint(ratio >= 0.8 ? Theme.fail : Theme.mute)
            Text(tokens.perSettle.map { "정산당 \($0.formatted())" } ?? "오늘 정산 0건")
        }
        .font(Theme.rounded(.caption)).foregroundStyle(Theme.mute).monospacedDigit()
    }
}

/// 가게 현황: experiments (the owner can only stop or revert one), the winners table, tokens per settle.
struct DeskSheet: View {
    @EnvironmentObject var model: AppModel
    @State private var confirm: (Dash.Experiment, Bool)?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                Text("가게 현황").font(Theme.rounded(.title2, .bold)).padding(.top, 20)
                if let d = model.dash {
                    Text(subtitle(d)).font(Theme.rounded(.footnote)).foregroundStyle(Theme.mute)
                    if let f = d.funnel { FunnelLine(funnel: f, stages: d.stages) }
                    agentLimits(d)
                    experiments(d)
                    winners(d)
                    tokens(d)
                    checks(d)
                } else {
                    Text(model.deskError ?? "불러오는 중").font(Theme.rounded(.footnote)).foregroundStyle(Theme.mute)
                }
            }
            .padding(.horizontal, 18).padding(.bottom, 30)
        }
        .background(Theme.paper.ignoresSafeArea())
        .presentationDetents([.large, .medium])
        .confirmationDialog(confirm.map { $0.1 ? "이 실험을 되돌릴까요?" : "이 실험을 중단할까요?" } ?? "",
                            isPresented: Binding(get: { confirm != nil }, set: { if !$0 { confirm = nil } }),
                            titleVisibility: .visible) {
            if let (e, revert) = confirm {
                Button(revert ? "되돌리기" : "중단", role: .destructive) { model.veto(e, revert: revert); confirm = nil }
            }
        } message: {
            Text("에이전트는 다음 실행에서 이 실험을 \(confirm?.1 == true ? "되돌리고" : "멈추고") 같은 변경을 다시 하지 않아요.")
        }
    }

    private func subtitle(_ d: Dash) -> String {
        (d.funnel.map { "FUNNEL \($0.at) 기준 (최근 60분)" } ?? "FUNNEL 없음")
            + " · 오늘 처분 손실 \(d.lossToday.formatted()) / \(d.limits.maxLossPerDay.formatted()) credits"
    }

    private func experiments(_ d: Dash) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            SectionTitle(text: "실험")
            if d.experiments.isEmpty { empty("아직 없어요. 에이전트가 EXP 줄을 쓰면 여기에 보여요.") }
            ForEach(d.experiments.reversed()) { e in
                SoftCard(padding: 14) {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text("\(e.at) · \(d.stages.first { $0.first == e.stage }?.last ?? e.stage ?? "")").font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
                            Spacer()
                            tag(e)
                        }
                        field("가설", e.diff)
                        field("바꾼 것", e.change)
                        if e.isOpen { field("판정", Dash.judgeLeft(e, now: model.now)) } else { field("결과", e.result) }
                        if e.isOpen {
                            HStack(spacing: 8) {
                                Button("중단") { confirm = (e, false) }.buttonStyle(PillButtonStyle(filled: false))
                                Button("되돌리기") { confirm = (e, true) }.buttonStyle(PillButtonStyle(filled: false))
                            }
                            .padding(.top, 4)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
        }
    }

    private func tag(_ e: Dash.Experiment) -> some View {
        let (text, color): (String, Color) = e.veto.map { ("주인 거부: \($0 == "stop" ? "중단" : "되돌리기")", Theme.fail) }
            ?? [("open", ("진행 중", Theme.warn)), ("kept", ("유지", Theme.ok)), ("reverted", ("되돌림", Theme.fail))]
                .first { $0.0 == e.state }?.1 ?? (e.state, Theme.mute)
        return Text(text).font(Theme.rounded(.caption, .bold)).foregroundStyle(color)
    }

    private func winners(_ d: Dash) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            SectionTitle(text: "잘 팔리는 가게와 비교")
            if d.winners.isEmpty { empty("아직 없어요. 에이전트의 다음 REVIEW 뒤에 보여요.") }
            ForEach(d.winners, id: \.self) { w in
                SoftCard(padding: 14) {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text(w.shop).font(Theme.rounded(.subheadline, .bold))
                            Spacer()
                            Text("재고 \(w.units) · \(w.lines)품목 · \(w.gap)").font(Theme.rounded(.caption, w.isUs ? .bold : .regular))
                                .foregroundStyle(w.isUs ? Theme.ink : Theme.mute).monospacedDigit()
                        }
                        Text(w.card).font(Theme.rounded(.footnote)).foregroundStyle(Theme.ink)
                    }
                }
                .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).stroke(w.isUs ? Theme.ink : .clear, lineWidth: 1))
            }
        }
    }

    private func tokens(_ d: Dash) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            SectionTitle(text: "모델 토큰")
            SoftCard(padding: 14) {
                VStack(alignment: .leading, spacing: 6) {
                    TokenMeter(tokens: d.tokens)
                    Text(d.tokens.perSettle.map { "오늘 정산 \(d.tokens.settlesToday ?? 0)건, 1건당 \($0.formatted()) 토큰" }
                         ?? "오늘 정산 0건: 쓴 토큰이 아직 판매로 이어지지 않았어요.")
                        .font(Theme.rounded(.footnote)).foregroundStyle(Theme.ink)
                }
            }
        }
    }

    /// The agent's operating limits against the owner's ceilings, as bars.
    private func agentLimits(_ d: Dash) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            SectionTitle(text: "에이전트 운영 한도")
            SoftCard(padding: 14) {
                if let a = d.agentLimits {
                    VStack(alignment: .leading, spacing: 10) {
                        ForEach([("매입/일", "max_pay_per_day", d.limits.maxPayPerDay), ("매입/회", "max_pay_per_call", d.limits.maxPayPerCall),
                                 ("처분 손실/일", "max_loss_per_day", d.limits.maxLossPerDay)], id: \.1) { label, key, ceil in
                            let v = a.value(key) ?? 0
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    Text(label).font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
                                    Spacer()
                                    Text("**\(v.formatted())** / \(ceil.formatted())").font(Theme.rounded(.caption)).monospacedDigit()
                                }
                                GeometryReader { g in
                                    ZStack(alignment: .leading) {
                                        Capsule().fill(Theme.soft)
                                        Capsule().fill(Theme.ink).frame(width: ceil > 0 ? g.size.width * min(1, Double(v) / Double(ceil)) : 0)
                                    }
                                }
                                .frame(height: 8)
                            }
                            .accessibilityElement(children: .combine)
                        }
                        Text([a.reason.isEmpty ? nil : a.reason, a.ageMin.map { "\($0)분 전 설정" }].compactMap { $0 }.joined(separator: ", "))
                            .font(Theme.rounded(.footnote)).foregroundStyle(Theme.mute)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                } else {
                    empty("아직 정하지 않았습니다.").frame(maxWidth: .infinity, alignment: .leading)
                }
            }
        }
    }

    /// ops/harness_check.py's problems; a transfer over 50k is shown in the warning colour.
    private func checks(_ d: Dash) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            SectionTitle(text: "하네스 점검")
            SoftCard(padding: 14) {
                let ps = d.checks?.problems ?? []
                VStack(alignment: .leading, spacing: 6) {
                    if d.checks?.at == nil { empty("아직 점검 전입니다. 코드가 10분마다 확인합니다.") }
                    else if ps.isEmpty { Label("문제 없음", systemImage: "checkmark.circle.fill").foregroundStyle(Theme.ok) }
                    ForEach(ps, id: \.self) { p in
                        Label(p, systemImage: "exclamationmark.triangle.fill")
                            .foregroundStyle(p.contains("5만 넘는 송금") ? Theme.warn : Theme.fail)
                    }
                }
                .font(Theme.rounded(.subheadline))
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }

    private func field(_ k: String, _ v: String?) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Text(k).font(Theme.rounded(.caption)).foregroundStyle(Theme.mute).frame(width: 48, alignment: .leading)
            Text((v ?? "").isEmpty ? "-" : v!).font(Theme.rounded(.subheadline))
        }
    }

    private func empty(_ t: String) -> some View {
        Text(t).font(Theme.rounded(.footnote)).foregroundStyle(Theme.mute)
    }
}
