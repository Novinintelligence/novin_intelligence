// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "novin_intelligence",
    platforms: [
        .iOS(.v15)
    ],
    products: [
        // Expose both the shim C module (NovinPythonBridge) and the binary framework module
        // so any target (including tests) can resolve `import NovinPythonBridge` during compile.
        .library(name: "NovinIntelligence", targets: ["NovinPythonBridge", "novin_intelligence"])    
    ],
    targets: [
        // Lightweight Clang module exposing NovinPythonBridge.h.
        // The actual symbol implementations are provided by the binary framework at link time.
        .target(
            name: "NovinPythonBridge",
            path: "Sources/NovinPythonBridge",
            publicHeadersPath: "include"
        ),
        .binaryTarget(
            name: "novin_intelligence",
            url: "https://github.com/Novinintelligence/novin_intelligence/releases/download/1.0.0/novin_intelligence.xcframework.zip",
            checksum: "93158d742b87531b1f77020c6692097b2cc8b09f535e0d41a687d29f517a4f76"
        )
    ]
)
