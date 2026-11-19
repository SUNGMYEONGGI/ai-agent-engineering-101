import SwiftUI

/// MeshKit: the agent wants to use another mini app's capability. Nothing runs until the owner allows it here.
/// It sits in the chat as a request card (the 확인 button jumps to it), not as a sheet over everything:
/// the owner reads what will run and on what, then answers this one call. 받침 stands for "waiting for you".
struct ConsentCard: View {
    @EnvironmentObject var model: AppModel
    let call: PendingCall

    var body: some View {
        SoftCard(padding: 18) {
            VStack(alignment: .leading, spacing: 14) {
                HStack(spacing: 10) {
                    CharacterBadge(character: .batchim, size: 34, trigger: model.beat)
                    VStack(alignment: .leading, spacing: 1) {
                        Text("허락이 필요해요").font(Theme.rounded(.subheadline, .bold))
                        Text("\(model.character.name)가 다른 앱 기능을 쓰려고 해요")
                            .font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
                    }
                }
                VStack(spacing: 0) {
                    row("실행할 작업", call.name, mono: true)
                    Divider()
                    row("적용 범위", "이번 1회만")
                    ForEach(Array(call.argPairs.enumerated()), id: \.offset) { _, kv in
                        Divider()
                        row(kv.0, kv.1, mono: true)
                    }
                }
                .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).stroke(Theme.line, lineWidth: 0.5))
                Text("허용하면 이 값 그대로 한 번 실행하고, 상대 앱이 서명한 영수증을 확인한 뒤에만 결과를 넘겨요.")
                    .font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
                HStack(spacing: 10) {
                    Button { model.answer(consent: call, approved: false) } label: {
                        Text("이번 요청 거절").frame(maxWidth: .infinity)
                    }
                    .buttonStyle(PillButtonStyle(filled: false))
                    Button { model.answer(consent: call, approved: true) } label: {
                        Text("이번 1회 허용").frame(maxWidth: .infinity)
                    }
                    .buttonStyle(PillButtonStyle())
                }
            }
        }
    }

    private func row(_ k: String, _ v: String, mono: Bool = false) -> some View {
        HStack(alignment: .top, spacing: 16) {
            Text(k).font(Theme.rounded(.footnote)).foregroundStyle(Theme.mute)
            Spacer()
            Text(v).font(mono ? Theme.mono.weight(.semibold) : Theme.rounded(.subheadline, .semibold))
                .multilineTextAlignment(.trailing)
        }
        .padding(.horizontal, 14).padding(.vertical, 10)
    }
}
