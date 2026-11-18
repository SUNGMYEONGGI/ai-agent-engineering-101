import SwiftUI
import UIKit

/// Character-led companion style: ivory paper, soft black ink, rounded type, one status color at a time.
/// Colors follow the character spec (#171717 body on #F8F7F3); dark mode inverts them.
enum Theme {
    static let paper = dynamic(light: 0xF8F7F3, dark: 0x0E0E0D)
    static let surface = dynamic(light: 0xFFFFFF, dark: 0x1A1A19)
    static let soft = dynamic(light: 0xEFEDE6, dark: 0x252523)
    static let ink = dynamic(light: 0x171717, dark: 0xF2F1EC)
    static let inkOn = dynamic(light: 0xF8F7F3, dark: 0x0E0E0D)      // text on an ink fill
    static let mute = dynamic(light: 0x77756E, dark: 0x9C9A93)
    static let line = dynamic(light: 0xE4E1D8, dark: 0x2E2E2B)
    static let ok = dynamic(light: 0x12A27A, dark: 0x34D399)
    static let warn = dynamic(light: 0xC98A00, dark: 0xFBBF24)
    static let fail = dynamic(light: 0xD93636, dark: 0xF87171)

    static let mono = Font.system(.footnote, design: .monospaced)
    static func rounded(_ style: Font.TextStyle, _ weight: Font.Weight = .regular) -> Font {
        .system(style, design: .rounded).weight(weight)
    }

    private static func dynamic(light: UInt32, dark: UInt32) -> Color {
        Color(uiColor: UIColor { $0.userInterfaceStyle == .dark ? UIColor(hex: dark) : UIColor(hex: light) })
    }
}

private extension UIColor {
    convenience init(hex: UInt32) {
        self.init(red: CGFloat((hex >> 16) & 0xFF) / 255, green: CGFloat((hex >> 8) & 0xFF) / 255,
                  blue: CGFloat(hex & 0xFF) / 255, alpha: 1)
    }
}

/// A rounded card on the paper background.
struct SoftCard<Content: View>: View {
    var padding: CGFloat = 16
    @ViewBuilder var content: Content

    var body: some View {
        content
            .padding(padding)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.surface, in: RoundedRectangle(cornerRadius: 22, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).stroke(Theme.line, lineWidth: 0.5))
            .shadow(color: .black.opacity(0.04), radius: 12, y: 6)
    }
}

/// Small status capsule: a dot and a few words.
struct StatusPill: View {
    let status: AppModel.Status

    var body: some View {
        HStack(spacing: 6) {
            Circle().fill(color).frame(width: 7, height: 7)
            Text(label).font(Theme.rounded(.caption, .medium)).foregroundStyle(Theme.mute)
        }
        .padding(.horizontal, 10).padding(.vertical, 5)
        .background(Theme.soft, in: Capsule())
    }

    private var color: Color {
        switch status { case .live: return Theme.ok; case .busy: return Theme.warn; case .offline: return Theme.fail; case .demo: return Theme.mute }
    }

    private var label: String {
        switch status {
        case .live: return "시장에서 거래 중"
        case .busy: return "생각하는 중"
        case .offline: return "연결 끊김"
        case .demo: return "데모"
        }
    }
}

/// Capsule button in ink or outline.
struct PillButtonStyle: ButtonStyle {
    var filled = true

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Theme.rounded(.subheadline, .semibold))
            .padding(.horizontal, 18).padding(.vertical, 12)
            .frame(minHeight: 46)
            .foregroundStyle(filled ? Theme.inkOn : Theme.ink)
            .background(filled ? Theme.ink : Theme.surface, in: Capsule())
            .overlay(Capsule().stroke(filled ? Color.clear : Theme.line))
            .scaleEffect(configuration.isPressed ? 0.97 : 1)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}

struct SectionTitle: View {
    let text: String
    var body: some View {
        Text(text).font(Theme.rounded(.footnote, .semibold)).foregroundStyle(Theme.mute)
            .frame(maxWidth: .infinity, alignment: .leading).padding(.leading, 4)
    }
}
