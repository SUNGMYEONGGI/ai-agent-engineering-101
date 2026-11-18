import SwiftUI
import UIKit

/// First screen: paste the link the kit prints ("[app] open https://...?k=..."), check it, and keep it.
struct LinkView: View {
    let connect: (AppLink) -> Void
    @State private var text = ""
    @State private var checking = false
    @State private var problem: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                ShopMark(size: 64).padding(.top, 48)
                Text("싸다싸 가게").font(.largeTitle.weight(.bold))
                Text("컴퓨터에서 돌고 있는 에이전트와 연결합니다. kit이 터미널에 출력한 `[app] open ...` 줄을 그대로 붙여 넣으세요.")
                    .font(.subheadline).foregroundStyle(Theme.mute)
                TextField("https://....trycloudflare.com/?k=...", text: $text, axis: .vertical)
                    .lineLimit(2...4)
                    .font(Theme.mono)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .padding(12)
                    .background(Theme.card, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                HStack {
                    Button {
                        text = UIPasteboard.general.string ?? text
                    } label: { Label("붙여넣기", systemImage: "doc.on.clipboard") }
                        .buttonStyle(.bordered).tint(Theme.ink)
                    Spacer()
                    Button {
                        Task { await check() }
                    } label: {
                        if checking { ProgressView().frame(minWidth: 60) } else { Text("연결").frame(minWidth: 60) }
                    }
                    .buttonStyle(.borderedProminent).tint(Theme.ink)
                    .disabled(AppLink(text) == nil || checking)
                }
                if let problem { Text(problem).font(.footnote).foregroundStyle(Theme.fail) }
                VStack(alignment: .leading, spacing: 8) {
                    tip("시뮬레이터", "컴퓨터와 네트워크를 같이 써서 http://127.0.0.1:8800/ 링크도 됩니다.")
                    tip("내 아이폰, 어디서나", "kit을 --app-tunnel로 실행하고 https:// 링크를 붙여 넣습니다.")
                    tip("내 아이폰, 같은 와이파이", "--app-host 0.0.0.0으로 실행하고 http://192.168.x.x:8800/?k=... 링크를 씁니다.")
                }
                .padding(.top, 8)
            }
            .padding(24)
        }
    }

    private func tip(_ title: String, _ body: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title).font(.footnote.weight(.semibold))
            Text(body).font(.footnote).foregroundStyle(Theme.mute)
        }
    }

    private func check() async {
        guard let link = AppLink(text) else { return }
        checking = true
        problem = nil
        defer { checking = false }
        do {
            _ = try await MiniAppClient(link: link).state()
            connect(link)
        } catch {
            problem = String(describing: error)
        }
    }
}
