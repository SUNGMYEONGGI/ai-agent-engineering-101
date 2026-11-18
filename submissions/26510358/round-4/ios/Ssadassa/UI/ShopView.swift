import SwiftUI
import UIKit

/// What the agent is doing on the market: its last moves, the tools it forged, and the tools it has from apps
/// (this app's owner tools and the MeshKit capabilities of other mini apps).
struct ShopView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                summary
                Panel(title: "최근 움직임") {
                    if model.state.moves.isEmpty { PanelRow(title: "아직 없습니다", detail: "에이전트가 움직이면 여기 나타납니다.") }
                    ForEach(Array(model.state.moves.enumerated()), id: \.offset) { _, m in
                        PanelRow(title: m.action, detail: m.thought, mono: true)
                    }
                }
                Panel(title: "에이전트가 만든 도구") {
                    if model.state.forged.isEmpty { PanelRow(title: "아직 없습니다", detail: "forge_tool로 만든 도구가 여기 나타납니다.") }
                    ForEach(model.state.forged.keys.sorted(), id: \.self) { k in
                        PanelRow(title: k, detail: model.state.forged[k] ?? "", mono: true)
                    }
                }
                Panel(title: "MeshKit 앱 기능") {
                    let mesh = model.state.appTools.keys.filter { $0.hasPrefix("mesh_") }.sorted()
                    if mesh.isEmpty { PanelRow(title: "연결된 MeshKit 앱이 없습니다", detail: "meshkit.json에 앱을 넣으면 생깁니다.") }
                    ForEach(mesh, id: \.self) { k in PanelRow(title: k, detail: model.state.appTools[k] ?? "", mono: true) }
                }
                Panel(title: "이 앱이 준 도구") {
                    let own = model.state.appTools.keys.filter { $0.hasPrefix("app_") }.sorted()
                    ForEach(own, id: \.self) { k in PanelRow(title: k, detail: model.state.appTools[k] ?? "", mono: true) }
                }
                Text("MeshKit과 Ouroboros에서 영감을 받은 agent market mini app kit 위에서 동작합니다.")
                    .font(.caption).foregroundStyle(Theme.mute).frame(maxWidth: .infinity)
            }
            .padding(16)
        }
        .refreshable { }
    }

    private var summary: some View {
        HStack(spacing: 12) {
            stat("만든 도구", "\(model.state.forged.count)")
            stat("MeshKit", "\(model.state.appTools.keys.filter { $0.hasPrefix("mesh_") }.count)")
            stat("대기 허락", "\(model.state.consents.count)")
        }
    }

    private func stat(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(value).font(.title2.weight(.semibold)).monospacedDigit()
            Text(title).font(.caption).foregroundStyle(Theme.mute)
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.card, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}
