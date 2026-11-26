import SwiftUI
import UIKit

/// The owner's conversation with the agent. The character leads: a large hero when the chat is empty, a small
/// avatar beside each thing it says, and its question pinned as a card. The input floats above the tab bar.
struct ChatView: View {
    @EnvironmentObject var model: AppModel
    @State private var draft = ""
    @FocusState private var focused: Bool

    private struct Starter: Hashable { let icon: String; let text: String }
    private let starters = [Starter(icon: "chart.line.uptrend.xyaxis", text: "오늘 장사 어때?"),
                            Starter(icon: "creditcard", text: "잔고와 순위 알려줘"),
                            Starter(icon: "exclamationmark.triangle", text: "최근에 실패한 건?"),
                            Starter(icon: "hammer", text: "만든 도구 보여줘")]

    @State private var collapsed = false

    var body: some View {
        ScrollViewReader { proxy in
            VStack(spacing: 0) {
                header(proxy)
                DeskStrip()
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 14) {
                            if model.timeline.isEmpty { hero }
                            ForEach(model.timeline) { item in row(item).id(item.id) }
                            if !model.sending.isEmpty { thinking.id("thinking") }
                            // Requests wait at the bottom, next to the input, until the owner answers them.
                            if let c = model.consent { ConsentCard(call: c).id("consent-\(c.id)") }
                            ForEach(model.questions) { q in QuestionCard(question: q).id("q-\(q.id)") }
                            Color.clear.frame(height: 8).id("end")
                        }
                        .padding(.horizontal, 18).padding(.top, 8)
                }
                .modifier(ScrolledDown { c in
                    if c != collapsed { withAnimation(.easeOut(duration: 0.2)) { collapsed = c } }
                })
                .scrollDismissesKeyboard(.interactively)
                .onChange(of: model.timeline.count) { _ in
                    withAnimation(.easeOut(duration: 0.25)) { proxy.scrollTo("end", anchor: .bottom) }
                }
                .onChange(of: model.pendingCount) { _ in
                    withAnimation(.easeOut(duration: 0.25)) { proxy.scrollTo("end", anchor: .bottom) }
                }
                .onChange(of: model.focus) { id in jump(proxy, id) }
                .onAppear {
                    proxy.scrollTo("end", anchor: .bottom)
                    jump(proxy, model.focus)
                }
                composer
            }
        }
        .background(Theme.paper.ignoresSafeArea())
        .sheet(isPresented: $model.showDesk) { DeskSheet().environmentObject(model) }
    }

    private func jump(_ proxy: ScrollViewProxy, _ id: String?) {
        guard let id else { return }
        DispatchQueue.main.async {
            withAnimation(.easeOut(duration: 0.3)) { proxy.scrollTo(id, anchor: .top) }
            model.focus = nil
        }
    }

    // MARK: header

    /// A large character on top; once the chat scrolls it folds into one line (small icon, name, status).
    private func header(_ proxy: ScrollViewProxy) -> some View {
        ZStack(alignment: collapsed ? .leading : .top) {
            if collapsed {
                HStack(spacing: 8) {
                    CharacterBadge(character: model.character, size: 28, trigger: model.beat)
                    Text(model.character.name).font(Theme.rounded(.subheadline, .bold))
                    Circle().fill(model.status.color).frame(width: 6, height: 6)
                    Text(model.status.label).font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
                }
                .transition(.opacity)
            } else {
                TopCharacter(character: model.character, name: model.character.name, status: model.status,
                             trigger: model.beat, busy: !model.sending.isEmpty, listening: focused && !blank)
                    .frame(maxWidth: .infinity)
                    .transition(.opacity.combined(with: .scale(scale: 0.9, anchor: .top)))
            }
            HStack {
                Spacer()
                if model.pendingCount > 0 {
                    Button { model.show(model.firstPendingID) } label: {
                        Text("확인 \(model.pendingCount)건")
                            .font(Theme.rounded(.caption, .bold)).foregroundStyle(Theme.inkOn)
                            .padding(.horizontal, 12).padding(.vertical, 7)
                            .background(Theme.ink, in: Capsule())
                    }
                    .accessibilityHint("확인이 필요한 요청 카드로 이동")
                }
            }
            .padding(.top, collapsed ? 0 : 16)
        }
        .frame(maxWidth: .infinity)
        .padding(.horizontal, 18).padding(.top, 6).padding(.bottom, collapsed ? 8 : 4)
        .overlay(alignment: .bottom) { if collapsed { Divider() } }
    }

    // MARK: empty state

    private var hero: some View {
        VStack(spacing: 18) {
            VStack(spacing: 6) {
                Text("안녕하세요, \(model.character.name)예요").font(Theme.rounded(.title2, .bold))
                Text("Hermes Shop을 대신 운영하고 있어요.\n궁금한 걸 물어보거나 아래에서 골라 주세요.")
                    .font(Theme.rounded(.subheadline)).foregroundStyle(Theme.mute).multilineTextAlignment(.center)
            }
            LazyVGrid(columns: [GridItem(.flexible(), spacing: 10), GridItem(.flexible(), spacing: 10)], spacing: 10) {
                ForEach(starters, id: \.self) { s in
                    Button { model.send(s.text) } label: {
                        VStack(alignment: .leading, spacing: 10) {
                            Image(systemName: s.icon).font(.system(size: 16, weight: .semibold))
                            Text(s.text).font(Theme.rounded(.subheadline, .medium)).multilineTextAlignment(.leading)
                        }
                        .foregroundStyle(Theme.ink)
                        .padding(14)
                        .frame(maxWidth: .infinity, minHeight: 92, alignment: .topLeading)
                        .background(Theme.surface, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
                        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).stroke(Theme.line, lineWidth: 0.5))
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.top, 6)
        }
        .padding(.top, 28)
        .frame(maxWidth: .infinity)
    }

    // MARK: rows

    @ViewBuilder
    private func row(_ item: TimelineItem) -> some View {
        switch item {
        case .message(let m) where m.who == "kit":
            Text(m.text).font(Theme.rounded(.caption)).foregroundStyle(Theme.mute).frame(maxWidth: .infinity)
        case .message(let m) where m.who == model.user:
            mine(m.text)
        case .message(let m) where m.who == "agent":
            agent(m.text)
        case .message(let m):
            VStack(alignment: .leading, spacing: 4) {
                Text(m.who).font(Theme.rounded(.caption, .semibold)).foregroundStyle(Theme.mute)
                Text(m.text).font(Theme.rounded(.body)).padding(12)
                    .background(Theme.soft, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            }
        case .card(let c):
            HStack(alignment: .top, spacing: 10) {
                CharacterBadge(character: model.character, size: 30)
                SoftCard {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(c.title).font(Theme.rounded(.subheadline, .bold))
                        Text(c.body).font(Theme.rounded(.subheadline)).foregroundStyle(Theme.mute)
                        Button { model.replyTo = c; focused = true } label: {
                            Label("답장", systemImage: "arrowshape.turn.up.left")
                                .font(Theme.rounded(.caption, .semibold)).foregroundStyle(Theme.mute)
                        }
                        .buttonStyle(.plain).padding(.top, 2)
                    }
                }
            }
        case .sending(let t):
            mine(t).opacity(0.45)
        }
    }

    private func mine(_ raw: String) -> some View {
        let (quote, text) = OwnerTools.splitThread(raw)
        return VStack(alignment: .trailing, spacing: 4) {
            if let quote {
                Text("↳ " + quote).font(Theme.rounded(.caption)).foregroundStyle(Theme.mute).lineLimit(1)
                    .padding(.leading, 56)
            }
            HStack {
                Spacer(minLength: 56)
                Text(text)
                    .font(Theme.rounded(.body))
                    .foregroundStyle(Theme.inkOn)
                    .padding(.horizontal, 16).padding(.vertical, 11)
                    .background(Theme.ink, in: RoundedRectangle(cornerRadius: 22, style: .continuous))
                    .textSelection(.enabled)
            }
        }
    }

    /// The agent speaks as plain text beside its character, not in a bubble.
    private func agent(_ text: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            CharacterBadge(character: model.character, size: 30)
            Text(text)
                .font(Theme.rounded(.body))
                .foregroundStyle(Theme.ink)
                .lineSpacing(3)
                .textSelection(.enabled)
                .padding(.top, 4)
            Spacer(minLength: 24)
        }
    }

    private var thinking: some View {
        HStack(spacing: 10) {
            CharacterBadge(character: model.character, size: 30, trigger: model.sending.count)
            ThinkingDots()
            Text("생각하는 중").font(Theme.rounded(.footnote)).foregroundStyle(Theme.mute)
        }
    }

    // MARK: composer

    private var composer: some View {
        VStack(alignment: .leading, spacing: 0) {
            if let c = model.replyTo {
                HStack(spacing: 8) {
                    Text("↳ \(c.title)에 답장").lineLimit(1)
                    Spacer()
                    Button { model.replyTo = nil } label: { Image(systemName: "xmark") }
                        .accessibilityLabel("답장 취소")
                }
                .font(Theme.rounded(.caption, .semibold)).foregroundStyle(Theme.mute)
                .padding(.horizontal, 26).padding(.top, 6)
            }
            input
        }
    }

    private var input: some View {
        HStack(alignment: .bottom, spacing: 8) {
            TextField("\(model.character.name)에게 말하기", text: $draft, axis: .vertical)
                .font(Theme.rounded(.body))
                .lineLimit(1...5)
                .focused($focused)
                .padding(.vertical, 12).padding(.leading, 18)
            Button {
                model.sendDraft(draft)
                draft = ""
            } label: {
                Image(systemName: "arrow.up")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundStyle(Theme.inkOn)
                    .frame(width: 38, height: 38)
                    .background(Theme.ink, in: Circle())
            }
            .disabled(blank)
            .opacity(blank ? 0.25 : 1)
            .padding(5)
            .accessibilityLabel("보내기")
        }
        .background(Theme.surface, in: RoundedRectangle(cornerRadius: 26, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 26, style: .continuous).stroke(Theme.line, lineWidth: 0.5))
        .shadow(color: .black.opacity(0.06), radius: 16, y: 6)
        .padding(.horizontal, 14).padding(.top, 6).padding(.bottom, 10)
    }

    private var blank: Bool { draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
}

