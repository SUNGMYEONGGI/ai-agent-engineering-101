import SwiftUI
import UIKit

/// MeshKit: the agent wants to use another mini app's capability. Nothing runs until the owner allows it here.
/// 받침 (BATCHIM) stands for "waiting for your confirmation" in the character spec.
struct ConsentSheet: View {
    let call: PendingCall
    let answer: (Bool) -> Void
    @State private var beat = 0

    var body: some View {
        VStack(spacing: 18) {
            CharacterStage(character: .batchim, size: 64, trigger: beat).frame(height: 120).padding(.top, 18)
            VStack(spacing: 6) {
                Text("확인 대기").font(Theme.rounded(.caption, .bold)).foregroundStyle(Theme.warn)
                    .padding(.horizontal, 10).padding(.vertical, 4).background(Theme.warn.opacity(0.14), in: Capsule())
                Text("에이전트가 허락을 구해요").font(Theme.rounded(.title2, .bold))
                (Text(call.name).font(Theme.mono.weight(.semibold))
                 + Text(" 을(를) 실행하려고 해요. 허용하면 이 내용 그대로 실행하고, 상대 앱이 서명한 영수증을 확인한 뒤에만 결과를 넘겨요."))
                    .font(Theme.rounded(.footnote)).foregroundStyle(Theme.mute).multilineTextAlignment(.center)
            }
            VStack(spacing: 0) {
                let pairs = call.argPairs
                if pairs.isEmpty { argRow("인자", "없음") }
                ForEach(Array(pairs.enumerated()), id: \.offset) { i, kv in
                    if i > 0 { Divider().padding(.leading, 16) }
                    argRow(kv.0, kv.1)
                }
            }
            .background(Theme.soft, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            Spacer(minLength: 0)
            HStack(spacing: 10) {
                Button { answer(false) } label: { Text("거절").frame(maxWidth: .infinity) }
                    .buttonStyle(PillButtonStyle(filled: false))
                Button { answer(true) } label: { Text("허용").frame(maxWidth: .infinity) }
                    .buttonStyle(PillButtonStyle())
            }
        }
        .padding(.horizontal, 22).padding(.bottom, 12)
        .background(Theme.paper.ignoresSafeArea())
        .presentationDetents([.large, .medium])
        .presentationDragIndicator(.visible)
        .interactiveDismissDisabled()
        .onAppear { DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) { beat += 1 } }
    }

    private func argRow(_ k: String, _ v: String) -> some View {
        HStack(alignment: .top, spacing: 16) {
            Text(k).font(Theme.mono).foregroundStyle(Theme.mute)
            Spacer()
            Text(v).font(Theme.rounded(.subheadline, .semibold)).multilineTextAlignment(.trailing)
        }
        .padding(.horizontal, 16).padding(.vertical, 12)
    }
}
