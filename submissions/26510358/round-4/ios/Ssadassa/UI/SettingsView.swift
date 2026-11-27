import SwiftUI
import UIKit

/// "나": the agent's character, the owner's limits (read by the agent with app_owner_limits) and the connection.
struct SettingsView: View {
    @EnvironmentObject var model: AppModel
    let disconnect: () -> Void
    @State private var draft = OwnerLimits()
    @State private var saved = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                Text("나").font(Theme.rounded(.largeTitle, .bold)).padding(.top, 8)
                characterSection
                limitsSection
                connectionSection
            }
            .padding(.horizontal, 18).padding(.bottom, 110)   // the last button clears the floating tab bar
        }
        .background(Theme.paper.ignoresSafeArea())
        .onAppear { draft = model.limits; saved = false }
        .onChange(of: draft) { _ in saved = false }
    }

    // MARK: character

    private var characterSection: some View {
        VStack(spacing: 12) {
            SectionTitle(text: "내 에이전트 캐릭터")
            SoftCard(padding: 18) {
                HStack(spacing: 16) {
                    CharacterStage(character: model.character, size: 56, trigger: model.beat).frame(width: 100, height: 100)
                    VStack(alignment: .leading, spacing: 4) {
                        Text(model.character.name).font(Theme.rounded(.title2, .bold))
                        Text(model.character.role).font(Theme.rounded(.subheadline)).foregroundStyle(Theme.mute)
                        Text(model.character.rawValue.uppercased()).font(Theme.mono).foregroundStyle(Theme.mute)
                    }
                }
            }
            if AgentCharacter.agents.count > 1 {   // a picker only once there is a second agent
                LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 10), count: 4), spacing: 10) {
                    ForEach(AgentCharacter.agents) { c in
                        Button {
                            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { model.character = c }
                            UISelectionFeedbackGenerator().selectionChanged()
                        } label: {
                            VStack(spacing: 6) {
                                CharacterView(character: c, size: 34, trigger: model.character == c ? model.beat : 0)
                                    .frame(height: 40)
                                Text(c.name).font(Theme.rounded(.caption2, .semibold))
                            }
                            .frame(maxWidth: .infinity).padding(.vertical, 12)
                            .background(model.character == c ? Theme.surface : Theme.soft,
                                        in: RoundedRectangle(cornerRadius: 16, style: .continuous))
                            .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous)
                                .stroke(model.character == c ? Theme.ink : Color.clear, lineWidth: 1.5))
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("\(c.name), \(c.role)")
                    }
                }
            }
        }
    }

    // MARK: limits

    private var limitsSection: some View {
        VStack(spacing: 12) {
            SectionTitle(text: "주인이 정한 한도")
            SoftCard(padding: 0) {
                VStack(spacing: 0) {
                    sliderRow("원가 아래 처분 손실 한도 (하루)", $draft.maxLossPerDay, 0...100_000, 5_000, "credits")
                    Divider().padding(.leading, 18)
                    sliderRow("매입 한도 (회당)", $draft.maxPayPerCall, 0...50_000, 1_000, "credits")
                    Divider().padding(.leading, 18)
                    sliderRow("매입 한도 (하루)", $draft.maxPayPerDay, 0...500_000, 10_000, "credits")
                    Divider().padding(.leading, 18)
                    sliderRow("하루 토큰 상한", $draft.dailyTokens, 0...100_000_000, 1_000_000, "토큰")
                    Divider().padding(.leading, 18)
                    TextField("에이전트에게 남길 말 (예: 오늘은 가구 재고를 늘리지 말 것)", text: $draft.note, axis: .vertical)
                        .font(Theme.rounded(.subheadline))
                        .lineLimit(2...5)
                        .padding(18)
                }
            }
            HStack {
                Text("서버에 저장돼요. 에이전트는 다음 실행 때 읽고, 토큰 상한은 바로 적용돼요. 재시작은 필요 없어요.")
                    .font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
                Spacer()
                Button(saved ? "저장됨" : "저장") {
                    Task {
                        saved = await model.save(limits: draft)
                        UINotificationFeedbackGenerator().notificationOccurred(saved ? .success : .error)
                    }
                }
                .buttonStyle(PillButtonStyle())
                .disabled(draft == model.limits && !saved)
            }
        }
    }

    private func sliderRow(_ title: String, _ value: Binding<Int>, _ range: ClosedRange<Int>, _ step: Int,
                           _ unit: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(title).font(Theme.rounded(.subheadline, .medium))
                Spacer()
                Text("\(value.wrappedValue.formatted()) \(unit)").font(Theme.rounded(.subheadline, .bold)).monospacedDigit()
            }
            Slider(value: Binding(get: { Double(min(value.wrappedValue, range.upperBound)) },
                                  set: { value.wrappedValue = Int($0) }),
                   in: Double(range.lowerBound)...Double(range.upperBound), step: Double(step))
                .tint(Theme.ink)
                .accessibilityLabel(title)
        }
        .padding(.horizontal, 18).padding(.vertical, 12)
    }

    // MARK: connection

    private var connectionSection: some View {
        VStack(spacing: 12) {
            SectionTitle(text: "연결")
            SoftCard {
                VStack(alignment: .leading, spacing: 10) {
                    infoRow("가게", "Hermes Shop")
                    infoRow("에이전트", model.character.name)
                    infoRow("마켓 ID", model.agentName)
                    infoRow("주소", model.isDemo ? "데모 모드" : (model.link?.base.host ?? "-"))
                    infoRow("접근 코드", model.isDemo ? "-" : (model.link?.accessCode == nil ? "없음" : "Keychain에 저장됨"))
                    if let e = model.error { Text(e).font(Theme.rounded(.caption)).foregroundStyle(Theme.fail) }
                }
            }
            Button(model.isDemo ? "에이전트에 연결하기" : "다른 링크로 연결", action: disconnect)
                .buttonStyle(PillButtonStyle(filled: false))
                .frame(maxWidth: .infinity)
        }
    }

    private func infoRow(_ k: String, _ v: String) -> some View {
        HStack {
            Text(k).font(Theme.rounded(.subheadline)).foregroundStyle(Theme.mute)
            Spacer()
            Text(v).font(Theme.rounded(.subheadline, .medium)).lineLimit(1)
        }
    }
}
