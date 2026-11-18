import SwiftUI
import UIKit

/// MeshKit: the agent wants to use another mini app's capability. Nothing runs until the owner allows it here.
struct ConsentSheet: View {
    let call: PendingCall
    let answer: (Bool) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 10) {
                Image(systemName: "hand.raised.fill").font(.title3).foregroundStyle(Theme.warn)
                Text("에이전트가 허락을 구합니다").font(.title3.weight(.semibold))
            }
            .padding(.top, 8)
            (Text(call.name).font(Theme.mono) + Text(" 실행을 요청했습니다. 허용하면 이 내용 그대로 실행하고, 상대 앱이 서명한 영수증을 확인한 뒤에만 결과를 에이전트에게 넘깁니다."))
                .font(.footnote).foregroundStyle(Theme.mute)
            VStack(spacing: 0) {
                let pairs = call.argPairs
                if pairs.isEmpty { argRow("인자", "없음") }
                ForEach(Array(pairs.enumerated()), id: \.offset) { _, kv in argRow(kv.0, kv.1) }
            }
            .background(Theme.card, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
            Spacer(minLength: 0)
            HStack(spacing: 10) {
                Button { answer(false) } label: { Text("거절").frame(maxWidth: .infinity, minHeight: 46) }
                    .buttonStyle(.bordered).tint(Theme.ink)
                Button { answer(true) } label: { Text("허용").frame(maxWidth: .infinity, minHeight: 46) }
                    .buttonStyle(.borderedProminent).tint(Theme.ink)
            }
            .font(.headline)
        }
        .padding(20)
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
        .interactiveDismissDisabled()
    }

    private func argRow(_ k: String, _ v: String) -> some View {
        HStack(alignment: .top, spacing: 16) {
            Text(k).font(Theme.mono).foregroundStyle(Theme.mute)
            Spacer()
            Text(v).font(.subheadline.weight(.medium)).multilineTextAlignment(.trailing)
        }
        .padding(.horizontal, 14).padding(.vertical, 10)
        .overlay(alignment: .bottom) { Divider() }
    }
}
