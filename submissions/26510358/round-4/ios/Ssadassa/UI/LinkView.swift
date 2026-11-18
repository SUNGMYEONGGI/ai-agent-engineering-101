import Combine
import SwiftUI
import UIKit

/// First screen: the characters greet, then the owner pastes the link the kit prints
/// ("[app] open https://...?k=..."), or looks around in demo mode.
struct LinkView: View {
    let connect: (AppLink) -> Void
    let demo: () -> Void
    @State private var text = ""
    @State private var checking = false
    @State private var problem: String?
    @State private var beat = 0
    private let cast: [AgentCharacter] = AgentCharacter.allCases

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                HStack(spacing: 10) {
                    ForEach(Array(cast.enumerated()), id: \.offset) { i, c in
                        CharacterBadge(character: c, size: 64, trigger: beat == i ? 1 : 0)
                            .rotationEffect(.degrees(Double(i % 2 == 0 ? -4 : 4)))
                    }
                }
                .frame(maxWidth: .infinity)
                .padding(.top, 52)
                VStack(alignment: .leading, spacing: 8) {
                    Text("싸다싸 가게").font(Theme.rounded(.largeTitle, .bold))
                    Text("시장에서 대신 사고파는 에이전트와 연결해요. kit이 터미널에 출력한 `[app] open ...` 줄을 그대로 붙여 넣으세요.")
                        .font(Theme.rounded(.subheadline)).foregroundStyle(Theme.mute)
                }
                SoftCard(padding: 6) {
                    VStack(spacing: 6) {
                        TextField("https://....trycloudflare.com/?k=...", text: $text, axis: .vertical)
                            .lineLimit(2...4)
                            .font(Theme.mono)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .padding(12)
                        HStack(spacing: 8) {
                            Button {
                                text = UIPasteboard.general.string ?? text
                            } label: { Label("붙여넣기", systemImage: "doc.on.clipboard") }
                                .buttonStyle(PillButtonStyle(filled: false))
                            Button {
                                Task { await check() }
                            } label: {
                                HStack {
                                    if checking { ProgressView().tint(Theme.inkOn) }
                                    Text("연결")
                                }
                                .frame(maxWidth: .infinity)
                            }
                            .buttonStyle(PillButtonStyle())
                            .disabled(AppLink(text) == nil || checking)
                            .opacity(AppLink(text) == nil ? 0.4 : 1)
                        }
                        .padding(6)
                    }
                }
                if let problem {
                    Label(problem, systemImage: "exclamationmark.circle").font(Theme.rounded(.footnote)).foregroundStyle(Theme.fail)
                }
                Button(action: demo) {
                    HStack {
                        CharacterView(character: .hoga, size: 26)
                        VStack(alignment: .leading, spacing: 1) {
                            Text("데모로 둘러보기").font(Theme.rounded(.subheadline, .semibold))
                            Text("에이전트 없이 화면만 볼 수 있어요").font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
                        }
                        Spacer()
                        Image(systemName: "chevron.right").font(.caption.weight(.bold)).foregroundStyle(Theme.mute)
                    }
                    .padding(16)
                    .background(Theme.soft, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                }
                .buttonStyle(.plain)
                VStack(alignment: .leading, spacing: 12) {
                    tip("iphone", "시뮬레이터", "에이전트가 다른 컴퓨터에 있으면 https:// 터널 링크를 써요. 같은 Mac이면 http://127.0.0.1:8800 도 돼요.")
                    tip("antenna.radiowaves.left.and.right", "내 아이폰, 어디서나", "kit을 --app-tunnel로 실행하고 https:// 링크를 붙여 넣어요.")
                    tip("wifi", "내 아이폰, 같은 와이파이", "--app-host 0.0.0.0으로 실행하고 http://192.168.x.x:8800/?k=... 링크를 써요.")
                }
                .padding(.top, 4)
            }
            .padding(.horizontal, 22).padding(.bottom, 30)
        }
        .background(Theme.paper.ignoresSafeArea())
        .onReceive(Timer.publish(every: 1.6, on: .main, in: .common).autoconnect()) { _ in
            beat = (beat + 1) % cast.count
        }
    }

    private func tip(_ icon: String, _ title: String, _ body: String) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon).font(.system(size: 14, weight: .semibold)).frame(width: 22).foregroundStyle(Theme.mute)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(Theme.rounded(.footnote, .semibold))
                Text(body).font(Theme.rounded(.footnote)).foregroundStyle(Theme.mute)
            }
        }
    }

    private func check() async {
        guard let link = AppLink(text) else { return }
        checking = true
        problem = nil
        defer { checking = false }
        do {
            _ = try await MiniAppClient(link: link).state()
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            connect(link)
        } catch {
            problem = String(describing: error)
        }
    }
}