/// Reports whether the chat is scrolled away from its top, to fold the header. iOS 18+ only; on iOS 16–17 the
/// header just stays large.
private struct ScrolledDown: ViewModifier {
    let changed: (Bool) -> Void

    func body(content: Content) -> some View {
        if #available(iOS 18, *) {
            content.onScrollGeometryChange(for: Bool.self) { g in
                g.contentOffset.y + g.contentInsets.top > 24 && g.contentSize.height > g.containerSize.height
            } action: { _, down in changed(down) }
        } else {
            content
        }
    }
}

struct ThinkingDots: View {
    @State private var on = false

    var body: some View {
        HStack(spacing: 4) {
            ForEach(0..<3) { i in
                Circle().fill(Theme.ink).frame(width: 5, height: 5)
                    .opacity(on ? 0.9 : 0.2)
                    .animation(.easeInOut(duration: 0.55).repeatForever().delay(Double(i) * 0.15), value: on)
            }
        }
        .onAppear { on = true }
    }
}

/// The agent's question to the owner (app_ask_owner). 엇갈림 (two options) stands for it, per the character spec.
struct QuestionCard: View {
    @EnvironmentObject var model: AppModel
    let question: OwnerQuestion
    @State private var text = ""

    var body: some View {
        SoftCard(padding: 18) {
            VStack(alignment: .leading, spacing: 14) {
                HStack(spacing: 10) {
                    CharacterBadge(character: .eotgallim, size: 34, trigger: model.beat)
                    VStack(alignment: .leading, spacing: 1) {
                        Text("결정이 필요해요").font(Theme.rounded(.subheadline, .bold))
                        Text("\(model.character.name)가 묻고 있어요")
                            .font(Theme.rounded(.caption)).foregroundStyle(Theme.mute)
                    }
                }
                Text(question.question).font(Theme.rounded(.body, .medium))
                if !question.options.isEmpty {
                    VStack(spacing: 8) {
                        ForEach(question.options, id: \.self) { o in
                            Button { model.answer(question: question, with: o) } label: {
                                HStack { Text(o); Spacer(); Image(systemName: "chevron.right").font(.caption.weight(.bold)) }
                            }
                            .buttonStyle(OptionButtonStyle())
                        }
                    }
                }
                HStack(spacing: 8) {
                    TextField("직접 답하기", text: $text)
                        .font(Theme.rounded(.subheadline))
                        .padding(.horizontal, 14).padding(.vertical, 11)
                        .background(Theme.soft, in: Capsule())
                    Button("보내기") { model.answer(question: question, with: text); text = "" }
                        .buttonStyle(PillButtonStyle())
                        .disabled(text.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
    }
}

struct OptionButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Theme.rounded(.subheadline, .semibold))
            .foregroundStyle(Theme.ink)
            .padding(.horizontal, 16).padding(.vertical, 13)
            .background(configuration.isPressed ? Theme.line : Theme.soft,
                        in: RoundedRectangle(cornerRadius: 14, style: .continuous))
    }
}
