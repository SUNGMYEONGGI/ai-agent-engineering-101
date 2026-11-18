import SwiftUI
import UIKit

/// Neutral grays, color only for status (the same rule as the Ouroboros console the kit's web app follows).
enum Theme {
    static let ink = Color.primary
    static let card = Color(uiColor: .secondarySystemBackground)
    static let line = Color(uiColor: .separator)
    static let mute = Color.secondary
    static let ok = Color.green
    static let warn = Color.orange
    static let fail = Color.red
    static let mono = Font.system(.footnote, design: .monospaced)
}

/// The shop's mark: "싸" on a dark rounded square.
struct ShopMark: View {
    var size: CGFloat = 36

    var body: some View {
        Text("싸")
            .font(.system(size: size * 0.5, weight: .bold))
            .foregroundStyle(Color(uiColor: .systemBackground))
            .frame(width: size, height: size)
            .background(Theme.ink, in: RoundedRectangle(cornerRadius: size * 0.28, style: .continuous))
    }
}

struct StatusDot: View {
    let status: AppModel.Status

    var body: some View {
        HStack(spacing: 6) {
            Circle().fill(color).frame(width: 7, height: 7)
            Text(label).font(.caption).foregroundStyle(Theme.mute)
        }
    }

    private var color: Color {
        switch status { case .live: return Theme.ok; case .busy: return Theme.warn; case .offline: return Theme.fail }
    }

    private var label: String {
        switch status {
        case .live: return "시장에서 거래 중"
        case .busy: return "답을 쓰는 중"
        case .offline: return "연결 끊김"
        }
    }
}

/// A titled section on a gray card, used by the shop and settings screens.
struct Panel<Content: View>: View {
    let title: String
    @ViewBuilder var content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title).font(.caption.weight(.semibold)).foregroundStyle(Theme.mute).textCase(.uppercase)
            VStack(alignment: .leading, spacing: 0) { content }
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Theme.card, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
    }
}

struct PanelRow: View {
    let title: String
    var detail: String = ""
    var mono = false

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title).font(mono ? Theme.mono : .subheadline)
            if !detail.isEmpty { Text(detail).font(.caption).foregroundStyle(Theme.mute).lineLimit(3) }
        }
        .padding(.horizontal, 14).padding(.vertical, 10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .overlay(alignment: .bottom) { Divider().padding(.leading, 14) }
    }
}
