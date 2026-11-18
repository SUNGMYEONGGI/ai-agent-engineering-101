import Security
import SwiftUI

/// 싸다싸 가게: the native iOS app of the Round 4 agent. The agent and its mini app server run on the computer
/// (agent_kit.py run ... --app 8800); this app talks to the same API the kit's web page uses (Core/), and answers
/// the owner tools (app_show_card, app_owner_limits, app_ask_owner) and MeshKit consents natively.
@main
struct SsadassaApp: App {
    var body: some Scene {
        WindowGroup {
            RootView()
        }
    }
}

struct RootView: View {
    @State private var link: AppLink? = LinkKeychain.load().flatMap(AppLink.init)

    var body: some View {
        if let link {
            MainView(link: link) {
                LinkKeychain.save(nil)
                self.link = nil
            }
            .id(link)
        } else {
            LinkView { new in
                LinkKeychain.save(new.base.absoluteString + (new.accessCode.map { "/?k=\($0)" } ?? ""))
                link = new
            }
        }
    }
}

struct MainView: View {
    @StateObject private var model: AppModel
    @Environment(\.scenePhase) private var phase
    let disconnect: () -> Void

    init(link: AppLink, disconnect: @escaping () -> Void) {
        _model = StateObject(wrappedValue: AppModel(link: link, user: OwnerID.value))
        self.disconnect = disconnect
    }

    var body: some View {
        TabView {
            NavigationStack {
                ChatView()
                    .navigationBarTitleDisplayMode(.inline)
                    .toolbar { header }
            }
            .tabItem { Label("대화", systemImage: "bubble.left.and.bubble.right") }
            .badge(model.questions.count)

            NavigationStack {
                ShopView().navigationTitle("가게")
            }
            .tabItem { Label("가게", systemImage: "storefront") }

            NavigationStack {
                SettingsView(disconnect: disconnect).navigationTitle("설정")
            }
            .tabItem { Label("설정", systemImage: "slider.horizontal.3") }
        }
        .tint(Theme.ink)
        .environmentObject(model)
        .sheet(item: Binding(get: { model.consent }, set: { _ in })) { call in
            ConsentSheet(call: call) { model.answer(consent: call, approved: $0) }
        }
        .onAppear { model.start() }
        .onDisappear { model.stop() }
        .onChange(of: phase) { p in
            if p == .active { model.start() } else if p == .background { model.stop() }
        }
    }

    @ToolbarContentBuilder
    private var header: some ToolbarContent {
        ToolbarItem(placement: .principal) {
            HStack(spacing: 10) {
                ShopMark(size: 30)
                VStack(alignment: .leading, spacing: 1) {
                    Text(model.agentName).font(.subheadline.weight(.semibold))
                    StatusDot(status: model.status)
                }
            }
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
