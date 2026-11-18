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
                VStack(spacing: 10) {
                    SectionTitle(text: "최근 움직임")
                    if model.state.moves.isEmpty {
                        empty(.teum, "아직 움직임이 없어요", "에이전트가 시장에서 움직이면 여기 나타나요.")
                    }
                    ForEach(Array(model.state.moves.enumerated()), id: \.offset) { i, m in
                        MoveRow(move: m, first: i == 0)
                    }
                }
                VStack(spacing: 10) {
                    SectionTitle(text: "에이전트가 만든 도구")
                    if model.state.forged.isEmpty {
                        empty(.cheungcheung, "아직 만든 도구가 없어요", "forge_tool로 만든 도구가 여기 쌓여요.")
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
                        toolRow(CharacterBadge(character: k.hasPrefix("mesh_") ? .kkwemi : .batchim, size: 34),
                                k, model.state.appTools[k] ?? "")
                    }
                }
            }
            .padding(.horizontal, 18).padding(.bottom, 24)
        }
        .background(Theme.paper.ignoresSafeArea())
    }

    private var tiles: some View {
        HStack(spacing: 10) {
            tile(.cheungcheung, "\(model.state.forged.count)", "만든 도구")
            tile(.kkwemi, "\(model.state.appTools.keys.filter { $0.hasPrefix("mesh_") }.count)", "MeshKit")
            tile(.batchim, "\(model.consent == nil ? 0 : 1)", "허락 대기")
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
                Text(move.thought).font(Theme.rounded(.subheadline)).foregroundStyle(Theme.ink).lineLimit(3)
            }
            .padding(.bottom, 14)
            Spacer(minLength: 0)
        }
        .fixedSize(horizontal: false, vertical: true)
    }
}
