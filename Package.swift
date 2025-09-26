// swift-tools-version:5.7
import PackageDescription

let package = Package(
    name: "NovinIntelligence",
    platforms: [
        .iOS(.v15)
    ],
    products: [
        .library(
            name: "NovinIntelligence",
            targets: ["NovinIntelligence"]
        )
    ],
    targets: [
        .binaryTarget(
            name: "PythonSupport",
            path: "Python.xcframework"
        ),
        .target(
            name: "NovinPythonBridge",
            dependencies: ["PythonSupport"],
            path: "Sources/NovinPythonBridge",
            publicHeadersPath: "include",
            cSettings: [
                .headerSearchPath("include"),
                .headerSearchPath("../../Python.xcframework/ios-arm64_x86_64-simulator/include/python3.13"),
                .headerSearchPath("../../Python.xcframework/ios-arm64/include/python3.13"),
                .unsafeFlags([
                    "-fno-modules"
                ])
            ]
        ),
        .target(
            name: "NovinIntelligence",
            dependencies: [
                "NovinPythonBridge",
                "PythonSupport"
            ],
            path: "Sources/NovinIntelligence",
            resources: [
                .copy("Resources/python"),
                .copy("Resources/install_dependencies.py"),
                .copy("Resources/requirements.txt"),
                .copy("Resources/novin_ai_bridge.py")
            ],
            plugins: [
                // .plugin(name: "SetupAIDependencies")  // Disabled for reliable builds
                // Users should run: bash setup_novin_sdk.sh manually after cloning
            ]
        ),
        .plugin(
            name: "SetupAIDependencies",
            capability: .buildTool(),
            path: "Plugins/SetupAIDependencies"
        ),
        .testTarget(
            name: "NovinIntelligenceTests",
            dependencies: ["NovinIntelligence"]
        )
    ]
)