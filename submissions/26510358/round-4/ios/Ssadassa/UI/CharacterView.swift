import SwiftUI
import UIKit

/// One character. Idle: a slow breath. When `trigger` changes (a real state change), the signature motion plays once
/// in 300–500 ms, as the character spec asks. With Reduce Motion on, it stays still.
struct CharacterView: View {
    let character: AgentCharacter
    var size: CGFloat = 40
    var trigger: Int = 0
    var breathing = false
    /// The agent is working: a quick hop with a wobble, until it stops.
    var busy = false
    /// The owner is typing: the character leans in and grows a little, as if listening.
    var listening = false
    var tint: Color = Theme.ink

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var pop = false
    @State private var inhale = false
    @State private var hop = false

    var body: some View {
        Image(character.asset)
            .renderingMode(.template)
            .resizable()
            .scaledToFit()
            .foregroundStyle(tint)
            .frame(width: size, height: size)
            .scaleEffect(x: pop ? 1.08 : 1, y: pop ? 0.94 : (inhale ? 1.025 : 1), anchor: .bottom)
            .scaleEffect(listening ? 1.06 : 1, anchor: .bottom)
            .rotationEffect(.degrees((pop ? motionTilt : 0) + (hop ? 5 : 0) + (listening ? -7 : 0)), anchor: .bottom)
            .offset(y: (pop ? -size * 0.06 : 0) + (hop ? -size * 0.1 : 0))
            .animation(reduceMotion ? nil : .spring(response: 0.35, dampingFraction: 0.6), value: listening)
            .accessibilityLabel("\(character.name), \(character.role)")
            .onAppear {
                if busy { setHop(true) }
                guard breathing, !reduceMotion else { return }
                withAnimation(.easeInOut(duration: 2.4).repeatForever(autoreverses: true)) { inhale = true }
            }
            .onChange(of: busy) { setHop($0) }
            .onChange(of: trigger) { _ in
                guard !reduceMotion else { return }
                withAnimation(.spring(response: 0.22, dampingFraction: 0.5)) { pop = true }
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.22) {
                    withAnimation(.spring(response: 0.28, dampingFraction: 0.75)) { pop = false }
                }
            }
    }

    private func setHop(_ on: Bool) {
        guard !reduceMotion else { return }
        if on {
            withAnimation(.easeInOut(duration: 0.32).repeatForever(autoreverses: true)) { hop = true }
        } else {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { hop = false }
        }
    }

    /// A small lean in the direction each shape "moves" in the spec (opening, pulling, sliding, rising).
    private var motionTilt: Double {
        switch character {
        case .teum, .eotgallim, .hoga, .matpyo: return 0
        case .ppichim, .deulchang: return -6
        case .gyeonbon, .kkwemi: return 6
        default: return -3
        }
    }
}

/// The character on a soft round stage, used as the hero of a screen.
struct CharacterStage: View {
    let character: AgentCharacter
    var size: CGFloat = 132
    var trigger: Int = 0

    var body: some View {
        ZStack {
            Circle().fill(Theme.soft).frame(width: size * 1.45, height: size * 1.45)
            Circle().stroke(Theme.line, lineWidth: 0.5).frame(width: size * 1.8, height: size * 1.8)
            CharacterView(character: character, size: size, trigger: trigger, breathing: true)
        }
    }
}

/// The chat's character, floating at the top centre with its name below. It breathes when idle, hops while the agent
/// works, leans in while the owner types, and on each new reply (or a tap) jumps once with a ripple.
struct TopCharacter: View {
    let character: AgentCharacter
    let name: String
    let status: AppModel.Status
    var trigger = 0
    var busy = false
    var listening = false

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var ripple = true          // true = finished (invisible)
    @State private var poke = 0

    var body: some View {
        VStack(spacing: 6) {
            ZStack {
                Circle().stroke(Theme.ink.opacity(0.3), lineWidth: 1.5)
                    .frame(width: 60, height: 60)
                    .scaleEffect(ripple ? 1.8 : 1)
                    .opacity(ripple ? 0 : 1)
                Circle().fill(Theme.surface).frame(width: 60, height: 60)
                    .shadow(color: .black.opacity(0.08), radius: 10, y: 4)
                CharacterView(character: character, size: 40, trigger: trigger + poke, breathing: true,
                              busy: busy, listening: listening)
            }
            .contentShape(Circle())
            .onTapGesture {
                poke += 1
                UIImpactFeedbackGenerator(style: .soft).impactOccurred()
            }
            HStack(spacing: 5) {
                Circle().fill(status.color).frame(width: 6, height: 6)
                Text(name).font(Theme.rounded(.footnote, .semibold)).foregroundStyle(Theme.ink)
            }
            .padding(.horizontal, 10).padding(.vertical, 4)
            .background(Theme.surface, in: Capsule())
            .overlay(Capsule().stroke(Theme.line, lineWidth: 0.5))
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(name), \(status.label)")
        .onChange(of: trigger + poke) { _ in
            guard !reduceMotion else { return }
            ripple = false
            withAnimation(.easeOut(duration: 0.6)) { ripple = true }
        }
    }
}

/// A character in a small rounded tile (avatars in lists and chat).
struct CharacterBadge: View {
    let character: AgentCharacter
    var size: CGFloat = 32
    var trigger: Int = 0

    var body: some View {
        CharacterView(character: character, size: size * 0.72, trigger: trigger)
            .frame(width: size, height: size)
            .background(Theme.soft, in: RoundedRectangle(cornerRadius: size * 0.32, style: .continuous))
    }
}
