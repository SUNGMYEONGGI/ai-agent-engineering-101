import SwiftUI
import UIKit

/// The owner's conversation with the agent, with the agent's cards and questions in line.
struct ChatView: View {
    @EnvironmentObject var model: AppModel
    @State private var draft = ""
    @FocusState private var focused: Bool

    private let starters = ["지금 잔고와 순위는?", "오늘 판 것 요약해줘", "최근에 실패한 것은?", "만든 도구 보여줘"]

    var body: some View {
        VStack(spacing: 0) {
            if let q = model.questions.first { QuestionCard(question: q, more: model.questions.count - 1) }
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 6) {
                        if model.timeline.isEmpty { empty }
                        ForEach(model.timeline) { item in row(item).id(item.id) }
                        if !model.sending.isEmpty { TypingBubble().id("typing") }
                    }
                    .padding(.horizontal, 16).padding(.vertical, 12)
                }
                .scrollDismissesKeyboard(.interactively)
                .onChange(of: model.timeline.count) { _ in
                    withAnimation(.easeOut(duration: 0.2)) { proxy.scrollTo(model.timeline.last?.id, anchor: .bottom) }
                }
            }
            inputBar
        }
    }

    private var empty: some View {
        VStack(spacing: 10) {
            ShopMark(size: 60).padding(.top, 60)
            Text(model.agentName).font(.title3.weight(.semibold))
            Text("싸다싸 가게의 에이전트입니다.\n대화하는 동안에도 시장에서 사고팝니다.")
                .font(.footnote).foregroundStyle(Theme.mute).multilineTextAlignment(.center)
            FlowChips(items: starters) { model.send($0) }.padding(.top, 8)
        }
        .frame(maxWidth: .infinity)
    }

    @ViewBuilder
    private func row(_ item: TimelineItem) -> some View {
        switch item {
        case .message(let m) where m.who == "kit":
            Text(m.text).font(.caption).foregroundStyle(Theme.mute).frame(maxWidth: .infinity).padding(.vertical, 6)
        case .message(let m) where m.who == model.user:
            Bubble(text: m.text, mine: true)
        case .message(let m):
            VStack(alignment: .leading, spacing: 3) {
                if m.who != "agent" { Text(m.who).font(.caption).foregroundStyle(Theme.mute).padding(.leading, 4) }
                Bubble(text: m.text, mine: false)
            }
        case .card(let c):
            VStack(alignment: .leading, spacing: 4) {
                Text(model.agentName.uppercased()).font(.caption2.weight(.semibold)).foregroundStyle(Theme.mute)
                Text(c.title).font(.subheadline.weight(.semibold))
                Text(c.body).font(.subheadline).foregroundStyle(.secondary)
            }
            .padding(14)
            .frame(maxWidth: 300, alignment: .leading)
            .background(Color(uiColor: .systemBackground), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).stroke(Theme.line))
            .shadow(color: .black.opacity(0.08), radius: 8, y: 4)
            .padding(.vertical, 4)
        case .sending(let t):
            Bubble(text: t, mine: true).opacity(0.5)
        }
    }

    private var inputBar: some View {
        HStack(alignment: .bottom, spacing: 8) {
            TextField("메시지 보내기", text: $draft, axis: .vertical)
                .lineLimit(1...5)
                .focused($focused)
                .padding(.vertical, 9).padding(.leading, 16)
            Button {
                model.send(draft)
                draft = ""
            } label: {
                Image(systemName: "arrow.up").font(.system(size: 15, weight: .bold))
                    .foregroundStyle(Color(uiColor: .systemBackground))
                    .frame(width: 34, height: 34)
                    .background(Theme.ink, in: Circle())
            }
            .disabled(draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            .opacity(draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? 0.25 : 1)
            .padding(4)
            .accessibilityLabel("보내기")
        }
        .background(Theme.card, in: RoundedRectangle(cornerRadius: 22, style: .continuous))
        .padding(.horizontal, 12).padding(.vertical, 8)
    }
}

struct Bubble: View {
    let text: String
    let mine: Bool

    var body: some View {
        HStack {
            if mine { Spacer(minLength: 48) }
            Text(text)
                .font(.body)
                .textSelection(.enabled)
                .padding(.horizontal, 14).padding(.vertical, 9)
                .foregroundStyle(mine ? Color(uiColor: .systemBackground) : Theme.ink)
                .background(mine ? Theme.ink : Theme.card,
                            in: UnevenBubble(mine: mine))
            if !mine { Spacer(minLength: 48) }
        }
    }
}

/// Rounded bubble with a tighter corner on the speaker's side.
struct UnevenBubble: Shape {
    let mine: Bool

