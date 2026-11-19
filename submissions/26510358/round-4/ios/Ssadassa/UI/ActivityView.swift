import SwiftUI
import UIKit

/// What the agent is doing on the market, told through the characters: each move gets the character whose role
/// matches it (호가 for replies, 들창 for stock, 맞표 for payments, 되감 for memory, ...).
struct ActivityView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                Text("활동").font(Theme.rounded(.largeTitle, .bold)).padding(.top, 8)
                tiles
                if model.pendingCount > 0 {
                    VStack(spacing: 10) {
                        SectionTitle(text: "확인 필요")
                        if let c = model.consent {
                            PendingRow(title: c.name, detail: "다른 앱 기능 실행 허락") { model.show("consent-\(c.id)") }
                        }
                        ForEach(model.questions) { q in
                            PendingRow(title: q.question, detail: "\(model.character.name)의 질문") { model.show("q-\(q.id)") }
                        }
                    }
                }
                if !model.log.isEmpty {
                    VStack(spacing: 10) {
                        SectionTitle(text: "내 결정과 변경")
                        ForEach(model.log) { DecisionRow(decision: $0) }
                    }
                }
                VStack(spacing: 10) {
                    SectionTitle(text: "최근 움직임")
                    if model.state.moves.isEmpty {
                        empty(model.character, "아직 움직임이 없어요", "에이전트가 시장에서 움직이면 여기 나타나요.")
                    }
                    ForEach(Array(model.state.moves.enumerated()), id: \.offset) { i, m in
                        MoveRow(move: m, first: i == 0)
                    }
                }
                VStack(spacing: 10) {
                    SectionTitle(text: "에이전트가 만든 도구")
                    if model.state.forged.isEmpty {
                        empty(model.character, "아직 만든 도구가 없어요", "forge_tool로 만든 도구가 여기 쌓여요.")
                    }
                    ForEach(model.state.forged.keys.sorted(), id: \.self) { k in
                        toolRow(CharacterBadge(character: AgentCharacter.forMove(k), size: 34), k, model.state.forged[k] ?? "")
                    }
                }
                VStack(spacing: 10) {
                    SectionTitle(text: "연결된 앱")
                    let apps = model.state.appTools.keys.sorted()
                    if apps.isEmpty { empty(.batchim, "연결된 앱이 없어요", "meshkit.json에 앱을 넣으면 생겨요.") }
                    ForEach(apps, id: \.self) { k in
                        toolRow(CharacterBadge(character: k.hasPrefix("mesh_") ? .batchim : model.character, size: 34),
                                k, model.state.appTools[k] ?? "")
                    }
                }
            }
            .padding(.horizontal, 18).padding(.bottom, 110)   // clear of the floating tab bar
        }
        .background(Theme.paper.ignoresSafeArea())
    }

    private var tiles: some View {
        HStack(spacing: 10) {
            tile(.batchim, "\(model.pendingCount)", "확인 필요")
            tile(model.character, "\(model.log.filter { $0.status == .running }.count)", "진행 중")
            tile(model.character, "\(model.log.filter { $0.status == .done }.count)", "완료")
        }
    }

    private func tile(_ c: AgentCharacter, _ value: String, _ title: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            CharacterView(character: c, size: 28, trigger: model.beat)
            Text(value).font(Theme.rounded(.title, .bold)).monospacedDigit()
            Text(title).font(Theme.rounded(.caption, .medium)).foregroundStyle(Theme.mute)
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.surface, in: RoundedRectangle(cornerRadius: 22, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).stroke(Theme.line, lineWidth: 0.5))
    }

    private func toolRow(_ badge: CharacterBadge, _ name: String, _ detail: String) -> some View {
        HStack(alignment: .top, spacing: 12) {
            badge
            VStack(alignment: .leading, spacing: 3) {
                Text(name).font(Theme.mono.weight(.semibold))
                Text(detail).font(Theme.rounded(.caption)).foregroundStyle(Theme.mute).lineLimit(2)
            }
            Spacer(minLength: 0)
        }
        .padding(12)
        .background(Theme.surface, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
    }

    private func empty(_ c: AgentCharacter, _ title: String, _ detail: String) -> some View {
        HStack(spacing: 14) {
            CharacterView(character: c, size: 40, tint: Theme.mute)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(Theme.rounded(.subheadline, .semibold))
                Text(detail).font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
            }
            Spacer(minLength: 0)
        }
        .padding(16)
        .background(Theme.soft, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
}

/// One move on a vertical thread, with the character for that kind of move.
struct MoveRow: View {
    let move: Move
    let first: Bool
    @State private var open = false

    var body: some View {
        let c = AgentCharacter.forMove(move.action)
        HStack(alignment: .top, spacing: 12) {
            VStack(spacing: 0) {
                CharacterBadge(character: c, size: 36, trigger: first ? 1 : 0)
                Rectangle().fill(Theme.line).frame(width: 1.5).frame(maxHeight: .infinity)
            }
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 6) {
                    Text(c.name).font(Theme.rounded(.caption, .bold))
                    Text(move.action).font(Theme.mono).foregroundStyle(Theme.mute)
                }
                Text(move.thought).font(Theme.rounded(.subheadline)).foregroundStyle(Theme.ink).lineLimit(open ? nil : 2)
            }
            .padding(.bottom, 14)
            Spacer(minLength: 0)
        }
        .fixedSize(horizontal: false, vertical: true)
        .contentShape(Rectangle())
        .onTapGesture { withAnimation(.easeOut(duration: 0.2)) { open.toggle() } }
    }
}

