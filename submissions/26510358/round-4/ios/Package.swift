// swift-tools-version:5.9
// Builds the app's Core (Foundation only) on Linux or macOS, and a check that drives it against a running mini app:
//   swift run CoreCheck "<the [app] open link>"
// The iOS app itself is Ssadassa.xcodeproj; this package is only for checking Core without Xcode.
import PackageDescription

let package = Package(
    name: "SsadassaCore",
    platforms: [.macOS(.v13), .iOS(.v16)],
    targets: [
        .target(name: "SsadassaCore", path: "Ssadassa/Core"),
        .executableTarget(name: "CoreCheck", dependencies: ["SsadassaCore"], path: "CoreCheck"),
    ]
)
