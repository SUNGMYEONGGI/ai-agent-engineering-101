import SwiftUI
import UIKit

/// "나": the agent's character, the owner's limits (read by the agent with app_owner_limits) and the connection.
struct SettingsView: View {
    @EnvironmentObject var model: AppModel
    let disconnect: () -> Void
    @State private var draft = OwnerLimits()
    @State private var saved = false
    @State private var confirmStop = false
    @State private var editingFloor = false

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

    /// The money ceilings come from the server (auto: a share of the wallet, every 10 minutes). The owner turns auto
    /// on or off, nudges the shares, stops restocking at once, and sets the token cap.
    private var limitsSection: some View {
        let cur = model.limits
        return VStack(spacing: 12) {
            SectionTitle(text: "돈 상한")
            if cur.isStopped {
                Label("매입이 정지되어 있어요. 에이전트는 송금하지 않아요.", systemImage: "pause.circle.fill")
                    .font(Theme.rounded(.footnote, .semibold)).foregroundStyle(Theme.fail)
                    .frame(maxWidth: .infinity, alignment: .leading).padding(12)
                    .background(Theme.fail.opacity(0.12), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
            }
            SoftCard(padding: 0) {
                VStack(spacing: 0) {
                    Toggle(isOn: Binding(get: { draft.mode == "auto" }, set: { draft.mode = $0 ? "auto" : "fixed" })) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("잔액 비례 자동").font(Theme.rounded(.subheadline, .medium))
                            Text("지갑 잔액의 일정 비율로 서버가 정해요").font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
                        }
                    }
                    .tint(Theme.ok).padding(.horizontal, 18).padding(.vertical, 12)
                    Divider().padding(.leading, 18)
                    HStack(spacing: 0) {
                        stat("하루 매입", cur.maxPayPerDay)
                        stat("회당 매입", cur.maxPayPerCall)
                        stat("처분 손실/일", cur.maxLossPerDay)
                    }
                    .padding(.vertical, 12)
                    if cur.isAuto, let c = cur.autoFromCredits {
                        Text("최근 잔액 \(c.formatted()) 기준, 10분마다 다시 계산").font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
                            .frame(maxWidth: .infinity, alignment: .leading).padding(.horizontal, 18).padding(.bottom, 12)
                    }
                    Divider().padding(.leading, 18)
                    DisclosureGroup("비율 조정") {
                        VStack(spacing: 8) {
                            pctRow("하루 매입", $draft.autoPct.maxPayPerDay)
                            pctRow("회당 매입", $draft.autoPct.maxPayPerCall)
                            pctRow("처분 손실/일", $draft.autoPct.maxLossPerDay)
                        }
                        .padding(.top, 8)
                    }
                    .font(Theme.rounded(.subheadline, .medium)).tint(Theme.ink)
                    .padding(.horizontal, 18).padding(.vertical, 12)
                    Divider().padding(.leading, 18)
                    minBalanceRow
                }
            }
            Button(cur.isStopped ? "매입 다시 시작" : "매입 즉시 정지") {
                if cur.isStopped { Task { await resume() } } else { confirmStop = true }
            }
            .buttonStyle(PillButtonStyle(filled: cur.isStopped))
            .foregroundStyle(cur.isStopped ? Theme.inkOn : Theme.fail)
            .frame(maxWidth: .infinity)
            .confirmationDialog("매입을 지금 멈출까요?", isPresented: $confirmStop, titleVisibility: .visible) {
                Button("매입 정지", role: .destructive) { Task { await stop() } }
            } message: {
                Text("회당·하루 매입 한도를 0으로 고정해요. 에이전트는 다시 시작할 때까지 송금하지 않아요.")
            }

            SectionTitle(text: "토큰과 남길 말")
            SoftCard(padding: 0) {
                VStack(spacing: 0) {
                    sliderRow("하루 토큰 상한", $draft.dailyTokens, 0...100_000_000, 1_000_000, "토큰")
                    Divider().padding(.leading, 18)
                    TextField("에이전트에게 남길 말 (예: 오늘은 가구 재고를 늘리지 말 것)", text: $draft.note, axis: .vertical)
                        .font(Theme.rounded(.subheadline))
                        .lineLimit(2...5)
                        .padding(18)
                }
            }
            HStack {
                Text("서버에 저장돼요. 에이전트는 다음 실행 때 읽고, 토큰 상한은 바로 적용돼요.")
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

    private func stat(_ title: String, _ v: Int) -> some View {
        VStack(spacing: 2) {
            Text(v.formatted()).font(Theme.rounded(.headline, .bold)).monospacedDigit().lineLimit(1).minimumScaleFactor(0.7)
            Text(title).font(Theme.rounded(.caption2)).foregroundStyle(Theme.mute)
        }
        .frame(maxWidth: .infinity)
        .accessibilityElement(children: .combine)
    }

    private func pctRow(_ title: String, _ v: Binding<Double>) -> some View {
        Stepper(value: Binding(get: { v.wrappedValue }, set: { v.wrappedValue = (($0 * 10).rounded() / 10) }), in: 0...20, step: 0.1) {
            HStack {
                Text(title).font(Theme.rounded(.subheadline))
                Spacer()
                Text(String(format: "%.1f%%", v.wrappedValue)).font(Theme.rounded(.subheadline, .bold)).monospacedDigit()
            }
        }
    }

    /// The floor the agent keeps in the wallet: shown as one number, edited only after a long press.
    private var minBalanceRow: some View {
        HStack {
            Text("잔액 하한").font(Theme.rounded(.subheadline, .medium))
            Spacer()
            if editingFloor {
                TextField("0", value: $draft.minBalance, format: .number)
                    .keyboardType(.numberPad).multilineTextAlignment(.trailing).frame(width: 140)
                    .font(Theme.rounded(.subheadline, .bold)).monospacedDigit()
                    .onChange(of: draft.minBalance) { v in draft.minBalance = max(0, min(5_000_000, v)) }
            } else {
                Text(draft.minBalance.formatted()).font(Theme.rounded(.subheadline, .bold)).monospacedDigit()
            }
        }
        .padding(.horizontal, 18).padding(.vertical, 14)
        .contentShape(Rectangle())
        .onLongPressGesture(minimumDuration: 0.6) { editingFloor = true; UIImpactFeedbackGenerator(style: .medium).impactOccurred() }
        .accessibilityHint("길게 누르면 고칠 수 있어요")
    }

    private func stop() async {
        var v = model.limits
        v.mode = "fixed"; v.maxPayPerCall = 0; v.maxPayPerDay = 0
        if await model.save(limits: v) { draft = model.limits }
    }

    private func resume() async {
        var v = model.limits
        v.mode = "auto"
        if await model.save(limits: v) { draft = model.limits }
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