/// A request waiting for the owner; tapping opens its card in the chat.
struct PendingRow: View {
    let title: String
    let detail: String
    let open: () -> Void

    var body: some View {
        Button(action: open) {
            HStack(spacing: 12) {
                StatusChip(text: "확인 필요", color: Theme.warn)
                VStack(alignment: .leading, spacing: 2) {
                    Text(title).font(Theme.rounded(.subheadline, .semibold)).lineLimit(2)
                    Text(detail).font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
                }
                Spacer(minLength: 0)
                Image(systemName: "chevron.right").font(.caption.weight(.bold)).foregroundStyle(Theme.mute)
            }
            .padding(14)
            .background(Theme.surface, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Theme.line, lineWidth: 0.5))
        }
        .buttonStyle(.plain)
    }
}

/// One decision or change, with its live status; tap to see the details (before → after, who, the agent's report).
struct DecisionRow: View {
    let decision: Decision
    @State private var open = false

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 12) {
                StatusChip(text: label, color: color)
                VStack(alignment: .leading, spacing: 2) {
                    Text(decision.title).font(Theme.rounded(.subheadline, .semibold)).lineLimit(open ? nil : 1)
                    Text("\(decision.choice) · \(decision.at.formatted(date: .omitted, time: .shortened))")
                        .font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
                }
                Spacer(minLength: 0)
                Image(systemName: open ? "chevron.up" : "chevron.down").font(.caption.weight(.bold)).foregroundStyle(Theme.mute)
            }
            if open {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(Array(decision.details.enumerated()), id: \.offset) { _, kv in
                        HStack(alignment: .top) {
                            Text(kv.0).foregroundStyle(Theme.mute)
                            Spacer()
                            Text(kv.1).multilineTextAlignment(.trailing)
                        }
                    }
                    if let r = decision.result {
                        Divider()
                        Text("\(AgentCharacter.hoga.name)의 보고").foregroundStyle(Theme.mute)
                        Text(r)
                    } else if decision.status == .running {
                        Text("\(AgentCharacter.hoga.name)가 결과를 알려 주면 여기 표시돼요.").foregroundStyle(Theme.mute)
                    }
                }
                .font(Theme.rounded(.footnote))
                .transition(.opacity)
            }
        }
        .padding(14)
        .background(Theme.surface, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Theme.line, lineWidth: 0.5))
        .contentShape(Rectangle())
        .onTapGesture { withAnimation(.easeOut(duration: 0.2)) { open.toggle() } }
    }

    private var label: String {
        switch decision.status { case .running: return "진행 중"; case .done: return "완료"; case .failed: return "실패"; case .declined: return "거절함" }
    }

    private var color: Color {
        switch decision.status { case .running: return Theme.ink; case .done: return Theme.ok; case .failed: return Theme.fail; case .declined: return Theme.mute }
    }
}

struct StatusChip: View {
    let text: String
    let color: Color

    var body: some View {
        Text(text).font(Theme.rounded(.caption2, .bold)).foregroundStyle(color)
            .padding(.horizontal, 8).padding(.vertical, 4)
            .overlay(Capsule().stroke(color.opacity(0.5), lineWidth: 1))
            .fixedSize()
    }
}
