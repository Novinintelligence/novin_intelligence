// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "novin_intelligence",
    platforms: [
        .iOS(.v15)
    ],
    products: [
        .library(name: "NovinIntelligence", targets: ["novin_intelligence"])
    ],
    targets: [
        .binaryTarget(
            name: "novin_intelligence",
            url: "https://raw.githubusercontent.com/Novinintelligence/novin_intelligence/main/artifacts/novin_intelligence.xcframework.zip",
            checksum: "93158d742b87531b1f77020c6692097b2cc8b09f535e0d41a687d29f517a4f76"
        )
    ]
)
