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
            .padding(.horizontal, 18).padding(.bottom, 28)
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
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 10), count: 4), spacing: 10) {
                ForEach(AgentCharacter.marketFirst) { c in
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

    // MARK: limits

    private var limitsSection: some View {
        VStack(spacing: 12) {
            SectionTitle(text: "주인이 정한 한도")
            SoftCard(padding: 0) {
                VStack(spacing: 0) {
                    stepperRow("한 번 최대 송금", $draft.maxPayPerCall, 0...1_000_000, 5_000)
                    Divider().padding(.leading, 18)
                    stepperRow("하루 최대 송금", $draft.maxPayPerDay, 0...10_000_000, 50_000)
                    Divider().padding(.leading, 18)
                    Toggle(isOn: $draft.buyerAllowed) {
                        Text("구매자 역할로 사도 됨").font(Theme.rounded(.subheadline, .medium))
                    }
                    .tint(Theme.ink)
                    .padding(.horizontal, 18).padding(.vertical, 12)
                    Divider().padding(.leading, 18)
                    TextField("에이전트에게 남길 말 (예: 오늘은 가구 재고를 늘리지 말 것)", text: $draft.note, axis: .vertical)
                        .font(Theme.rounded(.subheadline))
                        .lineLimit(2...5)
                        .padding(18)
                }
            }
            HStack {
                Text("에이전트는 송금이나 전략을 바꾸기 전에 이 값을 읽어요. 이 기기에만 저장돼요.")
                    .font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
                Spacer()
                Button(saved ? "저장됨" : "저장") {
                    model.save(limits: draft)
                    saved = true
                    UINotificationFeedbackGenerator().notificationOccurred(.success)
                }
                .buttonStyle(PillButtonStyle())
                .disabled(draft == model.limits && !saved)
            }
        }
    }

    private func stepperRow(_ title: String, _ value: Binding<Int>, _ range: ClosedRange<Int>, _ step: Int) -> some View {
        Stepper(value: value, in: range, step: step) {
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(Theme.rounded(.subheadline, .medium))
                Text("\(value.wrappedValue.formatted()) credits").font(Theme.rounded(.headline, .bold)).monospacedDigit()
            }
        }
        .padding(.horizontal, 18).padding(.vertical, 12)
    }

    // MARK: connection

    private var connectionSection: some View {
        VStack(spacing: 12) {
            SectionTitle(text: "연결")
            SoftCard {
                VStack(alignment: .leading, spacing: 10) {
                    infoRow("에이전트", model.agentName)
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