    func path(in r: CGRect) -> Path {
        let big: CGFloat = 18, small: CGFloat = 6
        let tl = big, tr = big, bl = mine ? big : small, br = mine ? small : big
        var p = Path()
        p.move(to: CGPoint(x: r.minX + tl, y: r.minY))
        p.addLine(to: CGPoint(x: r.maxX - tr, y: r.minY))
        p.addArc(center: CGPoint(x: r.maxX - tr, y: r.minY + tr), radius: tr, startAngle: .degrees(-90), endAngle: .degrees(0), clockwise: false)
        p.addLine(to: CGPoint(x: r.maxX, y: r.maxY - br))
        p.addArc(center: CGPoint(x: r.maxX - br, y: r.maxY - br), radius: br, startAngle: .degrees(0), endAngle: .degrees(90), clockwise: false)
        p.addLine(to: CGPoint(x: r.minX + bl, y: r.maxY))
        p.addArc(center: CGPoint(x: r.minX + bl, y: r.maxY - bl), radius: bl, startAngle: .degrees(90), endAngle: .degrees(180), clockwise: false)
        p.addLine(to: CGPoint(x: r.minX, y: r.minY + tl))
        p.addArc(center: CGPoint(x: r.minX + tl, y: r.minY + tl), radius: tl, startAngle: .degrees(180), endAngle: .degrees(270), clockwise: false)
        p.closeSubpath()
        return p
    }
}

struct TypingBubble: View {
    @State private var on = false

    var body: some View {
        HStack(spacing: 4) {
            ForEach(0..<3) { i in
                Circle().fill(Theme.mute).frame(width: 6, height: 6)
                    .opacity(on ? 1 : 0.3)
                    .animation(.easeInOut(duration: 0.6).repeatForever().delay(Double(i) * 0.15), value: on)
            }
        }
        .padding(14)
        .background(Theme.card, in: UnevenBubble(mine: false))
        .onAppear { on = true }
    }
}

/// The agent's question to the owner (app_ask_owner), pinned above the chat until answered.
struct QuestionCard: View {
    @EnvironmentObject var model: AppModel
    let question: OwnerQuestion
    let more: Int
    @State private var text = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Label("에이전트의 질문", systemImage: "questionmark.bubble.fill")
                    .font(.footnote.weight(.semibold)).foregroundStyle(Theme.warn)
                Spacer()
                if more > 0 { Text("+\(more)").font(.caption.weight(.bold)).foregroundStyle(Theme.mute) }
            }
            Text(question.question).font(.subheadline.weight(.medium))
            if !question.options.isEmpty {
                FlowChips(items: question.options) { model.answer(question: question, with: $0) }
            }
            HStack {
                TextField("직접 답하기", text: $text)
                    .textFieldStyle(.roundedBorder)
                Button("보내기") { model.answer(question: question, with: text); text = "" }
                    .buttonStyle(.borderedProminent).tint(Theme.ink)
                    .disabled(text.trimmingCharacters(in: .whitespaces).isEmpty)
            }
        }
        .padding(14)
        .background(Theme.warn.opacity(0.1))
        .overlay(alignment: .bottom) { Divider() }
    }
}

/// Wrapping row of capsule buttons.
struct FlowChips: View {
    let items: [String]
    let tap: (String) -> Void

    var body: some View {
        FlowLayout(spacing: 8) {
            ForEach(items, id: \.self) { s in
                Button(s) { tap(s) }
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 14).padding(.vertical, 7)
                    .overlay(Capsule().stroke(Theme.line))
            }
        }
    }
}

struct FlowLayout: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let rows = arrange(proposal.width ?? .infinity, subviews)
        return CGSize(width: proposal.width ?? rows.width, height: rows.height)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var x = bounds.minX, y = bounds.minY, rowH: CGFloat = 0
        for v in subviews {
            let s = v.sizeThatFits(.unspecified)
            if x + s.width > bounds.maxX && x > bounds.minX { x = bounds.minX; y += rowH + spacing; rowH = 0 }
            v.place(at: CGPoint(x: x, y: y), proposal: ProposedViewSize(s))
            x += s.width + spacing
            rowH = max(rowH, s.height)
        }
    }

    private func arrange(_ maxW: CGFloat, _ subviews: Subviews) -> (width: CGFloat, height: CGFloat) {
        var x: CGFloat = 0, y: CGFloat = 0, rowH: CGFloat = 0, width: CGFloat = 0
        for v in subviews {
            let s = v.sizeThatFits(.unspecified)
            if x + s.width > maxW && x > 0 { x = 0; y += rowH + spacing; rowH = 0 }
            x += s.width + spacing
            width = max(width, x - spacing)
            rowH = max(rowH, s.height)
        }
        return (width, y + rowH)
    }
}
