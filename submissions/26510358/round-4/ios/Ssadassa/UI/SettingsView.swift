import SwiftUI
import UIKit

/// The owner's limits (read by the agent with app_owner_limits) and the connection.
struct SettingsView: View {
    @EnvironmentObject var model: AppModel
    let disconnect: () -> Void
    @State private var draft = OwnerLimits()
    @State private var saved = false

    var body: some View {
        Form {
            Section {
                Stepper(value: $draft.maxPayPerCall, in: 0...1_000_000, step: 5_000) {
                    LabeledContent("한 번 최대 송금", value: "\(draft.maxPayPerCall.formatted()) cr")
                }
                Stepper(value: $draft.maxPayPerDay, in: 0...10_000_000, step: 50_000) {
                    LabeledContent("하루 최대 송금", value: "\(draft.maxPayPerDay.formatted()) cr")
                }
                Toggle("구매자(buyer) 역할로 사도 됨", isOn: $draft.buyerAllowed)
                TextField("에이전트에게 남길 말 (예: 오늘은 가구 재고를 늘리지 말 것)", text: $draft.note, axis: .vertical)
                    .lineLimit(2...5)
            } header: {
                Text("주인이 정한 한도")
            } footer: {
                Text("에이전트는 송금하거나 전략을 바꾸기 전에 app_owner_limits 도구로 이 값을 읽습니다. 이 기기에만 저장됩니다."
                     + (model.limits.setAt.isEmpty ? "" : "\n마지막 저장: \(model.limits.setAt)"))
            }
            Section {
                Button(saved ? "저장했습니다" : "저장") {
                    model.save(limits: draft)
                    saved = true
                    UINotificationFeedbackGenerator().notificationOccurred(.success)
                }
                .disabled(draft == model.limits && !saved)
            }
            Section("연결") {
                LabeledContent("에이전트", value: model.agentName)
                LabeledContent("주소", value: model.link.base.host ?? model.link.base.absoluteString)
                LabeledContent("접근 코드", value: model.link.accessCode == nil ? "없음 (이 컴퓨터 전용 링크)" : "저장됨")
                if let e = model.error { Text(e).font(.footnote).foregroundStyle(Theme.fail) }
                Button("다른 링크로 연결", role: .destructive, action: disconnect)
            }
        }
        .onAppear { draft = model.limits; saved = false }
        .onChange(of: draft) { _ in saved = false }
    }
}
