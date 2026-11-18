import SwiftUI

/// One character. Idle: a slow breath. When `trigger` changes (a real state change), the signature motion plays once
/// in 300–500 ms, as the character spec asks. With Reduce Motion on, it stays still.
struct CharacterView: View {
    let character: AgentCharacter
    var size: CGFloat = 40
    var trigger: Int = 0
    var breathing = false
    var tint: Color = Theme.ink

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var pop = false
    @State private var inhale = false

    var body: some View {
        Image(character.asset)
            .renderingMode(.template)
            .resizable()
            .scaledToFit()
            .foregroundStyle(tint)
            .frame(width: size, height: size)
            .scaleEffect(x: pop ? 1.08 : 1, y: pop ? 0.94 : (inhale ? 1.025 : 1), anchor: .bottom)
            .rotationEffect(.degrees(pop ? motionTilt : 0))
            .offset(y: pop ? -size * 0.06 : 0)
            .accessibilityLabel("\(character.name), \(character.role)")
            .onAppear {
                guard breathing, !reduceMotion else { return }
                withAnimation(.easeInOut(duration: 2.4).repeatForever(autoreverses: true)) { inhale = true }
            }
            .onChange(of: trigger) { _ in
                guard !reduceMotion else { return }
                withAnimation(.spring(response: 0.22, dampingFraction: 0.5)) { pop = true }
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.22) {
                    withAnimation(.spring(response: 0.28, dampingFraction: 0.75)) { pop = false }
                }
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
