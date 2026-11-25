import Security
import SwiftUI

/// Hermes Shop: the native iOS app of the Round 4 agent. The agent and its mini app server run on the computer
/// (agent_kit.py run ... --app 8800); this app talks to the same API the kit's web page uses (Core/), and answers
/// the owner tools (app_show_card, app_owner_limits, app_ask_owner) and MeshKit consents natively.
///
/// Launch arguments (ios/run-simulator.sh uses them): `-demo` opens demo mode, `-link <url>` connects at once,
/// `-tab 0|1|2` opens on 대화/활동/나 (for simulator screenshots, which cannot tap).
///
/// QR / deep link: `ssadassa://<host>/?k=<code>` opens the app and connects to `https://<host>/?k=<code>`
/// (the iPhone camera offers "Hermes Shop에서 열기" for it; the scheme is registered in Info.plist).
@main
struct SsadassaApp: App {
    var body: some Scene {
        WindowGroup {
            RootView()
        }
    }
}

struct RootView: View {
    enum Mode: Equatable { case link, demo, live(AppLink) }
    @State private var mode: Mode = RootView.initialMode()

    var body: some View {
        content.onOpenURL { url in
            guard let link = RootView.link(from: url) else { return }
            LinkKeychain.save(link.base.absoluteString + (link.accessCode.map { "/?k=\($0)" } ?? ""))
            mode = .live(link)
        }
    }

    /// `ssadassa://app.example.com/?k=CODE` -> the https link it stands for.
    static func link(from url: URL) -> AppLink? {
        guard url.scheme == "ssadassa", var comps = URLComponents(url: url, resolvingAgainstBaseURL: false),
              comps.host != nil else { return nil }
        comps.scheme = "https"
        return comps.url.flatMap { AppLink($0.absoluteString) }
    }

    @ViewBuilder private var content: some View {
        switch mode {
        case .link:
            LinkView(connect: { new in
                LinkKeychain.save(new.base.absoluteString + (new.accessCode.map { "/?k=\($0)" } ?? ""))
                mode = .live(new)
            }, demo: { mode = .demo })
        case .demo:
            MainView(link: nil) { mode = .link }
        case .live(let link):
            MainView(link: link) {
                LinkKeychain.save(nil)
                mode = .link
            }
            .id(link)
        }
    }

    private static func initialMode() -> Mode {
        let args = ProcessInfo.processInfo.arguments
        if args.contains("-demo") { return .demo }
        if let i = args.firstIndex(of: "-link"), i + 1 < args.count, let link = AppLink(args[i + 1]) {
            LinkKeychain.save(link.base.absoluteString + (link.accessCode.map { "/?k=\($0)" } ?? ""))
            return .live(link)
        }
        if let saved = LinkKeychain.load().flatMap(AppLink.init) { return .live(saved) }
        return .link
    }
}

struct MainView: View {
    @StateObject private var model: AppModel
    @Environment(\.scenePhase) private var phase
    let disconnect: () -> Void

    init(link: AppLink?, disconnect: @escaping () -> Void) {
        _model = StateObject(wrappedValue: AppModel(link: link, user: OwnerID.value))
        self.disconnect = disconnect
    }

    var body: some View {
        TabView(selection: $model.tab) {
            ChatView()
                .tabItem { Label("대화", systemImage: "bubble.left.and.bubble.right") }
                .badge(model.pendingCount)
                .tag(0)
                .toolbarBackground(Theme.paper, for: .tabBar)
                .toolbarBackground(.visible, for: .tabBar)
            ActivityView()
                .tabItem { Label("활동", systemImage: "sparkles") }
                .tag(1)
                .toolbarBackground(Theme.paper, for: .tabBar)
                .toolbarBackground(.visible, for: .tabBar)
            SettingsView(disconnect: disconnect)
                .tabItem { Label("나", systemImage: "person.crop.circle") }
                .tag(2)
                .toolbarBackground(Theme.paper, for: .tabBar)
                .toolbarBackground(.visible, for: .tabBar)
        }
        .tint(Theme.ink)
        .environmentObject(model)
        .onAppear { model.start() }
        .onDisappear { model.stop() }
        .onChange(of: phase) { p in
            if p == .active { model.start() } else if p == .background { model.stop() }
        }
    }
}

/// The owner's chat name, made once per install.
enum OwnerID {
    static var value: String {
        if let v = UserDefaults.standard.string(forKey: "ssadassa.owner") { return v }
        let v = "owner-" + String(UUID().uuidString.prefix(4)).lowercased()
        UserDefaults.standard.set(v, forKey: "ssadassa.owner")
        return v
    }
}

/// The link holds the access code, so it lives in the Keychain, not in UserDefaults.
enum LinkKeychain {
    private static let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                               kSecAttrService as String: "ssadassa.applink"]

    static func load() -> String? {
        var q = query
        q[kSecReturnData as String] = true
        var out: AnyObject?
        guard SecItemCopyMatching(q as CFDictionary, &out) == errSecSuccess, let data = out as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    static func save(_ value: String?) {
        SecItemDelete(query as CFDictionary)
        guard let value else { return }
        var q = query
        q[kSecValueData as String] = Data(value.utf8)
        q[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlock
        SecItemAdd(q as CFDictionary, nil)
    }
}
